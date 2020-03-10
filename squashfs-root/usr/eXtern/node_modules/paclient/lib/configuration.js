const { isIP } = require('net');
const { execSync } = require('child_process');
const { readFileSync } = require('fs');
const { homedir } = require('os');
const { isAbsolute } = require('path');

const RE_SERVER_STRING =
  /^(?:\{([^}]+)\})?(?:(?:unix:)?(\/.+)|tcp(4|6)?:(.+))$/;
const RE_SERVER_PORT = /:(\d+)$/;
const RE_XPROP = /^PULSE_(SERVER|COOKIE)[^=]+= "(.+)"$/;
const RE_CONF = /^(default-server)|(cookie-file)[^=]+= "(.+)"$/i;

const matchLocalName = (function() {
  var localHostname;
  var dbusMachineId;
  return function matchLocalName(name) {
    if (localHostname === undefined) {
      localHostname = require('os').hostname() || null;
      try {
        dbusMachineId = readFileSync('/etc/machine-id', 'utf8');
      } catch (ex) {}
      if (!dbusMachineId) {
        try {
          dbusMachineId = readFileSync('/var/lib/dbus/machine-id', 'utf8');
        } catch (ex) {}
      }
      if (dbusMachineId)
        dbusMachineId = dbusMachineId.trim();
      if (!dbusMachineId)
        dbusMachineId = null;
    }

    return (name === localHostname || name === dbusMachineId);
  };
})();

function parseServerString(serverStr) {
  const ret = [];
  const addrs = serverStr.split(/[ \t]+/g);
  for (var i = 0; i < addrs.length; ++i) {
    var m = RE_SERVER_STRING.exec(addrs[i]);
    if (m !== null) {
      if (m[1] !== undefined && !matchLocalName(m[1]))
        continue;
      const unixPath = m[2];
      const tcpType = (m[3] && +m[3]);
      const tcpAddrPort = m[4];
      if (unixPath) {
        ret.push(['unix', unixPath]);
      } else {
        var ipType = isIP(tcpAddrPort);
        var ip;
        var port;
        if (ipType === 0) {
          // hostname, hostname:port, or ip:port
          m = RE_SERVER_PORT.exec(tcpAddrPort);
          if (m !== null) {
            ip = tcpAddrPort.slice(0, -m[0].length);
            port = +m[1];
            ipType = isIP(ip);
            if (ipType === 0) {
              // hostname:port
              ret.push(['host', tcpType, ip, port]);
            } else {
              // ip:port
              ret.push(['ip', ip, port]);
            }
          } else {
            // hostname
            ret.push(['host', tcpType, tcpAddrPort, DEFAULT_PORT]);
          }
        } else {
          // ip
          ret.push(['ip', tcpAddrPort, DEFAULT_PORT]);
        }
      }
    }
  }
  return ret;
}

const getEnvConfig = (function() {
  var ret;
  return function getEnvConfig() {
    if (ret === undefined) {
      const cookiePath = (typeof process.env.PULSE_COOKIE === 'string'
                          && process.env.PULSE_COOKIE) || null;
      var addrs;
      if (typeof process.env.PULSE_SERVER === 'string'
          && process.env.PULSE_SERVER.length > 0) {
        addrs = parseServerString(process.env.PULSE_SERVER);
      }
      if ((addrs && addrs.length > 0) || cookiePath)
        ret = { addrs, cookiePath };
      else
        ret = null;
    }
    return ret;
  };
})();

const getX11Config = (function() {
  var ret;
  return function getX11Config() {
    if (ret === undefined) {
      var addrs;
      var cookie;
      try {
        const out =
          execSync('xprop -root', { encoding: 'utf8' }).split(/\r?\n/g);
        for (var i = 0; i < out.length; ++i) {
          const m = RE_XPROP.exec(out[i]);
          if (m !== null) {
            if (m[1] === 'SERVER')
              addrs = parseServerString(m[2]);
            else
              cookie = m[2];
          }
        }
        if ((addrs && addrs.length > 0) || cookie)
          ret = { addrs, cookie };
        else
          ret = null;
      } catch (ex) {
        ret = null;
      }
    }
    return ret;
  };
})();

function parseConfig(path) {
  try {
    const lines = readFileSync(path, 'utf8').split(/\r?\n/g);
    const ret = {
      addrs: [],
      cookieFile: undefined,
      'auto-connect-localhost': undefined,
      'auto-connect-display': undefined
    };
    for (var i = 0; i < lines.length; ++i) {
      var line = lines[i];
      const m = /^[^#;]*/.exec(line);
      if (m === null)
        continue;
      line = m[0].trim();
      var equals;
      if (line.length === 0 || (equals = line.indexOf('=')) === -1)
        continue;
      const key = line.slice(0, equals).trim();
      const val = line.slice(equals + 1).trim();
      switch (key) {
        case 'default-server':
          ret.addrs = parseServerString(val);
          break;
        case 'cookie-file':
          ret.cookieFile = val;
          break;
        case 'auto-connect-localhost':
        case 'auto-connect-display':
          ret[key] = (val === '1' || val === 'yes' || val === 'on'
                      || val === 'true');
          break;
      }
    }
    return ret;
  } catch (ex) {
    return null;
  }
}

const getHomePath = (function() {
  var home;
  return function getHomePath() {
    if (home === undefined) {
      if (typeof process.env.HOME === 'string'
          && process.env.HOME.length > 0) {
        home = process.env.HOME;
      } else if (typeof process.env.USERPROFILE === 'string'
                 && process.env.USERPROFILE.length > 0) {
        home = process.env.USERPROFILE;
      } else {
        home = homedir();
      }
      if (!home || !isAbsolute(home))
        home = null;
    }
    return home;
  };
})();

const getConfigHomePath = (function() {
  var configHome;
  return function getConfigHomePath() {
    if (configHome === undefined) {
      if (typeof process.env.XDG_CONFIG_HOME === 'string'
          && process.env.XDG_CONFIG_HOME.length > 0) {
        configHome = process.env.XDG_CONFIG_HOME;
      } else {
        const home = getHomePath();
        if (typeof home === 'string')
          configHome = `${home}/.config/pulse`;
        else
          configHome = null;
      }
    }
    return configHome;
  };
})();

const getRuntimePath = (function() {
  var runtimePath;
  return function getRuntimePath() {
    if (runtimePath === undefined) {
      if (typeof process.env.PULSE_RUNTIME_PATH === 'string'
          && process.env.PULSE_RUNTIME_PATH) {
        runtimePath = process.env.PULSE_RUNTIME_PATH;
      } else if (typeof process.env.XDG_RUNTIME_DIR === 'string'
          && process.env.XDG_RUNTIME_DIR.length > 0) {
        runtimePath = process.env.XDG_RUNTIME_DIR;
      } else {
        runtimePath = null;
      }
    }
    return runtimePath;
  };
})();

function readCookie(hexStr) {
  if (hexStr.length !== 512)
    return null;
  const cookie = Buffer.from(hexStr, 'hex');
  return (cookie.length === 256 ? cookie : null);
}

function readCookieFile(path) {
  try {
    return readCookie(readFileSync(path, 'ascii').trim());
  } catch (ex) {
    return null;
  }
}

const getCookie = (function() {
  var cookie;
  return function getCookie() {
    // This breaks a tad from PulseAudio's cookie lookup mechanism in that
    // PulseAudio only considers an application-level cookie value/file *after*
    // no cookie was found in either the environment *or* X11.
    if (cookie === undefined) {
      const configHome = getConfigHomePath();

      const envConfig = getEnvConfig();
      if (envConfig && envConfig.cookiePath) {
        if (!isAbsolute(envConfig.cookiePath)) {
          if (configHome) {
            envConfig.cookiePath = `${configHome}/${envConfig.cookiePath}`;
            if (cookie = readCookieFile(envConfig.cookiePath))
              return cookie;
          }
        } else if (cookie = readCookieFile(envConfig.cookiePath)) {
          return cookie;
        }
      }

      const x11Config = getX11Config();
      if (x11Config && x11Config.cookie
          && (cookie = readCookie(x11Config.cookie))) {
        return cookie;
      }

      const fileConfig = getFileConfig();
      if (fileConfig && fileConfig.cookiePath) {
        if (!isAbsolute(fileConfig.cookiePath)) {
          if (configHome) {
            fileConfig.cookiePath = `${configHome}/${fileConfig.cookiePath}`;
            if (cookie = readCookieFile(fileConfig.cookiePath))
              return cookie;
          }
        } else if (cookie = readCookieFile(fileConfig.cookiePath)) {
          return cookie;
        }
      }

      if (configHome && (cookie = readCookieFile(`${configHome}/cookie`)))
        return cookie;

      const home = getHomePath();
      if (home && (cookie = readCookieFile(`${home}/.pulse-cookie`)))
        return cookie;

      cookie = null;
    }
    return cookie;
  };
})();

const getFileConfig = (function() {
  var cfg;
  return function getFileConfig() {
    if (cfg === undefined) {
      var parsed;
      // Try env
      if (typeof process.env.PULSE_CLIENTCONFIG === 'string'
          && process.env.PULSE_CLIENTCONFIG.length > 0) {
        parsed = parseConfig(process.env.PULSE_CLIENTCONFIG);
        return (cfg = parsed);
      }
      // Try local paths
      if (typeof process.env.PULSE_CONFIG_PATH === 'string'
          && process.env.PULSE_CONFIG_PATH.length > 0) {
        parsed = parseConfig(process.env.PULSE_CONFIG_PATH);
        if (parsed !== null)
          return (cfg = parsed);
      } else {
        var homePath = getHomePath();
        if (typeof homePath !== 'string')
          return (cfg = null);
        parsed = parseConfig(`${homePath}/.pulse/client.conf`);
        if (parsed !== null)
          return (cfg = parsed);
        parsed = parseConfig(`${homePath}/.config/pulse/client.conf`);
        if (parsed !== null)
          return (cfg = parsed);
      }
      // Try common global paths -- this is more of a guess since typically the
      // real global path is baked into the PulseAudio library during build time
      parsed = parseConfig('/etc/pulse/client.conf');
      if (parsed !== null)
        return (cfg = parsed);
      parsed = parseConfig('/usr/local/etc/pulse/client.conf');
      return (cfg = parsed);
    }
    return cfg;
  };
})();


module.exports = {
  getAddrs: function getAddrs() {
    var addrs;
    const fileConfig = getFileConfig();
    const x11Config = getX11Config();
    const envConfig = getEnvConfig();
    if (envConfig && envConfig.addrs.length > 0) {
      addrs = envConfig.addrs;
    } else if (x11Config && x11Config.addrs.length > 0) {
      addrs = x11Config.addrs;
    } else if (fileConfig && fileConfig.addrs.length > 0) {
      addrs = fileConfig.addrs;
    } else {
      addrs = [];
      const autoConnectLocalhost =
        ((envConfig && envConfig['auto-connect-localhost'] === true)
         || (x11Config && x11Config['auto-connect-localhost'] === true)
         || (fileConfig && fileConfig['auto-connect-localhost'] === true));
      if (autoConnectLocalhost) {
        addrs.unshift(['ip', 6, '::1', DEFAULT_PORT]);
        addrs.unshift(['ip', 4, '127.0.0.1', DEFAULT_PORT]);
      }

      // Again, this one is more of a guess because it's typically baked into
      // PulseAudio at compile time
      addrs.unshift(['unix', '/var/run/pulse/native']);

      const runtimePath = getRuntimePath();
      if (runtimePath && isAbsolute(runtimePath))
        addrs.unshift(['unix', `${runtimePath}/pulse/native`]);
    }

    return addrs;
  },
  getCookie
};

// TODO:
//   * Support implicit writing of a new cookie to disk when one does not exist?
//   * Support other non-SHM/MemFD-related requests
//   * Support SHM-related requests?

const EventEmitter = require('events');
const { inherits } = require('util');
const { Socket, isIP } = require('net');
const { lookup } = require('dns');

const { descriptions:errors } = require('./errors.js');
const { getAddrs, getCookie } = require('./configuration.js');
const {
  PA_COMMAND_ERROR, PA_COMMAND_REPLY, PA_COMMAND_SUBSCRIBE_EVENT,
  PA_COMMAND_AUTH, PA_COMMAND_SET_CLIENT_NAME, PA_COMMAND_GET_MODULE_INFO_LIST,
  PA_COMMAND_GET_CLIENT_INFO_LIST, PA_COMMAND_GET_SINK_INFO_LIST,
  PA_COMMAND_GET_SOURCE_INFO_LIST, PA_COMMAND_GET_SINK_INPUT_INFO_LIST,
  PA_COMMAND_GET_SOURCE_OUTPUT_INFO_LIST, PA_COMMAND_GET_CARD_INFO_LIST,
  PA_COMMAND_LOOKUP_SINK, PA_COMMAND_LOOKUP_SOURCE, PA_COMMAND_SET_SINK_VOLUME,
  PA_COMMAND_SET_SOURCE_VOLUME, PA_COMMAND_SET_SINK_INPUT_VOLUME,
  PA_COMMAND_SET_SOURCE_OUTPUT_VOLUME, PA_COMMAND_SET_SINK_MUTE,
  PA_COMMAND_SET_SOURCE_MUTE, PA_COMMAND_SET_SINK_INPUT_MUTE,
  PA_COMMAND_SET_SOURCE_OUTPUT_MUTE, PA_COMMAND_SUSPEND_SINK,
  PA_COMMAND_SUSPEND_SOURCE, PA_COMMAND_SET_DEFAULT_SINK,
  PA_COMMAND_SET_DEFAULT_SOURCE, PA_COMMAND_KILL_CLIENT,
  PA_COMMAND_KILL_SINK_INPUT, PA_COMMAND_KILL_SOURCE_OUTPUT,
  PA_COMMAND_MOVE_SINK_INPUT, PA_COMMAND_MOVE_SOURCE_OUTPUT,
  PA_COMMAND_SET_SINK_PORT, PA_COMMAND_SET_SOURCE_PORT,
  PA_COMMAND_SET_CARD_PROFILE, PA_COMMAND_UPDATE_CLIENT_PROPLIST,
  PA_COMMAND_REMOVE_CLIENT_PROPLIST, PA_COMMAND_SUBSCRIBE,
  PA_COMMAND_GET_SINK_INPUT_INFO, PA_COMMAND_GET_SOURCE_OUTPUT_INFO,
  PA_COMMAND_GET_SOURCE_INFO, PA_COMMAND_GET_SINK_INFO,
  PA_COMMAND_GET_CLIENT_INFO, PA_COMMAND_GET_MODULE_INFO,
  PA_COMMAND_GET_CARD_INFO, PA_COMMAND_GET_SERVER_INFO
} = require('./packet-types.js');

const PA_TAG_INVALID = 0;
const PA_TAG_STRING = 116;
const PA_TAG_STRING_NULL = 78;
const PA_TAG_U32 = 76;
const PA_TAG_U8 = 66;
const PA_TAG_U64 = 82;
const PA_TAG_S64 = 114;
const PA_TAG_SAMPLE_SPEC = 97;
const PA_TAG_ARBITRARY = 120;
const PA_TAG_BOOLEAN_TRUE = 49;
const PA_TAG_BOOLEAN_FALSE = 48;
const PA_TAG_BOOLEAN = PA_TAG_BOOLEAN_TRUE;
const PA_TAG_TIMEVAL = 84;
const PA_TAG_USEC = 85/* 64bit unsigned */;
const PA_TAG_CHANNEL_MAP = 109;
const PA_TAG_CVOLUME = 118;
const PA_TAG_PROPLIST = 80;
const PA_TAG_VOLUME = 86;
const PA_TAG_FORMAT_INFO = 102;

const PA_SUBSCRIPTION_EVENT_SINK = 0x0000;
const PA_SUBSCRIPTION_EVENT_SOURCE = 0x0001;
const PA_SUBSCRIPTION_EVENT_SINK_INPUT = 0x0002;
const PA_SUBSCRIPTION_EVENT_SOURCE_OUTPUT = 0x0003;
const PA_SUBSCRIPTION_EVENT_MODULE = 0x0004;
const PA_SUBSCRIPTION_EVENT_CLIENT = 0x0005;
const PA_SUBSCRIPTION_EVENT_SAMPLE_CACHE = 0x0006;
const PA_SUBSCRIPTION_EVENT_SERVER = 0x0007;
const PA_SUBSCRIPTION_EVENT_AUTOLOAD = 0x0008;
const PA_SUBSCRIPTION_EVENT_CARD = 0x0009;
const PA_SUBSCRIPTION_EVENT_FACILITY_MASK = 0x000F;

const PA_SUBSCRIPTION_EVENT_NEW = 0x0000;
const PA_SUBSCRIPTION_EVENT_CHANGE = 0x0010;
const PA_SUBSCRIPTION_EVENT_REMOVE = 0x0020;
const PA_SUBSCRIPTION_EVENT_TYPE_MASK = 0x0030;

const PA_SINK_HW_VOLUME_CTRL = 0x0001;
const PA_SINK_LATENCY = 0x0002;
const PA_SINK_HARDWARE = 0x0004;
const PA_SINK_NETWORK = 0x0008;
const PA_SINK_HW_MUTE_CTRL = 0x0010;
const PA_SINK_DECIBEL_VOLUME = 0x0020;
const PA_SINK_FLAT_VOLUME = 0x0040;
const PA_SINK_DYNAMIC_LATENCY = 0x0080;
const PA_SINK_SET_FORMATS = 0x0100;


const DNS_4ONLY = { family: 4 };
const DNS_6ONLY = { family: 6 };
const DEFAULT_PORT = 4713;
const PROTOCOL_VERSION = 32;
const DEFAULT_CLIENT_PROPS = { application: { name: 'paclient.js' } };
const PACKET_STATIC_FIELDS = Buffer.from([
  0xFF, 0xFF, 0xFF, 0xFF,
  0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00
]);



function PAClient() {
  EventEmitter.call(this);
  this._socket = null;
  this._reqid = 0;
  this._reqs = null;
  this._index = -1;
  this._serverVer = -1;
}
inherits(PAClient, EventEmitter);

PAClient.prototype.connect = function(config) {
  if (this._socket)
    return;

  var addrs = [];
  var cookie;
  var props;
  if (typeof config === 'object' && config !== null) {
    if (typeof config.path === 'string' && config.path.length > 0) {
      addrs.push(['unix', config.path]);
    } else if (typeof config.host === 'string' && config.host.length > 0) {
      var port = DEFAULT_PORT;
      if (typeof config.port === 'number' && isFinite(config.port))
        port = config.port;
      addrs.push(['host', undefined, config.host, port]);
    }

    cookie = config.cookie;
    if (cookie !== undefined) {
      if (typeof cookie === 'string') {
        if (cookie.length === 512) {
          cookie = Buffer.from(cookie, 'hex');
        } else if (cookie.length === 256) {
          cookie = Buffer.from(cookie, 'latin1');
        } else {
          throw new Error(
            'cookie strings must be 512 byte hex or 256 byte binary'
          );
        }
      } else if (!Buffer.isBuffer(cookie) && cookie !== null) {
        throw new Error('cookie must be a Buffer or hex/binary string');
      }
    }

    if (typeof config.properties === 'object' && config.properties !== null)
      props = config.properties;
  }

  if (addrs.length === 0)
    addrs = getAddrs();

  if (addrs.length === 0)
    throw new Error('No host or path to connect to');

  if (cookie === undefined)
    cookie = getCookie();

  if (props === undefined)
    props = DEFAULT_CLIENT_PROPS;

  nextAddr(this, addrs, cookie, props);
};

PAClient.prototype.end = function() {
  if (this._socket && this._socket.writable)
    this._socket.end();
};

PAClient.prototype.getModules = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_MODULE_INFO_LIST, cb);
};

PAClient.prototype.getClients = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_CLIENT_INFO_LIST, cb);
};

PAClient.prototype.getSinks = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_SINK_INFO_LIST, cb);
};

PAClient.prototype.getSources = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_SOURCE_INFO_LIST, cb);
};

PAClient.prototype.getSinkInputs = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_SINK_INPUT_INFO_LIST, cb);
};

PAClient.prototype.getSourceOutputs = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_SOURCE_OUTPUT_INFO_LIST, cb);
};

PAClient.prototype.getCards = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_CARD_INFO_LIST, cb);
};

PAClient.prototype.getServerInfo = function(cb) {
  sendSimplePacket(this, PA_COMMAND_GET_SERVER_INFO, cb);
};

PAClient.prototype.getModuleByIndex = function(index, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid module index');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_GET_MODULE_INFO;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  this._socket.write(buf);
};

PAClient.prototype.getClientByIndex = function(index, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid client index');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_GET_CLIENT_INFO;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  this._socket.write(buf);
};

PAClient.prototype.getSink = function(criteria, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid sink index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Sink criteria must be a name or index');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(36);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(36 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_GET_SINK_INFO;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    buf.fill(0xFF, 31, 35);
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - 1] = 0;
    }
  }

  this._socket.write(buf);
};

PAClient.prototype.getSource = function(criteria, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid source index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Source criteria must be a name or index');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(36);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(36 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_GET_SOURCE_INFO;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - 1] = 0;
    }
  }

  this._socket.write(buf);
};

PAClient.prototype.getSinkInputByIndex = function(index, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid sink input index');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_GET_SINK_INPUT_INFO;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  this._socket.write(buf);
};

PAClient.prototype.getSourceOutputByIndex = function(index, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid source output index');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_GET_SOURCE_OUTPUT_INFO;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  this._socket.write(buf);
};

PAClient.prototype.getCard = function(criteria, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid card index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Card criteria must be a name or index');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(36);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(36 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_GET_CARD_INFO;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - 1] = 0;
    }
  }

  this._socket.write(buf);
};

PAClient.prototype.getSinkIndexByName = function(name, cb) {
  if (typeof name !== 'string')
    throw new Error('Invalid/Missing sink name');
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (name.length === 0)
    buf = Buffer.allocUnsafe(31);
  else
    buf = Buffer.allocUnsafe(31 + Buffer.byteLength(name) + 1);

  buf.writeUInt32BE(buf.length - 20, 0, true);  
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_LOOKUP_SINK;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  if (name.length === 0) {
    buf[30] = PA_TAG_STRING_NULL;
  } else {
    buf[30] = PA_TAG_STRING;
    buf.write(name, 31);
    buf[buf.length - 1] = 0;
  }

  this._socket.write(buf);
};

PAClient.prototype.getSourceIndexByName = function(name, cb) {
  if (typeof name !== 'string')
    throw new Error('Invalid/Missing source name');
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (name.length === 0)
    buf = Buffer.allocUnsafe(31);
  else
    buf = Buffer.allocUnsafe(31 + Buffer.byteLength(name) + 1);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_LOOKUP_SOURCE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  if (name.length === 0) {
    buf[30] = PA_TAG_STRING_NULL;
  } else {
    buf[30] = PA_TAG_STRING;
    buf.write(name, 31);
    buf[buf.length - 1] = 0;
  }

  this._socket.write(buf);
};

PAClient.prototype.setSinkVolumes = function(criteria, levels, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid sink index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Sink criteria must be a name or index');
  } else if (!Array.isArray(levels)) {
    throw new Error('Volume levels argument must be an array');
  } else if (levels.length === 0 || levels.length > 255) {
    throw new Error('Invalid volume level count (must be between 1 and 255)');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  const levelLen = levels.length * 4;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(38 + levelLen);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(38 + len + levelLen);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SINK_VOLUME;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - levelLen - 1] = 0;
    }
  }

  var p = buf.length - levelLen;
  buf[p++] = PA_TAG_CVOLUME;
  buf[p++] = levels.length;
  for (var i = 0; i < levels.length; ++i, p += 4) {
    const val = levels[i];
    if (typeof val !== 'number' || val < 0 || val > 0xFFFFFFFF)
      throw new Error('Invalid volume level: ' + val);
    buf.writeUInt32BE(val, p, true);
  }

  this._socket.write(buf);
};

PAClient.prototype.setSourceVolumes = function(criteria, levels, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid source index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Source criteria must be a name or index');
  } else if (!Array.isArray(levels)) {
    throw new Error('Volume levels argument must be an array');
  } else if (levels.length === 0 || levels.length > 255) {
    throw new Error('Invalid volume level count (must be between 1 and 255)');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  const levelLen = levels.length * 4;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(38 + levelLen);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(38 + len + levelLen);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SOURCE_VOLUME;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - levelLen - 1] = 0;
    }
  }

  var p = buf.length - levelLen;
  buf[p++] = PA_TAG_CVOLUME;
  buf[p++] = levels.length;
  for (var i = 0; i < levels.length; ++i, p += 4) {
    const val = levels[i];
    if (typeof val !== 'number' || val < 0 || val > 0xFFFFFFFF)
      throw new Error('Invalid volume level: ' + val);
    buf.writeUInt32BE(val, p, true);
  }

  this._socket.write(buf);
};

PAClient.prototype.setSinkInputVolumesByIndex = function(index, levels, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid sink input index');
  else if (!Array.isArray(levels))
    throw new Error('Volume levels argument must be an array');
  else if (levels.length === 0 || levels.length > 255)
    throw new Error('Invalid volume level count (must be between 1 and 255)');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(37 + (levels.length * 4));

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SINK_INPUT_VOLUME;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  buf[32] = PA_TAG_CVOLUME;
  buf[33] = levels.length;
  var p = 34;
  for (var i = 0; i < levels.length; ++i, p += 4) {
    const val = levels[i];
    if (typeof val !== 'number' || val < 0 || val > 0xFFFFFFFF)
      throw new Error('Invalid volume level: ' + val);
    buf.writeUInt32BE(val, p, true);
  }

  this._socket.write(buf);
};

PAClient.prototype.setSourceOutputVolumesByIndex = function(index, levels, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid source output index');
  else if (!Array.isArray(levels))
    throw new Error('Volume levels argument must be an array');
  else if (levels.length === 0 || levels.length > 255)
    throw new Error('Invalid volume level count (must be between 1 and 255)');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(37 + (levels.length * 4));

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SOURCE_OUTPUT_VOLUME;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  buf[32] = PA_TAG_CVOLUME;
  buf[33] = levels.length;
  var p = 34;
  for (var i = 0; i < levels.length; ++i, p += 4) {
    const val = levels[i];
    if (typeof val !== 'number' || val < 0 || val > 0xFFFFFFFF)
      throw new Error('Invalid volume level: ' + val);
    buf.writeUInt32BE(val, p, true);
  }

  this._socket.write(buf);
};

PAClient.prototype.setSinkMute = function(criteria, muted, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid sink index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Sink criteria must be a name or index');
  } else if (typeof muted !== 'boolean') {
    throw new Error('Muted argument must be a boolean');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(37);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(37 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SINK_MUTE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    buf.fill(0xFF, 31, 35);
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - 2] = 0;
    }
  }

  buf[buf.length - 1] = (muted ? PA_TAG_BOOLEAN_TRUE : PA_TAG_BOOLEAN_FALSE);

  this._socket.write(buf);
};

PAClient.prototype.setSourceMute = function(criteria, muted, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid source index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Source criteria must be a name or index');
  } else if (typeof muted !== 'boolean') {
    throw new Error('Muted argument must be a boolean');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(37);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(37 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SOURCE_MUTE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    buf.fill(0xFF, 31, 35);
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - 2] = 0;
    }
  }

  buf[buf.length - 1] = (muted ? PA_TAG_BOOLEAN_TRUE : PA_TAG_BOOLEAN_FALSE);

  this._socket.write(buf);
};

PAClient.prototype.setSinkInputMuteByIndex = function(index, muted, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid sink input index');
  else if (typeof muted !== 'boolean')
    throw new Error('Muted argument must be a boolean');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(36);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SINK_INPUT_MUTE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  buf[35] = (muted ? PA_TAG_BOOLEAN_TRUE : PA_TAG_BOOLEAN_FALSE);

  this._socket.write(buf);
};

PAClient.prototype.setSourceOutputMuteByIndex = function(index, muted, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid source output index');
  else if (typeof muted !== 'boolean')
    throw new Error('Muted argument must be a boolean');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(36);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SOURCE_OUTPUT_MUTE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  buf[35] = (muted ? PA_TAG_BOOLEAN_TRUE : PA_TAG_BOOLEAN_FALSE);

  this._socket.write(buf);
};

PAClient.prototype.setSinkSuspend = function(criteria, suspended, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid sink index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Sink criteria must be a name or index');
  } else if (typeof muted !== 'boolean') {
    throw new Error('Muted argument must be a boolean');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(37);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(37 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SUSPEND_SINK;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    buf.fill(0xFF, 31, 35);
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - 2] = 0;
    }
  }

  buf[buf.length - 1] = (muted ? PA_TAG_BOOLEAN_TRUE : PA_TAG_BOOLEAN_FALSE);

  this._socket.write(buf);
};

PAClient.prototype.setSourceSuspend = function(criteria, suspended, cb) {
  if (typeof criteria === 'number') {
    if (criteria < 0 || criteria > 0xFFFFFFFE)
      throw new Error('Invalid source index');
  } else if (typeof criteria !== 'string') {
    throw new Error('Source criteria must be a name or index');
  } else if (typeof muted !== 'boolean') {
    throw new Error('Muted argument must be a boolean');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof criteria === 'number') {
    buf = Buffer.allocUnsafe(37);
  } else {
    var len = Buffer.byteLength(criteria);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(37 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SUSPEND_SOURCE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  if (typeof criteria === 'number') {
    buf.writeUInt32BE(criteria, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
  } else {
    buf.fill(0xFF, 31, 35);
    if (criteria.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(criteria, 36);
      buf[buf.length - 2] = 0;
    }
  }

  buf[buf.length - 1] = (muted ? PA_TAG_BOOLEAN_TRUE : PA_TAG_BOOLEAN_FALSE);

  this._socket.write(buf);
};

PAClient.prototype.setDefaultSinkByName = function(name, cb) {
  if (typeof name !== 'string')
    throw new Error('Sink name must be a string');
  if (this._index === -1)
    throw new Error('Not ready');

  var nameLen = Buffer.byteLength(name);
  if (nameLen > 0)
    ++nameLen;
  const buf = Buffer.allocUnsafe(31 + nameLen);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_DEFAULT_SINK;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  if (nameLen === 0) {
    buf[30] = PA_TAG_STRING_NULL;
  } else {
    buf[30] = PA_TAG_STRING;
    buf.write(name, 31);
  }

  this._socket.write(buf);
};

PAClient.prototype.setDefaultSourceByName = function(name, cb) {
  if (typeof name !== 'string')
    throw new Error('Source name must be a string');
  if (this._index === -1)
    throw new Error('Not ready');

  var nameLen = Buffer.byteLength(name);
  if (nameLen > 0)
    ++nameLen;
  const buf = Buffer.allocUnsafe(31 + nameLen);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_DEFAULT_SOURCE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  if (nameLen === 0) {
    buf[30] = PA_TAG_STRING_NULL;
  } else {
    buf[30] = PA_TAG_STRING;
    buf.write(name, 31);
  }

  this._socket.write(buf);
};

PAClient.prototype.killClientByIndex = function(index, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid client index');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_KILL_CLIENT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  this._socket.write(buf);
};

PAClient.prototype.killSinkInputByIndex = function(index, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid sink input index');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_KILL_SINK_INPUT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  this._socket.write(buf);
};

PAClient.prototype.killSourceOutputByIndex = function(index, cb) {
  if (typeof index !== 'number' || index < 0 || index > 0xFFFFFFFE)
    throw new Error('Invalid source output index');
  if (this._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_KILL_SOURCE_OUTPUT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(index, 31, true);

  this._socket.write(buf);
};

PAClient.prototype.moveSinkInput = function(sinkInputIndex, destSink, cb) {
  if (typeof sinkInputIndex !== 'number' || sinkInputIndex < 0
      || sinkInputIndex > 0xFFFFFFFE) {
    throw new Error('Invalid sink input index');
  } else if (typeof destSink === 'number') {
    if (destSink < 0 || destSink > 0xFFFFFFFE)
      throw new Error('Invalid destination sink index');
  } else if (typeof destSink !== 'string') {
    throw new Error('Destination sink must be a name or index');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof destSink === 'number') {
    buf = Buffer.allocUnsafe(41);
  } else {
    var len = Buffer.byteLength(destSink);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(41 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_MOVE_SINK_INPUT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(sinkInputIndex, 31, true);

  buf[35] = PA_TAG_U32;
  if (typeof destSink === 'number') {
    buf.writeUInt32BE(destSink, 36, true);
    buf[40] = PA_TAG_STRING_NULL;
  } else {
    buf.fill(0xFF, 36, 40);
    if (destSink.length === 0) {
      buf[40] = PA_TAG_STRING_NULL;
    } else {
      buf[40] = PA_TAG_STRING;
      buf.write(destSink, 41);
      buf[buf.length - 1] = 0;
    }
  }

  this._socket.write(buf);
};

PAClient.prototype.moveSourceOutput =
function(sourceOutputIndex, destSource, cb) {
  if (typeof sourceOutputIndex !== 'number' || sourceOutputIndex < 0
      || sourceOutputIndex > 0xFFFFFFFE) {
    throw new Error('Invalid source output index');
  } else if (typeof destSource === 'number') {
    if (destSource < 0 || destSource > 0xFFFFFFFE)
      throw new Error('Invalid destination source index');
  } else if (typeof destSource !== 'string') {
    throw new Error('Destination source must be a name or index');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var buf;
  if (typeof destSource === 'number') {
    buf = Buffer.allocUnsafe(41);
  } else {
    var len = Buffer.byteLength(destSource);
    if (len > 0)
      ++len;
    buf = Buffer.allocUnsafe(41 + len);
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_MOVE_SOURCE_OUTPUT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(sourceOutputIndex, 31, true);

  buf[35] = PA_TAG_U32;
  if (typeof destSource === 'number') {
    buf.writeUInt32BE(destSource, 36, true);
    buf[40] = PA_TAG_STRING_NULL;
  } else {
    buf.fill(0xFF, 36, 40);
    if (destSource.length === 0) {
      buf[40] = PA_TAG_STRING_NULL;
    } else {
      buf[40] = PA_TAG_STRING;
      buf.write(destSource, 41);
      buf[buf.length - 1] = 0;
    }
  }

  this._socket.write(buf);
};

PAClient.prototype.setSinkPort = function(sink, portName, cb) {
  if (typeof sink === 'number') {
    if (sink < 0 || sink > 0xFFFFFFFE)
      throw new Error('Invalid sink index');
  } else if (typeof sink !== 'string') {
    throw new Error('Sink must be a name or index');
  } else if (typeof portName !== 'string') {
    throw new Error('Port name must be a string');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var total = 36;
  if (typeof sink !== 'number') {
    var sinkLen = Buffer.byteLength(sink);
    if (sinkLen > 0)
      ++sinkLen;
    total += sinkLen;
  }
  if (portName.length > 0)
    total += Buffer.byteLength(portName) + 1;
  const buf = Buffer.allocUnsafe(total);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SINK_PORT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  var p;
  if (typeof sink === 'number') {
    buf.writeUInt32BE(sink, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
    p = 36;
  } else {
    buf.fill(0xFF, 31, 35);
    if (sink.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
      p = 36;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(sink, 36);
      buf[36 + sinkLen] = 0;
      p = 36 + sinkLen + 1;
    }
  }

  if (portName.length === 0) {
    buf[p] = PA_TAG_STRING_NULL;
  } else {
    buf[p++] = PA_TAG_STRING;
    buf.write(portName, p);
  }

  this._socket.write(buf);
};

PAClient.prototype.setSourcePort = function(source, portName, cb) {
  if (typeof source === 'number') {
    if (source < 0 || source > 0xFFFFFFFE)
      throw new Error('Invalid source index');
  } else if (typeof source !== 'string') {
    throw new Error('Source must be a name or index');
  } else if (typeof portName !== 'string') {
    throw new Error('Port name must be a string');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var total = 36;
  if (typeof source !== 'number') {
    var sourceLen = Buffer.byteLength(source);
    if (sourceLen > 0)
      ++sourceLen;
    total += sourceLen;
  }
  if (portName.length > 0)
    total += Buffer.byteLength(portName) + 1;
  const buf = Buffer.allocUnsafe(total);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SOURCE_PORT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  var p;
  if (typeof source === 'number') {
    buf.writeUInt32BE(source, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
    p = 36;
  } else {
    buf.fill(0xFF, 31, 35);
    if (source.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
      p = 36;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(source, 36);
      buf[36 + sourceLen] = 0;
      p = 36 + sourceLen + 1;
    }
  }

  if (portName.length === 0) {
    buf[p] = PA_TAG_STRING_NULL;
  } else {
    buf[p++] = PA_TAG_STRING;
    buf.write(portName, p);
  }

  this._socket.write(buf);
};

PAClient.prototype.setCardProfile = function(card, profile, cb) {
  if (typeof card === 'number') {
    if (card < 0 || card > 0xFFFFFFFE)
      throw new Error('Invalid card index');
  } else if (typeof card !== 'string') {
    throw new Error('Card must be a name or index');
  } else if (typeof profile !== 'string') {
    throw new Error('Profile name must be a string');
  }
  if (this._index === -1)
    throw new Error('Not ready');

  var total = 36;
  if (typeof card !== 'number') {
    var cardLen = Buffer.byteLength(card);
    if (cardLen > 0)
      ++cardLen;
    total += cardLen;
  }
  if (profile.length > 0)
    total += Buffer.byteLength(profile) + 1;
  const buf = Buffer.allocUnsafe(total);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_SOURCE_PORT;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  var p;
  if (typeof card === 'number') {
    buf.writeUInt32BE(card, 31, true);
    buf[35] = PA_TAG_STRING_NULL;
    p = 36;
  } else {
    buf.fill(0xFF, 31, 35);
    if (card.length === 0) {
      buf[35] = PA_TAG_STRING_NULL;
      p = 36;
    } else {
      buf[35] = PA_TAG_STRING;
      buf.write(card, 36);
      buf[36 + cardLen] = 0;
      p = 36 + cardLen + 1;
    }
  }

  if (profile.length === 0) {
    buf[p] = PA_TAG_STRING_NULL;
  } else {
    buf[p++] = PA_TAG_STRING;
    buf.write(profile, p);
  }

  this._socket.write(buf);
};

PAClient.prototype.updateClientProperties = function(props, mode, cb) {
  if (typeof props !== 'object' || props === null)
    throw new Error('Properties argument must be an object');
  if (this._index === -1)
    throw new Error('Not ready');

  const propArray = propListToArray(props);
  const propLen = calcPropArrayLen(propArray);

  const buf = Buffer.allocUnsafe(35 + propLen);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_UPDATE_CLIENT_PROPLIST;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  var modeRaw;
  switch (mode) {
    case 'set':
      modeRaw = 0;
      break;
    case 'update':
      modeRaw = 1;
      break;
    case 'replace':
      modeRaw = 2;
      break;
    default:
      throw new Error('Invalid mode');
  }
  buf.writeUInt32BE(modeRaw, 31, true);

  writePropArray(propArray, buf, 35);

  this._socket.write(buf);
};

PAClient.prototype.removeClientProperties = function(keys, cb) {
  if (!Array.isArray(keys))
    throw new Error('Keys argument must be an array');
  if (this._index === -1)
    throw new Error('Not ready');

  var namesLen = 0;
  for (var i = 0; i < keys.length; ++i) {
    const key = keys[i];
    if (typeof key !== 'string')
      throw new Error('Key names must be strings');
    if (key.length > 0)
      namesLen += 2 + Buffer.byteLength(key);
  }

  const buf = Buffer.allocUnsafe(31 + namesLen);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_UPDATE_CLIENT_PROPLIST;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  var p = 30;
  for (var i = 0; i < keys.length; ++i) {
    const key = keys[i];
    if (typeof key !== 'string')
      throw new Error('Key names must be strings');
    if (key.length > 0) {
      buf[p++] = PA_TAG_STRING;
      p += buf.write(key, p);
      buf[p++] = 0;
    }
  }

  buf[buf.length - 1] = PA_TAG_STRING_NULL;

  this._socket.write(buf);
};

PAClient.prototype.subscribe = function(events, cb) {
  if (this._index === -1)
    throw new Error('Not ready');

  if (typeof events === 'string')
    events = [events];
  else if (!Array.isArray(events) || events.length === 0)
    throw new Error('Invalid event categories list');

  var mask = 0;
  for (var i = 0; i < events.length; ++i) {
    switch (events[i]) {
      case 'none':
        mask = 0;
        break;
      case 'sink':
        mask |= 0x0001;
        break;
      case 'source':
        mask |= 0x0002;
        break;
      case 'sinkInput':
        mask |= 0x0004;
        break;
      case 'sourceOutput':
        mask |= 0x0008;
        break;
      case 'module':
        mask |= 0x0010;
        break;
      case 'client':
        mask |= 0x0020;
        break;
      case 'sampleCache':
        mask |= 0x0040;
        break;
      case 'global':
        mask |= 0x0080;
        break;
      case 'card':
        mask |= 0x0200;
        break;
      case 'all':
        mask = 0x02FF;
        break;
      default:
        throw new Error('Invalid event category: ' + events[i]);
    }
  }

  const buf = Buffer.allocUnsafe(35);

  buf.writeUInt32BE(15, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SUBSCRIBE;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(this, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(mask, 31, true);

  this._socket.write(buf);
};

function nextAddr(client, addrs, cookie, props) {
  if (addrs.length === 0) {
    client.emit('error', new Error('Unable to connect to PulseAudio server'));
    return;
  }
  const addr = addrs.shift();
  const sock = new Socket();

  var connected = false;
  sock.on('connect', () => {
    connected = true;
    sock.client = client;
    client._socket = sock;
    client._reqs = Object.create(null);
    sendAuthPacket(client, cookie, (err, srvProtoVer) => {
      if (err) {
        client.emit('error', err);
        sock.end();
        return;
      }
      client._serverVer = srvProtoVer;
      sendClientNamePacket(client, props, (err, index) => {
        if (err) {
          client.emit('error', err);
          sock.end();
          return;
        }
        client._index = index;
        client.emit('ready');
      });
    });
    readLength.call(sock);
  });
  sock.on('error', (err) => {
    if (connected)
      client.emit('error', err);
  });
  sock.on('close', () => {
    client._index = -1;
    client._serverVer = -1;
    if (connected) {
      client._socket = null;
      client.emit('close');
    } else {
      connected = false;
      nextAddr(client, addrs, cookie);
    }
  });

  if (addr[0] === 'host' && addr[1] !== undefined) {
    const opts = (addr[1] === 4 ? DNS_4ONLY : DNS_6ONLY);
    lookup(addr[2], opts, (err, ip) => {
      if (err) {
        nextAddr(client, addrs, cookie);
        return;
      }
      sock.connect(addr[3], ip);
    });
  } else if (addr[0] === 'unix') {
    sock.connect(addr[1]);
  } else if (addr[0] === 'host') {
    sock.connect(addr[3], addr[2]);
  } else {
    sock.connect(addr[2], addr[1]);
  }
}

function readLength() {
  const header = this.read(20);
  if (header === null) {
    this.once('readable', readLength);
  } else {
    const len = header.readUInt32BE(0, true);
    const payload = this.read(len);
    if (payload === null) {
      this.len = len;
      this.once('readable', readPayload);
    } else {
      parsePayload(this.client, payload);
      readLength.call(this);
    }
  }
}

function readPayload() {
  const payload = this.read(this.len);
  if (payload === null) {
    this.once('readable', readPayload);
  } else {
    parsePayload(this.client, payload);
    readLength.call(this);
  }
}

function parsePayload(client, payload) {
  if (payload.length < 10 || payload[0] !== PA_TAG_U32
      || payload[5] !== PA_TAG_U32) {
    return malformedPacket(client);
  }

  const type = payload.readUInt32BE(1, true);
  const reqid = payload.readUInt32BE(6, true);
  if (type === PA_COMMAND_ERROR || type === PA_COMMAND_REPLY) {
    var req;
    if (reqid === 0xFFFFFFFF || (req = client._reqs[reqid]) === undefined)
      return malformedPacket(client);
    delete client._reqs[req];
    const cb = req.cb;
    if (typeof cb !== 'function')
      return;
    if (type === PA_COMMAND_ERROR) {
      const ret = parseError(payload);
      if (ret === undefined)
        return malformedPacket(client);
      cb(ret);
    } else {
      const ret = parseReply(payload, req.cmd, client._serverVer);
      if (ret === undefined)
        return malformedPacket(client);
      cb(null, ret);
    }
  } else if (type === PA_COMMAND_SUBSCRIBE_EVENT) {
    // TODO: Check if we actually subscribed first?
    if (reqid !== 0xFFFFFFFF)
      return malformedPacket(client);
    if (!handleEvent(payload, client))
      return malformedPacket(client);
  } else {
    return malformedPacket(client);
  }
}

function malformedPacket(client) {
  client.emit('error', new Error('Received malformed packet'));
  client._socket.end();
}

function parseError(payload) {
  if (payload.length < 15 || payload[10] !== PA_TAG_U32)
    return;

  const errCode = payload.readUInt32BE(11, true);

  if (errCode === 0) // Should this ever happen?
    return null;

  const errMsg = errors[errCode];
  if (errMsg === undefined)
    errMsg = `Unknown error code ${errCode}`;

  const err = new Error(errMsg);
  err.code = errCode;

  return err;
}

function handleEvent(payload, client) {
  if (payload.length !== 20 || payload[10] !== PA_TAG_U32
      || payload[15] !== PA_TAG_U32) {
    return false;
  }

  const details = payload.readUInt32BE(11, true);
  const index = payload.readUInt32BE(16, true);

  var eventCategory;
  switch (details & PA_SUBSCRIPTION_EVENT_FACILITY_MASK) {
    case PA_SUBSCRIPTION_EVENT_SINK:
      eventCategory = 'sink';
      break;
    case PA_SUBSCRIPTION_EVENT_SOURCE:
      eventCategory = 'source';
      break;
    case PA_SUBSCRIPTION_EVENT_SINK_INPUT:
      eventCategory = 'sinkInput';
      break;
    case PA_SUBSCRIPTION_EVENT_SOURCE_OUTPUT:
      eventCategory = 'sourceOutput';
      break;
    case PA_SUBSCRIPTION_EVENT_MODULE:
      eventCategory = 'module';
      break;
    case PA_SUBSCRIPTION_EVENT_CLIENT:
      eventCategory = 'client';
      break;
    case PA_SUBSCRIPTION_EVENT_SAMPLE_CACHE:
      eventCategory = 'sampleCache';
      break;
    case PA_SUBSCRIPTION_EVENT_SERVER:
      eventCategory = 'server';
      break;
    case PA_SUBSCRIPTION_EVENT_AUTOLOAD:
      eventCategory = 'autoload';
      break;
    case PA_SUBSCRIPTION_EVENT_CARD:
      eventCategory = 'card';
      break;
    default:
      return true;
  }

  switch (details & PA_SUBSCRIPTION_EVENT_TYPE_MASK) {
    case PA_SUBSCRIPTION_EVENT_NEW:
      client.emit('new', eventCategory, index);
      break;
    case PA_SUBSCRIPTION_EVENT_CHANGE:
      client.emit('change', eventCategory, index);
      break;
    case PA_SUBSCRIPTION_EVENT_REMOVE:
      client.emit('remove', eventCategory, index);
      break;
  }

  return true;
}

function parseReply(payload, cmd, serverVer) {
  var p;
  const len = payload.length;
  switch (cmd) {
    case PA_COMMAND_AUTH:
      if (len < 15 || payload[10] !== PA_TAG_U32)
        return;
      return (payload.readUInt32BE(11, true) & 0xFFFF); // server protocol ver
    case PA_COMMAND_SET_CLIENT_NAME:
      if (len < 15 || payload[10] !== PA_TAG_U32)
        return;
      return (payload.readUInt32BE(11, true)); // client index
    case PA_COMMAND_GET_MODULE_INFO_LIST: {
      const modules = [];
      p = 10;
      while (p < len) {
        var mod = readModule(payload, p, len, serverVer);
        if (mod === undefined)
          return;
        [p, mod] = mod;
        modules.push(mod);
      }
      return modules;
    }
    case PA_COMMAND_GET_CLIENT_INFO_LIST: {
      const clients = [];
      p = 10;
      while (p < len) {
        var client = readClient(payload, p, len, serverVer);
        if (client === undefined)
          return;
        [p, client] = client;
        clients.push(client);
      }
      return clients;
    }
    case PA_COMMAND_GET_SINK_INFO_LIST: {
      const sinks = [];
      p = 10;
      while (p < len) {
        var sink = readSink(payload, p, len, serverVer);
        if (sink === undefined)
          return;
        [p, sink] = sink;
        sinks.push(sink);
      }
      return sinks;
    }
    case PA_COMMAND_GET_SOURCE_INFO_LIST: {
      const sources = [];
      p = 10;
      while (p < len) {
        var source = readSource(payload, p, len, serverVer);
        if (source === undefined)
          return;
        [p, source] = source;
        sources.push(source);
      }
      return sources;
    }
    case PA_COMMAND_GET_SINK_INPUT_INFO_LIST: {
      const sinkInputs = [];
      p = 10;
      while (p < len) {
        var sinkInput = readSinkInput(payload, p, len, serverVer);
        if (sinkInput === undefined)
          return;
        [p, sinkInput] = sinkInput;
        sinkInputs.push(sinkInput);
      }
      return sinkInputs;
    }
    case PA_COMMAND_GET_SOURCE_OUTPUT_INFO_LIST: {
      const sourceOutputs = [];
      p = 10;
      while (p < len) {
        var sourceOutput = readSourceOutput(payload, p, len, serverVer);
        if (sourceOutput === undefined)
          return;
        [p, sourceOutput] = sourceOutput;
        sourceOutputs.push(sourceOutput);
      }
      return sourceOutputs;
    }
    case PA_COMMAND_GET_CARD_INFO_LIST: {
      const cards = [];
      p = 10;
      while (p < len) {
        var card = readCard(payload, p, len, serverVer);
        if (card === undefined)
          return;
        [p, card] = card;
        cards.push(card);
      }
      return cards;
    }
    case PA_COMMAND_LOOKUP_SINK:
    case PA_COMMAND_LOOKUP_SOURCE:
      if (len < 15 || payload[10] !== PA_TAG_U32)
        return;
      var index = payload.readUInt32BE(11, true);
      if (index === 0xFFFFFFFF)
        index = -1;
      return index;
    case PA_COMMAND_GET_SERVER_INFO: {
      var packageName = readString(payload, p, len);
      if (packageName === undefined)
        return;
      [p, packageName] = packageName;
      var packageVersion = readString(payload, p, len);
      if (packageVersion === undefined)
        return;
      [p, packageVersion] = packageVersion;
      var username = readString(payload, p, len);
      if (username === undefined)
        return;
      [p, username] = username;
      var hostname = readString(payload, p, len);
      if (hostname === undefined)
        return;
      [p, hostname] = hostname;
      var defaultSampleSpec = readSampleSpec(payload, p, len);
      if (defaultSampleSpec === undefined)
        return;
      [p, defaultSampleSpec] = defaultSampleSpec;
      var defaultSinkName = readString(payload, p, len);
      if (defaultSinkName === undefined)
        return;
      [p, defaultSinkName] = defaultSinkName;
      var defaultSourceName = readString(payload, p, len);
      if (defaultSourceName === undefined)
        return;
      [p, defaultSourceName] = defaultSourceName;
      if (p + 5 > len || payload[p++] !== PA_TAG_U32)
        return;
      const cookie = payload.readUInt32BE(p, true);
      p += 4;
      if (serverVer >= 15) {
        var defaultChannelMap = readChannelMap(payload, p, len);
        if (defaultChannelMap === undefined)
          return;
        [p, defaultChannelMap] = defaultChannelMap;
      }
      return {
        packageName,
        packageVersion,
        username,
        hostname,
        defaultSampleSpec,
        defaultSinkName,
        defaultSourceName,
        cookie,
        defaultChannelMap
      };
    }
    case PA_COMMAND_GET_MODULE_INFO: {
      const mod = readModule(payload, 10, len, serverVer);
      if (mod === undefined)
        return;
      return mod[1];
    }
    case PA_COMMAND_GET_CLIENT_INFO: {
      const client = readClient(payload, 10, len, serverVer);
      if (client === undefined)
        return;
      return client[1];
    }
    case PA_COMMAND_GET_SINK_INFO: {
      const sink = readSink(payload, 10, len, serverVer);
      if (sink === undefined)
        return;
      return sink[1];
    }
    case PA_COMMAND_GET_SOURCE_INFO: {
      const source = readSource(payload, 10, len, serverVer);
      if (source === undefined)
        return;
      return source[1];
    }
    case PA_COMMAND_GET_SINK_INPUT_INFO: {
      const sinkInput = readSinkInput(payload, 10, len, serverVer);
      if (sinkInput === undefined)
        return;
      return sinkInput[1];
    }
    case PA_COMMAND_GET_SOURCE_OUTPUT_INFO: {
      const sourceOutput = readSourceOutput(payload, 10, len, serverVer);
      if (sourceOutput === undefined)
        return;
      return sourceOutput[1];
    }
    default:
      return null;
  }
}

const _result = [0, null];
function returnResult(p, val) {
  _result[0] = p;
  _result[1] = val;
  return _result;
}

function readString(payload, p, len) {
  if (p >= len)
    return;
  const type = payload[p++];
  if (type === PA_TAG_STRING_NULL)
    return returnResult(p, '');
  if (type !== PA_TAG_STRING)
    return;
  const start = p;
  for (; p < len; ++p) {
    if (payload[p] === 0)
      return returnResult(p + 1, payload.toString('utf8', start, p));
  }
}

function readSampleSpec(payload, p, len) {
  if (p + 7 >= len || payload[p++] !== PA_TAG_SAMPLE_SPEC)
    return;
  const format = payload[p++];
  const channels = payload[p++];
  const rate = payload.readUInt32BE(p, true);
  return returnResult(p + 4, { format, channels, rate });
}

function readChannelMap(payload, p, len) {
  if (p + 2 >= len || payload[p++] !== PA_TAG_CHANNEL_MAP)
    return;
  const channels = payload[p++];
  if (p + channels > len)
    return;
  const types = [];
  for (var i = 0; i < channels; ++i)
    types.push(payload[p++]);
  return returnResult(p, types);
}

function readChannelVolumes(payload, p, len) {
  if (p + 2 >= len || payload[p++] !== PA_TAG_CVOLUME)
    return;
  const channels = payload[p++];
  if (p + (channels * 4) > len)
    return;
  const vols = [];
  for (var i = 0; i < channels; ++i, p += 4)
    vols.push(payload.readUInt32BE(p, true));
  return returnResult(p, vols);
}

function readProplist(payload, p, len) {
  if (p >= len || payload[p++] !== PA_TAG_PROPLIST)
    return;
  const props = Object.create(null);
  while (true) {
    var key = readString(payload, p, len);
    if (key === undefined)
      return;
    [p, key] = key;
    if (key.length === 0)
      break;
    if (p + 10 > len || payload[p] !== PA_TAG_U32
        || payload[p + 5] !== PA_TAG_ARBITRARY) {
      return;
    }
    const valLen = payload.readUInt32BE(p + 1, true);
    const arbLen = payload.readUInt32BE(p + 6, true);
    if (valLen !== arbLen)
      return;
    p += 10;
    if (p + valLen >= len)
      return;

    key = key.split('.');
    var ptr = props;
    for (var j = 0; j < key.length - 1; ++j) {
      if (ptr[key[j]] === undefined)
        ptr = ptr[key[j]] = Object.create(null);
      else
        ptr = ptr[key[j]];
    }
    var end;
    if (valLen > 0) {
      if (payload[(p + valLen) - 1] === 0)
        end = (p + valLen) - 1;
      else
        end = p + valLen;
      ptr[key[j]] = payload.toString('utf8', p, end);
      p += valLen;
    } else {
      ptr[key[j]] = '';
    }
  }
  return returnResult(p, props);
}

function readModule(payload, p, len, serverVer) {
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  const index = payload.readUInt32BE(p, true);
  p += 4;
  var name = readString(payload, p, len);
  if (name === undefined)
    return;
  [p, name] = name;
  var args = readString(payload, p, len);
  if (args === undefined)
    return;
  [p, args] = args;
  if (p + 5 >= len || payload[p] !== PA_TAG_U32)
    return;
  var usage = payload.readUInt32BE(p + 1);
  if (usage === 0xFFFFFFFF)
    usage = -1;
  p += 5;
  if (serverVer >= 15) {
    var properties = readProplist(payload, p, len);
    if (properties === undefined)
      return;
    [p, properties] = properties;
  } else {
    // Skip over obsolete "autoload" boolean
    ++p;
  }
  return returnResult(p, { name, index, args, usage, properties });
}

function readClient(payload, p, len, serverVer) {
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  const index = payload.readUInt32BE(p, true);
  p += 4;
  var name = readString(payload, p, len);
  if (name === undefined)
    return;
  [p, name] = name;
  if (p + 5 >= len || payload[p] !== PA_TAG_U32)
    return;
  var moduleIndex = payload.readUInt32BE(p + 1);
  if (moduleIndex === 0xFFFFFFFF)
    moduleIndex = -1;
  p += 5;
  var driverName = readString(payload, p, len);
  if (driverName === undefined)
    return;
  [p, driverName] = driverName;
  if (serverVer >= 13) {
    var properties = readProplist(payload, p, len);
    if (properties === undefined)
      return;
    [p, properties] = properties;
  }
  return returnResult(p, { name, index, moduleIndex, driverName, properties });
}

function readSink(payload, p, len, serverVer) {
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  const index = payload.readUInt32BE(p, true);
  p += 4;
  var name = readString(payload, p, len);
  if (name === undefined)
    return;
  [p, name] = name;
  var description = readString(payload, p, len);
  if (description === undefined)
    return;
  [p, description] = description;
  var sampleSpec = readSampleSpec(payload, p, len);
  if (sampleSpec === undefined)
    return;
  [p, sampleSpec] = sampleSpec;
  var channelMap = readChannelMap(payload, p, len);
  if (channelMap === undefined)
    return;
  [p, channelMap] = channelMap;
  if (p + 5 >= len || payload[p] !== PA_TAG_U32)
    return;
  var moduleIndex = payload.readUInt32BE(p + 1);
  if (moduleIndex === 0xFFFFFFFF)
    moduleIndex = -1;
  p += 5;
  var channelVolumes = readChannelVolumes(payload, p, len);
  if (channelVolumes === undefined)
    return;
  [p, channelVolumes] = channelVolumes;
  if (p + 6 >= len || payload[p + 1] !== PA_TAG_U32)
    return;
  var muted;
  switch (payload[p]) {
    case PA_TAG_BOOLEAN_FALSE:
      muted = false;
      break;
    case PA_TAG_BOOLEAN_TRUE:
      muted = true;
      break;
    default:
      return;
  }
  var monitorSourceIndex = payload.readUInt32BE(p += 2, true);
  if (monitorSourceIndex === 0xFFFFFFFF)
    monitorSourceIndex = -1;
  p += 4;
  var monitorSourceName = readString(payload, p, len);
  if (monitorSourceName === undefined)
    return;
  [p, monitorSourceName] = monitorSourceName;
  if (p + 9 >= len || payload[p++] !== PA_TAG_USEC)
    return;
  const latency = (payload[p++] * 72057594037927940)
                  + (payload[p++] * 281474976710656)
                  + (payload[p++] * 1099511627776)
                  + (payload[p++] * 4294967296)
                  + (payload[p++] * 16777216)
                  + (payload[p++] * 65536)
                  + (payload[p++] * 256)
                  + payload[p++];
  var driverName = readString(payload, p, len);
  if (driverName === undefined)
    return;
  [p, driverName] = driverName;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  const flagsRaw = payload.readUInt32BE(p, true);
  const flags = {
    hasHardwareVolume: !!(flagsRaw & PA_SINK_HW_VOLUME_CTRL),
    canQueryLatency: !!(flagsRaw & PA_SINK_LATENCY),
    isHardware: !!(flagsRaw & PA_SINK_HARDWARE),
    isNetwork: !!(flagsRaw & PA_SINK_NETWORK),
    hasHardwareMute: !!(flagsRaw & PA_SINK_HW_MUTE_CTRL),
    canTranslateVolume: !!(flagsRaw & PA_SINK_DECIBEL_VOLUME),
    hasFlatVolume: !!(flagsRaw & PA_SINK_FLAT_VOLUME),
    hasDynamicLatency: !!(flagsRaw & PA_SINK_DYNAMIC_LATENCY),
    canSetFormats: !!(flagsRaw & PA_SINK_SET_FORMATS)
  };
  p += 4;
  if (serverVer >= 13) {
    var properties = readProplist(payload, p, len);
    if (properties === undefined)
      return;
    [p, properties] = properties;
    if (p + 9 > len || payload[p++] !== PA_TAG_USEC) {
      return;
    }
    var configLatency = (payload[p++] * 72057594037927940)
                         + (payload[p++] * 281474976710656)
                         + (payload[p++] * 1099511627776)
                         + (payload[p++] * 4294967296)
                         + (payload[p++] * 16777216)
                         + (payload[p++] * 65536)
                         + (payload[p++] * 256)
                         + payload[p++];
  }
  if (serverVer >= 15) {
    if (p + 20 > len || payload[p] !== PA_TAG_VOLUME
        || payload[p + 5] !== PA_TAG_U32
        || payload[p + 10] !== PA_TAG_U32
        || payload[p + 15] !== PA_TAG_U32) {
      return;
    }
    var baseVolume = payload.readUInt32BE(p + 1, true);
    var state;
    switch (payload.readUInt32BE(p + 6, true)) {
      case 0:
        state = 'running';
        break;
      case 1:
        state = 'idle';
        break;
      case 2:
        state = 'suspended';
        break;
      default:
        state = 'unknown';
    }
    var volumeSteps = payload.readUInt32BE(p + 11, true);
    var cardIndex = payload.readUInt32BE(p + 16, true);
    if (cardIndex === 0xFFFFFFFF)
      cardIndex = -1;
    p += 20;
  }
  if (serverVer >= 16) {
    if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
      return;
    const numPorts = payload.readUInt32BE(p, true);
    var ports = [];
    p += 4;
    for (var i = 0; i < numPorts; ++i) {
      var portName = readString(payload, p, len);
      if (portName === undefined)
        return;
      [p, portName] = portName;
      var portDescription = readString(payload, p, len);
      if (portDescription === undefined)
        return;
      [p, portDescription] = portDescription;
      if (p + 10 >= len || payload[p] !== PA_TAG_U32
          || payload[p + 5] !== PA_TAG_U32) {
        return;
      }
      const priority = payload.readUInt32BE(p + 1, true);
      var availability;
      switch (payload.readUInt32BE(p + 6, true)) {
        case 1:
          availability = 'unavailable';
          break;
        case 2:
          availability = 'available';
          break;
        default:
          availability = 'unknown';
      }
      p += 10;
      ports.push({
        name: portName,
        description: portDescription,
        priority,
        availability
      });
    }
    var activePortName = readString(payload, p, len);
    if (activePortName === undefined)
      return;
    [p, activePortName] = activePortName;
  }
  if (serverVer >= 21) {
    if (p + 2 > len || payload[p++] !== PA_TAG_U8)
      return;
    const numFormats = payload[p++];
    var formats = [];
    for (var i = 0; i < numFormats; ++i) {
      if (p + 3 >= len || payload[p++] !== PA_TAG_FORMAT_INFO
          || payload[p++] !== PA_TAG_U8) {
        return;
      }
      const encoding = payload[p++];
      var formatProperties = readProplist(payload, p, len);
      if (formatProperties === undefined)
        return;
      [p, formatProperties] = formatProperties;
      formats.push({
        encoding,
        properties: formatProperties
      });
    }
  }

  return returnResult(p, {
    name,
    index,
    description,
    sampleSpec,
    channelMap,
    moduleIndex,
    channelVolumes,
    muted,
    monitorSourceIndex,
    monitorSourceName,
    latency,
    driverName,
    flags,
    properties,
    configLatency,
    baseVolume,
    state,
    volumeSteps,
    cardIndex,
    ports,
    activePortName,
    formats
  });
}

function readSource(payload, p, len, serverVer) {
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  const index = payload.readUInt32BE(p, true);
  p += 4;
  var name = readString(payload, p, len);
  if (name === undefined)
    return;
  [p, name] = name;
  var description = readString(payload, p, len);
  if (description === undefined)
    return;
  [p, description] = description;
  var sampleSpec = readSampleSpec(payload, p, len);
  if (sampleSpec === undefined)
    return;
  [p, sampleSpec] = sampleSpec;
  var channelMap = readChannelMap(payload, p, len);
  if (channelMap === undefined)
    return;
  [p, channelMap] = channelMap;
  if (p + 5 >= len || payload[p] !== PA_TAG_U32)
    return;
  var moduleIndex = payload.readUInt32BE(p + 1);
  if (moduleIndex === 0xFFFFFFFF)
    moduleIndex = -1;
  p += 5;
  var channelVolumes = readChannelVolumes(payload, p, len);
  if (channelVolumes === undefined)
    return;
  [p, channelVolumes] = channelVolumes;
  if (p + 6 >= len || payload[p + 1] !== PA_TAG_U32)
    return;
  var muted;
  switch (payload[p]) {
    case PA_TAG_BOOLEAN_FALSE:
      muted = false;
      break;
    case PA_TAG_BOOLEAN_TRUE:
      muted = true;
      break;
    default:
      return;
  }
  var monitorSourceIndex = payload.readUInt32BE(p += 2, true);
  if (monitorSourceIndex === 0xFFFFFFFF)
    monitorSourceIndex = -1;
  p += 4;
  var monitorSourceName = readString(payload, p, len);
  if (monitorSourceName === undefined)
    return;
  [p, monitorSourceName] = monitorSourceName;
  if (p + 9 >= len || payload[p++] !== PA_TAG_USEC)
    return;
  const latency = (payload[p++] * 72057594037927940)
                  + (payload[p++] * 281474976710656)
                  + (payload[p++] * 1099511627776)
                  + (payload[p++] * 4294967296)
                  + (payload[p++] * 16777216)
                  + (payload[p++] * 65536)
                  + (payload[p++] * 256)
                  + payload[p++];
  var driverName = readString(payload, p, len);
  if (driverName === undefined)
    return;
  [p, driverName] = driverName;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  const flagsRaw = payload.readUInt32BE(p, true);
  const flags = {
    hasHardwareVolume: !!(flagsRaw & PA_SINK_HW_VOLUME_CTRL),
    canQueryLatency: !!(flagsRaw & PA_SINK_LATENCY),
    isHardware: !!(flagsRaw & PA_SINK_HARDWARE),
    isNetwork: !!(flagsRaw & PA_SINK_NETWORK),
    hasHardwareMute: !!(flagsRaw & PA_SINK_HW_MUTE_CTRL),
    canTranslateVolume: !!(flagsRaw & PA_SINK_DECIBEL_VOLUME),
    hasFlatVolume: !!(flagsRaw & PA_SINK_FLAT_VOLUME),
    hasDynamicLatency: !!(flagsRaw & PA_SINK_DYNAMIC_LATENCY),
    canSetFormats: !!(flagsRaw & PA_SINK_SET_FORMATS)
  };
  p += 4;
  if (serverVer >= 13) {
    var properties = readProplist(payload, p, len);
    if (properties === undefined)
      return;
    [p, properties] = properties;
    if (p + 9 > len || payload[p++] !== PA_TAG_USEC) {
      return;
    }
    var configLatency = (payload[p++] * 72057594037927940)
                         + (payload[p++] * 281474976710656)
                         + (payload[p++] * 1099511627776)
                         + (payload[p++] * 4294967296)
                         + (payload[p++] * 16777216)
                         + (payload[p++] * 65536)
                         + (payload[p++] * 256)
                         + payload[p++];
  }
  if (serverVer >= 15) {
    if (p + 20 > len || payload[p] !== PA_TAG_VOLUME
        || payload[p + 5] !== PA_TAG_U32
        || payload[p + 10] !== PA_TAG_U32
        || payload[p + 15] !== PA_TAG_U32) {
      return;
    }
    var baseVolume = payload.readUInt32BE(p + 1, true);
    var state;
    switch (payload.readUInt32BE(p + 6, true)) {
      case 0:
        state = 'running';
        break;
      case 1:
        state = 'idle';
        break;
      case 2:
        state = 'suspended';
        break;
      default:
        state = 'unknown';
    }
    var volumeSteps = payload.readUInt32BE(p + 11, true);
    var cardIndex = payload.readUInt32BE(p + 16, true);
    if (cardIndex === 0xFFFFFFFF)
      cardIndex = -1;
    p += 20;
  }
  if (serverVer >= 16) {
    if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
      return;
    const numPorts = payload.readUInt32BE(p, true);
    var ports = [];
    p += 4;
    for (var i = 0; i < numPorts; ++i) {
      var portName = readString(payload, p, len);
      if (portName === undefined)
        return;
      [p, portName] = portName;
      var portDescription = readString(payload, p, len);
      if (portDescription === undefined)
        return;
      [p, portDescription] = portDescription;
      if (p + 10 >= len || payload[p] !== PA_TAG_U32
          || payload[p + 5] !== PA_TAG_U32) {
        return;
      }
      const priority = payload.readUInt32BE(p + 1, true);
      var availability;
      switch (payload.readUInt32BE(p + 6, true)) {
        case 1:
          availability = 'unavailable';
          break;
        case 2:
          availability = 'available';
          break;
        default:
          availability = 'unknown';
      }
      p += 10;
      ports.push({
        name: portName,
        description: portDescription,
        priority,
        availability
      });
    }
    var activePortName = readString(payload, p, len);
    if (activePortName === undefined)
      return;
    [p, activePortName] = activePortName;
  }
  if (serverVer >= 22) {
    if (p + 2 > len || payload[p++] !== PA_TAG_U8)
      return;
    const numFormats = payload[p++];
    var formats = [];
    for (var i = 0; i < numFormats; ++i) {
      if (p + 3 >= len || payload[p++] !== PA_TAG_FORMAT_INFO
          || payload[p++] !== PA_TAG_U8) {
        return;
      }
      const encoding = payload[p++];
      var formatProperties = readProplist(payload, p, len);
      if (formatProperties === undefined)
        return;
      [p, formatProperties] = formatProperties;
      formats.push({
        encoding,
        properties: formatProperties
      });
    }
  }

  return returnResult(p, {
    name,
    index,
    description,
    sampleSpec,
    channelMap,
    moduleIndex,
    channelVolumes,
    muted,
    monitorSourceIndex,
    monitorSourceName,
    latency,
    driverName,
    flags,
    properties,
    configLatency,
    baseVolume,
    state,
    volumeSteps,
    cardIndex,
    ports,
    activePortName,
    formats
  });
}

function readSinkInput(payload, p, len, serverVer) {
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var index = payload.readUInt32BE(p, true);
  if (index === 0xFFFFFFFF)
    index = -1;
  p += 4;
  var name = readString(payload, p, len);
  if (name === undefined)
    return;
  [p, name] = name;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var moduleIndex = payload.readUInt32BE(p, true);
  if (moduleIndex === 0xFFFFFFFF)
    moduleIndex = -1;
  p += 4;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var clientIndex = payload.readUInt32BE(p, true);
  if (clientIndex === 0xFFFFFFFF)
    clientIndex = -1;
  p += 4;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var sinkIndex = payload.readUInt32BE(p, true);
  if (sinkIndex === 0xFFFFFFFF)
    sinkIndex = -1;
  p += 4;
  var sampleSpec = readSampleSpec(payload, p, len);
  if (sampleSpec === undefined)
    return;
  [p, sampleSpec] = sampleSpec;
  var channelMap = readChannelMap(payload, p, len);
  if (channelMap === undefined)
    return;
  [p, channelMap] = channelMap;
  var channelVolumes = readChannelVolumes(payload, p, len);
  if (channelVolumes === undefined)
    return;
  [p, channelVolumes] = channelVolumes;
  if (p + 9 > len || payload[p++] !== PA_TAG_USEC)
    return;
  var bufferLatency = (payload[p++] * 72057594037927940)
                       + (payload[p++] * 281474976710656)
                       + (payload[p++] * 1099511627776)
                       + (payload[p++] * 4294967296)
                       + (payload[p++] * 16777216)
                       + (payload[p++] * 65536)
                       + (payload[p++] * 256)
                       + payload[p++];
  if (p + 9 > len || payload[p++] !== PA_TAG_USEC)
    return;
  var sinkLatency = (payload[p++] * 72057594037927940)
                     + (payload[p++] * 281474976710656)
                     + (payload[p++] * 1099511627776)
                     + (payload[p++] * 4294967296)
                     + (payload[p++] * 16777216)
                     + (payload[p++] * 65536)
                     + (payload[p++] * 256)
                     + payload[p++];
  var resampleMethod = readString(payload, p, len);
  if (resampleMethod === undefined)
    return;
  [p, resampleMethod] = resampleMethod;
  var driverName = readString(payload, p, len);
  if (driverName === undefined)
    return;
  [p, driverName] = driverName;
  if (serverVer >= 11) {
    if (p >= len)
      return;
    var muted;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        muted = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        muted = true;
        break;
      default:
        return;
    }
  }
  if (serverVer >= 13) {
    var properties = readProplist(payload, p, len);
    if (properties === undefined)
      return;
    [p, properties] = properties;
  }
  if (serverVer >= 19) {
    if (p >= len)
      return;
    var corked;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        corked = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        corked = true;
        break;
      default:
        return;
    }
  }
  if (serverVer >= 20) {
    if (p + 1 >= len)
      return;
    var hasVolume;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        hasVolume = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        hasVolume = true;
        break;
      default:
        return;
    }
    var canSetVolume;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        canSetVolume = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        canSetVolume = true;
        break;
      default:
        return;
    }
  }
  if (serverVer >= 21) {
    if (p + 3 > len || payload[p++] !== PA_TAG_FORMAT_INFO
        || payload[p++] !== PA_TAG_U8) {
      return;
    }
    const encoding = payload[p++];
    var formatProperties = readProplist(payload, p, len);
    if (formatProperties === undefined)
      return;
    [p, formatProperties] = formatProperties;
    var format = { encoding, properties: formatProperties };
  }

  return returnResult(p, {
    index,
    name,
    moduleIndex,
    clientIndex,
    sinkIndex,
    sampleSpec,
    channelMap,
    channelVolumes,
    bufferLatency,
    sinkLatency,
    resampleMethod,
    driverName,
    muted,
    properties,
    corked,
    hasVolume,
    canSetVolume,
    format
  });
}

function readSourceOutput(payload, p, len, serverVer) {
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var index = payload.readUInt32BE(p, true);
  if (index === 0xFFFFFFFF)
    index = -1;
  p += 4;
  var name = readString(payload, p, len);
  if (name === undefined)
    return;
  [p, name] = name;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var moduleIndex = payload.readUInt32BE(p, true);
  if (moduleIndex === 0xFFFFFFFF)
    moduleIndex = -1;
  p += 4;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var clientIndex = payload.readUInt32BE(p, true);
  if (clientIndex === 0xFFFFFFFF)
    clientIndex = -1;
  p += 4;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var sourceIndex = payload.readUInt32BE(p, true);
  if (sourceIndex === 0xFFFFFFFF)
    sourceIndex = -1;
  p += 4;
  var sampleSpec = readSampleSpec(payload, p, len);
  if (sampleSpec === undefined)
    return;
  [p, sampleSpec] = sampleSpec;
  var channelMap = readChannelMap(payload, p, len);
  if (channelMap === undefined)
    return;
  [p, channelMap] = channelMap;
  if (p + 9 > len || payload[p++] !== PA_TAG_USEC)
    return;
  var bufferLatency = (payload[p++] * 72057594037927940)
                       + (payload[p++] * 281474976710656)
                       + (payload[p++] * 1099511627776)
                       + (payload[p++] * 4294967296)
                       + (payload[p++] * 16777216)
                       + (payload[p++] * 65536)
                       + (payload[p++] * 256)
                       + payload[p++];
  if (p + 9 > len || payload[p++] !== PA_TAG_USEC)
    return;
  var sourceLatency = (payload[p++] * 72057594037927940)
                       + (payload[p++] * 281474976710656)
                       + (payload[p++] * 1099511627776)
                       + (payload[p++] * 4294967296)
                       + (payload[p++] * 16777216)
                       + (payload[p++] * 65536)
                       + (payload[p++] * 256)
                       + payload[p++];
  var resampleMethod = readString(payload, p, len);
  if (resampleMethod === undefined)
    return;
  [p, resampleMethod] = resampleMethod;
  var driverName = readString(payload, p, len);
  if (driverName === undefined)
    return;
  [p, driverName] = driverName;
  if (serverVer >= 13) {
    var properties = readProplist(payload, p, len);
    if (properties === undefined)
      return;
    [p, properties] = properties;
  }
  if (serverVer >= 19) {
    if (p >= len)
      return;
    var corked;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        corked = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        corked = true;
        break;
      default:
        return;
    }
  }
  if (serverVer >= 22) {
    var channelVolumes = readChannelVolumes(payload, p, len);
    if (channelVolumes === undefined)
      return;
    [p, channelVolumes] = channelVolumes;
    if (p + 5 >= len)
      return;
    var muted;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        muted = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        muted = true;
        break;
      default:
        return;
    }
    var hasVolume;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        hasVolume = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        hasVolume = true;
        break;
      default:
        return;
    }
    var canSetVolume;
    switch (payload[p++]) {
      case PA_TAG_BOOLEAN_FALSE:
        canSetVolume = false;
        break;
      case PA_TAG_BOOLEAN_TRUE:
        canSetVolume = true;
        break;
      default:
        return;
    }
    if (payload[p++] !== PA_TAG_FORMAT_INFO
        || payload[p++] !== PA_TAG_U8) {
      return;
    }
    const encoding = payload[p++];
    var formatProperties = readProplist(payload, p, len);
    if (formatProperties === undefined)
      return;
    [p, formatProperties] = formatProperties;
    var format = { encoding, properties: formatProperties };
  }

  return returnResult(p, {
    index,
    name,
    moduleIndex,
    clientIndex,
    sourceIndex,
    sampleSpec,
    channelMap,
    channelVolumes,
    bufferLatency,
    sourceLatency,
    resampleMethod,
    driverName,
    muted,
    properties,
    corked,
    hasVolume,
    canSetVolume,
    format
  });
}

function readCard(payload, p, len, serverVer) {
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var index = payload.readUInt32BE(p, true);
  if (index === 0xFFFFFFFF)
    index = -1;
  p += 4;
  var name = readString(payload, p, len);
  if (name === undefined)
    return;
  [p, name] = name;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var moduleIndex = payload.readUInt32BE(p, true);
  if (moduleIndex === 0xFFFFFFFF)
    moduleIndex = -1;
  p += 4;
  var driverName = readString(payload, p, len);
  if (driverName === undefined)
    return;
  [p, driverName] = driverName;
  if (p + 5 >= len || payload[p++] !== PA_TAG_U32)
    return;
  var numProfiles = payload.readUInt32BE(p, true);
  var profiles = [];
  p += 4;
  for (var i = 0; i < numProfiles; ++i) {
    var profileName = readString(payload, p, len);
    if (profileName === undefined)
      return;
    [p, profileName] = profileName;
    var profileDescription = readString(payload, p, len);
    if (profileDescription === undefined)
      return;
    [p, profileDescription] = profileDescription;
    if (p + 15 > len || payload[p] !== PA_TAG_U32
        || payload[p + 5] !== PA_TAG_U32
        || payload[p + 10] !== PA_TAG_U32) {
      return;
    }
    const numSinks = payload.readUInt32BE(++p, true);
    const numSources = payload.readUInt32BE(p += 5, true);
    const priority = payload.readUInt32BE(p += 5, true);
    p += 4;
    var profileAvailable;
    if (serverVer >= 29) {
      if (p + 5 > len || payload[p++] !== PA_TAG_U32)
        return;
      const avRaw = payload.readUInt32BE(p, true);
      if (avRaw !== 0 && avRaw !== 1)
        return;
      p += 4;
      profileAvailable = (avRaw === 1);
    } else {
      profileAvailable = true;
    }

    profiles.push({
      name: profileName,
      description: profileDescription,
      numSinks,
      numSources,
      priority,
      available: profileAvailable
    });
  }
  var activeProfileName = readString(payload, p, len);
  if (activeProfileName === undefined)
    return;
  [p, activeProfileName] = activeProfileName;
  var properties = readProplist(payload, p, len);
  if (properties === undefined)
    return;
  [p, properties] = properties;
  if (serverVer >= 26) {
    if (p + 5 > len || payload[p++] !== PA_TAG_U32)
      return;
    var numPorts = payload.readUInt32BE(p, true);
    var ports = [];
    p += 4;
    for (var i = 0; i < numPorts; ++i) {
      var portName = readString(payload, p, len);
      if (portName === undefined)
        return;
      [p, portName] = portName;
      var portDescription = readString(payload, p, len);
      if (portDescription === undefined)
        return;
      [p, portDescription] = portDescription;
      if (p + 12 > len || payload[p] !== PA_TAG_U32
          || payload[p + 5] !== PA_TAG_U32
          || payload[p + 10] !== PA_TAG_U8) {
        return;
      }
      const priority = payload.readUInt32BE(++p, true);
      var availability;
      switch (payload.readUInt32BE(p += 5, true)) {
        case 1:
          availability = 'unavailable';
          break;
        case 2:
          availability = 'available';
          break;
        default:
          availability = 'unknown';
      }
      var direction;
      switch (payload[p += 5]) {
        case 1:
          direction = 'output';
          break;
        case 2:
          direction = 'input';
          break;
        default:
          direction = 'unknown';
          break;
      }
      var portProperties = readProplist(payload, ++p, len);
      if (portProperties === undefined)
        return;
      [p, portProperties] = portProperties;
      if (p + 5 > len || payload[p++] !== PA_TAG_U32)
        return;
      const numProfiles = payload.readUInt32BE(p, true);
      const portProfiles = [];
      p += 4;
      for (var j = 0; j < numProfiles; ++j) {
        var portProfileName = readString(payload, p, len);
        if (portProfileName === undefined)
          return;
        [p, portProfileName] = portProfileName;
        portProfiles.push(portProfileName);
      }
      if (serverVer >= 27) {
        if (p + 9 > len || payload[p++] !== PA_TAG_S64)
          return;
        var profileLatencyOffset
        var sign;
        if (payload[p] & 0x80) {
          sign = -1;
          payload[p] &= ~0x80;
        } else {
          sign = 1;
        }
        var latencyOffset = ((payload[p++] * 72057594037927940)
                              + (payload[p++] * 281474976710656)
                              + (payload[p++] * 1099511627776)
                              + (payload[p++] * 4294967296)
                              + (payload[p++] * 16777216)
                              + (payload[p++] * 65536)
                              + (payload[p++] * 256)
                              + payload[p++]) * sign;
      }

      ports.push({
        name: portName,
        description: portDescription,
        priority,
        availability,
        direction,
        properties: portProperties,
        profiles: portProfiles,
        latencyOffset
      });
    }
  }

  return returnResult(p, {
    index,
    name,
    moduleIndex,
    driverName,
    profiles,
    activeProfileName,
    properties,
    ports
  });
}

function addReq(client, cmd, cb) {
  const num = client._reqid++;
  if (num === 0xFFFFFFFF)
    client._reqid = 0;
  client._reqs[num] = { cmd, cb };
  return num;
}

function propListToArray(list, ret, prefix) {
  const keys = Object.keys(list);
  if (ret === undefined) {
    ret = [];
    prefix = '';
  }
  for (var i = 0; i < keys.length; ++i) {
    const key = keys[i];
    if (key.length > 0) {
      const val = list[key];
      if (typeof val === 'object' && val !== null)
        propListToArray(val, ret, (prefix ? `${prefix}.${key}` : key));
      else if (typeof val === 'string' || Buffer.isBuffer(val))
        ret.push((prefix ? `${prefix}.${key}` : key), val);
      else
        throw new Error('Invalid property list value type: ' + typeof val);
    }
  }
  return ret;
}

function calcPropArrayLen(props) {
  var len = 2;
  for (var i = 0; i < props.length; i += 2) {
    const key = props[i];
    const val = props[i + 1];
    len += 12 + Buffer.byteLength(key);
    if (typeof val === 'string')
      len += Buffer.byteLength(val) + 1;
    else
      len += val.length;
  }
  return len;
}

function writePropArray(props, payload, p) {
  payload[p++] = PA_TAG_PROPLIST;
  for (var i = 0; i < props.length; i += 2) {
    const key = props[i];
    const val = props[i + 1];
    payload[p++] = PA_TAG_STRING;
    p += payload.write(key, p);
    payload[p++] = 0; // NULL terminator
    if (typeof val === 'string') {
      const len = Buffer.byteLength(val) + 1;
      payload[p++] = PA_TAG_U32;
      payload.writeUInt32BE(len, p, true);
      p += 4;
      payload[p++] = PA_TAG_ARBITRARY;
      payload.writeUInt32BE(len, p, true);
      p += 4;
      p += payload.write(val, p, len - 1);
      payload[p++] = 0; // NULL terminator
    } else {
      const len = val.length;
      payload[p++] = PA_TAG_U32;
      payload.writeUInt32BE(len, p, true);
      p += 4;
      payload[p++] = PA_TAG_ARBITRARY;
      payload.writeUInt32BE(len, p, true);
      p += 4;
      p += val.copy(payload, p);
    }
  }
  payload[p++] = PA_TAG_STRING_NULL;
  return p;
}

function sendSimplePacket(client, cmd, cb) {
  if (client._index === -1)
    throw new Error('Not ready');

  const buf = Buffer.allocUnsafe(30);

  buf.writeUInt32BE(10, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(client, cmd, cb), 26, true);

  client._socket.write(buf);
}

function sendAuthPacket(client, cookie, cb) {
  const cookieLen = (cookie ? cookie.length : 0);

  const buf = Buffer.allocUnsafe(30 + (2 * 4) + 2 + cookieLen);

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_AUTH;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(client, cmd, cb), 26, true);

  buf[30] = PA_TAG_U32;
  buf.writeUInt32BE(PROTOCOL_VERSION, 31, true);
  buf[35] = PA_TAG_ARBITRARY;
  buf.writeUInt32BE(cookieLen, 36, true);
  if (cookieLen > 0)
    cookie.copy(buf, 40);

  client._socket.write(buf);
}

function sendClientNamePacket(client, props, cb) {
  var buf;
  if (client._serverVer >= 13) {
    const propArray = propListToArray(props);
    const propLen = calcPropArrayLen(propArray);
    buf = Buffer.allocUnsafe(30 + propLen);
    writePropArray(propArray, buf, 30);
  } else if (props.application && typeof props.application.name === 'string'
             && props.application.name.length > 0) {
    const nameLen = Buffer.byteLength(props.application.name);
    buf = Buffer.allocUnsafe(32 + nameLen);
    buf[30] = PA_TAG_STRING;
    buf.write(props.application.name, 31);
    buf[buf.length - 1] = 0; // NULL terminator
  } else {
    buf = Buffer.allocUnsafe(31);
    buf[30] = PA_TAG_STRING_NULL;
  }

  buf.writeUInt32BE(buf.length - 20, 0, true);
  PACKET_STATIC_FIELDS.copy(buf, 4);

  const cmd = PA_COMMAND_SET_CLIENT_NAME;
  buf[20] = PA_TAG_U32;
  buf.writeUInt32BE(cmd, 21, true);
  buf[25] = PA_TAG_U32;
  buf.writeUInt32BE(addReq(client, cmd, cb), 26, true);

  client._socket.write(buf);
}


module.exports = PAClient;

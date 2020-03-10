var spawn = require('child_process').spawn;
var exec = require('child_process').exec;
var inpath = require('inpath').sync;
var pidof = require('pidof');
var sudo = inpath('sudo');
var isWin = (process.platform == 'win32');
var messages = [
    'PID is null',
    'Password is invalid'
];

function sudoCommand(command, password, withResult, callback) {
    password = password || '';
    withResult = withResult === undefined ? true : withResult;
    callback = callback || function() {

    };

    var error = null;
    var pid = '';
    var result = '';
    var prompt = '#sudo-js-passwd#';
    var prompts = 0;
    var args = ['-S', '-k', '-p', prompt].concat(command);

    var spawnProcess = spawn(sudo, args, {stdio: 'pipe'});
    
    var bin = command.filter(function(i) {
        return i.indexOf('-') !== 0;
    })[0];

    spawnProcess.stdout.on('data', function(data) {
        result += "\n"+ data.toString();
    });

    if (withResult) {
        spawnProcess.on('close', function(code) {
            callback(error, pid, result);
        });
    }

    function waitForStartup(err, _pid) {
        if (err) {
            throw new Error('Couldn\'t start '+ bin);
        }

        if (_pid || spawnProcess.exitCode !== null) {
            error = null;
            pid = _pid;
            if (!withResult) {
                callback(error, pid, result);
            }
        } else {
            setTimeout(function() {
                pidof(bin, waitForStartup);
            }, 100);
        }
    }
    pidof(bin, waitForStartup);

    spawnProcess.stderr.on("data", function (data) {
        data.toString().trim().split('\n').forEach(function(line) {
            if (line === prompt) {
                if (++prompts > 1) {
                    callback(true, {code: 1, msg: messages[1]}, result);
                    spawnProcess.stdin.write("\n\n\n\n");
                } else {
                    spawnProcess.stdin.write(password + "\n");
                }
            }
        });
    });
}

function sudoCommandForWindows(command, withResult, callback) {
    var bin = command[0];
    command.splice(0, 1);
    var result = '';
    var task = spawn(bin, command, {
        shell: true
    });

    task.stderr.on('data', function(data) {
        data = data.toString();
        if (data.trim() != '' && withResult) {
            result += "\n"+ data;
        }
    });

    task.stdout.on('data', function(data) {
        data = data.toString();
        if (data.trim() != '' && withResult) {
            result += "\n"+ data;
        }
    });

    task.on('close', function(code) {
        callback(null, null, result);
    });

    task.on('error', function(code) {
        callback(true, null, result);
    });
}

module.exports = {
    password: '',
    setPassword: function(password) {
        this.password = password;
    },
    check: function(callback) {
        if (isWin) {
            // next update
            callback(true);
        } else {
            sudoCommand(['ls'], this.password, false, (function(i) {
              return function (err) {
                if (!i++) {
                  callback(!err)
                }
              }
            })(0));
        }
    },
    exec: function(command, options, callback) {
        var self = this;
        if (typeof options === 'function') {
            callback = options;
            options = {};
        }

        if (typeof options !== 'object') {
            options = {};
        }

        if (typeof callback !== 'function') {
            callback = function() {

            }
        }

        if (!Array.isArray(command)) {
            command = [command];
        }

        if (isWin) {
            // exec(command.join(' '), function(err, stdout, stderr) {
            //     callback(err, {}, stdout.toString());
            // });
            // change method to spawn
            sudoCommandForWindows(command, options.withResult, callback);
        } else {
            if (options.check === true || options.check === undefined) {
                this.check(function(valid) {
                    if (valid) {
                        sudoCommand(command, self.password,
                            options.withResult, callback);
                    } else {
                        callback(true, {code: 1, msg: messages[1]}, '');
                    }
                });
            } else {
                sudoCommand(command, self.password, options.withResult, callback);
            }
        }
    },
    killByPid: function(pid, callback) {
        if (pid) {
            pid = pid.toString();
            if (isWin) {
                this.exec(["tskill", pid], callback);
            } else {
                this.exec(["kill", "-9", pid], callback);
            }
        }
    },
    killByName: function(name, callback) {
        var self = this;
        pidof(name, function(err, pid) {
            if (pid) {
                self.killByPid(pid, callback);
            } else {
                callback(true, {code: 0, msg: messages[0]}, '');
            }
        });
    }
}
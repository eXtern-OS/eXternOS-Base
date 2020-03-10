"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var cp = require("child_process");
var glob = require("glob");
var fs = require("fs");
var os = require("os");
var path = require("path");
var pty = require("node-pty");
var chai_1 = require("chai");
var Terminal_1 = require("./Terminal");
var Buffer_1 = require("./Buffer");
var primitivePty;
function ptyWriteRead(data, cb) {
    fs.writeSync(primitivePty.slave, data);
    setTimeout(function () {
        var b = new Buffer(64000);
        var bytes = fs.readSync(primitivePty.master, b, 0, 64000, null);
        cb(b.toString('utf8', 0, bytes));
    });
}
function ptyReset(cb) {
    ptyWriteRead('\r\n', cb);
}
function formatError(input, output, expected) {
    function addLineNumber(start, color) {
        var counter = start || 0;
        return function (s) {
            counter += 1;
            return '\x1b[33m' + (' ' + counter).slice(-2) + color + s;
        };
    }
    var line80 = '12345678901234567890123456789012345678901234567890123456789012345678901234567890';
    var s = '';
    s += '\n\x1b[34m' + JSON.stringify(input);
    s += '\n\x1b[33m  ' + line80 + '\n';
    s += output.split('\n').map(addLineNumber(0, '\x1b[31m')).join('\n');
    s += '\n\x1b[33m  ' + line80 + '\n';
    s += expected.split('\n').map(addLineNumber(0, '\x1b[32m')).join('\n');
    return s;
}
function terminalToString(term) {
    var result = '';
    var lineText = '';
    for (var line = term.buffer.ybase; line < term.buffer.ybase + term.rows; line++) {
        lineText = '';
        for (var cell = 0; cell < term.cols; ++cell) {
            lineText += term.buffer.lines.get(line)[cell][Buffer_1.CHAR_DATA_CHAR_INDEX];
        }
        lineText = lineText.replace(/\s+$/, '');
        result += lineText;
        result += '\n';
    }
    return result;
}
if (os.platform() !== 'win32') {
    var CONSOLE_LOG_1 = console.log;
    var COLS_1 = 80;
    var ROWS_1 = 25;
    primitivePty = pty.native.open(COLS_1, ROWS_1);
    describe('xterm output comparison', function () {
        var xterm;
        beforeEach(function () {
            xterm = new Terminal_1.Terminal({ cols: COLS_1, rows: ROWS_1 });
            xterm.refresh = function () { };
            xterm.viewport = {
                syncScrollArea: function () { }
            };
        });
        Error.stackTraceLimit = 0;
        var files = glob.sync('**/escape_sequence_files/*.in', { cwd: path.join(__dirname, '..') });
        var skip = [
            10, 16, 17, 19, 32, 33, 34, 35, 36, 39,
            40, 42, 43, 44, 45, 46, 47, 48, 49, 50,
            51, 52, 54, 55, 56, 57, 58, 59, 60, 61,
            63, 68
        ];
        if (os.platform() === 'darwin') {
            skip.push(3, 7, 11, 67);
        }
        for (var i = 0; i < files.length; i++) {
            if (skip.indexOf(i) >= 0) {
                continue;
            }
            (function (filename) {
                it(filename.split('/').slice(-1)[0], function (done) {
                    ptyReset(function () {
                        var inFile = fs.readFileSync(filename, 'utf8');
                        ptyWriteRead(inFile, function (fromPty) {
                            xterm.writeBuffer.push(fromPty);
                            xterm._innerWrite();
                            var fromEmulator = terminalToString(xterm);
                            console.log = CONSOLE_LOG_1;
                            var expected = fs.readFileSync(filename.split('.')[0] + '.text', 'utf8');
                            var expectedRightTrimmed = expected.split('\n').map(function (l) { return l.replace(/\s+$/, ''); }).join('\n');
                            if (fromEmulator !== expectedRightTrimmed) {
                                throw new Error(formatError(inFile, fromEmulator, expected));
                            }
                            done();
                        });
                    });
                });
            })(files[i]);
        }
    });
}
describe('typings', function () {
    it('should throw no compile errors', function () {
        this.timeout(20000);
        var tsc = path.join(__dirname, '..', 'node_modules', '.bin', 'tsc');
        if (process.platform === 'win32') {
            tsc += '.cmd';
        }
        var fixtureDir = path.join(__dirname, '..', 'fixtures', 'typings-test');
        var result = cp.spawnSync(tsc, { cwd: fixtureDir });
        chai_1.assert.equal(result.status, 0, "build did not succeed:\nstdout: " + result.stdout.toString() + "\nstderr: " + result.stderr.toString() + "\n");
        fs.unlinkSync(path.join(fixtureDir, 'typings-test.js'));
    });
});

//# sourceMappingURL=Terminal.integration.js.map

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var zmodem;
function zmodemAttach(term, ws, opts) {
    if (opts === void 0) { opts = {}; }
    var senderFunc = function (octets) { return ws.send(new Uint8Array(octets)); };
    var zsentry;
    function _shouldWrite() {
        return !!zsentry.get_confirmed_session() || !opts.noTerminalWriteOutsideSession;
    }
    zsentry = new zmodem.Sentry({
        to_terminal: function (octets) {
            if (_shouldWrite()) {
                term.write(String.fromCharCode.apply(String, octets));
            }
        },
        sender: senderFunc,
        on_retract: function () { return term.emit('zmodemRetract'); },
        on_detect: function (detection) { return term.emit('zmodemDetect', detection); }
    });
    function handleWSMessage(evt) {
        if (typeof evt.data === 'string') {
            if (_shouldWrite()) {
                term.write(evt.data);
            }
        }
        else {
            zsentry.consume(evt.data);
        }
    }
    ws.binaryType = 'arraybuffer';
    ws.addEventListener('message', handleWSMessage);
}
exports.zmodemAttach = zmodemAttach;
function apply(terminalConstructor) {
    zmodem = (typeof window === 'object') ? window.ZModem : { Browser: null };
    terminalConstructor.prototype.zmodemAttach = zmodemAttach.bind(this, this);
    terminalConstructor.prototype.zmodemBrowser = zmodem.Browser;
}
exports.apply = apply;

//# sourceMappingURL=zmodem.js.map

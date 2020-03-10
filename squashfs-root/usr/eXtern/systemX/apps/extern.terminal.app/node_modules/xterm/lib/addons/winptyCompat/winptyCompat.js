"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
function winptyCompatInit(terminal) {
    var addonTerminal = terminal;
    var isWindows = ['Windows', 'Win16', 'Win32', 'WinCE'].indexOf(navigator.platform) >= 0;
    if (!isWindows) {
        return;
    }
    addonTerminal.on('linefeed', function () {
        var line = addonTerminal.buffer.lines.get(addonTerminal.buffer.ybase + addonTerminal.buffer.y - 1);
        var lastChar = line[addonTerminal.cols - 1];
        if (lastChar[3] !== 32) {
            var nextLine = addonTerminal.buffer.lines.get(addonTerminal.buffer.ybase + addonTerminal.buffer.y);
            nextLine.isWrapped = true;
        }
    });
}
exports.winptyCompatInit = winptyCompatInit;
function apply(terminalConstructor) {
    terminalConstructor.prototype.winptyCompatInit = function () {
        winptyCompatInit(this);
    };
}
exports.apply = apply;

//# sourceMappingURL=winptyCompat.js.map

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var chai_1 = require("chai");
var Clipboard = require("./Clipboard");
describe('evaluatePastedTextProcessing', function () {
    it('should replace carriage return and/or line feed with carriage return', function () {
        var pastedText = {
            unix: 'foo\nbar\n',
            windows: 'foo\r\nbar\r\n'
        };
        var processedText = {
            unix: Clipboard.prepareTextForTerminal(pastedText.unix),
            windows: Clipboard.prepareTextForTerminal(pastedText.windows)
        };
        chai_1.assert.equal(processedText.unix, 'foo\rbar\r');
        chai_1.assert.equal(processedText.windows, 'foo\rbar\r');
    });
    it('should bracket pasted text in bracketedPasteMode', function () {
        var pastedText = 'foo bar';
        var unbracketedText = Clipboard.bracketTextForPaste(pastedText, false);
        var bracketedText = Clipboard.bracketTextForPaste(pastedText, true);
        chai_1.assert.equal(unbracketedText, 'foo bar');
        chai_1.assert.equal(bracketedText, '\x1b[200~foo bar\x1b[201~');
    });
});

//# sourceMappingURL=Clipboard.test.js.map

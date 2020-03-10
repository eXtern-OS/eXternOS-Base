"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var chai_1 = require("chai");
var InputHandler_1 = require("./InputHandler");
var TestUtils_test_1 = require("./utils/TestUtils.test");
describe('InputHandler', function () {
    describe('save and restore cursor', function () {
        var terminal = new TestUtils_test_1.MockInputHandlingTerminal();
        terminal.buffer.x = 1;
        terminal.buffer.y = 2;
        var inputHandler = new InputHandler_1.InputHandler(terminal);
        inputHandler.saveCursor([]);
        chai_1.assert.equal(terminal.buffer.x, 1);
        chai_1.assert.equal(terminal.buffer.y, 2);
        terminal.buffer.x = 10;
        terminal.buffer.y = 20;
        inputHandler.restoreCursor([]);
        chai_1.assert.equal(terminal.buffer.x, 1);
        chai_1.assert.equal(terminal.buffer.y, 2);
    });
    describe('setCursorStyle', function () {
        it('should call Terminal.setOption with correct params', function () {
            var terminal = new TestUtils_test_1.MockInputHandlingTerminal();
            var inputHandler = new InputHandler_1.InputHandler(terminal);
            inputHandler.setCursorStyle([0]);
            chai_1.assert.equal(terminal.options['cursorStyle'], 'block');
            chai_1.assert.equal(terminal.options['cursorBlink'], true);
            terminal.options = {};
            inputHandler.setCursorStyle([1]);
            chai_1.assert.equal(terminal.options['cursorStyle'], 'block');
            chai_1.assert.equal(terminal.options['cursorBlink'], true);
            terminal.options = {};
            inputHandler.setCursorStyle([2]);
            chai_1.assert.equal(terminal.options['cursorStyle'], 'block');
            chai_1.assert.equal(terminal.options['cursorBlink'], false);
            terminal.options = {};
            inputHandler.setCursorStyle([3]);
            chai_1.assert.equal(terminal.options['cursorStyle'], 'underline');
            chai_1.assert.equal(terminal.options['cursorBlink'], true);
            terminal.options = {};
            inputHandler.setCursorStyle([4]);
            chai_1.assert.equal(terminal.options['cursorStyle'], 'underline');
            chai_1.assert.equal(terminal.options['cursorBlink'], false);
            terminal.options = {};
            inputHandler.setCursorStyle([5]);
            chai_1.assert.equal(terminal.options['cursorStyle'], 'bar');
            chai_1.assert.equal(terminal.options['cursorBlink'], true);
            terminal.options = {};
            inputHandler.setCursorStyle([6]);
            chai_1.assert.equal(terminal.options['cursorStyle'], 'bar');
            chai_1.assert.equal(terminal.options['cursorBlink'], false);
        });
    });
    describe('setMode', function () {
        it('should toggle Terminal.bracketedPasteMode', function () {
            var terminal = new TestUtils_test_1.MockInputHandlingTerminal();
            terminal.prefix = '?';
            terminal.bracketedPasteMode = false;
            var inputHandler = new InputHandler_1.InputHandler(terminal);
            inputHandler.setMode([2004]);
            chai_1.assert.equal(terminal.bracketedPasteMode, true);
            inputHandler.resetMode([2004]);
            chai_1.assert.equal(terminal.bracketedPasteMode, false);
        });
    });
});

//# sourceMappingURL=InputHandler.test.js.map

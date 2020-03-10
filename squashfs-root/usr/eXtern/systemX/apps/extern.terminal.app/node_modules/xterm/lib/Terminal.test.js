"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = Object.setPrototypeOf ||
        ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
        function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var chai_1 = require("chai");
var Terminal_1 = require("./Terminal");
var attach = require("./addons/attach/attach");
var TestUtils_test_1 = require("./utils/TestUtils.test");
var Buffer_1 = require("./Buffer");
var INIT_COLS = 80;
var INIT_ROWS = 24;
var TestTerminal = (function (_super) {
    __extends(TestTerminal, _super);
    function TestTerminal() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    TestTerminal.prototype.evaluateKeyEscapeSequence = function (ev) { return this._evaluateKeyEscapeSequence(ev); };
    TestTerminal.prototype.keyDown = function (ev) { return this._keyDown(ev); };
    TestTerminal.prototype.keyPress = function (ev) { return this._keyPress(ev); };
    return TestTerminal;
}(Terminal_1.Terminal));
describe('term.js addons', function () {
    var term;
    var termOptions = {
        cols: INIT_COLS,
        rows: INIT_ROWS
    };
    beforeEach(function () {
        term = new TestTerminal(termOptions);
        term.refresh = function () { };
        term.renderer = new TestUtils_test_1.MockRenderer();
        term.viewport = new TestUtils_test_1.MockViewport();
        term._compositionHelper = new TestUtils_test_1.MockCompositionHelper();
        term.write = function (data) {
            term.writeBuffer.push(data);
            term._innerWrite();
        };
        term.element = {
            classList: {
                toggle: function () { },
                remove: function () { }
            }
        };
    });
    it('should not mutate the options parameter', function () {
        term.setOption('cols', 1000);
        chai_1.assert.deepEqual(termOptions, {
            cols: INIT_COLS,
            rows: INIT_ROWS
        });
    });
    it('should apply addons with Terminal.applyAddon', function () {
        Terminal_1.Terminal.applyAddon(attach);
        chai_1.assert.equal(typeof Terminal_1.Terminal.prototype.attach, 'function');
    });
    describe('getOption', function () {
        it('should retrieve the option correctly', function () {
            term.options.cursorBlink = true;
            chai_1.assert.equal(term.getOption('cursorBlink'), true);
            delete term.options.cursorBlink;
            term.options.cursorBlink = false;
            chai_1.assert.equal(term.getOption('cursorBlink'), false);
        });
        it('should throw when retrieving a non-existant option', function () {
            chai_1.assert.throws(term.getOption.bind(term, 'fake', true));
        });
    });
    describe('attachCustomKeyEventHandler', function () {
        var evKeyDown = {
            preventDefault: function () { },
            stopPropagation: function () { },
            type: 'keydown',
            keyCode: 77
        };
        var evKeyPress = {
            preventDefault: function () { },
            stopPropagation: function () { },
            type: 'keypress',
            keyCode: 77
        };
        beforeEach(function () {
            term.handler = function () { };
            term.showCursor = function () { };
            term.clearSelection = function () { };
        });
        it('should process the keydown/keypress event based on what the handler returns', function () {
            chai_1.assert.equal(term.keyDown(evKeyDown), true);
            chai_1.assert.equal(term.keyPress(evKeyPress), true);
            term.attachCustomKeyEventHandler(function (ev) { return ev.keyCode === 77; });
            chai_1.assert.equal(term.keyDown(evKeyDown), true);
            chai_1.assert.equal(term.keyPress(evKeyPress), true);
            term.attachCustomKeyEventHandler(function (ev) { return ev.keyCode !== 77; });
            chai_1.assert.equal(term.keyDown(evKeyDown), false);
            chai_1.assert.equal(term.keyPress(evKeyPress), false);
        });
        it('should alive after reset(ESC c Full Reset (RIS))', function () {
            term.attachCustomKeyEventHandler(function (ev) { return ev.keyCode !== 77; });
            chai_1.assert.equal(term.keyDown(evKeyDown), false);
            chai_1.assert.equal(term.keyPress(evKeyPress), false);
            term.reset();
            chai_1.assert.equal(term.keyDown(evKeyDown), false);
            chai_1.assert.equal(term.keyPress(evKeyPress), false);
        });
    });
    describe('setOption', function () {
        it('should set the option correctly', function () {
            term.setOption('cursorBlink', true);
            chai_1.assert.equal(term.options.cursorBlink, true);
            term.setOption('cursorBlink', false);
            chai_1.assert.equal(term.options.cursorBlink, false);
        });
        it('should throw when setting a non-existant option', function () {
            chai_1.assert.throws(term.setOption.bind(term, 'fake', true));
        });
    });
    describe('clear', function () {
        it('should clear a buffer equal to rows', function () {
            var promptLine = term.buffer.lines.get(term.buffer.ybase + term.buffer.y);
            term.clear();
            chai_1.assert.equal(term.buffer.y, 0);
            chai_1.assert.equal(term.buffer.ybase, 0);
            chai_1.assert.equal(term.buffer.ydisp, 0);
            chai_1.assert.equal(term.buffer.lines.length, term.rows);
            chai_1.assert.deepEqual(term.buffer.lines.get(0), promptLine);
            for (var i = 1; i < term.rows; i++) {
                chai_1.assert.deepEqual(term.buffer.lines.get(i), term.blankLine());
            }
        });
        it('should clear a buffer larger than rows', function () {
            for (var i = 0; i < term.rows * 2; i++) {
                term.write('test\n');
            }
            var promptLine = term.buffer.lines.get(term.buffer.ybase + term.buffer.y);
            term.clear();
            chai_1.assert.equal(term.buffer.y, 0);
            chai_1.assert.equal(term.buffer.ybase, 0);
            chai_1.assert.equal(term.buffer.ydisp, 0);
            chai_1.assert.equal(term.buffer.lines.length, term.rows);
            chai_1.assert.deepEqual(term.buffer.lines.get(0), promptLine);
            for (var i = 1; i < term.rows; i++) {
                chai_1.assert.deepEqual(term.buffer.lines.get(i), term.blankLine());
            }
        });
        it('should not break the prompt when cleared twice', function () {
            var promptLine = term.buffer.lines.get(term.buffer.ybase + term.buffer.y);
            term.clear();
            term.clear();
            chai_1.assert.equal(term.buffer.y, 0);
            chai_1.assert.equal(term.buffer.ybase, 0);
            chai_1.assert.equal(term.buffer.ydisp, 0);
            chai_1.assert.equal(term.buffer.lines.length, term.rows);
            chai_1.assert.deepEqual(term.buffer.lines.get(0), promptLine);
            for (var i = 1; i < term.rows; i++) {
                chai_1.assert.deepEqual(term.buffer.lines.get(i), term.blankLine());
            }
        });
    });
    describe('scroll', function () {
        describe('scrollLines', function () {
            var startYDisp;
            beforeEach(function () {
                for (var i = 0; i < term.rows * 2; i++) {
                    term.writeln('test');
                }
                startYDisp = term.rows + 1;
            });
            it('should scroll a single line', function () {
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollLines(-1);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp - 1);
                term.scrollLines(1);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
            });
            it('should scroll multiple lines', function () {
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollLines(-5);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp - 5);
                term.scrollLines(5);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
            });
            it('should not scroll beyond the bounds of the buffer', function () {
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollLines(1);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                for (var i = 0; i < startYDisp; i++) {
                    term.scrollLines(-1);
                }
                chai_1.assert.equal(term.buffer.ydisp, 0);
                term.scrollLines(-1);
                chai_1.assert.equal(term.buffer.ydisp, 0);
            });
        });
        describe('scrollPages', function () {
            var startYDisp;
            beforeEach(function () {
                for (var i = 0; i < term.rows * 3; i++) {
                    term.writeln('test');
                }
                startYDisp = (term.rows * 2) + 1;
            });
            it('should scroll a single page', function () {
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollPages(-1);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp - (term.rows - 1));
                term.scrollPages(1);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
            });
            it('should scroll a multiple pages', function () {
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollPages(-2);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp - (term.rows - 1) * 2);
                term.scrollPages(2);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
            });
        });
        describe('scrollToTop', function () {
            beforeEach(function () {
                for (var i = 0; i < term.rows * 3; i++) {
                    term.writeln('test');
                }
            });
            it('should scroll to the top', function () {
                chai_1.assert.notEqual(term.buffer.ydisp, 0);
                term.scrollToTop();
                chai_1.assert.equal(term.buffer.ydisp, 0);
            });
        });
        describe('scrollToBottom', function () {
            var startYDisp;
            beforeEach(function () {
                for (var i = 0; i < term.rows * 3; i++) {
                    term.writeln('test');
                }
                startYDisp = (term.rows * 2) + 1;
            });
            it('should scroll to the bottom', function () {
                term.scrollLines(-1);
                term.scrollToBottom();
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollPages(-1);
                term.scrollToBottom();
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollToTop();
                term.scrollToBottom();
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
            });
        });
        describe('scrollToLine', function () {
            var startYDisp;
            beforeEach(function () {
                for (var i = 0; i < term.rows * 3; i++) {
                    term.writeln('test');
                }
                startYDisp = (term.rows * 2) + 1;
            });
            it('should scroll to requested line', function () {
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollToLine(0);
                chai_1.assert.equal(term.buffer.ydisp, 0);
                term.scrollToLine(10);
                chai_1.assert.equal(term.buffer.ydisp, 10);
                term.scrollToLine(startYDisp);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollToLine(20);
                chai_1.assert.equal(term.buffer.ydisp, 20);
            });
            it('should not scroll beyond boundary lines', function () {
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollToLine(-1);
                chai_1.assert.equal(term.buffer.ydisp, 0);
                term.scrollToLine(startYDisp + 1);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
            });
        });
        describe('keyDown', function () {
            it('should scroll down, when a key is pressed and terminal is scrolled up', function () {
                term._evaluateKeyEscapeSequence = function () {
                    return { key: 'a' };
                };
                var event = {
                    type: 'keydown',
                    keyCode: 0,
                    preventDefault: function () { },
                    stopPropagation: function () { }
                };
                term.buffer.ydisp = 0;
                term.buffer.ybase = 40;
                term.keyDown(event);
                chai_1.assert.equal(term.buffer.ydisp, term.buffer.ybase);
            });
            it('should not scroll down, when a custom keydown handler prevents the event', function () {
                for (var i = 0; i < term.rows * 3; i++) {
                    term.writeln('test');
                }
                var startYDisp = (term.rows * 2) + 1;
                term.attachCustomKeyEventHandler(function () {
                    return false;
                });
                chai_1.assert.equal(term.buffer.ydisp, startYDisp);
                term.scrollLines(-1);
                chai_1.assert.equal(term.buffer.ydisp, startYDisp - 1);
                term.keyDown({ keyCode: 0 });
                chai_1.assert.equal(term.buffer.ydisp, startYDisp - 1);
            });
        });
        describe('scroll() function', function () {
            describe('when scrollback > 0', function () {
                it('should create a new line and scroll', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(INIT_ROWS - 1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.y = INIT_ROWS - 1;
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS + 1);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'a');
                    chai_1.assert.equal(term.buffer.lines.get(INIT_ROWS - 1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'b');
                    chai_1.assert.equal(term.buffer.lines.get(INIT_ROWS)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], ' ');
                });
                it('should properly scroll inside a scroll region (scrollTop set)', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'c';
                    term.buffer.y = INIT_ROWS - 1;
                    term.buffer.scrollTop = 1;
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'a');
                    chai_1.assert.equal(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'c');
                });
                it('should properly scroll inside a scroll region (scrollBottom set)', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'c';
                    term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'd';
                    term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'e';
                    term.buffer.y = 3;
                    term.buffer.scrollBottom = 3;
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS + 1);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'a', '\'a\' should be pushed to the scrollback');
                    chai_1.assert.equal(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'b');
                    chai_1.assert.equal(term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'c');
                    chai_1.assert.equal(term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'd');
                    chai_1.assert.equal(term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], ' ', 'a blank line should be added at scrollBottom\'s index');
                    chai_1.assert.equal(term.buffer.lines.get(5)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'e');
                });
                it('should properly scroll inside a scroll region (scrollTop and scrollBottom set)', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'c';
                    term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'd';
                    term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'e';
                    term.buffer.y = INIT_ROWS - 1;
                    term.buffer.scrollTop = 1;
                    term.buffer.scrollBottom = 3;
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'a');
                    chai_1.assert.equal(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'c', '\'b\' should be removed from the buffer');
                    chai_1.assert.equal(term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'd');
                    chai_1.assert.equal(term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], ' ', 'a blank line should be added at scrollBottom\'s index');
                    chai_1.assert.equal(term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'e');
                });
            });
            describe('when scrollback === 0', function () {
                beforeEach(function () {
                    term.setOption('scrollback', 0);
                    chai_1.assert.equal(term.buffer.lines.maxLength, INIT_ROWS);
                });
                it('should create a new line and shift everything up', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.lines.get(INIT_ROWS - 1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'c';
                    term.buffer.y = INIT_ROWS - 1;
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS);
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'b');
                    chai_1.assert.equal(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], ' ');
                    chai_1.assert.equal(term.buffer.lines.get(INIT_ROWS - 2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'c');
                    chai_1.assert.equal(term.buffer.lines.get(INIT_ROWS - 1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], ' ');
                });
                it('should properly scroll inside a scroll region (scrollTop set)', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'c';
                    term.buffer.y = INIT_ROWS - 1;
                    term.buffer.scrollTop = 1;
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'a');
                    chai_1.assert.equal(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'c');
                });
                it('should properly scroll inside a scroll region (scrollBottom set)', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'c';
                    term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'd';
                    term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'e';
                    term.buffer.y = 3;
                    term.buffer.scrollBottom = 3;
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'b');
                    chai_1.assert.equal(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'c');
                    chai_1.assert.equal(term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'd');
                    chai_1.assert.equal(term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], ' ', 'a blank line should be added at scrollBottom\'s index');
                    chai_1.assert.equal(term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'e');
                });
                it('should properly scroll inside a scroll region (scrollTop and scrollBottom set)', function () {
                    term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'a';
                    term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'b';
                    term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'c';
                    term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'd';
                    term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX] = 'e';
                    term.buffer.y = INIT_ROWS - 1;
                    term.buffer.scrollTop = 1;
                    term.buffer.scrollBottom = 3;
                    term.scroll();
                    chai_1.assert.equal(term.buffer.lines.length, INIT_ROWS);
                    chai_1.assert.equal(term.buffer.lines.get(0)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'a');
                    chai_1.assert.equal(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'c', '\'b\' should be removed from the buffer');
                    chai_1.assert.equal(term.buffer.lines.get(2)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'd');
                    chai_1.assert.equal(term.buffer.lines.get(3)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], ' ', 'a blank line should be added at scrollBottom\'s index');
                    chai_1.assert.equal(term.buffer.lines.get(4)[0][Buffer_1.CHAR_DATA_CHAR_INDEX], 'e');
                });
            });
        });
    });
    describe('evaluateKeyEscapeSequence', function () {
        it('should return the correct escape sequence for unmodified keys', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 8 }).key, '\x7f');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 9 }).key, '\t');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 13 }).key, '\r');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 27 }).key, '\x1b');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 33 }).key, '\x1b[5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 34 }).key, '\x1b[6~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 35 }).key, '\x1b[F');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 36 }).key, '\x1b[H');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 37 }).key, '\x1b[D');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 38 }).key, '\x1b[A');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 39 }).key, '\x1b[C');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 40 }).key, '\x1b[B');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 45 }).key, '\x1b[2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 46 }).key, '\x1b[3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 112 }).key, '\x1bOP');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 113 }).key, '\x1bOQ');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 114 }).key, '\x1bOR');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 115 }).key, '\x1bOS');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 116 }).key, '\x1b[15~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 117 }).key, '\x1b[17~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 118 }).key, '\x1b[18~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 119 }).key, '\x1b[19~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 120 }).key, '\x1b[20~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 121 }).key, '\x1b[21~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 122 }).key, '\x1b[23~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ keyCode: 123 }).key, '\x1b[24~');
        });
        it('should return \\x1b[3;5~ for ctrl+delete', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 46 }).key, '\x1b[3;5~');
        });
        it('should return \\x1b[3;2~ for shift+delete', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 46 }).key, '\x1b[3;2~');
        });
        it('should return \\x1b[3;3~ for alt+delete', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 46 }).key, '\x1b[3;3~');
        });
        it('should return \\x1b[5D for ctrl+left', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 37 }).key, '\x1b[1;5D');
        });
        it('should return \\x1b[5C for ctrl+right', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 39 }).key, '\x1b[1;5C');
        });
        it('should return \\x1b[5A for ctrl+up', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 38 }).key, '\x1b[1;5A');
        });
        it('should return \\x1b[5B for ctrl+down', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 40 }).key, '\x1b[1;5B');
        });
        describe('On non-macOS platforms', function () {
            beforeEach(function () {
                term.browser.isMac = false;
            });
            it('should return \\x1b[5D for alt+left', function () {
                chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 37 }).key, '\x1b[1;5D');
            });
            it('should return \\x1b[5C for alt+right', function () {
                chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 39 }).key, '\x1b[1;5C');
            });
            it('should return \\x1ba for alt+a', function () {
                chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 65 }).key, '\x1ba');
            });
        });
        describe('On macOS platforms', function () {
            beforeEach(function () {
                term.browser.isMac = true;
            });
            it('should return \\x1bb for alt+left', function () {
                chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 37 }).key, '\x1bb');
            });
            it('should return \\x1bf for alt+right', function () {
                chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 39 }).key, '\x1bf');
            });
            it('should return undefined for alt+a', function () {
                chai_1.assert.strictEqual(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 65 }).key, undefined);
            });
        });
        describe('with macOptionIsMeta', function () {
            beforeEach(function () {
                term.browser.isMac = true;
                term.setOption('macOptionIsMeta', true);
            });
            it('should return \\x1ba for alt+a', function () {
                chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 65 }).key, '\x1ba');
            });
        });
        it('should return \\x1b[5A for alt+up', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 38 }).key, '\x1b[1;5A');
        });
        it('should return \\x1b[5B for alt+down', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 40 }).key, '\x1b[1;5B');
        });
        it('should return the correct escape sequence for modified F1-F12 keys', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 112 }).key, '\x1b[1;2P');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 113 }).key, '\x1b[1;2Q');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 114 }).key, '\x1b[1;2R');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 115 }).key, '\x1b[1;2S');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 116 }).key, '\x1b[15;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 117 }).key, '\x1b[17;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 118 }).key, '\x1b[18;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 119 }).key, '\x1b[19;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 120 }).key, '\x1b[20;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 121 }).key, '\x1b[21;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 122 }).key, '\x1b[23;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ shiftKey: true, keyCode: 123 }).key, '\x1b[24;2~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 112 }).key, '\x1b[1;3P');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 113 }).key, '\x1b[1;3Q');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 114 }).key, '\x1b[1;3R');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 115 }).key, '\x1b[1;3S');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 116 }).key, '\x1b[15;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 117 }).key, '\x1b[17;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 118 }).key, '\x1b[18;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 119 }).key, '\x1b[19;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 120 }).key, '\x1b[20;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 121 }).key, '\x1b[21;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 122 }).key, '\x1b[23;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, keyCode: 123 }).key, '\x1b[24;3~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 112 }).key, '\x1b[1;5P');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 113 }).key, '\x1b[1;5Q');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 114 }).key, '\x1b[1;5R');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 115 }).key, '\x1b[1;5S');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 116 }).key, '\x1b[15;5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 117 }).key, '\x1b[17;5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 118 }).key, '\x1b[18;5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 119 }).key, '\x1b[19;5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 120 }).key, '\x1b[20;5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 121 }).key, '\x1b[21;5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 122 }).key, '\x1b[23;5~');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ ctrlKey: true, keyCode: 123 }).key, '\x1b[24;5~');
        });
        it('should return proper sequence for ctrl+alt+a', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, ctrlKey: true, keyCode: 65 }).key, '\x1b\x01');
        });
        it('should return proper sequences for alt+0', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 48 }).key, '\x1b0');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 48 }).key, '\x1b)');
        });
        it('should return proper sequences for alt+1', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 49 }).key, '\x1b1');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 49 }).key, '\x1b!');
        });
        it('should return proper sequences for alt+2', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 50 }).key, '\x1b2');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 50 }).key, '\x1b@');
        });
        it('should return proper sequences for alt+3', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 51 }).key, '\x1b3');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 51 }).key, '\x1b#');
        });
        it('should return proper sequences for alt+4', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 52 }).key, '\x1b4');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 52 }).key, '\x1b$');
        });
        it('should return proper sequences for alt+5', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 53 }).key, '\x1b5');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 53 }).key, '\x1b%');
        });
        it('should return proper sequences for alt+6', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 54 }).key, '\x1b6');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 54 }).key, '\x1b^');
        });
        it('should return proper sequences for alt+7', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 55 }).key, '\x1b7');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 55 }).key, '\x1b&');
        });
        it('should return proper sequences for alt+8', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 56 }).key, '\x1b8');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 56 }).key, '\x1b*');
        });
        it('should return proper sequences for alt+9', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 57 }).key, '\x1b9');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 57 }).key, '\x1b(');
        });
        it('should return proper sequences for alt+;', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 186 }).key, '\x1b;');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 186 }).key, '\x1b:');
        });
        it('should return proper sequences for alt+=', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 187 }).key, '\x1b=');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 187 }).key, '\x1b+');
        });
        it('should return proper sequences for alt+,', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 188 }).key, '\x1b,');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 188 }).key, '\x1b<');
        });
        it('should return proper sequences for alt+-', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 189 }).key, '\x1b-');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 189 }).key, '\x1b_');
        });
        it('should return proper sequences for alt+.', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 190 }).key, '\x1b.');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 190 }).key, '\x1b>');
        });
        it('should return proper sequences for alt+/', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 191 }).key, '\x1b/');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 191 }).key, '\x1b?');
        });
        it('should return proper sequences for alt+~', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 192 }).key, '\x1b`');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 192 }).key, '\x1b~');
        });
        it('should return proper sequences for alt+[', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 219 }).key, '\x1b[');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 219 }).key, '\x1b{');
        });
        it('should return proper sequences for alt+\\', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 220 }).key, '\x1b\\');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 220 }).key, '\x1b|');
        });
        it('should return proper sequences for alt+]', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 221 }).key, '\x1b]');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 221 }).key, '\x1b}');
        });
        it('should return proper sequences for alt+\'', function () {
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: false, keyCode: 222 }).key, '\x1b\'');
            chai_1.assert.equal(term.evaluateKeyEscapeSequence({ altKey: true, shiftKey: true, keyCode: 222 }).key, '\x1b"');
        });
    });
    describe('Third level shift', function () {
        var evKeyDown;
        var evKeyPress;
        beforeEach(function () {
            term.handler = function () { };
            term.showCursor = function () { };
            term.clearSelection = function () { };
            evKeyDown = {
                preventDefault: function () { },
                stopPropagation: function () { },
                type: 'keydown',
                altKey: null,
                keyCode: null
            };
            evKeyPress = {
                preventDefault: function () { },
                stopPropagation: function () { },
                type: 'keypress',
                altKey: null,
                charCode: null,
                keyCode: null
            };
        });
        describe('with macOptionIsMeta', function () {
            beforeEach(function () {
                term.browser.isMac = true;
                term.setOption('macOptionIsMeta', true);
            });
            it('should interfere with the alt key on keyDown', function () {
                evKeyDown.altKey = true;
                evKeyDown.keyCode = 81;
                chai_1.assert.equal(term.keyDown(evKeyDown), false);
                evKeyDown.altKey = true;
                evKeyDown.keyCode = 192;
                chai_1.assert.equal(term.keyDown(evKeyDown), false);
            });
        });
        describe('On Mac OS', function () {
            beforeEach(function () {
                term.browser.isMac = true;
            });
            it('should not interfere with the alt key on keyDown', function () {
                evKeyDown.altKey = true;
                evKeyDown.keyCode = 81;
                chai_1.assert.equal(term.keyDown(evKeyDown), true);
                evKeyDown.altKey = true;
                evKeyDown.keyCode = 192;
                chai_1.assert.equal(term.keyDown(evKeyDown), true);
            });
            it('should interefere with the alt + arrow keys', function () {
                evKeyDown.altKey = true;
                evKeyDown.keyCode = 37;
                chai_1.assert.equal(term.keyDown(evKeyDown), false);
                evKeyDown.altKey = true;
                evKeyDown.keyCode = 39;
                chai_1.assert.equal(term.keyDown(evKeyDown), false);
            });
            it('should emit key with alt + key on keyPress', function (done) {
                var keys = ['@', '@', '\\', '\\', '|', '|'];
                term.on('keypress', function (key) {
                    if (key) {
                        var index = keys.indexOf(key);
                        chai_1.assert(index !== -1, 'Emitted wrong key: ' + key);
                        keys.splice(index, 1);
                    }
                    if (keys.length === 0)
                        done();
                });
                evKeyPress.altKey = true;
                evKeyPress.charCode = null;
                evKeyPress.keyCode = 64;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = 64;
                evKeyPress.keyCode = 0;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = null;
                evKeyPress.keyCode = 92;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = 92;
                evKeyPress.keyCode = 0;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = null;
                evKeyPress.keyCode = 124;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = 124;
                evKeyPress.keyCode = 0;
                term.keyPress(evKeyPress);
            });
        });
        describe('On MS Windows', function () {
            beforeEach(function () {
                term.browser.isMSWindows = true;
            });
            it('should not interfere with the alt + ctrl key on keyDown', function () {
                evKeyPress.altKey = true;
                evKeyPress.ctrlKey = true;
                evKeyPress.keyCode = 81;
                chai_1.assert.equal(term.keyDown(evKeyPress), true);
                evKeyDown.altKey = true;
                evKeyDown.ctrlKey = true;
                evKeyDown.keyCode = 81;
                chai_1.assert.equal(term.keyDown(evKeyDown), true);
            });
            it('should interefere with the alt + ctrl + arrow keys', function () {
                evKeyDown.altKey = true;
                evKeyDown.ctrlKey = true;
                evKeyDown.keyCode = 37;
                chai_1.assert.equal(term.keyDown(evKeyDown), false);
                evKeyDown.keyCode = 39;
                chai_1.assert.equal(term.keyDown(evKeyDown), false);
            });
            it('should emit key with alt + ctrl + key on keyPress', function (done) {
                var keys = ['@', '@', '\\', '\\', '|', '|'];
                term.on('keypress', function (key) {
                    if (key) {
                        var index = keys.indexOf(key);
                        chai_1.assert(index !== -1, 'Emitted wrong key: ' + key);
                        keys.splice(index, 1);
                    }
                    if (keys.length === 0)
                        done();
                });
                evKeyPress.altKey = true;
                evKeyPress.ctrlKey = true;
                evKeyPress.charCode = null;
                evKeyPress.keyCode = 64;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = 64;
                evKeyPress.keyCode = 0;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = null;
                evKeyPress.keyCode = 92;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = 92;
                evKeyPress.keyCode = 0;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = null;
                evKeyPress.keyCode = 124;
                term.keyPress(evKeyPress);
                evKeyPress.charCode = 124;
                evKeyPress.keyCode = 0;
                term.keyPress(evKeyPress);
            });
        });
    });
    describe('unicode - surrogates', function () {
        it('2 characters per cell', function () {
            this.timeout(10000);
            var high = String.fromCharCode(0xD800);
            for (var i = 0xDC00; i <= 0xDCFF; ++i) {
                term.write(high + String.fromCharCode(i));
                var tchar = term.buffer.lines.get(0)[0];
                chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(high + String.fromCharCode(i));
                chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
                chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
                chai_1.expect(term.buffer.lines.get(0)[1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
                term.reset();
            }
        });
        it('2 characters at last cell', function () {
            var high = String.fromCharCode(0xD800);
            for (var i = 0xDC00; i <= 0xDCFF; ++i) {
                term.buffer.x = term.cols - 1;
                term.write(high + String.fromCharCode(i));
                chai_1.expect(term.buffer.lines.get(0)[term.buffer.x - 1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(high + String.fromCharCode(i));
                chai_1.expect(term.buffer.lines.get(0)[term.buffer.x - 1][Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
                chai_1.expect(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
                term.reset();
            }
        });
        it('2 characters per cell over line end with autowrap', function () {
            var high = String.fromCharCode(0xD800);
            for (var i = 0xDC00; i <= 0xDCFF; ++i) {
                term.buffer.x = term.cols - 1;
                term.wraparoundMode = true;
                term.write('a' + high + String.fromCharCode(i));
                chai_1.expect(term.buffer.lines.get(0)[term.cols - 1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('a');
                chai_1.expect(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(high + String.fromCharCode(i));
                chai_1.expect(term.buffer.lines.get(1)[0][Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
                chai_1.expect(term.buffer.lines.get(1)[1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
                term.reset();
            }
        });
        it('2 characters per cell over line end without autowrap', function () {
            var high = String.fromCharCode(0xD800);
            for (var i = 0xDC00; i <= 0xDCFF; ++i) {
                term.buffer.x = term.cols - 1;
                term.wraparoundMode = false;
                term.write('a' + high + String.fromCharCode(i));
                chai_1.expect(term.buffer.lines.get(0)[term.cols - 1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('a');
                chai_1.expect(term.buffer.lines.get(0)[term.cols - 1][Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
                chai_1.expect(term.buffer.lines.get(1)[1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
                term.reset();
            }
        });
        it('splitted surrogates', function () {
            var high = String.fromCharCode(0xD800);
            for (var i = 0xDC00; i <= 0xDCFF; ++i) {
                term.write(high);
                term.write(String.fromCharCode(i));
                var tchar = term.buffer.lines.get(0)[0];
                chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(high + String.fromCharCode(i));
                chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
                chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
                chai_1.expect(term.buffer.lines.get(0)[1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
                term.reset();
            }
        });
    });
    describe('unicode - combining characters', function () {
        it('café', function () {
            term.write('cafe\u0301');
            chai_1.expect(term.buffer.lines.get(0)[3][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('e\u0301');
            chai_1.expect(term.buffer.lines.get(0)[3][Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
            chai_1.expect(term.buffer.lines.get(0)[3][Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
        });
        it('café - end of line', function () {
            term.buffer.x = term.cols - 1 - 3;
            term.write('cafe\u0301');
            chai_1.expect(term.buffer.lines.get(0)[term.cols - 1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('e\u0301');
            chai_1.expect(term.buffer.lines.get(0)[term.cols - 1][Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
            chai_1.expect(term.buffer.lines.get(0)[term.cols - 1][Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
            chai_1.expect(term.buffer.lines.get(0)[1][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
            chai_1.expect(term.buffer.lines.get(0)[1][Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
            chai_1.expect(term.buffer.lines.get(0)[1][Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
        });
        it('multiple combined é', function () {
            term.wraparoundMode = true;
            term.write(Array(100).join('e\u0301'));
            for (var i = 0; i < term.cols; ++i) {
                var tchar_1 = term.buffer.lines.get(0)[i];
                chai_1.expect(tchar_1[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('e\u0301');
                chai_1.expect(tchar_1[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
                chai_1.expect(tchar_1[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
            }
            var tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('e\u0301');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
        });
        it('multiple surrogate with combined', function () {
            term.wraparoundMode = true;
            term.write(Array(100).join('\uD800\uDC00\u0301'));
            for (var i = 0; i < term.cols; ++i) {
                var tchar_2 = term.buffer.lines.get(0)[i];
                chai_1.expect(tchar_2[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('\uD800\uDC00\u0301');
                chai_1.expect(tchar_2[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(3);
                chai_1.expect(tchar_2[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
            }
            var tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('\uD800\uDC00\u0301');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(3);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
        });
    });
    describe('unicode - fullwidth characters', function () {
        it('cursor movement even', function () {
            chai_1.expect(term.buffer.x).eql(0);
            term.write('￥');
            chai_1.expect(term.buffer.x).eql(2);
        });
        it('cursor movement odd', function () {
            term.buffer.x = 1;
            chai_1.expect(term.buffer.x).eql(1);
            term.write('￥');
            chai_1.expect(term.buffer.x).eql(3);
        });
        it('line of ￥ even', function () {
            term.wraparoundMode = true;
            term.write(Array(50).join('￥'));
            for (var i = 0; i < term.cols; ++i) {
                var tchar_3 = term.buffer.lines.get(0)[i];
                if (i % 2) {
                    chai_1.expect(tchar_3[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
                    chai_1.expect(tchar_3[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(0);
                    chai_1.expect(tchar_3[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(0);
                }
                else {
                    chai_1.expect(tchar_3[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
                    chai_1.expect(tchar_3[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
                    chai_1.expect(tchar_3[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
                }
            }
            var tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
        });
        it('line of ￥ odd', function () {
            term.wraparoundMode = true;
            term.buffer.x = 1;
            term.write(Array(50).join('￥'));
            for (var i = 1; i < term.cols - 1; ++i) {
                var tchar_4 = term.buffer.lines.get(0)[i];
                if (!(i % 2)) {
                    chai_1.expect(tchar_4[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
                    chai_1.expect(tchar_4[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(0);
                    chai_1.expect(tchar_4[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(0);
                }
                else {
                    chai_1.expect(tchar_4[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
                    chai_1.expect(tchar_4[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
                    chai_1.expect(tchar_4[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
                }
            }
            var tchar = term.buffer.lines.get(0)[term.cols - 1];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
            tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
        });
        it('line of ￥ with combining odd', function () {
            term.wraparoundMode = true;
            term.buffer.x = 1;
            term.write(Array(50).join('￥\u0301'));
            for (var i = 1; i < term.cols - 1; ++i) {
                var tchar_5 = term.buffer.lines.get(0)[i];
                if (!(i % 2)) {
                    chai_1.expect(tchar_5[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
                    chai_1.expect(tchar_5[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(0);
                    chai_1.expect(tchar_5[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(0);
                }
                else {
                    chai_1.expect(tchar_5[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥\u0301');
                    chai_1.expect(tchar_5[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
                    chai_1.expect(tchar_5[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
                }
            }
            var tchar = term.buffer.lines.get(0)[term.cols - 1];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
            tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥\u0301');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
        });
        it('line of ￥ with combining even', function () {
            term.wraparoundMode = true;
            term.write(Array(50).join('￥\u0301'));
            for (var i = 0; i < term.cols; ++i) {
                var tchar_6 = term.buffer.lines.get(0)[i];
                if (i % 2) {
                    chai_1.expect(tchar_6[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
                    chai_1.expect(tchar_6[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(0);
                    chai_1.expect(tchar_6[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(0);
                }
                else {
                    chai_1.expect(tchar_6[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥\u0301');
                    chai_1.expect(tchar_6[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
                    chai_1.expect(tchar_6[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
                }
            }
            var tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥\u0301');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(2);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
        });
        it('line of surrogate fullwidth with combining odd', function () {
            term.wraparoundMode = true;
            term.buffer.x = 1;
            term.write(Array(50).join('\ud843\ude6d\u0301'));
            for (var i = 1; i < term.cols - 1; ++i) {
                var tchar_7 = term.buffer.lines.get(0)[i];
                if (!(i % 2)) {
                    chai_1.expect(tchar_7[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
                    chai_1.expect(tchar_7[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(0);
                    chai_1.expect(tchar_7[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(0);
                }
                else {
                    chai_1.expect(tchar_7[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('\ud843\ude6d\u0301');
                    chai_1.expect(tchar_7[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(3);
                    chai_1.expect(tchar_7[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
                }
            }
            var tchar = term.buffer.lines.get(0)[term.cols - 1];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(1);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(1);
            tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('\ud843\ude6d\u0301');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(3);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
        });
        it('line of surrogate fullwidth with combining even', function () {
            term.wraparoundMode = true;
            term.write(Array(50).join('\ud843\ude6d\u0301'));
            for (var i = 0; i < term.cols; ++i) {
                var tchar_8 = term.buffer.lines.get(0)[i];
                if (i % 2) {
                    chai_1.expect(tchar_8[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
                    chai_1.expect(tchar_8[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(0);
                    chai_1.expect(tchar_8[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(0);
                }
                else {
                    chai_1.expect(tchar_8[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('\ud843\ude6d\u0301');
                    chai_1.expect(tchar_8[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(3);
                    chai_1.expect(tchar_8[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
                }
            }
            var tchar = term.buffer.lines.get(1)[0];
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('\ud843\ude6d\u0301');
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_CHAR_INDEX].length).eql(3);
            chai_1.expect(tchar[Buffer_1.CHAR_DATA_WIDTH_INDEX]).eql(2);
        });
    });
    describe('insert mode', function () {
        it('halfwidth - all', function () {
            term.write(Array(9).join('0123456789').slice(-80));
            term.buffer.x = 10;
            term.buffer.y = 0;
            term.insertMode = true;
            term.write('abcde');
            chai_1.expect(term.buffer.lines.get(0).length).eql(term.cols);
            chai_1.expect(term.buffer.lines.get(0)[10][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('a');
            chai_1.expect(term.buffer.lines.get(0)[14][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('e');
            chai_1.expect(term.buffer.lines.get(0)[15][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('0');
            chai_1.expect(term.buffer.lines.get(0)[79][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('4');
        });
        it('fullwidth - insert', function () {
            term.write(Array(9).join('0123456789').slice(-80));
            term.buffer.x = 10;
            term.buffer.y = 0;
            term.insertMode = true;
            term.write('￥￥￥');
            chai_1.expect(term.buffer.lines.get(0).length).eql(term.cols);
            chai_1.expect(term.buffer.lines.get(0)[10][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
            chai_1.expect(term.buffer.lines.get(0)[11][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
            chai_1.expect(term.buffer.lines.get(0)[14][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
            chai_1.expect(term.buffer.lines.get(0)[15][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
            chai_1.expect(term.buffer.lines.get(0)[79][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('3');
        });
        it('fullwidth - right border', function () {
            term.write(Array(41).join('￥'));
            term.buffer.x = 10;
            term.buffer.y = 0;
            term.insertMode = true;
            term.write('a');
            chai_1.expect(term.buffer.lines.get(0).length).eql(term.cols);
            chai_1.expect(term.buffer.lines.get(0)[10][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('a');
            chai_1.expect(term.buffer.lines.get(0)[11][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
            chai_1.expect(term.buffer.lines.get(0)[79][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql(' ');
            term.write('b');
            chai_1.expect(term.buffer.lines.get(0).length).eql(term.cols);
            chai_1.expect(term.buffer.lines.get(0)[11][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('b');
            chai_1.expect(term.buffer.lines.get(0)[12][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('￥');
            chai_1.expect(term.buffer.lines.get(0)[79][Buffer_1.CHAR_DATA_CHAR_INDEX]).eql('');
        });
    });
});

//# sourceMappingURL=Terminal.test.js.map

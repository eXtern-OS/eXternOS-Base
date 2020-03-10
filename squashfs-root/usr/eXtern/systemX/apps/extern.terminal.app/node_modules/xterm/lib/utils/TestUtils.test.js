"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Buffer_1 = require("../Buffer");
var Browser = require("../shared/utils/Browser");
var MockTerminal = (function () {
    function MockTerminal() {
        this.options = {};
        this.browser = Browser;
    }
    MockTerminal.prototype.addMarker = function (cursorYOffset) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.selectLines = function (start, end) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.scrollToLine = function (line) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.getOption = function (key) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.setOption = function (key, value) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.blur = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.focus = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.resize = function (columns, rows) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.writeln = function (data) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.open = function (parent) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.attachCustomKeyEventHandler = function (customKeyEventHandler) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.registerLinkMatcher = function (regex, handler, options) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.deregisterLinkMatcher = function (matcherId) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.hasSelection = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.getSelection = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.clearSelection = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.selectAll = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.destroy = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.scrollPages = function (pageCount) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.scrollToTop = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.scrollToBottom = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.clear = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.write = function (data) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.send = function (data) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.handler = function (data) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.on = function (event, callback) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.off = function (type, listener) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.addDisposableListener = function (type, handler) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.scrollLines = function (disp, suppressScrollEvent) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.scrollToRow = function (absoluteRow) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.cancel = function (ev, force) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.log = function (text) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.emit = function (event, data) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.reset = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.showCursor = function () {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.refresh = function (start, end) {
        throw new Error('Method not implemented.');
    };
    MockTerminal.prototype.blankLine = function (cur, isWrapped, cols) {
        var line = [];
        cols = cols || this.cols;
        for (var i = 0; i < cols; i++) {
            line.push([0, ' ', 1, 32]);
        }
        return line;
    };
    return MockTerminal;
}());
exports.MockTerminal = MockTerminal;
var MockCharMeasure = (function () {
    function MockCharMeasure() {
    }
    MockCharMeasure.prototype.measure = function (options) {
        throw new Error('Method not implemented.');
    };
    return MockCharMeasure;
}());
exports.MockCharMeasure = MockCharMeasure;
var MockInputHandlingTerminal = (function () {
    function MockInputHandlingTerminal() {
        this.options = {};
        this.buffer = new MockBuffer();
    }
    MockInputHandlingTerminal.prototype.focus = function () {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.bell = function () {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.updateRange = function (y) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.scroll = function (isWrapped) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.nextStop = function (x) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.setgLevel = function (g) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.eraseAttr = function () {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.eraseRight = function (x, y) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.eraseLine = function (y) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.eraseLeft = function (x, y) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.blankLine = function (cur, isWrapped) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.prevStop = function (x) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.is = function (term) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.send = function (data) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.setgCharset = function (g, charset) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.resize = function (x, y) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.log = function (text, data) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.reset = function () {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.showCursor = function () {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.refresh = function (start, end) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.matchColor = function (r1, g1, b1) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.error = function (text, data) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.setOption = function (key, value) {
        this.options[key] = value;
    };
    MockInputHandlingTerminal.prototype.on = function (type, listener) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.off = function (type, listener) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.emit = function (type, data) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.addDisposableListener = function (type, handler) {
        throw new Error('Method not implemented.');
    };
    MockInputHandlingTerminal.prototype.tabSet = function () {
        throw new Error('Method not implemented.');
    };
    return MockInputHandlingTerminal;
}());
exports.MockInputHandlingTerminal = MockInputHandlingTerminal;
var MockBuffer = (function () {
    function MockBuffer() {
    }
    MockBuffer.prototype.translateBufferLineToString = function (lineIndex, trimRight, startCol, endCol) {
        return Buffer_1.Buffer.prototype.translateBufferLineToString.apply(this, arguments);
    };
    MockBuffer.prototype.nextStop = function (x) {
        throw new Error('Method not implemented.');
    };
    MockBuffer.prototype.prevStop = function (x) {
        throw new Error('Method not implemented.');
    };
    return MockBuffer;
}());
exports.MockBuffer = MockBuffer;
var MockRenderer = (function () {
    function MockRenderer() {
    }
    MockRenderer.prototype.on = function (type, listener) {
        throw new Error('Method not implemented.');
    };
    MockRenderer.prototype.off = function (type, listener) {
        throw new Error('Method not implemented.');
    };
    MockRenderer.prototype.emit = function (type, data) {
        throw new Error('Method not implemented.');
    };
    MockRenderer.prototype.addDisposableListener = function (type, handler) {
        throw new Error('Method not implemented.');
    };
    MockRenderer.prototype.setTheme = function (theme) { return {}; };
    MockRenderer.prototype.onResize = function (cols, rows) { };
    MockRenderer.prototype.onCharSizeChanged = function () { };
    MockRenderer.prototype.onBlur = function () { };
    MockRenderer.prototype.onFocus = function () { };
    MockRenderer.prototype.onSelectionChanged = function (start, end) { };
    MockRenderer.prototype.onCursorMove = function () { };
    MockRenderer.prototype.onOptionsChanged = function () { };
    MockRenderer.prototype.onWindowResize = function (devicePixelRatio) { };
    MockRenderer.prototype.clear = function () { };
    MockRenderer.prototype.refreshRows = function (start, end) { };
    return MockRenderer;
}());
exports.MockRenderer = MockRenderer;
var MockViewport = (function () {
    function MockViewport() {
        this.scrollBarWidth = 0;
    }
    MockViewport.prototype.onThemeChanged = function (colors) {
        throw new Error('Method not implemented.');
    };
    MockViewport.prototype.onWheel = function (ev) {
        throw new Error('Method not implemented.');
    };
    MockViewport.prototype.onTouchStart = function (ev) {
        throw new Error('Method not implemented.');
    };
    MockViewport.prototype.onTouchMove = function (ev) {
        throw new Error('Method not implemented.');
    };
    MockViewport.prototype.syncScrollArea = function () { };
    MockViewport.prototype.getLinesScrolled = function (ev) {
        throw new Error('Method not implemented.');
    };
    return MockViewport;
}());
exports.MockViewport = MockViewport;
var MockCompositionHelper = (function () {
    function MockCompositionHelper() {
    }
    MockCompositionHelper.prototype.compositionstart = function () {
        throw new Error('Method not implemented.');
    };
    MockCompositionHelper.prototype.compositionupdate = function (ev) {
        throw new Error('Method not implemented.');
    };
    MockCompositionHelper.prototype.compositionend = function () {
        throw new Error('Method not implemented.');
    };
    MockCompositionHelper.prototype.updateCompositionElements = function (dontRecurse) {
        throw new Error('Method not implemented.');
    };
    MockCompositionHelper.prototype.keydown = function (ev) {
        return true;
    };
    return MockCompositionHelper;
}());
exports.MockCompositionHelper = MockCompositionHelper;

//# sourceMappingURL=TestUtils.test.js.map

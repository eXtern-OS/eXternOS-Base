"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Strings = require("./Strings");
var Browser_1 = require("./shared/utils/Browser");
var RenderDebouncer_1 = require("./utils/RenderDebouncer");
var Dom_1 = require("./utils/Dom");
var MAX_ROWS_TO_READ = 20;
var BoundaryPosition;
(function (BoundaryPosition) {
    BoundaryPosition[BoundaryPosition["Top"] = 0] = "Top";
    BoundaryPosition[BoundaryPosition["Bottom"] = 1] = "Bottom";
})(BoundaryPosition || (BoundaryPosition = {}));
var AccessibilityManager = (function () {
    function AccessibilityManager(_terminal) {
        var _this = this;
        this._terminal = _terminal;
        this._liveRegionLineCount = 0;
        this._disposables = [];
        this._charsToConsume = [];
        this._accessibilityTreeRoot = document.createElement('div');
        this._accessibilityTreeRoot.classList.add('xterm-accessibility');
        this._rowContainer = document.createElement('div');
        this._rowContainer.classList.add('xterm-accessibility-tree');
        this._rowElements = [];
        for (var i = 0; i < this._terminal.rows; i++) {
            this._rowElements[i] = this._createAccessibilityTreeNode();
            this._rowContainer.appendChild(this._rowElements[i]);
        }
        this._topBoundaryFocusListener = function (e) { return _this._onBoundaryFocus(e, BoundaryPosition.Top); };
        this._bottomBoundaryFocusListener = function (e) { return _this._onBoundaryFocus(e, BoundaryPosition.Bottom); };
        this._rowElements[0].addEventListener('focus', this._topBoundaryFocusListener);
        this._rowElements[this._rowElements.length - 1].addEventListener('focus', this._bottomBoundaryFocusListener);
        this._refreshRowsDimensions();
        this._accessibilityTreeRoot.appendChild(this._rowContainer);
        this._renderRowsDebouncer = new RenderDebouncer_1.RenderDebouncer(this._terminal, this._renderRows.bind(this));
        this._refreshRows();
        this._liveRegion = document.createElement('div');
        this._liveRegion.classList.add('live-region');
        this._liveRegion.setAttribute('aria-live', 'assertive');
        this._accessibilityTreeRoot.appendChild(this._liveRegion);
        this._terminal.element.insertAdjacentElement('afterbegin', this._accessibilityTreeRoot);
        this._disposables.push(this._renderRowsDebouncer);
        this._disposables.push(this._terminal.addDisposableListener('resize', function (data) { return _this._onResize(data.cols, data.rows); }));
        this._disposables.push(this._terminal.addDisposableListener('refresh', function (data) { return _this._refreshRows(data.start, data.end); }));
        this._disposables.push(this._terminal.addDisposableListener('scroll', function (data) { return _this._refreshRows(); }));
        this._disposables.push(this._terminal.addDisposableListener('a11y.char', function (char) { return _this._onChar(char); }));
        this._disposables.push(this._terminal.addDisposableListener('linefeed', function () { return _this._onChar('\n'); }));
        this._disposables.push(this._terminal.addDisposableListener('a11y.tab', function (spaceCount) { return _this._onTab(spaceCount); }));
        this._disposables.push(this._terminal.addDisposableListener('key', function (keyChar) { return _this._onKey(keyChar); }));
        this._disposables.push(this._terminal.addDisposableListener('blur', function () { return _this._clearLiveRegion(); }));
        this._disposables.push(this._terminal.addDisposableListener('dprchange', function () { return _this._refreshRowsDimensions(); }));
        this._disposables.push(this._terminal.renderer.addDisposableListener('resize', function () { return _this._refreshRowsDimensions(); }));
        this._disposables.push(Dom_1.addDisposableListener(window, 'resize', function () { return _this._refreshRowsDimensions(); }));
    }
    AccessibilityManager.prototype.dispose = function () {
        this._disposables.forEach(function (d) { return d.dispose(); });
        this._disposables.length = 0;
        this._terminal.element.removeChild(this._accessibilityTreeRoot);
        this._rowElements.length = 0;
    };
    AccessibilityManager.prototype._onBoundaryFocus = function (e, position) {
        var boundaryElement = e.target;
        var beforeBoundaryElement = this._rowElements[position === BoundaryPosition.Top ? 1 : this._rowElements.length - 2];
        var posInSet = boundaryElement.getAttribute('aria-posinset');
        var lastRowPos = position === BoundaryPosition.Top ? '1' : "" + this._terminal.buffer.lines.length;
        if (posInSet === lastRowPos) {
            return;
        }
        if (e.relatedTarget !== beforeBoundaryElement) {
            return;
        }
        var topBoundaryElement;
        var bottomBoundaryElement;
        if (position === BoundaryPosition.Top) {
            topBoundaryElement = boundaryElement;
            bottomBoundaryElement = this._rowElements.pop();
            this._rowContainer.removeChild(bottomBoundaryElement);
        }
        else {
            topBoundaryElement = this._rowElements.shift();
            bottomBoundaryElement = boundaryElement;
            this._rowContainer.removeChild(topBoundaryElement);
        }
        topBoundaryElement.removeEventListener('focus', this._topBoundaryFocusListener);
        bottomBoundaryElement.removeEventListener('focus', this._bottomBoundaryFocusListener);
        if (position === BoundaryPosition.Top) {
            var newElement = this._createAccessibilityTreeNode();
            this._rowElements.unshift(newElement);
            this._rowContainer.insertAdjacentElement('afterbegin', newElement);
        }
        else {
            var newElement = this._createAccessibilityTreeNode();
            this._rowElements.push(newElement);
            this._rowContainer.appendChild(newElement);
        }
        this._rowElements[0].addEventListener('focus', this._topBoundaryFocusListener);
        this._rowElements[this._rowElements.length - 1].addEventListener('focus', this._bottomBoundaryFocusListener);
        this._terminal.scrollLines(position === BoundaryPosition.Top ? -1 : 1);
        this._rowElements[position === BoundaryPosition.Top ? 1 : this._rowElements.length - 2].focus();
        e.preventDefault();
        e.stopImmediatePropagation();
    };
    AccessibilityManager.prototype._onResize = function (cols, rows) {
        this._rowElements[this._rowElements.length - 1].removeEventListener('focus', this._bottomBoundaryFocusListener);
        for (var i = this._rowContainer.children.length; i < this._terminal.rows; i++) {
            this._rowElements[i] = this._createAccessibilityTreeNode();
            this._rowContainer.appendChild(this._rowElements[i]);
        }
        while (this._rowElements.length > rows) {
            this._rowContainer.removeChild(this._rowElements.pop());
        }
        this._rowElements[this._rowElements.length - 1].addEventListener('focus', this._bottomBoundaryFocusListener);
        this._refreshRowsDimensions();
    };
    AccessibilityManager.prototype._createAccessibilityTreeNode = function () {
        var element = document.createElement('div');
        element.setAttribute('role', 'listitem');
        element.tabIndex = -1;
        this._refreshRowDimensions(element);
        return element;
    };
    AccessibilityManager.prototype._onTab = function (spaceCount) {
        for (var i = 0; i < spaceCount; i++) {
            this._onChar(' ');
        }
    };
    AccessibilityManager.prototype._onChar = function (char) {
        var _this = this;
        if (this._liveRegionLineCount < MAX_ROWS_TO_READ + 1) {
            if (this._charsToConsume.length > 0) {
                var shiftedChar = this._charsToConsume.shift();
                if (shiftedChar !== char) {
                    this._announceCharacter(char);
                }
            }
            else {
                this._announceCharacter(char);
            }
            if (char === '\n') {
                this._liveRegionLineCount++;
                if (this._liveRegionLineCount === MAX_ROWS_TO_READ + 1) {
                    this._liveRegion.textContent += Strings.tooMuchOutput;
                }
            }
            if (Browser_1.isMac) {
                if (this._liveRegion.textContent && this._liveRegion.textContent.length > 0 && !this._liveRegion.parentNode) {
                    setTimeout(function () {
                        _this._accessibilityTreeRoot.appendChild(_this._liveRegion);
                    }, 0);
                }
            }
        }
    };
    AccessibilityManager.prototype._clearLiveRegion = function () {
        this._liveRegion.textContent = '';
        this._liveRegionLineCount = 0;
        if (Browser_1.isMac) {
            if (this._liveRegion.parentNode) {
                this._accessibilityTreeRoot.removeChild(this._liveRegion);
            }
        }
    };
    AccessibilityManager.prototype._onKey = function (keyChar) {
        this._clearLiveRegion();
        this._charsToConsume.push(keyChar);
    };
    AccessibilityManager.prototype._refreshRows = function (start, end) {
        this._renderRowsDebouncer.refresh(start, end);
    };
    AccessibilityManager.prototype._renderRows = function (start, end) {
        var buffer = this._terminal.buffer;
        var setSize = buffer.lines.length.toString();
        for (var i = start; i <= end; i++) {
            var lineData = buffer.translateBufferLineToString(buffer.ydisp + i, true);
            var posInSet = (buffer.ydisp + i + 1).toString();
            var element = this._rowElements[i];
            element.textContent = lineData.length === 0 ? Strings.blankLine : lineData;
            element.setAttribute('aria-posinset', posInSet);
            element.setAttribute('aria-setsize', setSize);
        }
    };
    AccessibilityManager.prototype._refreshRowsDimensions = function () {
        if (!this._terminal.renderer.dimensions.actualCellHeight) {
            return;
        }
        for (var i = 0; i < this._terminal.rows; i++) {
            this._refreshRowDimensions(this._rowElements[i]);
        }
    };
    AccessibilityManager.prototype._refreshRowDimensions = function (element) {
        element.style.height = this._terminal.renderer.dimensions.actualCellHeight + "px";
    };
    AccessibilityManager.prototype._announceCharacter = function (char) {
        if (char === ' ') {
            this._liveRegion.innerHTML += '&nbsp;';
        }
        else {
            this._liveRegion.textContent += char;
        }
    };
    return AccessibilityManager;
}());
exports.AccessibilityManager = AccessibilityManager;

//# sourceMappingURL=AccessibilityManager.js.map

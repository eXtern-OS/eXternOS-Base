"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var FALLBACK_SCROLL_BAR_WIDTH = 15;
var Viewport = (function () {
    function Viewport(_terminal, _viewportElement, _scrollArea, _charMeasure) {
        var _this = this;
        this._terminal = _terminal;
        this._viewportElement = _viewportElement;
        this._scrollArea = _scrollArea;
        this._charMeasure = _charMeasure;
        this.scrollBarWidth = 0;
        this._currentRowHeight = 0;
        this._lastRecordedBufferLength = 0;
        this._lastRecordedViewportHeight = 0;
        this._lastRecordedBufferHeight = 0;
        this._wheelPartialScroll = 0;
        this.scrollBarWidth = (this._viewportElement.offsetWidth - this._scrollArea.offsetWidth) || FALLBACK_SCROLL_BAR_WIDTH;
        this._viewportElement.addEventListener('scroll', this._onScroll.bind(this));
        setTimeout(function () { return _this.syncScrollArea(); }, 0);
    }
    Viewport.prototype.onThemeChanged = function (colors) {
        this._viewportElement.style.backgroundColor = colors.background.css;
    };
    Viewport.prototype._refresh = function () {
        if (this._charMeasure.height > 0) {
            this._currentRowHeight = this._terminal.renderer.dimensions.scaledCellHeight / window.devicePixelRatio;
            this._lastRecordedViewportHeight = this._viewportElement.offsetHeight;
            var newBufferHeight = Math.round(this._currentRowHeight * this._lastRecordedBufferLength) + (this._lastRecordedViewportHeight - this._terminal.renderer.dimensions.canvasHeight);
            if (this._lastRecordedBufferHeight !== newBufferHeight) {
                this._lastRecordedBufferHeight = newBufferHeight;
                this._scrollArea.style.height = this._lastRecordedBufferHeight + 'px';
            }
        }
    };
    Viewport.prototype.syncScrollArea = function () {
        if (this._lastRecordedBufferLength !== this._terminal.buffer.lines.length) {
            this._lastRecordedBufferLength = this._terminal.buffer.lines.length;
            this._refresh();
        }
        else if (this._lastRecordedViewportHeight !== this._terminal.renderer.dimensions.canvasHeight) {
            this._refresh();
        }
        else {
            if (this._terminal.renderer.dimensions.scaledCellHeight / window.devicePixelRatio !== this._currentRowHeight) {
                this._refresh();
            }
        }
        var scrollTop = this._terminal.buffer.ydisp * this._currentRowHeight;
        if (this._viewportElement.scrollTop !== scrollTop) {
            this._viewportElement.scrollTop = scrollTop;
        }
    };
    Viewport.prototype._onScroll = function (ev) {
        if (!this._viewportElement.offsetParent) {
            return;
        }
        var newRow = Math.round(this._viewportElement.scrollTop / this._currentRowHeight);
        var diff = newRow - this._terminal.buffer.ydisp;
        this._terminal.scrollLines(diff, true);
    };
    Viewport.prototype.onWheel = function (ev) {
        var amount = this._getPixelsScrolled(ev);
        if (amount === 0) {
            return;
        }
        this._viewportElement.scrollTop += amount;
        ev.preventDefault();
    };
    Viewport.prototype._getPixelsScrolled = function (ev) {
        if (ev.deltaY === 0) {
            return 0;
        }
        var amount = ev.deltaY;
        if (ev.deltaMode === WheelEvent.DOM_DELTA_LINE) {
            amount *= this._currentRowHeight;
        }
        else if (ev.deltaMode === WheelEvent.DOM_DELTA_PAGE) {
            amount *= this._currentRowHeight * this._terminal.rows;
        }
        return amount;
    };
    Viewport.prototype.getLinesScrolled = function (ev) {
        if (ev.deltaY === 0) {
            return 0;
        }
        var amount = ev.deltaY;
        if (ev.deltaMode === WheelEvent.DOM_DELTA_PIXEL) {
            amount /= this._currentRowHeight + 0.0;
            this._wheelPartialScroll += amount;
            amount = Math.floor(Math.abs(this._wheelPartialScroll)) * (this._wheelPartialScroll > 0 ? 1 : -1);
            this._wheelPartialScroll %= 1;
        }
        else if (ev.deltaMode === WheelEvent.DOM_DELTA_PAGE) {
            amount *= this._terminal.rows;
        }
        return amount;
    };
    Viewport.prototype.onTouchStart = function (ev) {
        this._lastTouchY = ev.touches[0].pageY;
    };
    Viewport.prototype.onTouchMove = function (ev) {
        var deltaY = this._lastTouchY - ev.touches[0].pageY;
        this._lastTouchY = ev.touches[0].pageY;
        if (deltaY === 0) {
            return;
        }
        this._viewportElement.scrollTop += deltaY;
        ev.preventDefault();
    };
    return Viewport;
}());
exports.Viewport = Viewport;

//# sourceMappingURL=Viewport.js.map

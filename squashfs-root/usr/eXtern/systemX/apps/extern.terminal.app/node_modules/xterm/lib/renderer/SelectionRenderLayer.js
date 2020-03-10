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
var BaseRenderLayer_1 = require("./BaseRenderLayer");
var SelectionRenderLayer = (function (_super) {
    __extends(SelectionRenderLayer, _super);
    function SelectionRenderLayer(container, zIndex, colors) {
        var _this = _super.call(this, container, 'selection', zIndex, true, colors) || this;
        _this._state = {
            start: null,
            end: null
        };
        return _this;
    }
    SelectionRenderLayer.prototype.resize = function (terminal, dim) {
        _super.prototype.resize.call(this, terminal, dim);
        this._state = {
            start: null,
            end: null
        };
    };
    SelectionRenderLayer.prototype.reset = function (terminal) {
        if (this._state.start && this._state.end) {
            this._state = {
                start: null,
                end: null
            };
            this.clearAll();
        }
    };
    SelectionRenderLayer.prototype.onSelectionChanged = function (terminal, start, end) {
        if (this._state.start === start || this._state.end === end) {
            return;
        }
        this.clearAll();
        if (!start || !end) {
            return;
        }
        var viewportStartRow = start[1] - terminal.buffer.ydisp;
        var viewportEndRow = end[1] - terminal.buffer.ydisp;
        var viewportCappedStartRow = Math.max(viewportStartRow, 0);
        var viewportCappedEndRow = Math.min(viewportEndRow, terminal.rows - 1);
        if (viewportCappedStartRow >= terminal.rows || viewportCappedEndRow < 0) {
            return;
        }
        var startCol = viewportStartRow === viewportCappedStartRow ? start[0] : 0;
        var startRowEndCol = viewportCappedStartRow === viewportCappedEndRow ? end[0] : terminal.cols;
        this._ctx.fillStyle = this._colors.selection.css;
        this.fillCells(startCol, viewportCappedStartRow, startRowEndCol - startCol, 1);
        var middleRowsCount = Math.max(viewportCappedEndRow - viewportCappedStartRow - 1, 0);
        this.fillCells(0, viewportCappedStartRow + 1, terminal.cols, middleRowsCount);
        if (viewportCappedStartRow !== viewportCappedEndRow) {
            var endCol = viewportEndRow === viewportCappedEndRow ? end[0] : terminal.cols;
            this.fillCells(0, viewportCappedEndRow, endCol, 1);
        }
        this._state.start = [start[0], start[1]];
        this._state.end = [end[0], end[1]];
    };
    return SelectionRenderLayer;
}(BaseRenderLayer_1.BaseRenderLayer));
exports.SelectionRenderLayer = SelectionRenderLayer;

//# sourceMappingURL=SelectionRenderLayer.js.map

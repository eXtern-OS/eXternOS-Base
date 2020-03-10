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
var Buffer_1 = require("../Buffer");
var Types_1 = require("./Types");
var Types_2 = require("./atlas/Types");
var GridCache_1 = require("./GridCache");
var BaseRenderLayer_1 = require("./BaseRenderLayer");
var TextRenderLayer = (function (_super) {
    __extends(TextRenderLayer, _super);
    function TextRenderLayer(container, zIndex, colors, alpha) {
        var _this = _super.call(this, container, 'text', zIndex, alpha, colors) || this;
        _this._characterOverlapCache = {};
        _this._state = new GridCache_1.GridCache();
        return _this;
    }
    TextRenderLayer.prototype.resize = function (terminal, dim) {
        _super.prototype.resize.call(this, terminal, dim);
        var terminalFont = this._getFont(terminal, false);
        if (this._characterWidth !== dim.scaledCharWidth || this._characterFont !== terminalFont) {
            this._characterWidth = dim.scaledCharWidth;
            this._characterFont = terminalFont;
            this._characterOverlapCache = {};
        }
        this._state.clear();
        this._state.resize(terminal.cols, terminal.rows);
    };
    TextRenderLayer.prototype.reset = function (terminal) {
        this._state.clear();
        this.clearAll();
    };
    TextRenderLayer.prototype.onGridChanged = function (terminal, startRow, endRow) {
        if (this._state.cache.length === 0) {
            return;
        }
        for (var y = startRow; y <= endRow; y++) {
            var row = y + terminal.buffer.ydisp;
            var line = terminal.buffer.lines.get(row);
            this.clearCells(0, y, terminal.cols, 1);
            for (var x = 0; x < terminal.cols; x++) {
                var charData = line[x];
                var code = charData[Buffer_1.CHAR_DATA_CODE_INDEX];
                var char = charData[Buffer_1.CHAR_DATA_CHAR_INDEX];
                var attr = charData[Buffer_1.CHAR_DATA_ATTR_INDEX];
                var width = charData[Buffer_1.CHAR_DATA_WIDTH_INDEX];
                if (width === 0) {
                    continue;
                }
                if (code === 32) {
                    if (x > 0) {
                        var previousChar = line[x - 1];
                        if (this._isOverlapping(previousChar)) {
                            continue;
                        }
                    }
                }
                var flags = attr >> 18;
                var bg = attr & 0x1ff;
                var isDefaultBackground = bg >= 256;
                var isInvisible = flags & Types_1.FLAGS.INVISIBLE;
                var isInverted = flags & Types_1.FLAGS.INVERSE;
                if (!code || (code === 32 && isDefaultBackground && !isInverted) || isInvisible) {
                    continue;
                }
                if (width !== 0 && this._isOverlapping(charData)) {
                    if (x < line.length - 1 && line[x + 1][Buffer_1.CHAR_DATA_CODE_INDEX] === 32) {
                        width = 2;
                    }
                }
                var fg = (attr >> 9) & 0x1ff;
                if (isInverted) {
                    var temp = bg;
                    bg = fg;
                    fg = temp;
                    if (fg === 256) {
                        fg = Types_2.INVERTED_DEFAULT_COLOR;
                    }
                    if (bg === 257) {
                        bg = Types_2.INVERTED_DEFAULT_COLOR;
                    }
                }
                if (width === 2) {
                }
                if (bg < 256) {
                    this._ctx.save();
                    this._ctx.fillStyle = (bg === Types_2.INVERTED_DEFAULT_COLOR ? this._colors.foreground.css : this._colors.ansi[bg].css);
                    this.fillCells(x, y, width, 1);
                    this._ctx.restore();
                }
                this._ctx.save();
                if (flags & Types_1.FLAGS.BOLD) {
                    this._ctx.font = this._getFont(terminal, true);
                    if (fg < 8) {
                        fg += 8;
                    }
                }
                if (flags & Types_1.FLAGS.UNDERLINE) {
                    if (fg === Types_2.INVERTED_DEFAULT_COLOR) {
                        this._ctx.fillStyle = this._colors.background.css;
                    }
                    else if (fg < 256) {
                        this._ctx.fillStyle = this._colors.ansi[fg].css;
                    }
                    else {
                        this._ctx.fillStyle = this._colors.foreground.css;
                    }
                    this.fillBottomLineAtCells(x, y);
                }
                this.drawChar(terminal, char, code, width, x, y, fg, bg, !!(flags & Types_1.FLAGS.BOLD), !!(flags & Types_1.FLAGS.DIM));
                this._ctx.restore();
            }
        }
    };
    TextRenderLayer.prototype.onOptionsChanged = function (terminal) {
        this.setTransparency(terminal, terminal.options.allowTransparency);
    };
    TextRenderLayer.prototype._isOverlapping = function (charData) {
        if (charData[Buffer_1.CHAR_DATA_WIDTH_INDEX] !== 1) {
            return false;
        }
        var code = charData[Buffer_1.CHAR_DATA_CODE_INDEX];
        if (code < 256) {
            return false;
        }
        var char = charData[Buffer_1.CHAR_DATA_CHAR_INDEX];
        if (this._characterOverlapCache.hasOwnProperty(char)) {
            return this._characterOverlapCache[char];
        }
        this._ctx.save();
        this._ctx.font = this._characterFont;
        var overlaps = Math.floor(this._ctx.measureText(char).width) > this._characterWidth;
        this._ctx.restore();
        this._characterOverlapCache[char] = overlaps;
        return overlaps;
    };
    return TextRenderLayer;
}(BaseRenderLayer_1.BaseRenderLayer));
exports.TextRenderLayer = TextRenderLayer;

//# sourceMappingURL=TextRenderLayer.js.map

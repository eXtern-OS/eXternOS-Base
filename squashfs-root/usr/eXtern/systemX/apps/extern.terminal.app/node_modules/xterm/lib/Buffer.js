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
var CircularList_1 = require("./utils/CircularList");
var EventEmitter_1 = require("./EventEmitter");
exports.CHAR_DATA_ATTR_INDEX = 0;
exports.CHAR_DATA_CHAR_INDEX = 1;
exports.CHAR_DATA_WIDTH_INDEX = 2;
exports.CHAR_DATA_CODE_INDEX = 3;
exports.MAX_BUFFER_SIZE = 4294967295;
var Buffer = (function () {
    function Buffer(_terminal, _hasScrollback) {
        this._terminal = _terminal;
        this._hasScrollback = _hasScrollback;
        this.markers = [];
        this.clear();
    }
    Object.defineProperty(Buffer.prototype, "lines", {
        get: function () {
            return this._lines;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(Buffer.prototype, "hasScrollback", {
        get: function () {
            return this._hasScrollback && this.lines.maxLength > this._terminal.rows;
        },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(Buffer.prototype, "isCursorInViewport", {
        get: function () {
            var absoluteY = this.ybase + this.y;
            var relativeY = absoluteY - this.ydisp;
            return (relativeY >= 0 && relativeY < this._terminal.rows);
        },
        enumerable: true,
        configurable: true
    });
    Buffer.prototype._getCorrectBufferLength = function (rows) {
        if (!this._hasScrollback) {
            return rows;
        }
        var correctBufferLength = rows + this._terminal.options.scrollback;
        return correctBufferLength > exports.MAX_BUFFER_SIZE ? exports.MAX_BUFFER_SIZE : correctBufferLength;
    };
    Buffer.prototype.fillViewportRows = function () {
        if (this._lines.length === 0) {
            var i = this._terminal.rows;
            while (i--) {
                this.lines.push(this._terminal.blankLine());
            }
        }
    };
    Buffer.prototype.clear = function () {
        this.ydisp = 0;
        this.ybase = 0;
        this.y = 0;
        this.x = 0;
        this._lines = new CircularList_1.CircularList(this._getCorrectBufferLength(this._terminal.rows));
        this.scrollTop = 0;
        this.scrollBottom = this._terminal.rows - 1;
        this.setupTabStops();
    };
    Buffer.prototype.resize = function (newCols, newRows) {
        var newMaxLength = this._getCorrectBufferLength(newRows);
        if (newMaxLength > this._lines.maxLength) {
            this._lines.maxLength = newMaxLength;
        }
        if (this._lines.length > 0) {
            if (this._terminal.cols < newCols) {
                var ch = [this._terminal.defAttr, ' ', 1, 32];
                for (var i = 0; i < this._lines.length; i++) {
                    while (this._lines.get(i).length < newCols) {
                        this._lines.get(i).push(ch);
                    }
                }
            }
            var addToY = 0;
            if (this._terminal.rows < newRows) {
                for (var y = this._terminal.rows; y < newRows; y++) {
                    if (this._lines.length < newRows + this.ybase) {
                        if (this.ybase > 0 && this._lines.length <= this.ybase + this.y + addToY + 1) {
                            this.ybase--;
                            addToY++;
                            if (this.ydisp > 0) {
                                this.ydisp--;
                            }
                        }
                        else {
                            this._lines.push(this._terminal.blankLine(undefined, undefined, newCols));
                        }
                    }
                }
            }
            else {
                for (var y = this._terminal.rows; y > newRows; y--) {
                    if (this._lines.length > newRows + this.ybase) {
                        if (this._lines.length > this.ybase + this.y + 1) {
                            this._lines.pop();
                        }
                        else {
                            this.ybase++;
                            this.ydisp++;
                        }
                    }
                }
            }
            if (newMaxLength < this._lines.maxLength) {
                var amountToTrim = this._lines.length - newMaxLength;
                if (amountToTrim > 0) {
                    this._lines.trimStart(amountToTrim);
                    this.ybase = Math.max(this.ybase - amountToTrim, 0);
                    this.ydisp = Math.max(this.ydisp - amountToTrim, 0);
                }
                this._lines.maxLength = newMaxLength;
            }
            this.x = Math.min(this.x, newCols - 1);
            this.y = Math.min(this.y, newRows - 1);
            if (addToY) {
                this.y += addToY;
            }
            this.savedY = Math.min(this.savedY, newRows - 1);
            this.savedX = Math.min(this.savedX, newCols - 1);
            this.scrollTop = 0;
        }
        this.scrollBottom = newRows - 1;
    };
    Buffer.prototype.translateBufferLineToString = function (lineIndex, trimRight, startCol, endCol) {
        if (startCol === void 0) { startCol = 0; }
        if (endCol === void 0) { endCol = null; }
        var lineString = '';
        var line = this.lines.get(lineIndex);
        if (!line) {
            return '';
        }
        var startIndex = startCol;
        if (endCol === null) {
            endCol = line.length;
        }
        var endIndex = endCol;
        for (var i = 0; i < line.length; i++) {
            var char = line[i];
            lineString += char[exports.CHAR_DATA_CHAR_INDEX];
            if (char[exports.CHAR_DATA_WIDTH_INDEX] === 0) {
                if (startCol >= i) {
                    startIndex--;
                }
                if (endCol >= i) {
                    endIndex--;
                }
            }
            else {
                if (char[exports.CHAR_DATA_CHAR_INDEX].length > 1) {
                    if (startCol > i) {
                        startIndex += char[exports.CHAR_DATA_CHAR_INDEX].length - 1;
                    }
                    if (endCol > i) {
                        endIndex += char[exports.CHAR_DATA_CHAR_INDEX].length - 1;
                    }
                }
            }
        }
        if (trimRight) {
            var rightWhitespaceIndex = lineString.search(/\s+$/);
            if (rightWhitespaceIndex !== -1) {
                endIndex = Math.min(endIndex, rightWhitespaceIndex);
            }
            if (endIndex <= startIndex) {
                return '';
            }
        }
        return lineString.substring(startIndex, endIndex);
    };
    Buffer.prototype.setupTabStops = function (i) {
        if (i != null) {
            if (!this.tabs[i]) {
                i = this.prevStop(i);
            }
        }
        else {
            this.tabs = {};
            i = 0;
        }
        for (; i < this._terminal.cols; i += this._terminal.options.tabStopWidth) {
            this.tabs[i] = true;
        }
    };
    Buffer.prototype.prevStop = function (x) {
        if (x == null) {
            x = this.x;
        }
        while (!this.tabs[--x] && x > 0)
            ;
        return x >= this._terminal.cols ? this._terminal.cols - 1 : x < 0 ? 0 : x;
    };
    Buffer.prototype.nextStop = function (x) {
        if (x == null) {
            x = this.x;
        }
        while (!this.tabs[++x] && x < this._terminal.cols)
            ;
        return x >= this._terminal.cols ? this._terminal.cols - 1 : x < 0 ? 0 : x;
    };
    Buffer.prototype.addMarker = function (y) {
        var _this = this;
        var marker = new Marker(y);
        this.markers.push(marker);
        marker.disposables.push(this._lines.addDisposableListener('trim', function (amount) {
            marker.line -= amount;
            if (marker.line < 0) {
                marker.dispose();
            }
        }));
        marker.on('dispose', function () { return _this._removeMarker(marker); });
        return marker;
    };
    Buffer.prototype._removeMarker = function (marker) {
        this.markers.splice(this.markers.indexOf(marker), 1);
    };
    return Buffer;
}());
exports.Buffer = Buffer;
var Marker = (function (_super) {
    __extends(Marker, _super);
    function Marker(line) {
        var _this = _super.call(this) || this;
        _this.line = line;
        _this._id = Marker.NEXT_ID++;
        _this.isDisposed = false;
        _this.disposables = [];
        return _this;
    }
    Object.defineProperty(Marker.prototype, "id", {
        get: function () { return this._id; },
        enumerable: true,
        configurable: true
    });
    Marker.prototype.dispose = function () {
        if (this.isDisposed) {
            return;
        }
        this.isDisposed = true;
        this.disposables.forEach(function (d) { return d.dispose(); });
        this.disposables.length = 0;
        this.emit('dispose');
    };
    Marker.NEXT_ID = 1;
    return Marker;
}(EventEmitter_1.EventEmitter));
exports.Marker = Marker;

//# sourceMappingURL=Buffer.js.map

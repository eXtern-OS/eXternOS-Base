"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var SearchHelper = (function () {
    function SearchHelper(_terminal) {
        this._terminal = _terminal;
    }
    SearchHelper.prototype.findNext = function (term) {
        if (!term || term.length === 0) {
            return false;
        }
        var result;
        var startRow = this._terminal.buffer.ydisp;
        if (this._terminal.selectionManager.selectionEnd) {
            startRow = this._terminal.selectionManager.selectionEnd[1];
        }
        for (var y = startRow + 1; y < this._terminal.buffer.ybase + this._terminal.rows; y++) {
            result = this._findInLine(term, y);
            if (result) {
                break;
            }
        }
        if (!result) {
            for (var y = 0; y < startRow; y++) {
                result = this._findInLine(term, y);
                if (result) {
                    break;
                }
            }
        }
        return this._selectResult(result);
    };
    SearchHelper.prototype.findPrevious = function (term) {
        if (!term || term.length === 0) {
            return false;
        }
        var result;
        var startRow = this._terminal.buffer.ydisp;
        if (this._terminal.selectionManager.selectionStart) {
            startRow = this._terminal.selectionManager.selectionStart[1];
        }
        for (var y = startRow - 1; y >= 0; y--) {
            result = this._findInLine(term, y);
            if (result) {
                break;
            }
        }
        if (!result) {
            for (var y = this._terminal.buffer.ybase + this._terminal.rows - 1; y > startRow; y--) {
                result = this._findInLine(term, y);
                if (result) {
                    break;
                }
            }
        }
        return this._selectResult(result);
    };
    SearchHelper.prototype._findInLine = function (term, y) {
        var lowerStringLine = this._terminal.buffer.translateBufferLineToString(y, true).toLowerCase();
        var lowerTerm = term.toLowerCase();
        var searchIndex = lowerStringLine.indexOf(lowerTerm);
        if (searchIndex >= 0) {
            var line = this._terminal.buffer.lines.get(y);
            for (var i = 0; i < searchIndex; i++) {
                var charData = line[i];
                var char = charData[1];
                if (char.length > 1) {
                    searchIndex -= char.length - 1;
                }
                var charWidth = charData[2];
                if (charWidth === 0) {
                    searchIndex++;
                }
            }
            return {
                term: term,
                col: searchIndex,
                row: y
            };
        }
    };
    SearchHelper.prototype._selectResult = function (result) {
        if (!result) {
            return false;
        }
        this._terminal.selectionManager.setSelection(result.col, result.row, result.term.length);
        this._terminal.scrollLines(result.row - this._terminal.buffer.ydisp);
        return true;
    };
    return SearchHelper;
}());
exports.SearchHelper = SearchHelper;

//# sourceMappingURL=SearchHelper.js.map

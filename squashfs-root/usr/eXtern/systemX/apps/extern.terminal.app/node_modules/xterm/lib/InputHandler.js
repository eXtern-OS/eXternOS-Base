"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var EscapeSequences_1 = require("./EscapeSequences");
var Charsets_1 = require("./Charsets");
var Buffer_1 = require("./Buffer");
var Types_1 = require("./renderer/Types");
var CharWidth_1 = require("./CharWidth");
var InputHandler = (function () {
    function InputHandler(_terminal) {
        this._terminal = _terminal;
    }
    InputHandler.prototype.addChar = function (char, code) {
        if (char >= ' ') {
            var chWidth = CharWidth_1.wcwidth(code);
            if (this._terminal.charset && this._terminal.charset[char]) {
                char = this._terminal.charset[char];
            }
            if (this._terminal.options.screenReaderMode) {
                this._terminal.emit('a11y.char', char);
            }
            var row = this._terminal.buffer.y + this._terminal.buffer.ybase;
            if (!chWidth && this._terminal.buffer.x) {
                if (this._terminal.buffer.lines.get(row)[this._terminal.buffer.x - 1]) {
                    if (!this._terminal.buffer.lines.get(row)[this._terminal.buffer.x - 1][Buffer_1.CHAR_DATA_WIDTH_INDEX]) {
                        if (this._terminal.buffer.lines.get(row)[this._terminal.buffer.x - 2]) {
                            this._terminal.buffer.lines.get(row)[this._terminal.buffer.x - 2][Buffer_1.CHAR_DATA_CHAR_INDEX] += char;
                            this._terminal.buffer.lines.get(row)[this._terminal.buffer.x - 2][3] = char.charCodeAt(0);
                        }
                    }
                    else {
                        this._terminal.buffer.lines.get(row)[this._terminal.buffer.x - 1][Buffer_1.CHAR_DATA_CHAR_INDEX] += char;
                        this._terminal.buffer.lines.get(row)[this._terminal.buffer.x - 1][3] = char.charCodeAt(0);
                    }
                    this._terminal.updateRange(this._terminal.buffer.y);
                }
                return;
            }
            if (this._terminal.buffer.x + chWidth - 1 >= this._terminal.cols) {
                if (this._terminal.wraparoundMode) {
                    this._terminal.buffer.x = 0;
                    this._terminal.buffer.y++;
                    if (this._terminal.buffer.y > this._terminal.buffer.scrollBottom) {
                        this._terminal.buffer.y--;
                        this._terminal.scroll(true);
                    }
                    else {
                        this._terminal.buffer.lines.get(this._terminal.buffer.y).isWrapped = true;
                    }
                }
                else {
                    if (chWidth === 2) {
                        return;
                    }
                }
            }
            row = this._terminal.buffer.y + this._terminal.buffer.ybase;
            if (this._terminal.insertMode) {
                for (var moves = 0; moves < chWidth; ++moves) {
                    var removed = this._terminal.buffer.lines.get(this._terminal.buffer.y + this._terminal.buffer.ybase).pop();
                    if (removed[Buffer_1.CHAR_DATA_WIDTH_INDEX] === 0
                        && this._terminal.buffer.lines.get(row)[this._terminal.cols - 2]
                        && this._terminal.buffer.lines.get(row)[this._terminal.cols - 2][Buffer_1.CHAR_DATA_WIDTH_INDEX] === 2) {
                        this._terminal.buffer.lines.get(row)[this._terminal.cols - 2] = [this._terminal.curAttr, ' ', 1, ' '.charCodeAt(0)];
                    }
                    this._terminal.buffer.lines.get(row).splice(this._terminal.buffer.x, 0, [this._terminal.curAttr, ' ', 1, ' '.charCodeAt(0)]);
                }
            }
            this._terminal.buffer.lines.get(row)[this._terminal.buffer.x] = [this._terminal.curAttr, char, chWidth, char.charCodeAt(0)];
            this._terminal.buffer.x++;
            this._terminal.updateRange(this._terminal.buffer.y);
            if (chWidth === 2) {
                this._terminal.buffer.lines.get(row)[this._terminal.buffer.x] = [this._terminal.curAttr, '', 0, undefined];
                this._terminal.buffer.x++;
            }
        }
    };
    InputHandler.prototype.bell = function () {
        this._terminal.bell();
    };
    InputHandler.prototype.lineFeed = function () {
        if (this._terminal.convertEol) {
            this._terminal.buffer.x = 0;
        }
        this._terminal.buffer.y++;
        if (this._terminal.buffer.y > this._terminal.buffer.scrollBottom) {
            this._terminal.buffer.y--;
            this._terminal.scroll();
        }
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x--;
        }
        this._terminal.emit('linefeed');
    };
    InputHandler.prototype.carriageReturn = function () {
        this._terminal.buffer.x = 0;
    };
    InputHandler.prototype.backspace = function () {
        if (this._terminal.buffer.x > 0) {
            this._terminal.buffer.x--;
        }
    };
    InputHandler.prototype.tab = function () {
        var originalX = this._terminal.buffer.x;
        this._terminal.buffer.x = this._terminal.buffer.nextStop();
        if (this._terminal.options.screenReaderMode) {
            this._terminal.emit('a11y.tab', this._terminal.buffer.x - originalX);
        }
    };
    InputHandler.prototype.shiftOut = function () {
        this._terminal.setgLevel(1);
    };
    InputHandler.prototype.shiftIn = function () {
        this._terminal.setgLevel(0);
    };
    InputHandler.prototype.insertChars = function (params) {
        var param = params[0];
        if (param < 1)
            param = 1;
        var row = this._terminal.buffer.y + this._terminal.buffer.ybase;
        var j = this._terminal.buffer.x;
        var ch = [this._terminal.eraseAttr(), ' ', 1, 32];
        while (param-- && j < this._terminal.cols) {
            this._terminal.buffer.lines.get(row).splice(j++, 0, ch);
            this._terminal.buffer.lines.get(row).pop();
        }
    };
    InputHandler.prototype.cursorUp = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.y -= param;
        if (this._terminal.buffer.y < 0) {
            this._terminal.buffer.y = 0;
        }
    };
    InputHandler.prototype.cursorDown = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.y += param;
        if (this._terminal.buffer.y >= this._terminal.rows) {
            this._terminal.buffer.y = this._terminal.rows - 1;
        }
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x--;
        }
    };
    InputHandler.prototype.cursorForward = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.x += param;
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x = this._terminal.cols - 1;
        }
    };
    InputHandler.prototype.cursorBackward = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x--;
        }
        this._terminal.buffer.x -= param;
        if (this._terminal.buffer.x < 0) {
            this._terminal.buffer.x = 0;
        }
    };
    InputHandler.prototype.cursorNextLine = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.y += param;
        if (this._terminal.buffer.y >= this._terminal.rows) {
            this._terminal.buffer.y = this._terminal.rows - 1;
        }
        this._terminal.buffer.x = 0;
    };
    InputHandler.prototype.cursorPrecedingLine = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.y -= param;
        if (this._terminal.buffer.y < 0) {
            this._terminal.buffer.y = 0;
        }
        this._terminal.buffer.x = 0;
    };
    InputHandler.prototype.cursorCharAbsolute = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.x = param - 1;
    };
    InputHandler.prototype.cursorPosition = function (params) {
        var col;
        var row = params[0] - 1;
        if (params.length >= 2) {
            col = params[1] - 1;
        }
        else {
            col = 0;
        }
        if (row < 0) {
            row = 0;
        }
        else if (row >= this._terminal.rows) {
            row = this._terminal.rows - 1;
        }
        if (col < 0) {
            col = 0;
        }
        else if (col >= this._terminal.cols) {
            col = this._terminal.cols - 1;
        }
        this._terminal.buffer.x = col;
        this._terminal.buffer.y = row;
    };
    InputHandler.prototype.cursorForwardTab = function (params) {
        var param = params[0] || 1;
        while (param--) {
            this._terminal.buffer.x = this._terminal.buffer.nextStop();
        }
    };
    InputHandler.prototype.eraseInDisplay = function (params) {
        var j;
        switch (params[0]) {
            case 0:
                this._terminal.eraseRight(this._terminal.buffer.x, this._terminal.buffer.y);
                j = this._terminal.buffer.y + 1;
                for (; j < this._terminal.rows; j++) {
                    this._terminal.eraseLine(j);
                }
                break;
            case 1:
                this._terminal.eraseLeft(this._terminal.buffer.x, this._terminal.buffer.y);
                j = this._terminal.buffer.y;
                while (j--) {
                    this._terminal.eraseLine(j);
                }
                break;
            case 2:
                j = this._terminal.rows;
                while (j--)
                    this._terminal.eraseLine(j);
                break;
            case 3:
                var scrollBackSize = this._terminal.buffer.lines.length - this._terminal.rows;
                if (scrollBackSize > 0) {
                    this._terminal.buffer.lines.trimStart(scrollBackSize);
                    this._terminal.buffer.ybase = Math.max(this._terminal.buffer.ybase - scrollBackSize, 0);
                    this._terminal.buffer.ydisp = Math.max(this._terminal.buffer.ydisp - scrollBackSize, 0);
                    this._terminal.emit('scroll', 0);
                }
                break;
        }
    };
    InputHandler.prototype.eraseInLine = function (params) {
        switch (params[0]) {
            case 0:
                this._terminal.eraseRight(this._terminal.buffer.x, this._terminal.buffer.y);
                break;
            case 1:
                this._terminal.eraseLeft(this._terminal.buffer.x, this._terminal.buffer.y);
                break;
            case 2:
                this._terminal.eraseLine(this._terminal.buffer.y);
                break;
        }
    };
    InputHandler.prototype.insertLines = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        var row = this._terminal.buffer.y + this._terminal.buffer.ybase;
        var scrollBottomRowsOffset = this._terminal.rows - 1 - this._terminal.buffer.scrollBottom;
        var scrollBottomAbsolute = this._terminal.rows - 1 + this._terminal.buffer.ybase - scrollBottomRowsOffset + 1;
        while (param--) {
            this._terminal.buffer.lines.splice(scrollBottomAbsolute - 1, 1);
            this._terminal.buffer.lines.splice(row, 0, this._terminal.blankLine(true));
        }
        this._terminal.updateRange(this._terminal.buffer.y);
        this._terminal.updateRange(this._terminal.buffer.scrollBottom);
    };
    InputHandler.prototype.deleteLines = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        var row = this._terminal.buffer.y + this._terminal.buffer.ybase;
        var j;
        j = this._terminal.rows - 1 - this._terminal.buffer.scrollBottom;
        j = this._terminal.rows - 1 + this._terminal.buffer.ybase - j;
        while (param--) {
            this._terminal.buffer.lines.splice(row, 1);
            this._terminal.buffer.lines.splice(j, 0, this._terminal.blankLine(true));
        }
        this._terminal.updateRange(this._terminal.buffer.y);
        this._terminal.updateRange(this._terminal.buffer.scrollBottom);
    };
    InputHandler.prototype.deleteChars = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        var row = this._terminal.buffer.y + this._terminal.buffer.ybase;
        var ch = [this._terminal.eraseAttr(), ' ', 1, 32];
        while (param--) {
            this._terminal.buffer.lines.get(row).splice(this._terminal.buffer.x, 1);
            this._terminal.buffer.lines.get(row).push(ch);
        }
        this._terminal.updateRange(this._terminal.buffer.y);
    };
    InputHandler.prototype.scrollUp = function (params) {
        var param = params[0] || 1;
        while (param--) {
            this._terminal.buffer.lines.splice(this._terminal.buffer.ybase + this._terminal.buffer.scrollTop, 1);
            this._terminal.buffer.lines.splice(this._terminal.buffer.ybase + this._terminal.buffer.scrollBottom, 0, this._terminal.blankLine());
        }
        this._terminal.updateRange(this._terminal.buffer.scrollTop);
        this._terminal.updateRange(this._terminal.buffer.scrollBottom);
    };
    InputHandler.prototype.scrollDown = function (params) {
        var param = params[0] || 1;
        while (param--) {
            this._terminal.buffer.lines.splice(this._terminal.buffer.ybase + this._terminal.buffer.scrollBottom, 1);
            this._terminal.buffer.lines.splice(this._terminal.buffer.ybase + this._terminal.buffer.scrollTop, 0, this._terminal.blankLine());
        }
        this._terminal.updateRange(this._terminal.buffer.scrollTop);
        this._terminal.updateRange(this._terminal.buffer.scrollBottom);
    };
    InputHandler.prototype.eraseChars = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        var row = this._terminal.buffer.y + this._terminal.buffer.ybase;
        var j = this._terminal.buffer.x;
        var ch = [this._terminal.eraseAttr(), ' ', 1, 32];
        while (param-- && j < this._terminal.cols) {
            this._terminal.buffer.lines.get(row)[j++] = ch;
        }
    };
    InputHandler.prototype.cursorBackwardTab = function (params) {
        var param = params[0] || 1;
        while (param--) {
            this._terminal.buffer.x = this._terminal.buffer.prevStop();
        }
    };
    InputHandler.prototype.charPosAbsolute = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.x = param - 1;
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x = this._terminal.cols - 1;
        }
    };
    InputHandler.prototype.HPositionRelative = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.x += param;
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x = this._terminal.cols - 1;
        }
    };
    InputHandler.prototype.repeatPrecedingCharacter = function (params) {
        var param = params[0] || 1;
        var line = this._terminal.buffer.lines.get(this._terminal.buffer.ybase + this._terminal.buffer.y);
        var ch = line[this._terminal.buffer.x - 1] || [this._terminal.defAttr, ' ', 1, 32];
        while (param--) {
            line[this._terminal.buffer.x++] = ch;
        }
    };
    InputHandler.prototype.sendDeviceAttributes = function (params) {
        if (params[0] > 0) {
            return;
        }
        if (!this._terminal.prefix) {
            if (this._terminal.is('xterm') || this._terminal.is('rxvt-unicode') || this._terminal.is('screen')) {
                this._terminal.send(EscapeSequences_1.C0.ESC + '[?1;2c');
            }
            else if (this._terminal.is('linux')) {
                this._terminal.send(EscapeSequences_1.C0.ESC + '[?6c');
            }
        }
        else if (this._terminal.prefix === '>') {
            if (this._terminal.is('xterm')) {
                this._terminal.send(EscapeSequences_1.C0.ESC + '[>0;276;0c');
            }
            else if (this._terminal.is('rxvt-unicode')) {
                this._terminal.send(EscapeSequences_1.C0.ESC + '[>85;95;0c');
            }
            else if (this._terminal.is('linux')) {
                this._terminal.send(params[0] + 'c');
            }
            else if (this._terminal.is('screen')) {
                this._terminal.send(EscapeSequences_1.C0.ESC + '[>83;40003;0c');
            }
        }
    };
    InputHandler.prototype.linePosAbsolute = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.y = param - 1;
        if (this._terminal.buffer.y >= this._terminal.rows) {
            this._terminal.buffer.y = this._terminal.rows - 1;
        }
    };
    InputHandler.prototype.VPositionRelative = function (params) {
        var param = params[0];
        if (param < 1) {
            param = 1;
        }
        this._terminal.buffer.y += param;
        if (this._terminal.buffer.y >= this._terminal.rows) {
            this._terminal.buffer.y = this._terminal.rows - 1;
        }
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x--;
        }
    };
    InputHandler.prototype.HVPosition = function (params) {
        if (params[0] < 1)
            params[0] = 1;
        if (params[1] < 1)
            params[1] = 1;
        this._terminal.buffer.y = params[0] - 1;
        if (this._terminal.buffer.y >= this._terminal.rows) {
            this._terminal.buffer.y = this._terminal.rows - 1;
        }
        this._terminal.buffer.x = params[1] - 1;
        if (this._terminal.buffer.x >= this._terminal.cols) {
            this._terminal.buffer.x = this._terminal.cols - 1;
        }
    };
    InputHandler.prototype.tabClear = function (params) {
        var param = params[0];
        if (param <= 0) {
            delete this._terminal.buffer.tabs[this._terminal.buffer.x];
        }
        else if (param === 3) {
            this._terminal.buffer.tabs = {};
        }
    };
    InputHandler.prototype.setMode = function (params) {
        if (params.length > 1) {
            for (var i = 0; i < params.length; i++) {
                this.setMode([params[i]]);
            }
            return;
        }
        if (!this._terminal.prefix) {
            switch (params[0]) {
                case 4:
                    this._terminal.insertMode = true;
                    break;
                case 20:
                    break;
            }
        }
        else if (this._terminal.prefix === '?') {
            switch (params[0]) {
                case 1:
                    this._terminal.applicationCursor = true;
                    break;
                case 2:
                    this._terminal.setgCharset(0, Charsets_1.DEFAULT_CHARSET);
                    this._terminal.setgCharset(1, Charsets_1.DEFAULT_CHARSET);
                    this._terminal.setgCharset(2, Charsets_1.DEFAULT_CHARSET);
                    this._terminal.setgCharset(3, Charsets_1.DEFAULT_CHARSET);
                    break;
                case 3:
                    this._terminal.savedCols = this._terminal.cols;
                    this._terminal.resize(132, this._terminal.rows);
                    break;
                case 6:
                    this._terminal.originMode = true;
                    break;
                case 7:
                    this._terminal.wraparoundMode = true;
                    break;
                case 12:
                    break;
                case 66:
                    this._terminal.log('Serial port requested application keypad.');
                    this._terminal.applicationKeypad = true;
                    this._terminal.viewport.syncScrollArea();
                    break;
                case 9:
                case 1000:
                case 1002:
                case 1003:
                    this._terminal.x10Mouse = params[0] === 9;
                    this._terminal.vt200Mouse = params[0] === 1000;
                    this._terminal.normalMouse = params[0] > 1000;
                    this._terminal.mouseEvents = true;
                    this._terminal.element.classList.add('enable-mouse-events');
                    this._terminal.selectionManager.disable();
                    this._terminal.log('Binding to mouse events.');
                    break;
                case 1004:
                    this._terminal.sendFocus = true;
                    break;
                case 1005:
                    this._terminal.utfMouse = true;
                    break;
                case 1006:
                    this._terminal.sgrMouse = true;
                    break;
                case 1015:
                    this._terminal.urxvtMouse = true;
                    break;
                case 25:
                    this._terminal.cursorHidden = false;
                    break;
                case 1049:
                case 47:
                case 1047:
                    this._terminal.buffers.activateAltBuffer();
                    this._terminal.viewport.syncScrollArea();
                    this._terminal.showCursor();
                    break;
                case 2004:
                    this._terminal.bracketedPasteMode = true;
                    break;
            }
        }
    };
    InputHandler.prototype.resetMode = function (params) {
        if (params.length > 1) {
            for (var i = 0; i < params.length; i++) {
                this.resetMode([params[i]]);
            }
            return;
        }
        if (!this._terminal.prefix) {
            switch (params[0]) {
                case 4:
                    this._terminal.insertMode = false;
                    break;
                case 20:
                    break;
            }
        }
        else if (this._terminal.prefix === '?') {
            switch (params[0]) {
                case 1:
                    this._terminal.applicationCursor = false;
                    break;
                case 3:
                    if (this._terminal.cols === 132 && this._terminal.savedCols) {
                        this._terminal.resize(this._terminal.savedCols, this._terminal.rows);
                    }
                    delete this._terminal.savedCols;
                    break;
                case 6:
                    this._terminal.originMode = false;
                    break;
                case 7:
                    this._terminal.wraparoundMode = false;
                    break;
                case 12:
                    break;
                case 66:
                    this._terminal.log('Switching back to normal keypad.');
                    this._terminal.applicationKeypad = false;
                    this._terminal.viewport.syncScrollArea();
                    break;
                case 9:
                case 1000:
                case 1002:
                case 1003:
                    this._terminal.x10Mouse = false;
                    this._terminal.vt200Mouse = false;
                    this._terminal.normalMouse = false;
                    this._terminal.mouseEvents = false;
                    this._terminal.element.classList.remove('enable-mouse-events');
                    this._terminal.selectionManager.enable();
                    break;
                case 1004:
                    this._terminal.sendFocus = false;
                    break;
                case 1005:
                    this._terminal.utfMouse = false;
                    break;
                case 1006:
                    this._terminal.sgrMouse = false;
                    break;
                case 1015:
                    this._terminal.urxvtMouse = false;
                    break;
                case 25:
                    this._terminal.cursorHidden = true;
                    break;
                case 1049:
                case 47:
                case 1047:
                    this._terminal.buffers.activateNormalBuffer();
                    this._terminal.refresh(0, this._terminal.rows - 1);
                    this._terminal.viewport.syncScrollArea();
                    this._terminal.showCursor();
                    break;
                case 2004:
                    this._terminal.bracketedPasteMode = false;
                    break;
            }
        }
    };
    InputHandler.prototype.charAttributes = function (params) {
        if (params.length === 1 && params[0] === 0) {
            this._terminal.curAttr = this._terminal.defAttr;
            return;
        }
        var l = params.length;
        var flags = this._terminal.curAttr >> 18;
        var fg = (this._terminal.curAttr >> 9) & 0x1ff;
        var bg = this._terminal.curAttr & 0x1ff;
        var p;
        for (var i = 0; i < l; i++) {
            p = params[i];
            if (p >= 30 && p <= 37) {
                fg = p - 30;
            }
            else if (p >= 40 && p <= 47) {
                bg = p - 40;
            }
            else if (p >= 90 && p <= 97) {
                p += 8;
                fg = p - 90;
            }
            else if (p >= 100 && p <= 107) {
                p += 8;
                bg = p - 100;
            }
            else if (p === 0) {
                flags = this._terminal.defAttr >> 18;
                fg = (this._terminal.defAttr >> 9) & 0x1ff;
                bg = this._terminal.defAttr & 0x1ff;
            }
            else if (p === 1) {
                flags |= Types_1.FLAGS.BOLD;
            }
            else if (p === 4) {
                flags |= Types_1.FLAGS.UNDERLINE;
            }
            else if (p === 5) {
                flags |= Types_1.FLAGS.BLINK;
            }
            else if (p === 7) {
                flags |= Types_1.FLAGS.INVERSE;
            }
            else if (p === 8) {
                flags |= Types_1.FLAGS.INVISIBLE;
            }
            else if (p === 2) {
                flags |= Types_1.FLAGS.DIM;
            }
            else if (p === 22) {
                flags &= ~Types_1.FLAGS.BOLD;
                flags &= ~Types_1.FLAGS.DIM;
            }
            else if (p === 24) {
                flags &= ~Types_1.FLAGS.UNDERLINE;
            }
            else if (p === 25) {
                flags &= ~Types_1.FLAGS.BLINK;
            }
            else if (p === 27) {
                flags &= ~Types_1.FLAGS.INVERSE;
            }
            else if (p === 28) {
                flags &= ~Types_1.FLAGS.INVISIBLE;
            }
            else if (p === 39) {
                fg = (this._terminal.defAttr >> 9) & 0x1ff;
            }
            else if (p === 49) {
                bg = this._terminal.defAttr & 0x1ff;
            }
            else if (p === 38) {
                if (params[i + 1] === 2) {
                    i += 2;
                    fg = this._terminal.matchColor(params[i] & 0xff, params[i + 1] & 0xff, params[i + 2] & 0xff);
                    if (fg === -1)
                        fg = 0x1ff;
                    i += 2;
                }
                else if (params[i + 1] === 5) {
                    i += 2;
                    p = params[i] & 0xff;
                    fg = p;
                }
            }
            else if (p === 48) {
                if (params[i + 1] === 2) {
                    i += 2;
                    bg = this._terminal.matchColor(params[i] & 0xff, params[i + 1] & 0xff, params[i + 2] & 0xff);
                    if (bg === -1)
                        bg = 0x1ff;
                    i += 2;
                }
                else if (params[i + 1] === 5) {
                    i += 2;
                    p = params[i] & 0xff;
                    bg = p;
                }
            }
            else if (p === 100) {
                fg = (this._terminal.defAttr >> 9) & 0x1ff;
                bg = this._terminal.defAttr & 0x1ff;
            }
            else {
                this._terminal.error('Unknown SGR attribute: %d.', p);
            }
        }
        this._terminal.curAttr = (flags << 18) | (fg << 9) | bg;
    };
    InputHandler.prototype.deviceStatus = function (params) {
        if (!this._terminal.prefix) {
            switch (params[0]) {
                case 5:
                    this._terminal.send(EscapeSequences_1.C0.ESC + '[0n');
                    break;
                case 6:
                    this._terminal.send(EscapeSequences_1.C0.ESC + '['
                        + (this._terminal.buffer.y + 1)
                        + ';'
                        + (this._terminal.buffer.x + 1)
                        + 'R');
                    break;
            }
        }
        else if (this._terminal.prefix === '?') {
            switch (params[0]) {
                case 6:
                    this._terminal.send(EscapeSequences_1.C0.ESC + '[?'
                        + (this._terminal.buffer.y + 1)
                        + ';'
                        + (this._terminal.buffer.x + 1)
                        + 'R');
                    break;
                case 15:
                    break;
                case 25:
                    break;
                case 26:
                    break;
                case 53:
                    break;
            }
        }
    };
    InputHandler.prototype.softReset = function (params) {
        this._terminal.cursorHidden = false;
        this._terminal.insertMode = false;
        this._terminal.originMode = false;
        this._terminal.wraparoundMode = true;
        this._terminal.applicationKeypad = false;
        this._terminal.viewport.syncScrollArea();
        this._terminal.applicationCursor = false;
        this._terminal.buffer.scrollTop = 0;
        this._terminal.buffer.scrollBottom = this._terminal.rows - 1;
        this._terminal.curAttr = this._terminal.defAttr;
        this._terminal.buffer.x = this._terminal.buffer.y = 0;
        this._terminal.charset = null;
        this._terminal.glevel = 0;
        this._terminal.charsets = [null];
    };
    InputHandler.prototype.setCursorStyle = function (params) {
        var param = params[0] < 1 ? 1 : params[0];
        switch (param) {
            case 1:
            case 2:
                this._terminal.setOption('cursorStyle', 'block');
                break;
            case 3:
            case 4:
                this._terminal.setOption('cursorStyle', 'underline');
                break;
            case 5:
            case 6:
                this._terminal.setOption('cursorStyle', 'bar');
                break;
        }
        var isBlinking = param % 2 === 1;
        this._terminal.setOption('cursorBlink', isBlinking);
    };
    InputHandler.prototype.setScrollRegion = function (params) {
        if (this._terminal.prefix)
            return;
        this._terminal.buffer.scrollTop = (params[0] || 1) - 1;
        this._terminal.buffer.scrollBottom = (params[1] && params[1] <= this._terminal.rows ? params[1] : this._terminal.rows) - 1;
        this._terminal.buffer.x = 0;
        this._terminal.buffer.y = 0;
    };
    InputHandler.prototype.saveCursor = function (params) {
        this._terminal.buffer.savedX = this._terminal.buffer.x;
        this._terminal.buffer.savedY = this._terminal.buffer.y;
    };
    InputHandler.prototype.restoreCursor = function (params) {
        this._terminal.buffer.x = this._terminal.buffer.savedX || 0;
        this._terminal.buffer.y = this._terminal.buffer.savedY || 0;
    };
    return InputHandler;
}());
exports.InputHandler = InputHandler;

//# sourceMappingURL=InputHandler.js.map

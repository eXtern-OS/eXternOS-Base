"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var chai_1 = require("chai");
var webLinks = require("./webLinks");
var MockTerminal = (function () {
    function MockTerminal() {
    }
    MockTerminal.prototype.registerLinkMatcher = function (regex, handler, options) {
        this.regex = regex;
        this.handler = handler;
        this.options = options;
        return 0;
    };
    return MockTerminal;
}());
describe('webLinks addon', function () {
    describe('apply', function () {
        it('should do register the `webLinksInit` method', function () {
            webLinks.apply(MockTerminal);
            chai_1.assert.equal(typeof MockTerminal.prototype.webLinksInit, 'function');
        });
    });
    it('should allow ~ character in URI path', function () {
        var term = new MockTerminal();
        webLinks.webLinksInit(term);
        var row = '  http://foo.com/a~b#c~d?e~f  ';
        var match = row.match(term.regex);
        var uri = match[term.options.matchIndex];
        chai_1.assert.equal(uri, 'http://foo.com/a~b#c~d?e~f');
    });
});

//# sourceMappingURL=webLinks.test.js.map

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
var Linkifier_1 = require("./Linkifier");
var TestUtils_test_1 = require("./utils/TestUtils.test");
var CircularList_1 = require("./utils/CircularList");
var TestLinkifier = (function (_super) {
    __extends(TestLinkifier, _super);
    function TestLinkifier(_terminal) {
        var _this = _super.call(this, _terminal) || this;
        Linkifier_1.Linkifier.TIME_BEFORE_LINKIFY = 0;
        return _this;
    }
    Object.defineProperty(TestLinkifier.prototype, "linkMatchers", {
        get: function () { return this._linkMatchers; },
        enumerable: true,
        configurable: true
    });
    TestLinkifier.prototype.linkifyRows = function () { _super.prototype.linkifyRows.call(this, 0, this._terminal.buffer.lines.length - 1); };
    return TestLinkifier;
}(Linkifier_1.Linkifier));
var TestMouseZoneManager = (function () {
    function TestMouseZoneManager() {
        this.clears = 0;
        this.zones = [];
    }
    TestMouseZoneManager.prototype.add = function (zone) {
        this.zones.push(zone);
    };
    TestMouseZoneManager.prototype.clearAll = function () {
        this.clears++;
    };
    return TestMouseZoneManager;
}());
describe('Linkifier', function () {
    var terminal;
    var linkifier;
    var mouseZoneManager;
    beforeEach(function () {
        terminal = new TestUtils_test_1.MockTerminal();
        terminal.cols = 100;
        terminal.buffer = new TestUtils_test_1.MockBuffer();
        terminal.buffer.lines = new CircularList_1.CircularList(20);
        terminal.buffer.ydisp = 0;
        linkifier = new TestLinkifier(terminal);
        mouseZoneManager = new TestMouseZoneManager();
    });
    function stringToRow(text) {
        var result = [];
        for (var i = 0; i < text.length; i++) {
            result.push([0, text.charAt(i), 1, text.charCodeAt(i)]);
        }
        return result;
    }
    function addRow(text) {
        terminal.buffer.lines.push(stringToRow(text));
    }
    function assertLinkifiesRow(rowText, linkMatcherRegex, links, done) {
        addRow(rowText);
        linkifier.registerLinkMatcher(linkMatcherRegex, function () { });
        linkifier.linkifyRows();
        setTimeout(function () {
            chai_1.assert.equal(mouseZoneManager.zones.length, links.length);
            links.forEach(function (l, i) {
                chai_1.assert.equal(mouseZoneManager.zones[i].x1, l.x + 1);
                chai_1.assert.equal(mouseZoneManager.zones[i].x2, l.x + l.length + 1);
                chai_1.assert.equal(mouseZoneManager.zones[i].y1, terminal.buffer.lines.length);
                chai_1.assert.equal(mouseZoneManager.zones[i].y2, terminal.buffer.lines.length);
            });
            done();
        }, 0);
    }
    function assertLinkifiesMultiLineLink(rowText, linkMatcherRegex, links, done) {
        addRow(rowText);
        linkifier.registerLinkMatcher(linkMatcherRegex, function () { });
        linkifier.linkifyRows();
        setTimeout(function () {
            chai_1.assert.equal(mouseZoneManager.zones.length, links.length);
            links.forEach(function (l, i) {
                chai_1.assert.equal(mouseZoneManager.zones[i].x1, l.x1 + 1);
                chai_1.assert.equal(mouseZoneManager.zones[i].x2, l.x2 + 1);
                chai_1.assert.equal(mouseZoneManager.zones[i].y1, l.y1 + 1);
                chai_1.assert.equal(mouseZoneManager.zones[i].y2, l.y2 + 1);
            });
            done();
        }, 0);
    }
    describe('before attachToDom', function () {
        it('should allow link matcher registration', function (done) {
            chai_1.assert.doesNotThrow(function () {
                var linkMatcherId = linkifier.registerLinkMatcher(/foo/, function () { });
                chai_1.assert.isTrue(linkifier.deregisterLinkMatcher(linkMatcherId));
                done();
            });
        });
    });
    describe('after attachToDom', function () {
        beforeEach(function () {
            linkifier.attachToDom(mouseZoneManager);
        });
        describe('link matcher', function () {
            it('should match a single link', function (done) {
                assertLinkifiesRow('foo', /foo/, [{ x: 0, length: 3 }], done);
            });
            it('should match a single link at the start of a text node', function (done) {
                assertLinkifiesRow('foo bar', /foo/, [{ x: 0, length: 3 }], done);
            });
            it('should match a single link in the middle of a text node', function (done) {
                assertLinkifiesRow('foo bar baz', /bar/, [{ x: 4, length: 3 }], done);
            });
            it('should match a single link at the end of a text node', function (done) {
                assertLinkifiesRow('foo bar', /bar/, [{ x: 4, length: 3 }], done);
            });
            it('should match a link after a link at the start of a text node', function (done) {
                assertLinkifiesRow('foo bar', /foo|bar/, [{ x: 0, length: 3 }, { x: 4, length: 3 }], done);
            });
            it('should match a link after a link in the middle of a text node', function (done) {
                assertLinkifiesRow('foo bar baz', /bar|baz/, [{ x: 4, length: 3 }, { x: 8, length: 3 }], done);
            });
            it('should match a link immediately after a link at the end of a text node', function (done) {
                assertLinkifiesRow('foo barbaz', /bar|baz/, [{ x: 4, length: 3 }, { x: 7, length: 3 }], done);
            });
            it('should not duplicate text after a unicode character (wrapped in a span)', function (done) {
                assertLinkifiesRow('echo \'🔷foo\'', /foo/, [{ x: 8, length: 3 }], done);
            });
            describe('multi-line links', function () {
                it('should match links that start on line 1/2 of a wrapped line and end on the last character of line 1/2', function (done) {
                    terminal.cols = 4;
                    assertLinkifiesMultiLineLink('12345', /1234/, [{ x1: 0, x2: 4, y1: 0, y2: 0 }], done);
                });
                it('should match links that start on line 1/2 of a wrapped line and wrap to line 2/2', function (done) {
                    terminal.cols = 4;
                    assertLinkifiesMultiLineLink('12345', /12345/, [{ x1: 0, x2: 1, y1: 0, y2: 1 }], done);
                });
                it('should match links that start and end on line 2/2 of a wrapped line', function (done) {
                    terminal.cols = 4;
                    assertLinkifiesMultiLineLink('12345678', /5678/, [{ x1: 0, x2: 4, y1: 1, y2: 1 }], done);
                });
                it('should match links that start on line 2/3 of a wrapped line and wrap to line 3/3', function (done) {
                    terminal.cols = 4;
                    assertLinkifiesMultiLineLink('123456789', /56789/, [{ x1: 0, x2: 1, y1: 1, y2: 2 }], done);
                });
            });
        });
        describe('validationCallback', function () {
            it('should enable link if true', function (done) {
                addRow('test');
                linkifier.registerLinkMatcher(/test/, function () { return done(); }, {
                    validationCallback: function (url, cb) {
                        chai_1.assert.equal(mouseZoneManager.zones.length, 0);
                        cb(true);
                        chai_1.assert.equal(mouseZoneManager.zones.length, 1);
                        chai_1.assert.equal(mouseZoneManager.zones[0].x1, 1);
                        chai_1.assert.equal(mouseZoneManager.zones[0].x2, 5);
                        chai_1.assert.equal(mouseZoneManager.zones[0].y1, 1);
                        chai_1.assert.equal(mouseZoneManager.zones[0].y2, 1);
                        mouseZoneManager.zones[0].clickCallback({});
                    }
                });
                linkifier.linkifyRows();
            });
            it('should validate the uri, not the row', function (done) {
                addRow('abc test abc');
                linkifier.registerLinkMatcher(/test/, function () { return done(); }, {
                    validationCallback: function (uri, cb) {
                        chai_1.assert.equal(uri, 'test');
                        done();
                    }
                });
                linkifier.linkifyRows();
            });
            it('should disable link if false', function (done) {
                addRow('test');
                linkifier.registerLinkMatcher(/test/, function () { return chai_1.assert.fail(); }, {
                    validationCallback: function (url, cb) {
                        chai_1.assert.equal(mouseZoneManager.zones.length, 0);
                        cb(false);
                        chai_1.assert.equal(mouseZoneManager.zones.length, 0);
                    }
                });
                linkifier.linkifyRows();
                setTimeout(function () { return done(); }, 10);
            });
            it('should trigger for multiple link matches on one row', function (done) {
                addRow('test test');
                var count = 0;
                linkifier.registerLinkMatcher(/test/, function () { return chai_1.assert.fail(); }, {
                    validationCallback: function (url, cb) {
                        count += 1;
                        if (count === 2) {
                            done();
                        }
                        cb(false);
                    }
                });
                linkifier.linkifyRows();
            });
        });
        describe('priority', function () {
            it('should order the list from highest priority to lowest #1', function () {
                var aId = linkifier.registerLinkMatcher(/a/, function () { }, { priority: 1 });
                var bId = linkifier.registerLinkMatcher(/b/, function () { }, { priority: -1 });
                chai_1.assert.deepEqual(linkifier.linkMatchers.map(function (lm) { return lm.id; }), [aId, bId]);
            });
            it('should order the list from highest priority to lowest #2', function () {
                var aId = linkifier.registerLinkMatcher(/a/, function () { }, { priority: -1 });
                var bId = linkifier.registerLinkMatcher(/b/, function () { }, { priority: 1 });
                chai_1.assert.deepEqual(linkifier.linkMatchers.map(function (lm) { return lm.id; }), [bId, aId]);
            });
            it('should order items of equal priority in the order they are added', function () {
                var aId = linkifier.registerLinkMatcher(/a/, function () { }, { priority: 0 });
                var bId = linkifier.registerLinkMatcher(/b/, function () { }, { priority: 0 });
                chai_1.assert.deepEqual(linkifier.linkMatchers.map(function (lm) { return lm.id; }), [aId, bId]);
            });
        });
    });
});

//# sourceMappingURL=Linkifier.test.js.map

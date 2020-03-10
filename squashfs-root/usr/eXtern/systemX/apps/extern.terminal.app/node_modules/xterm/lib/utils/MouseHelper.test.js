"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var jsdom = require("jsdom");
var chai_1 = require("chai");
var MouseHelper_1 = require("./MouseHelper");
var TestUtils_test_1 = require("./TestUtils.test");
var CHAR_WIDTH = 10;
var CHAR_HEIGHT = 20;
describe('MouseHelper.getCoords', function () {
    var dom;
    var window;
    var document;
    var mouseHelper;
    var charMeasure;
    beforeEach(function () {
        dom = new jsdom.JSDOM('');
        window = dom.window;
        document = window.document;
        charMeasure = new TestUtils_test_1.MockCharMeasure();
        charMeasure.width = CHAR_WIDTH;
        charMeasure.height = CHAR_HEIGHT;
        var renderer = new TestUtils_test_1.MockRenderer();
        renderer.dimensions = {
            actualCellWidth: CHAR_WIDTH,
            actualCellHeight: CHAR_HEIGHT
        };
        mouseHelper = new MouseHelper_1.MouseHelper(renderer);
    });
    describe('when charMeasure is not initialized', function () {
        it('should return null', function () {
            charMeasure = new TestUtils_test_1.MockCharMeasure();
            chai_1.assert.equal(mouseHelper.getCoords({ pageX: 0, pageY: 0 }, document.createElement('div'), charMeasure, 1, 10, 10), null);
        });
    });
    describe('when pageX/pageY are not supported', function () {
        it('should return null', function () {
            chai_1.assert.equal(mouseHelper.getCoords({ pageX: undefined, pageY: undefined }, document.createElement('div'), charMeasure, 1, 10, 10), null);
        });
    });
    it('should return the cell that was clicked', function () {
        var coords;
        coords = mouseHelper.getCoords({ pageX: CHAR_WIDTH / 2, pageY: CHAR_HEIGHT / 2 }, document.createElement('div'), charMeasure, 1, 10, 10);
        chai_1.assert.deepEqual(coords, [1, 1]);
        coords = mouseHelper.getCoords({ pageX: CHAR_WIDTH, pageY: CHAR_HEIGHT }, document.createElement('div'), charMeasure, 1, 10, 10);
        chai_1.assert.deepEqual(coords, [1, 1]);
        coords = mouseHelper.getCoords({ pageX: CHAR_WIDTH, pageY: CHAR_HEIGHT + 1 }, document.createElement('div'), charMeasure, 1, 10, 10);
        chai_1.assert.deepEqual(coords, [1, 2]);
        coords = mouseHelper.getCoords({ pageX: CHAR_WIDTH + 1, pageY: CHAR_HEIGHT }, document.createElement('div'), charMeasure, 1, 10, 10);
        chai_1.assert.deepEqual(coords, [2, 1]);
    });
    it('should ensure the coordinates are returned within the terminal bounds', function () {
        var coords;
        coords = mouseHelper.getCoords({ pageX: -1, pageY: -1 }, document.createElement('div'), charMeasure, 1, 10, 10);
        chai_1.assert.deepEqual(coords, [1, 1]);
        coords = mouseHelper.getCoords({ pageX: CHAR_WIDTH * 20, pageY: CHAR_HEIGHT * 20 }, document.createElement('div'), charMeasure, 1, 10, 10);
        chai_1.assert.deepEqual(coords, [10, 10], 'coordinates should never come back as larger than the terminal');
    });
});

//# sourceMappingURL=MouseHelper.test.js.map

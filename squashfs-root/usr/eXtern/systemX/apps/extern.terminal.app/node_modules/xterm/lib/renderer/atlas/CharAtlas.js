"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var CharAtlasGenerator_1 = require("../../shared/atlas/CharAtlasGenerator");
var CharAtlasUtils_1 = require("./CharAtlasUtils");
var charAtlasCache = [];
function acquireCharAtlas(terminal, colors, scaledCharWidth, scaledCharHeight) {
    var newConfig = CharAtlasUtils_1.generateConfig(scaledCharWidth, scaledCharHeight, terminal, colors);
    for (var i = 0; i < charAtlasCache.length; i++) {
        var entry = charAtlasCache[i];
        var ownedByIndex = entry.ownedBy.indexOf(terminal);
        if (ownedByIndex >= 0) {
            if (CharAtlasUtils_1.configEquals(entry.config, newConfig)) {
                return entry.bitmap;
            }
            else {
                if (entry.ownedBy.length === 1) {
                    charAtlasCache.splice(i, 1);
                }
                else {
                    entry.ownedBy.splice(ownedByIndex, 1);
                }
                break;
            }
        }
    }
    for (var i = 0; i < charAtlasCache.length; i++) {
        var entry = charAtlasCache[i];
        if (CharAtlasUtils_1.configEquals(entry.config, newConfig)) {
            entry.ownedBy.push(terminal);
            return entry.bitmap;
        }
    }
    var canvasFactory = function (width, height) {
        var canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        return canvas;
    };
    var newEntry = {
        bitmap: CharAtlasGenerator_1.generateCharAtlas(window, canvasFactory, newConfig),
        config: newConfig,
        ownedBy: [terminal]
    };
    charAtlasCache.push(newEntry);
    return newEntry.bitmap;
}
exports.acquireCharAtlas = acquireCharAtlas;

//# sourceMappingURL=CharAtlas.js.map

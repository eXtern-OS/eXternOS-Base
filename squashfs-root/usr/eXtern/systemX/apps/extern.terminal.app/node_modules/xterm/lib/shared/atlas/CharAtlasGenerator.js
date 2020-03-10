"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var Types_1 = require("./Types");
var Browser_1 = require("../utils/Browser");
function generateCharAtlas(context, canvasFactory, config) {
    var cellWidth = config.scaledCharWidth + Types_1.CHAR_ATLAS_CELL_SPACING;
    var cellHeight = config.scaledCharHeight + Types_1.CHAR_ATLAS_CELL_SPACING;
    var canvas = canvasFactory(255 * cellWidth, (2 + 16) * cellHeight);
    var ctx = canvas.getContext('2d', { alpha: config.allowTransparency });
    ctx.fillStyle = config.colors.background.css;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.fillStyle = config.colors.foreground.css;
    ctx.font = getFont(config.fontWeight, config);
    ctx.textBaseline = 'top';
    for (var i = 0; i < 256; i++) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(i * cellWidth, 0, cellWidth, cellHeight);
        ctx.clip();
        ctx.fillText(String.fromCharCode(i), i * cellWidth, 0);
        ctx.restore();
    }
    ctx.save();
    ctx.font = getFont(config.fontWeightBold, config);
    for (var i = 0; i < 256; i++) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(i * cellWidth, cellHeight, cellWidth, cellHeight);
        ctx.clip();
        ctx.fillText(String.fromCharCode(i), i * cellWidth, cellHeight);
        ctx.restore();
    }
    ctx.restore();
    ctx.font = getFont(config.fontWeight, config);
    for (var colorIndex = 0; colorIndex < 16; colorIndex++) {
        if (colorIndex === 8) {
            ctx.font = getFont(config.fontWeightBold, config);
        }
        var y = (colorIndex + 2) * cellHeight;
        for (var i = 0; i < 256; i++) {
            ctx.save();
            ctx.beginPath();
            ctx.rect(i * cellWidth, y, cellWidth, cellHeight);
            ctx.clip();
            ctx.fillStyle = config.colors.ansi[colorIndex].css;
            ctx.fillText(String.fromCharCode(i), i * cellWidth, y);
            ctx.restore();
        }
    }
    ctx.restore();
    if (!('createImageBitmap' in context) || Browser_1.isFirefox) {
        if (canvas instanceof HTMLCanvasElement) {
            return canvas;
        }
        else {
            return new Promise(function (r) { return r(canvas.transferToImageBitmap()); });
        }
    }
    var charAtlasImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    var r = config.colors.background.rgba >>> 24;
    var g = config.colors.background.rgba >>> 16 & 0xFF;
    var b = config.colors.background.rgba >>> 8 & 0xFF;
    clearColor(charAtlasImageData, r, g, b);
    return context.createImageBitmap(charAtlasImageData);
}
exports.generateCharAtlas = generateCharAtlas;
function clearColor(imageData, r, g, b) {
    for (var offset = 0; offset < imageData.data.length; offset += 4) {
        if (imageData.data[offset] === r &&
            imageData.data[offset + 1] === g &&
            imageData.data[offset + 2] === b) {
            imageData.data[offset + 3] = 0;
        }
    }
}
function getFont(fontWeight, config) {
    return fontWeight + " " + config.fontSize * config.devicePixelRatio + "px " + config.fontFamily;
}

//# sourceMappingURL=CharAtlasGenerator.js.map

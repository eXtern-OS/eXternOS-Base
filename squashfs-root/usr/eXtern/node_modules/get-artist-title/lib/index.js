var removeFileExtensionPlugin = require('./plugins/remove-file-extension')
var basePlugin = require('./plugins/base')
var quotedTitlePlugin = require('./plugins/quoted-title')
var cleanFluffPlugin = require('./plugins/common-fluff')

var getArtistTitleInternal = require('./core')

exports = module.exports = function getArtistTitle (str, options) {
  return getArtistTitleInternal(str, options, [
    removeFileExtensionPlugin,
    basePlugin,
    quotedTitlePlugin,
    cleanFluffPlugin
  ])
}

exports.fallBackToArtist = require('./fallBackToArtist')
exports.fallBackToTitle = require('./fallBackToTitle')

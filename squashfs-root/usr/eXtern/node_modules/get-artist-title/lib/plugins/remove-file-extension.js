var videoExtensions = require('video-extensions')
var audioExtensions = require('audio-extensions')

var fileExtensions = videoExtensions.concat(audioExtensions)
var fileExtensionRx = new RegExp('\\.(' + fileExtensions.join('|') + ')$', 'i')
function removeFileExtension (title) {
  return title.replace(fileExtensionRx, '')
}

exports.before = removeFileExtension

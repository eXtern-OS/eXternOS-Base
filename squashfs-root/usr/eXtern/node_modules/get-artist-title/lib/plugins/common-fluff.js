var mapTitle = require('../core').mapTitle

function cleanTitle (title) {
  return title
    // Sub Pop includes "(not the video)" on audio tracks.
    // The " video" part might be stripped by other plugins.
    .replace(/\(not the( video)?\)\s*$/, '')
    // Lyrics videos
    .replace(/(\s*[-~_/]\s*)?\b(with\s+)?lyrics\s*/i, '')
    .replace(/\(\s*(with\s+)?lyrics\s*\)\s*/i, '')
    .trim()
}

exports.after = mapTitle(cleanTitle)

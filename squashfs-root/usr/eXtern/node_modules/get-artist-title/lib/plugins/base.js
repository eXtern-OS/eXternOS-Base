var mapArtistTitle = require('../core').mapArtistTitle

var separators = [
  ' -- ',
  '--',
  ' - ',
  ' – ',
  ' — ',
  ' _ ',
  '-',
  '–',
  '—',
  ':',
  '|',
  '///',
  ' / ',
  '_',
  '/'
]

// Most of this is taken from the YouTube connector in David Šabata's Last.fm
// web scrobbler: https://github.com/david-sabata/web-scrobbler

// Remove various versions of "MV" and "PV" markers
function cleanMVPV (string) {
  return string
    .replace(/\s*\[\s*(?:off?icial\s+)?([PM]\/?V)\s*]/i, '') // [MV] or [M/V]
    .replace(/\s*\(\s*(?:off?icial\s+)?([PM]\/?V)\s*\)/i, '') // (MV) or (M/V)
    .replace(/\s*【\s*(?:off?icial\s+)?([PM]\/?V)\s*】/i, '') // 【MV】 or 【M/V】
    .replace(/[\s\-–_]+(?:off?icial\s+)?([PM]\/?V)\s*/i, '') // MV or M/V at the end
    .replace(/(?:off?icial\s+)?([PM]\/?V)[\s\-–_]+/, '') // MV or M/V at the start
}

function cleanFluff (string) {
  return cleanMVPV(string)
    .replace(/\s*\[[^\]]+]$/, '') // [whatever] at the end
    .replace(/^\s*\[[^\]]+]\s*/, '') // [whatever] at the start
    .replace(/\s*\([^)]*\bver(\.|sion)?\s*\)$/i, '') // (whatever version)
    .replace(/\s*[a-z]*\s*\bver(\.|sion)?$/i, '') // ver. and 1 word before (no parens)
    .replace(/\s*(of+icial\s*)?(music\s*)?video/i, '') // (official)? (music)? video
    .replace(/\s*(ALBUM TRACK\s*)?(album track\s*)/i, '') // (ALBUM TRACK)
    .replace(/\s*\(\s*of+icial\s*\)/i, '') // (official)
    .replace(/\s*\(\s*[0-9]{4}\s*\)/i, '') // (1999)
    .replace(/\s+\(\s*(HD|HQ)\s*\)$/, '') // HD (HQ)
    .replace(/[\s\-–_]+(HD|HQ)\s*$/, '') // HD (HQ)
}

function cleanTitle (title) {
  return cleanFluff(title.trim())
    .replace(/\s*\*+\s?\S+\s?\*+$/, '') // **NEW**
    .replace(/\s*video\s*clip/i, '') // video clip
    .replace(/\s+\(?live\)?$/i, '') // live
    .replace(/\(\s*\)/, '') // Leftovers after e.g. (official video)
    .replace(/\[\s*]/, '') // Leftovers after e.g. [1080p]
    .replace(/【\s*】/, '') // Leftovers after e.g. 【MV】
    .replace(/^(|.*\s)"(.*)"(\s.*|)$/, '$2') // Artist - The new "Track title" featuring someone
    .replace(/^(|.*\s)'(.*)'(\s.*|)$/, '$2') // 'Track title'
    .replace(/^[/\s,:;~\-–_\s"]+/, '') // trim starting white chars and dash
    .replace(/[/\s,:;~\-–_\s"]+$/, '') // trim trailing white chars and dash
}

function cleanArtist (artist) {
  return cleanFluff(artist.trim())
    .replace(/\s*[0-1][0-9][0-1][0-9][0-3][0-9]\s*/, '') // date formats ex. 130624
    .replace(/^[/\s,:;~\-–_\s"]+/, '') // trim starting white chars and dash
    .replace(/[/\s,:;~\-–_\s"]+$/, '') // trim trailing white chars and dash
}

function splitArtistTitle (str) {
  for (var i = 0, l = separators.length; i < l; i++) {
    var sep = separators[i]
    var idx = str.indexOf(sep)
    if (idx > -1) {
      return [ str.slice(0, idx), str.slice(idx + sep.length) ]
    }
  }
}

exports.separators = separators
exports.before = cleanFluff
exports.split = splitArtistTitle
exports.after = mapArtistTitle(cleanArtist, cleanTitle)

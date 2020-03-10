#!/usr/bin/env node

var getArtistTitle = require('./')

var help = '\n' +
  'Usage\n' +
  '  $ format-artist-title <input>\n' +
  '\n' +
  'Example\n' +
  '  $ format-artist-title "Ga-In (가인) - Nostalgia (노스텔지아) - Lyrics [Hangul+Translation] .mov"\n' +
  '  Ga-In (가인) – Nostalgia (노스텔지아)\n'

var format = '%artist – %title'
var input = process.argv[2]

if (input) {
  var result = getArtistTitle(input)
  if (result) {
    console.log(format.replace('%artist', result[0]).replace('%title', result[1]))
  } else {
    console.error('Could not extract an artist and title.')
    process.exit(1)
  }
} else {
  console.log(help)
  process.exit(1)
}

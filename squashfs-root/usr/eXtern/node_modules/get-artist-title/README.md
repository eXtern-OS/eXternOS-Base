# get-artist-title

[![travis](https://img.shields.io/travis/goto-bus-stop/get-artist-title.svg?style=flat-square)](https://travis-ci.org/goto-bus-stop/get-artist-title)
[![npm](https://img.shields.io/npm/v/get-artist-title.svg?style=flat-square)](https://npmjs.com/package/get-artist-title)
[![js-standard-style](https://img.shields.io/badge/code%20style-standard-brightgreen.svg?style=flat-square)](http://standardjs.com/)

Get the artist and title from a full song name, eg. a YouTube video title.

## Installation

```bash
npm install --save get-artist-title
```

## Usage

### CLI

```bash
$ npm install --global get-artist-title

$ format-artist-title

Usage
  $ format-artist-title <input>

Example
  $ format-artist-title "Ga-In (가인) - Nostalgia (노스텔지아) - Lyrics [Hangul+Translation] .mov"
  Ga-In (가인) – Nostalgia (노스텔지아)

```

### JavaScript

```js
const getArtistTitle = require('get-artist-title')
getArtistTitle('Taylor Swift - Out Of The Woods')
//→ ['Taylor Swift', 'Out Of The Woods']

let [ artist, title ] = getArtistTitle('FEMM - PoW! (Music Video)')
//→ ['FEMM', 'PoW!']
```

## API

### getArtistTitle(string, options={})

Extract the artist and title from `string`. Returns an Array with two elements,
`[artist, title]`, or `null` if no artist/title can be found.

Possible `options` are:

  - `defaultArtist` - Artist name to use if an artist name/song title pair can't
    be extracted. The input string, minus any cruft, will be used as the song
    title.
  - `defaultTitle` - Song title to use if an artist name/song title pair can't
    be extracted. The input string, minus any cruft, will be used as the artist
    name.

It's useful to provide defaults if you're passing strings from an external
service. For example, a YouTube video title may not always contain the artist
name, but the name of the channel that uploaded it might be relevant.

```js
const [ artist, title ] = getArtistTitle('[MV] A Brand New Song!', {
  defaultArtist: 'Channel Name'
})
// → ['Channel Name', 'A Brand New Song!']
```

```js
// Assuming `video` is a Video resource from the YouTube Data API:
const [ artist, title ] = getArtistTitle(video.snippet.title, {
  defaultArtist: video.snippet.channelTitle
})
```

## Licence

[MIT](./LICENSE)

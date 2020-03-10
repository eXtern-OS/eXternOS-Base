module.exports = {
  tests: [
    // https://youtu.be/A2RwHnfI2y8
    { input: 'Ga-In (가인) - Nostalgia (노스텔지아) - Lyrics [Hangul+Translation] .mov',
      expected: [ 'Ga-In (가인)', 'Nostalgia (노스텔지아)' ] },
    // https://www.youtube.com/watch?v=PYBuIwuD1DA
    { input: 'show me - B-free.m4v',
      expected: [ 'show me', 'B-free' ] },
    // https://www.youtube.com/watch?v=5hINYNZslP0
    { input: '성시경 Sung Si Kyung - 내게 오는 길.mp4',
      expected: [ '성시경 Sung Si Kyung', '내게 오는 길' ] },

    // Things that are NOT file extensions are not removed:
    // https://www.youtube.com/watch?v=E2yLg9iW1_0
    { input: '에이핑크 - Mr.chu',
      expected: [ '에이핑크', 'Mr.chu' ] },
    // https://www.youtube.com/watch?v=P1Oya1PqKFc
    { input: 'Far East Movement - Live My Life (Feat. Justin Bieber) cover by J.Fla',
      expected: [ 'Far East Movement', 'Live My Life (Feat. Justin Bieber) cover by J.Fla' ] },
    // https://www.youtube.com/watch?v=rnQBF2CIygg
    // Thing that ends in a file extension without a preceding `.`:
    { input: 'Baka Oppai - A Piece Of Toast',
      expected: [ 'Baka Oppai', 'A Piece Of Toast' ] }
  ]
}

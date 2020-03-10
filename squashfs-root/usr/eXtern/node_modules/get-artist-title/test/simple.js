module.exports = {
  tests: [
    // https://youtu.be/hn4EIv1-uz0
    { input: 'Boats & BIrds - Gregory & the Hawk',
      expected: [ 'Boats & BIrds', 'Gregory & the Hawk' ] },
    // https://youtu.be/JoC3PUBmhFs
    { input: 'Sum 41 - In Too Deep (Official Video)',
      expected: [ 'Sum 41', 'In Too Deep' ] },
    // Punctuation mark at the end
    // https://youtu.be/fz3jLeDvpu4
    { input: 'FEMM - PoW! (Music Video)',
      expected: [ 'FEMM', 'PoW!' ] },
    // Song with a separator in its name (-), and unparenthesised "official video"
    // https://youtu.be/ti1W7Zu8j9k
    { input: 'The Wombats - Anti-D Official Video',
      expected: [ 'The Wombats', 'Anti-D' ] },
    // Words containing "…ver" should not be removed--only standalone "ver(.)".
    { input: '4MINUTE – Whatever',
      expected: [ '4MINUTE', 'Whatever' ] },
    { input: '4MINUTE – Whatever (Test Ver)',
      expected: [ '4MINUTE', 'Whatever' ] },
    // Quoted song title
    // https://www.youtube.com/watch?v=VVF0zxw4tuM
    { input: 'Low Roar - "Half Asleep"',
      expected: [ 'Low Roar', 'Half Asleep' ] },
    // Quoted song title _and_ "official video"
    // https://www.youtube.com/watch?v=qsWl1--Niyg
    { input: '4MINUTE - \'Volume Up\' (Official Music Video)',
      expected: [ '4MINUTE', 'Volume Up' ] },
    // Things with punctuation in front
    // https://www.youtube.com/watch?v=zsF5y1XhGuA
    { input: '...AND YOU WILL KNOW US BY THE TRAIL OF DEAD - Summer Of All Dead Souls',
      expected: [ '...AND YOU WILL KNOW US BY THE TRAIL OF DEAD', 'Summer Of All Dead Souls' ] },
    // File extensions _and_ "official video"
    // https://www.youtube.com/watch?v=ZPjwdiD24Kg
    { input: 'Low Roar - Give Up (Official Video).mov',
      expected: [ 'Low Roar', 'Give Up' ] },
    // A separator with _only_ fluff like "MV" on one side
    // https://www.youtube.com/watch?v=yRMvzyN-__Q
    { input: 'MV_Planet Shiver_Rainbow [feat. Crush]',
      expected: [ 'Planet Shiver', 'Rainbow' ] },
    // "Official MV"
    // https://www.youtube.com/watch?v=qSKPj--tyiM
    { input: '임정희 Lim Jeong Hee - I.O.U Official MV',
      expected: [ '임정희 Lim Jeong Hee', 'I.O.U' ] }
  ]
}

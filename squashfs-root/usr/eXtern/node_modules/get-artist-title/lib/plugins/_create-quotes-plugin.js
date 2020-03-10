var mapArtistTitle = require('../core').mapArtistTitle

module.exports = function (quotes) {
  var matchLooseRxes = quotes.map(function (set) {
    var open = set[0]
    var close = set[1]
    return new RegExp(open + '(.*?)' + close)
  })

  var matchStartRxes = quotes.map(function (set) {
    var open = set[0]
    var close = set[1]
    return new RegExp('^' + open + '(.*?)' + close + '\\s*')
  })

  function split (string) {
    for (var i = 0; i < matchLooseRxes.length; i++) {
      string = string
        .replace(matchLooseRxes[i], function ($0) { return ' ' + $0 + ' ' })
      var match = string.match(matchLooseRxes[i])
      if (match) {
        var split = match.index
        var title = string.slice(split)
        var artist = string.slice(0, split)
        return [artist, title]
      }
    }
  }

  function clean (artistOrTitle) {
    return matchStartRxes.reduce(function (string, rx) {
      return string.replace(rx, '$1 ')
    }, artistOrTitle).trim()
  }

  return {
    split: split,
    after: mapArtistTitle(clean, clean)
  }
}

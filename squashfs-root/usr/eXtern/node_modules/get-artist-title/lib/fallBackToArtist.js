// Create a plugin to fall back to the given artist name when no other plugins
// detected an artist/title combination.
module.exports = function fallBackToArtist (artist) {
  return {
    split: function (title) {
      return [artist, title]
    }
  }
}

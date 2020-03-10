// Create a plugin to fall back to the given title name when no other plugins
// detected an artist/title combination.
module.exports = function fallBackToTitle (title) {
  return {
    split: function (artist) {
      return [artist, title]
    }
  }
}

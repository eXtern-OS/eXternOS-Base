var fallBackToArtist = require('./fallBackToArtist')
var fallBackToTitle = require('./fallBackToTitle')

// Like `compose`, but left-to-right.
// flow([f, g])(x) = g(f(x))
function flow (functions) {
  if (!functions.length) {
    return function (arg) { return arg }
  }

  return function () {
    var result = functions[0].apply(this, arguments)
    for (var i = 1; i < functions.length; i++) {
      result = functions[i](result)
    }
    return result
  }
}

// Return the result of the first splitter function that matches.
function combineSplitters (splitters) {
  var l = splitters.length
  return function (str) {
    for (var i = 0; i < l; i++) {
      var result = splitters[i](str)
      if (result) return result
    }
  }
}

// Combine multiple plugins into a single plugin.
function reducePlugins (plugins) {
  var before = []
  var split = []
  var after = []
  plugins.forEach(function (plugin) {
    if (plugin.before) before.push(plugin.before)
    if (plugin.split) split.push(plugin.split)
    if (plugin.after) after.push(plugin.after)
  })
  return {
    before: flow(before),
    split: combineSplitters(split),
    after: flow(after)
  }
}

// Helpful-ish plugin checks
function checkPlugin (plugin) {
  if (plugin.split.length === 0) {
    throw new Error('no title splitter was specified by any plugin')
  }
}

function mapArtist (fn) {
  return function (parts) {
    return [fn(parts[0]), parts[1]]
  }
}

function mapTitle (fn) {
  return function (parts) {
    return [parts[0], fn(parts[1])]
  }
}

function mapArtistTitle (mapArtist, mapTitle) {
  return function (parts) {
    return [mapArtist(parts[0]), mapTitle(parts[1])]
  }
}

// Get an artist name and song title from a string.
function getSongArtistTitle (str, options, plugins) {
  if (options) {
    if (options.defaultArtist) {
      plugins.push(fallBackToArtist(options.defaultArtist))
    }
    if (options.defaultTitle) {
      plugins.push(fallBackToTitle(options.defaultTitle))
    }
  }

  var plugin = reducePlugins(plugins)

  checkPlugin(plugin)

  var split = plugin.split(plugin.before(str))
  if (!split) return

  return plugin.after(split)
}

exports = module.exports = getSongArtistTitle
exports.combineSplitters = combineSplitters
exports.mapArtist = mapArtist
exports.mapTitle = mapTitle
exports.mapArtistTitle = mapArtistTitle
exports.combinePlugins = reducePlugins

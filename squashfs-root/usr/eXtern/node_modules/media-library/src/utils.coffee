path = require 'path'

compare = (x, y) ->
  return 0 if x == y
  return (if x > y then 1 else -1)
  
escapeRegExp = (str) ->
  str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&")
  
mapPathToFolder = (p) ->
  path: p
  name: path.basename(p)
  type: 'folder'

mapTrackToFile = (track) ->
  path: track.path
  name: path.basename(track.path)
  type: 'file'
  track: track
  
getPathRegex = (p) ->
  new RegExp([
    '^',
    escapeRegExp(p + path.sep),
    '[^', escapeRegExp(path.sep), ']+',
    '$'
  ].join(""))
  
immediatly = global.setImmediate || process.nextTick
  
module.exports = {
  compare,
  escapeRegExp,
  mapPathToFolder,
  mapTrackToFile,
  getPathRegex,
  immediatly
}

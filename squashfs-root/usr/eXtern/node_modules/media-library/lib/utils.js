(function() {
  var compare, escapeRegExp, getPathRegex, immediatly, mapPathToFolder, mapTrackToFile, path;

  path = require('path');

  compare = function(x, y) {
    if (x === y) {
      return 0;
    }
    return (x > y ? 1 : -1);
  };

  escapeRegExp = function(str) {
    return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
  };

  mapPathToFolder = function(p) {
    return {
      path: p,
      name: path.basename(p),
      type: 'folder'
    };
  };

  mapTrackToFile = function(track) {
    return {
      path: track.path,
      name: path.basename(track.path),
      type: 'file',
      track: track
    };
  };

  getPathRegex = function(p) {
    return new RegExp(['^', escapeRegExp(p + path.sep), '[^', escapeRegExp(path.sep), ']+', '$'].join(""));
  };

  immediatly = global.setImmediate || process.nextTick;

  module.exports = {
    compare: compare,
    escapeRegExp: escapeRegExp,
    mapPathToFolder: mapPathToFolder,
    mapTrackToFile: mapTrackToFile,
    getPathRegex: getPathRegex,
    immediatly: immediatly
  };

}).call(this);

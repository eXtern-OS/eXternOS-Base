var path = require('path');

var MAX_FILE_LIST_LENGTH = 20;

function existsMessage(_path) {
  var file = require('./file-helper').file;
  var dir = require('./dir-helper').dir;

  var message = '';

  function checkParent(_path) {
    var parentPath = path.dirname(_path);
    if (parentPath === '.') { return; }

    var d = dir(parentPath);
    if (!d.exists) {
      message += 'parent path "' + parentPath + '" does not exist.\n';

      if (parentPath !== '/') {
        checkParent(parentPath);
      }
    } else if (!d.stats.isDirectory()) {
      message += 'parent path "' + parentPath + '" exists and is a file.\n';

    } else {
      message += 'parent path "' + parentPath + '" exists and contains:\n';

      d.content.slice(0, MAX_FILE_LIST_LENGTH).forEach(function(child) {
        var f = file(path.join(parentPath, child));
        message += '- ' + child + (f.stats.isDirectory() ? '/' : '') + '\n';
      });

      if (d.content.length > MAX_FILE_LIST_LENGTH) {
        message += '- [' + (d.content.length - MAX_FILE_LIST_LENGTH) + ' more...]';
      }
    }
  }

  checkParent(_path);

  var prefix = 'expected "' + _path + '" to exist';
  if (message) {
    prefix += '\n\n' + message.trim();
  }

  return prefix;
}

module.exports = existsMessage;

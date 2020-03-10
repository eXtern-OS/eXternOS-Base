var fs = require('fs');
var path = require('path');
var AssertionError = require('assertion-error');

var existsMessage = require('./exists-message');

function DirectoryHelper(path) {
  this.path = path;
  this._exists = null;
  this._content = null;
}

Object.defineProperty(DirectoryHelper.prototype, 'absolutePath', {
  get: function() {
    return path.resolve(process.cwd(), this.path);
  }
});

Object.defineProperty(DirectoryHelper.prototype, 'stats', {
  get: function() {
    if (this._stats === undefined) {
      try {
        this._stats = fs.statSync(this.absolutePath);
      } catch (e) {
        this._stats = null;
      }
    }

    return this._stats;
  }
});

Object.defineProperty(DirectoryHelper.prototype, 'exists', {
  get: function() {
    return Boolean(this.stats);
  }
});

Object.defineProperty(DirectoryHelper.prototype, 'content', {
  get: function() {
    if (this._content === null) {
      this._content = fs.readdirSync(this.absolutePath);
    }

    return this._content;
  }
});

Object.defineProperty(DirectoryHelper.prototype, 'isEmpty', {
  get: function() {
    return this.content.length === 0;
  }
});

DirectoryHelper.prototype.assertExists = function(ssf) {
  if (!this.exists) {
    throw new AssertionError(existsMessage(this.path), {}, ssf);
  } else if (!this.stats.isDirectory()) {
    throw new AssertionError('expected "' + this.path + '" to be a directory', {}, ssf);
  }
};

DirectoryHelper.prototype.assertDoesNotExist = function(ssf) {
  if (this.exists) {
    throw new AssertionError('expected "' + this.path + '" to not exist', {}, ssf);
  }
};

DirectoryHelper.prototype.assertIsEmpty = function(ssf) {
  this.assertExists(ssf);

  if (!this.isEmpty) {
    throw new AssertionError('expected "' + this.path + '" to be empty', {
      showDiff: true,
      actual: this.content,
      expected: [],
    }, ssf);
  }
};

DirectoryHelper.prototype.assertIsNotEmpty = function(ssf) {
  this.assertExists(ssf);

  if (this.isEmpty) {
    throw new AssertionError('expected "' + this.path + '" to not be empty', {}, ssf);
  }
};

DirectoryHelper.prototype.inspect = function() {
  return 'dir(\'' + this.path + '\')';
};

function dir(path) {
  return new DirectoryHelper(path);
}

module.exports = {
  dir: dir,
  DirectoryHelper: DirectoryHelper,
};

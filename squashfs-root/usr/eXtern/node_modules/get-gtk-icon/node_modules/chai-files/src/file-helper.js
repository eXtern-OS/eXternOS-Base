var fs = require('fs');
var path = require('path');
var AssertionError = require('assertion-error');

var existsMessage = require('./exists-message');

function FileHelper(path) {
  this.path = path;
  this._exists = null;
  this._content = null;
}

Object.defineProperty(FileHelper.prototype, 'absolutePath', {
  get: function() {
    return path.resolve(process.cwd(), this.path);
  }
});

Object.defineProperty(FileHelper.prototype, 'stats', {
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

Object.defineProperty(FileHelper.prototype, 'exists', {
  get: function() {
    return Boolean(this.stats);
  }
});

Object.defineProperty(FileHelper.prototype, 'content', {
  get: function() {
    if (this._content === null) {
      this._content = fs.readFileSync(this.absolutePath, {encoding: 'utf-8'});
    }

    return this._content;
  }
});

Object.defineProperty(FileHelper.prototype, 'isEmpty', {
  get: function() {
    return this.content === '';
  }
});

FileHelper.prototype.assertExists = function(ssf) {
  if (!this.exists) {
    throw new AssertionError(existsMessage(this.path), {}, ssf);
  } else if (!this.stats.isFile()) {
    throw new AssertionError('expected "' + this.path + '" to be a file', {}, ssf);
  }
};

FileHelper.prototype.assertDoesNotExist = function(ssf) {
  if (this.exists) {
    throw new AssertionError('expected "' + this.path + '" to not exist', {}, ssf);
  }
};

FileHelper.prototype.equals = function(str) {
  return this.content === str;
};

FileHelper.prototype.assertEquals = function(value, ssf, invert) {
  var valueIsFile = (value instanceof FileHelper);

  this.assertExists(ssf);
  if (valueIsFile) {
    value.assertExists(ssf);
  }

  var str = valueIsFile ? value.content : value;
  if (!this.equals(str)) {
    var valueOrPath = valueIsFile ? value.path : value;
    var message = invert ?
      'expected "' + valueOrPath + '" to equal "' + this.path + '"' :
      'expected "' + this.path + '" to equal "' + valueOrPath + '"';

    throw new AssertionError(message, {
      showDiff: true,
      actual: this.content,
      expected: str,
    }, ssf);
  }
};

FileHelper.prototype.assertDoesNotEqual = function(value, ssf, invert) {
  var valueIsFile = (value instanceof FileHelper);

  this.assertExists(ssf);
  if (valueIsFile) {
    value.assertExists(ssf);
  }

  var str = valueIsFile ? value.content : value;
  if (this.equals(str)) {
    var valueOrPath = valueIsFile ? value.path : value;
    var message = invert ?
      'expected "' + valueOrPath + '" to not equal "' + this.path + '"' :
      'expected "' + this.path + '" to not equal "' + valueOrPath + '"';

    throw new AssertionError(message, {}, ssf);
  }
};

FileHelper.prototype.assertIsEmpty = function(ssf) {
  this.assertExists(ssf);

  if (!this.isEmpty) {
    throw new AssertionError('expected "' + this.path + '" to be empty', {
      showDiff: true,
      actual: this.content,
      expected: '',
    }, ssf);
  }
};

FileHelper.prototype.assertIsNotEmpty = function(ssf) {
  this.assertExists(ssf);

  if (this.isEmpty) {
    throw new AssertionError('expected "' + this.path + '" to not be empty', {}, ssf);
  }
};

FileHelper.prototype.contains = function(str) {
  return this.content.indexOf(str) !== -1;
};

FileHelper.prototype.assertContains = function(str, ssf) {
  this.assertExists(ssf);
  if (!this.contains(str)) {
    throw new AssertionError('expected "' + this.path + '" to contain "' + str + '"', {
      showDiff: true,
      actual: this.content,
      expected: str,
    }, ssf);
  }
};

FileHelper.prototype.assertDoesNotContain = function(str, ssf) {
  this.assertExists(ssf);
  if (this.contains(str)) {
    throw new AssertionError('expected "' + this.path + '" to not contain "' + str + '"', {}, ssf);
  }
};

FileHelper.prototype.matches = function(regex) {
  return regex.test(this.content);
};

FileHelper.prototype.assertMatches = function(regex, ssf) {
  this.assertExists(ssf);
  if (!this.matches(regex)) {
    throw new AssertionError('expected "' + this.path + '" to match ' + regex, {
      showDiff: true,
      actual: this.content,
      expected: regex,
    }, ssf);
  }
};

FileHelper.prototype.assertDoesNotMatch = function(regex, ssf) {
  this.assertExists(ssf);
  if (this.matches(regex)) {
    throw new AssertionError('expected "' + this.path + '" to not match ' + regex, {}, ssf);
  }
};

FileHelper.prototype.inspect = function() {
  return 'file(\'' + this.path + '\')';
};

function file(path) {
  return new FileHelper(path);
}

module.exports = {
  file: file,
  FileHelper: FileHelper,
};

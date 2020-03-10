var FileHelper = require('./file-helper').FileHelper;
var DirectoryHelper = require('./dir-helper').DirectoryHelper;

module.exports = function(chai, utils) {
  var Assertion = chai.Assertion;

  /**
   * ### .exist
   *
   * Asserts that a file or directory exists.
   *
   *     expect(file('index.js')).to.exist;
   *     expect(file('index.coffee')).to.not.exist;
   *
   *     expect(dir('foo')).to.exist;
   *     expect(dir('missing')).to.not.exist;
   *
   * @name exist
   * @namespace BDD
   * @api public
   */

  function exist(_super) {
    return function() {
      var obj = this._obj;
      if (obj instanceof FileHelper || obj instanceof DirectoryHelper) {
        var ssf = utils.flag(this, 'ssfi');

        if (utils.flag(this, 'negate')) {
          obj.assertDoesNotExist(ssf);
        } else {
          obj.assertExists(ssf);
        }

      } else {
        _super.call(this);
      }
    };
  }

  Assertion.overwriteProperty('exist', exist);


  /**
   * ### .equal(value)
   *
   * Asserts that the file content equals a certain string or the content
   * of another file.
   *
   *     expect(file('foo.txt')).to.equal('foo');
   *     expect(file('foo.txt')).to.not.equal('bar');
   *
   *     expect(file('foo.txt')).to.equal(file('foo-copy.txt'));
   *     expect(file('foo.txt')).to.not.equal(file('bar.txt'));
   *
   *     expect('foo').to.equal(file('foo.txt'))
   *     expect('foo').to.not.equal(file('foo.txt'))
   *
   * @name match
   * @alias matches
   * @param {String|FileHelper} value
   * @namespace BDD
   * @api public
   */

  function assertEqual(_super) {
    return function(value) {
      var obj = this._obj;
      var ssf = utils.flag(this, 'ssfi');

      if (obj instanceof FileHelper) {
        if (utils.flag(this, 'negate')) {
          obj.assertDoesNotEqual(value, ssf);
        } else {
          obj.assertEquals(value, ssf);
        }

      } else if (value instanceof FileHelper) {
        if (utils.flag(this, 'negate')) {
          value.assertDoesNotEqual(obj, ssf, true);
        } else {
          value.assertEquals(obj, ssf, true);
        }

      } else {
        _super.apply(this, arguments);
      }
    };
  }

  Assertion.overwriteMethod('equal', assertEqual);
  Assertion.overwriteMethod('equals', assertEqual);
  Assertion.overwriteMethod('eq', assertEqual);


  /**
   * ### .empty
   *
   * Asserts that a file or directory is empty.
   *
   *     expect(file('empty.txt')).to.be.empty;
   *     expect(file('foo.txt')).to.not.be.empty;
   *
   *     expect(dir('empty')).to.be.empty;
   *     expect(dir('foo')).to.not.be.empty;
   *
   * @name empty
   * @namespace BDD
   * @api public
   */

  function empty(_super) {
    return function() {
      var obj = this._obj;
      if (obj instanceof FileHelper || obj instanceof DirectoryHelper) {
        var ssf = utils.flag(this, 'ssfi');

        if (utils.flag(this, 'negate')) {
          obj.assertIsNotEmpty(ssf);
        } else {
          obj.assertIsEmpty(ssf);
        }

      } else {
        _super.call(this);
      }
    };
  }

  Assertion.overwriteProperty('empty', empty);


  /**
   * ### .include(value)
   *
   * Asserts that the file content includes a certain string.
   *
   *     expect(file('foo.txt')).to.include('foo');
   *     expect(file('foo.txt')).to.not.include('bar');
   *
   * @name include
   * @alias contain
   * @alias includes
   * @alias contains
   * @param {String} value
   * @namespace BDD
   * @api public
   */

  function includeChainingBehavior(_super) {
    return function() {
      return _super.apply(this, arguments);
    }
  }

  function include(_super) {
    return function(value) {
      var obj = this._obj;
      if (obj instanceof FileHelper) {
        var ssf = utils.flag(this, 'ssfi');

        if (utils.flag(this, 'negate')) {
          obj.assertDoesNotContain(value, ssf);
        } else {
          obj.assertContains(value, ssf);
        }

      } else {
        _super.apply(this, arguments);
      }
    };
  }

  Assertion.overwriteChainableMethod('include', include, includeChainingBehavior);
  Assertion.overwriteChainableMethod('contain', include, includeChainingBehavior);
  Assertion.overwriteChainableMethod('includes', include, includeChainingBehavior);
  Assertion.overwriteChainableMethod('contains', include, includeChainingBehavior);

  /**
   * ### .match(regexp)
   *
   * Asserts that the file content matches a regular expression.
   *
   *     expect(file('foo.txt')).to.match(/fo+/);
   *     expect(file('foo.txt')).to.not.match(/bar/);
   *
   * @name match
   * @alias matches
   * @param {RegExp} regex
   * @namespace BDD
   * @api public
   */

  function assertMatch(_super) {
    return function(regex) {
      var obj = this._obj;
      if (obj instanceof FileHelper) {
        var ssf = utils.flag(this, 'ssfi');

        if (utils.flag(this, 'negate')) {
          obj.assertDoesNotMatch(regex, ssf);
        } else {
          obj.assertMatches(regex, ssf);
        }

      } else {
        _super.apply(this, arguments);
      }
    };
  }

  Assertion.overwriteMethod('match', assertMatch);
  Assertion.overwriteMethod('matches', assertMatch);
};

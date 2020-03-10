/*jshint -W054 */
;(function (exports) {
  'use strict';

  var BREAK = {}
    , exp = {}
    ;

  function create(PromiseA) {
    PromiseA = PromiseA.Promise || PromiseA;


    function forEachAsync(arr, fn, thisArg) {
      var result = PromiseA.resolve()
        ;

      arr.forEach(function (item, k) {
        result = result.then(function () {

          var ret
            ;

          if (thisArg) {
            ret = fn.call(thisArg, item, k, arr);
          } else {
            ret = result = fn(item, k, arr);
          }

          if (!ret || !ret.then) {
            ret = PromiseA.resolve(ret);
          }

          return ret.then(function (val) {
            if (val === forEachAsync.__BREAK) {
              return PromiseA.reject(new Error('break'));
              //throw new Error('break');
            }

            return val;
          });
        });
      });

      result.catch(function (e) {
        if ('break' !== e.message) {
          throw e;
        }
      });

      return result;
    }

    forEachAsync.__BREAK = BREAK;

    return forEachAsync;
  }

  /*
  exp = forEachAsync.forEachAsync = forEachAsync;
  exports = exports.forEachAsync = forEachAsync.forEachAsycn = forEachAsync;
  exports.create = forEachAsync.create = function () {};
  */


  try { 
   exp.forEachAsync = create(require('bluebird'));
  } catch(e) {
    if ('undefined' !== typeof Promise) {
      exp.forEachAsync = create(Promise);
    } else {
      try { 
       exp.forEachAsync = create(require('es6-promise'));
      } catch(e) {
        try { 
         exp.forEachAsync = create(require('rsvp'));
        } catch(e) {
          console.warn('forEachAsync needs requires a promise implementation and your environment does not provide one.'
            + '\nYou may provide your own by calling forEachAsync.create(Promise) with a PromiseA+ implementation'
          );
        }
      }
    }
  }

  exports.forEachAsync = exp.forEachAsync.forEachAsync = exp.forEachAsync || function () {
    throw new Error("You did not supply a Promises/A+ implementation. See the warning above.");
  };
  exports.forEachAsync.create = create;

}('undefined' !== typeof exports && exports || new Function('return this')()));

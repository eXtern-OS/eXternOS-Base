var test = require('tape');
var tou8 = require('../');

test('string to uint8', function (t) {
    t.plan(2);
    var str = 'whatever';
    var a = tou8(str);
    t.equal(a.constructor.name, 'Uint8Array', 'constructor name');
    t.equal(a.length, 8, 'length');
});

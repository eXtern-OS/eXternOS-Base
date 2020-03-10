var test = require('tape');
var tou8 = require('../');

test('buffer to uint8', function (t) {
    t.plan(2);
    var buf = new Buffer('whatever');
    var a = tou8(buf);
    t.equal(a.constructor.name, 'Uint8Array', 'constructor name');
    t.equal(a.length, 8, 'buffer length');
});

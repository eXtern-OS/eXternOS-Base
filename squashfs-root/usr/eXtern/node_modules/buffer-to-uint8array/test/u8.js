var test = require('tape');
var tou8 = require('../');

test('uint8 to uint8', function (t) {
    t.plan(3);
    var a = new Uint8Array(8);
    var buf = Buffer('whatever');
    for (var i = 0; i < buf.length; i++) a[i] = buf[i];
    
    var b = tou8(a);
    
    t.equal(a, b, 'reference equality');
    t.equal(a.constructor.name, 'Uint8Array', 'constructor name');
    t.equal(a.length, 8, 'u8 length');
});

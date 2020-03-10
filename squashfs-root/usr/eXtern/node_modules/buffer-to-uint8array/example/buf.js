var tou8 = require('../');
var buf = new Buffer('whatever');
var a = tou8(buf);
console.log(a.constructor.name);
console.log(a);

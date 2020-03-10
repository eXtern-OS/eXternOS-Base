# buffer-to-uint8array

convert a buffer (or string) to a Uint8Array

# example

``` js
var tou8 = require('buffer-to-uint8array');
var buf = new Buffer('whatever');
var a = tou8(buf);
console.log(a.constructor.name);
console.log(a);
```

# methods

``` js
var tou8 = require('buffer-to-uint8array')
```

## var u = tou8(buf)

Convert `buf`, a `Buffer` or `string` to a `Uint8Array`.

If `buf` is already a Uint8Array, it will be returned.

# install

With [npm](https://npmjs.org) do:

```
npm install buffer-to-uint8array
```

# license

MIT

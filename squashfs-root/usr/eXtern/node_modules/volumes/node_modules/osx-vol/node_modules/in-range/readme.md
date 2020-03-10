# in-range [![Build Status](https://travis-ci.org/sindresorhus/in-range.svg?branch=master)](https://travis-ci.org/sindresorhus/in-range)

> Check if a number is in a specified range


## Install

```
$ npm install --save in-range
```


## Usage

```js
var inRange = require('in-range');

inRange(30, 100); // 0..100
//=> true

inRange(30, 10, 100); // 10..100
//=> true

inRange(30, 100, 10); // 10..100
//=> true

inRange(30, 10); // 0..10
//=> false
```


## API

### inRange(value, [start], end)

#### value

Type: `number`

Number to check.

#### start

Type: `number`  
Default: `0`

Start of the range.

#### end

Type: `number`

End of the range.


## License

MIT © [Sindre Sorhus](http://sindresorhus.com)

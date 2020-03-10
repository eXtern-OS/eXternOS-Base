# osx-vol

> Get and set volume in OS X systems.


## Install

```
$ npm install --save osx-vol
```


## Usage

```js
const osxVol = require('osx-vol');

osxVol.get().then(level => {
	console.log(level);
	//=> 0.45
});

osxVol.set(0.65).then(() => {
	console.log('Changed volume level to 65%');
});
```


## API

### .get()

Returns a promise that resolves to current volume level.

### .set(level)

Returns a promise that resolves nothing.

#### level

*Required*
Type: `number`

A number between `0` and `1`.


## CLI

See the [vol](https://github.com/gillstrom/vol) CLI.


## License

MIT © [Andreas Gillström](http://github.com/gillstrom)

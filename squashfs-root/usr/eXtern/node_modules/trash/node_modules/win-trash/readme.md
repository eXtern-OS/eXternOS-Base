# win-trash

> Move files to the trash using the cmdutils [`Recycle.exe`](http://www.maddogsw.com/cmdutils/) binary


## Install

```
$ npm install --save win-trash
```


## Usage

```js
var winTrash = require('win-trash');

winTrash(['unicorn.png', 'rainbow.jpg'], function (error) {
	console.log('Successfully moved files to the trash');
});
```


## CLI

```
$ npm install --global win-trash
```

```
$ trash unicorn.png rainbow.png
```


## Related

See [`trash`](https://github.com/sindresorhus/trash) for a cross-platform trash CLI app.


## License

MIT © [Sindre Sorhus](http://sindresorhus.com)

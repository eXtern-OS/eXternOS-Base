# xdg-trashdir [![Build Status](http://img.shields.io/travis/kevva/xdg-trashdir.svg?style=flat)](https://travis-ci.org/kevva/xdg-trashdir)

> Get the correct trash path on Linux according to the [spec](http://www.ramendik.ru/docs/trashspec.html)

## Install

```sh
$ npm install --save xdg-trashdir
```

## Usage

```js
var trashdir = require('xdg-trashdir');

trashdir(function (err, dir) {
	console.log(dir);
	//=> /home/johndoe/.local/share/Trash
});

trashdir('foo.zip', function (err, dir) {
	console.log(dir);
	//=> /media/johndoe/UUI/.Trash-1000
});
```

## License

MIT © [Kevin Mårtensson](https://github.com/kevva)

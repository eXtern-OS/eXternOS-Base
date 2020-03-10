# xdg-trash [![Build Status](http://img.shields.io/travis/kevva/xdg-trash.svg?style=flat)](https://travis-ci.org/kevva/xdg-trash)

> Safely move files and directories to trash on Linux


## Install

```
$ npm install --save xdg-trash
```


## Usage

```js
var xdgTrash = require('xdg-trash');

xdgTrash(['foo.txt', 'bar.tar'], function (err) {
	console.log('Files successfully moved to trash!');
});
```


## API

### xdgTrash(files, callback)

Move files to trash.

#### files

*Required*
Type: `array`

Files to be moved to trash.

#### callback(err)

Type: `function`

Returns nothing but a possible exception.


## CLI

See the [trash](https://github.com/sindresorhus/trash#cli) CLI.


## License

MIT © [Kevin Mårtensson](https://github.com/kevva)

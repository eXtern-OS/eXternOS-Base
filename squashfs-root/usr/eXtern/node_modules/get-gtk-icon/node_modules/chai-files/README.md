
chai-files
==============================================================================

[![Build Status](https://travis-ci.org/Turbo87/chai-files.svg?branch=master)](https://travis-ci.org/Turbo87/chai-files)
[![Build status](https://ci.appveyor.com/api/projects/status/github/Turbo87/chai-files?svg=true)](https://ci.appveyor.com/project/Turbo87/chai-files/branch/master)
[![npm](https://img.shields.io/npm/v/chai-files.svg)](https://www.npmjs.com/package/chai-files)

file system assertions for chai


Installation
------------------------------------------------------------------------------

```
npm install --save-dev chai-files
```

Usage
------------------------------------------------------------------------------

After importing `chai` add the following code to use `chai-files` assertions:

```js
var chai = require('chai');
var chaiFiles = require('chai-files');

chai.use(chaiFiles);

var expect = chai.expect;
var file = chaiFiles.file;
var dir = chaiFiles.dir;
```


### .to.exist

Check if a file or directory exist:

```js
expect(file('index.js')).to.exist;
expect(file('index.coffee')).to.not.exist;

expect(dir('foo')).to.exist;
expect(dir('missing')).to.not.exist;
```


### .to.equal(...)

Check if the file content equals a string:

```js
expect(file('foo.txt')).to.equal('foo');
expect(file('foo.txt')).to.not.equal('bar');

expect('foo').to.equal(file('foo.txt'));
expect('foo').to.not.equal(file('foo.txt'));
```


### .to.equal(file(...))

Check if the file equals another file:

```js
expect(file('foo.txt')).to.equal(file('foo-copy.txt'));
expect(file('foo.txt')).to.not.equal(file('bar.txt'));
```


### .to.be.empty

Check if a file or directory is empty:

```js
expect(file('empty.txt')).to.be.empty;
expect(file('foo.txt')).to.not.be.empty;

expect(dir('empty')).to.be.empty;
expect(dir('foo')).to.not.be.empty;
```


### .to.contain(...)

Check if a file contains a string:

```js
expect(file('foo.txt')).to.contain('foo');
expect(file('foo.txt')).to.not.contain('bar');
```


### .to.match(/.../)

Check if a file matches a regular expression:

```js
expect(file('foo.txt')).to.match(/fo+/);
expect(file('foo.txt')).to.not.match(/bar?/);
```


License
------------------------------------------------------------------------------
chai-files is licensed under the [MIT License](LICENSE).

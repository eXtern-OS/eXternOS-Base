# sudo-js

Using sudo with password for node-js.

sudo-js by default has support for windows, linux and osx. But the root access (UAC) in Windows is not running. This feature will be added later.

Install `npm install sudo-js --save`


### Running

basic

```javascript
var sudo = require('sudo-js');
sudo.setPassword('your-password');

var command = ['chmod', '0777', '/Users/didanurwanda/Downloads'];
sudo.exec(command, function(err, pid, result) {
	console.log(result);
});

```

performance optimizer

```javascript
var sudo = require('sudo-js');
sudo.setPassword('your-password');

var options = {check: false, withResult: false};
var command = ['chmod', '0777', '/Users/didanurwanda/Downloads'];
sudo.exec(command, options, function(err, pid, result) {
	console.log(result); // output '';
});
```

check password

```javascript
var sudo = require('sudo-js');
sudo.setPassword('your-password');

sudo.check(function(valid) {
	console.log('password valid : ', valid);
});
```

### API

- password
- setPassword (string)
- check (function)
- exec (array, object|function, function)
- killByPid (int, function)
- killByName (string, function)

### Options

- `check` check password before execute
- `withResult` sending result in callback

### Contributor

Dida Nurwanda

* [http://www.didanurwanda.com](http://www.didanurwanda.com)
* [Blog](http://blog.didanurwanda.com)
* [Github Repository](https://github.com/didanurwanda?tab=repositories)
* [NPM](https://www.npmjs.com/~didanurwanda)
* [Twitter](https://www.twitter.com/didanurwanda)
'use strict';
var path = require('path');
var execFile = require('child_process').execFile;

module.exports = function (paths, cb) {
	cb = cb || function () {};

	if (process.platform !== 'win32') {
		throw new Error('Windows only');
	}

	if (!Array.isArray(paths)) {
		throw new Error('Please supply an array of filepaths');
	}

	if (paths.length === 0) {
		setImmediate(cb);
		return;
	}

	paths = paths.map(function (el) {
		return path.resolve(String(el));
	});

	execFile('./Recycle.exe', ['-f'].concat(paths), {
		cwd: path.join(__dirname, 'cmdutils')
	}, function (err) {
		cb(err);
	});
};

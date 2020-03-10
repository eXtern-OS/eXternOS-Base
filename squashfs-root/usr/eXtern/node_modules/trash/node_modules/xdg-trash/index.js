'use strict';

var path = require('path');
var eachAsync = require('each-async');
var fs = require('fs-extra');
var uuid = require('uuid');
var xdgTrashdir = require('xdg-trashdir');

function trash(src, cb) {
	xdgTrashdir(src, function (err, dir) {
		if (err) {
			if (err.code === 'ENOENT') {
				err.noStack = true;
			}

			cb(err);
			return;
		}

		var name = uuid.v4();
		var dest = path.join(dir, 'files', name);
		var info = path.join(dir, 'info', name + '.trashinfo');

		var msg = [
			'[Trash Info]',
			'Path=' + src.replace(/\s/g, '%20'),
			'DeletionDate=' + new Date().toISOString()
		].join('\n');

		fs.move(src, dest, {mkdirp: true}, function (err) {
			if (err) {
				cb(err);
				return;
			}

			fs.outputFile(info, msg, function (err) {
				if (err) {
					cb(err);
					return;
				}

				cb(null, {
					path: dest,
					info: info
				});
			});
		});
	});
}

module.exports = function (paths, cb) {
	var files = [];
	cb = cb || function () {};

	if (process.platform !== 'linux') {
		throw new Error ('Only Linux systems are supported');
	}

	if (!Array.isArray(paths)) {
		throw new Error('`paths` is required');
	}

	paths = paths.map(function (p) {
		return path.resolve(String(p));
	});

	eachAsync(paths, function (path, i, next) {
		trash(path, function (err, file) {
			if (err) {
				next(err);
				return;
			}

			files.push(file);
			next();
		});
	}, function (err) {
		if (err) {
			cb(err);
			return;
		}

		cb(null, files);
	});
};

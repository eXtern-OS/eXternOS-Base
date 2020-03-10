'use strict';

var base = require('xdg-basedir');
var fs = require('fs');
var mount = require('mount-point');
var path = require('path');
var userHome = require('user-home');

/**
 * Get the correct trash path on Linux
 *
 * @param {String} file
 * @param {Function} cb
 * @api public
 */

module.exports = function (file, cb) {
	if (typeof file === 'function' && !cb) {
		cb = file;
		file = undefined;
	}

	if (process.platform !== 'linux') {
		throw new Error('Only Linux systems are supported');
	}

	if (!file) {
		cb(null, path.join(base.data, 'Trash'));
		return;
	}

	mount(userHome, function (err, ret) {
		if (err) {
			cb(err);
			return;
		}

		mount(file, function (err, res) {
			if (err) {
				cb(err);
				return;
			}

			if (res.mount === ret.mount) {
				cb(null, path.join(base.data, 'Trash'));
				return;
			}

			var top = path.join(res.mount, '.Trash');
			var topuid = top + '-' + process.getuid();
			var stickyBitMode = 17407;

			fs.lstat(top, function (err, stats) {
				if (err) {
					if (err.code === 'ENOENT') {
						cb(null, topuid);
						return;
					}

					cb(null, path.join(base.data, 'Trash'));
					return;
				}

				if (stats.isSymbolicLink() || stats.mode !== stickyBitMode) {
					cb(null, topuid);
					return;
				}

				cb(null, path.join(top, String(process.getuid())));
			});
		});
	});
};

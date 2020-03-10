'use strict';
var runApplescript = require('run-applescript');
var inRange = require('in-range');
var toPercent = require('to-percent');
var toDecimal = require('to-decimal');
var Promise = require('pinkie-promise');

exports.get = function () {
	if (process.platform !== 'darwin') {
		return Promise.reject(new Error('Only OS X systems are supported'));
	}

	return runApplescript('get volume settings').then(function (res) {
		return toDecimal(parseInt(res.split(':')[1], 10));
	});
};

exports.set = function (level) {
	if (process.platform !== 'darwin') {
		return Promise.reject(new Error('Only OS X systems are supported'));
	}

	if (typeof level !== 'number') {
		return Promise.reject(new TypeError('Expected a number'));
	}

	if (!inRange(level, 1)) {
		return Promise.reject(new Error('Expected a level between 0 and 1'));
	}

	return runApplescript('set volume output volume ' + toPercent(level));
};

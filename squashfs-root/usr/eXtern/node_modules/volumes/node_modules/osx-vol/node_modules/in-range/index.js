'use strict';
module.exports = function (x, start, end) {
	if (end === undefined) {
		end = start;
		start = 0;
	}

	if (typeof x !== 'number' || typeof start !== 'number' || typeof end !== 'number') {
		throw new TypeError('Expected all arguments to be numbers');
	}

	return x >= Math.min(start, end) && x <= Math.max(end, start);
};

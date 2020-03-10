const child_process = require('child_process');
const os = require('os');

let cppgeticon;
let searchedGtk3 = false;
let foundGtk3 = true;
let gtkSearchPromise;

function canQueryIcons(callback) {
	if (!searchedGtk3) {
		// Node.js is single-threaded so this is not a race condition.
		searchedGtk3 = true;
		gtkSearchPromise = new Promise(resolve => {
			if (!isSupportedOs()) resolve(false);
			child_process.spawn('pkg-config', ['gtk+-3.0'])
				.on('exit', code => {
					resolve(code === 0);
				});
		}).then(result => foundGtk3 = result);
	}
	let resultPromise = gtkSearchPromise || Promise.resolve(foundGtk3);
	const callbacktype = typeof callback;
	if (callbacktype === 'function') {
		resultPromise.then(result => callback(null, result), error => callback(error));
		return undefined;
	} else if (callbacktype === 'undefined') {
		return resultPromise;
	} else {
		throw new Error('The provided callback was not a function!');
	}
}

function canQueryIconsSync() {
	if (!searchedGtk3) {
		// if there’s already a pending async call, we will do the work two times.
		// But clients really shouldn’t do that, should they?
		searchedGtk3 = true;
		foundGtk3 = isSupportedOs()
			&& child_process.spawnSync('pkg-config', ['gtk+-3.0']).status === 0;
	}
	return foundGtk3;
}

function isSupportedOs() {
	// we currently only support linux 64 bit
	return os.platform() === 'linux' && os.arch() === 'x64';
}

function getIconPath(name, size, callback) {
	checkFirstTwoArgs(name, size);

	const callbacktype = typeof callback;
	const iconPromise = canQueryIcons()
		.then(hasGtk => new Promise((resolve, reject) => {
			if (!hasGtk) {
				reject(new Error('Cannot obtain icons from GTK 3 on this system!'));
			}
			loadCppModule();
			cppgeticon.getIcon(name, size, wrap(resolve, reject));
		}));
	if (callbacktype === 'function') {
		iconPromise.then(result => callback(null, result), error => callback(error));
		return undefined;
	} else if (callbacktype === 'undefined') {
		return iconPromise;
	} else {
		throw new Error('The third argument, if given, must be a callback!');
	}
}

// callbacks must be called with a clear stack. Promise callbacks will fail
// otherwise.
function wrap(resolve, reject) {
	return result => setImmediate(() => {
		if (result === null) {
			reject(new Error('No icon found'));
		} else {
			resolve(result);
		}
	});
}

function getIconPathSync(name, size) {
	checkFirstTwoArgs(name, size);
	if (!canQueryIconsSync()) {
		throw new Error('Cannot obtain icons from GTK 3 on this system!');
	}
	loadCppModule();

	return cppgeticon.getIconSync(name, size);
}

function loadCppModule() {
	cppgeticon = cppgeticon || require('bindings')('gtkicon.node');
}

function checkFirstTwoArgs(iconName, iconSize) {
	if (typeof iconName !== 'string') {
		throw new Error('The icon name must be a string!');
	}
	if (typeof iconSize !== 'number') {
		throw new Error('The icon size must be a number!');
	}
}

module.exports = {
	canQueryIcons,
	getIconPath,
	canQueryIconsSync,
	getIconPathSync
};

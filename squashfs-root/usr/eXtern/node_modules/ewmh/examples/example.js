var x11 = require('x11');
var EWMH = require('../lib/ewmh');

x11.createClient(function(err, display) {
    if (err) {
        throw err;
    }

    var ewmh = new EWMH(display.client, display.screen[0].root);
    ewmh.on('CurrentDesktop', function(d) {
        console.log('Client requested current desktop to be: ' + d);
    });

    ewmh.set_number_of_desktops(4, function(err) {
    	if (err) {
    		throw err;
    	}

    	ewmh.set_current_desktop(1);
    });
});

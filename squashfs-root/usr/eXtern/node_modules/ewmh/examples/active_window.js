var x11 = require('x11');
var EWMH = require('../lib/ewmh');

x11.createClient(function(err, display) {
    if (err) {
        throw err;
    }

    var ewmh = new EWMH(display.client, display.screen[0].root);
    ewmh.on('ActiveWindowChange', function(wid) {
        console.log('new active window:', wid);
    });
});

var x11 = require('x11');
var get_property = require('../lib/get_prop');
var set_property = require('../lib/set_prop');

x11.createClient(function(err, display) {
    if (err) {
        throw err;
    }

    var X = display.client;
    var root = display.screen[0].root;
    var wid = X.AllocID();

    /* Create a new window */
    X.CreateWindow(wid, root, 0, 0, 1, 1); // 1x1 pixel window
    X.ChangeWindowAttributes(wid, { eventMask: x11.eventMask.PropertyChange });
    X.on('event', function(ev) {
        /* Get WM_CLASS property */
        get_property(X, wid, ev.atom, 'STRING', function(err, data) {
            if (!err) {
                console.log('WM_CLASS: ' + data);
            }
        });
    });

    /* Set WM_CLASS property. */
    set_property(X, wid, 'WM_CLASS', 'STRING', 8, [ 'My Name', 'My Class' ], true);
});

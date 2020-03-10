var x11 = require('x11');
var decoder = require('../lib/decoder');
var encoder = require('../lib/encoder');

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
        /* Get property and decode the data */
        X.GetProperty(0, wid, X.atoms.WM_CLASS, X.atoms.STRING, 0, 1000000000, function(err, prop) {
            if (!err) {
                var decoded_data = decoder.decode('STRING', prop.data);
                console.log('Decoded WM_CLASS: ' + decoded_data);
            }
        });
    });

    /*
     * Set WM_CLASS property. Use the encoder to generate the data
     * We set the third parameter to true because WM_CLASS strings are null terminated.
     */
    var data = encoder.encode('STRING', [ 'My Name', 'My Class' ], true);
    X.ChangeProperty(0, wid, X.atoms.WM_CLASS, X.atoms.STRING, 8, data);
});

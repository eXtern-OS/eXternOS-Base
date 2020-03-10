var x11 = require('x11');
var xsettings = require('../index.js');

x11.createClient(function(err, display) {
    var X = display.client;
    X.InternAtom(false, '_XSETTINGS_S0', function(err, settingsOwnerAtom) {
      X.InternAtom(false, '_XSETTINGS_SETTINGS', function(err, xsettingsAtom) {
        if (err) {
          throw err;
        }

        X.GetSelectionOwner(settingsOwnerAtom, function(err, win) {
          if (err) {
            throw err
          }

          X.GetProperty(0, win, xsettingsAtom, 0, 0, 1e20, function(err, propValue) {
            if (err) {
              throw err;
            }

            var decoded = xsettings.decode(propValue.data);
            console.log(decoded);
            var encoded = xsettings.encode(decoded, 0);
            var decoded_again = xsettings.decode(encoded);
            console.log(decoded_again);
          });
        });
      });
    });
});

# node-x11-prop

Utility to deal with X11 properties

## Example

Install x11 and x11-prop module
```
npm install x11 x11-prop
```
You can setting, getting properties easily

```
var x11 = require('x11');
var x11prop = require('x11-prop');
var get_property = x11prop.get_property;
var set_property = x11prop.set_property;

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
```

You can also encode / decode them and then using the x11 core requests directly

```
var x11 = require('x11');
var x11prop = require('x11-prop');
var decoder = x11prop.decoder;
var encoder = x11prop.encoder;

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
```


## Supported Types

STRING, UTF8_STRING, ATOM, INTEGER, CARDINAL, WINDOW, WM_STATE, _XSETTINGS_SETTINGS

## API

### Set property

```
x11prop.set_property(X, wid, prop, type, format, data[, null_terminated], cb)

X : X client from x11 library
wid : window id
prop : property (string or atom)
type : type of the property (string or atom)
format : 8, 16, 32
data : 1 - Array of strings for string properties: STRING, UTF8_STRING
       2 - Array of integers for ATOM, INTEGER, CARDINAL, WINDOW
       3 - For WM_STATE: { state : integer [, icon : integer ]}
       4 - For _XSETTINGS_SETTINGS: { serial: integer, setting1 : { type:
                                      integer, serial: integer, value: {}}, ... }
           See: https://github.com/sidorares/x11-xsettings
null_terminated : (optional AND only for string properties) if true, the strings will be null terminated.
                  Otherwise, they will be null separated.
```
### Get property

```
x11prop.get_property(X, wid, prop, type, cb)

X : X client from x11 library
wid : window id
prop : property (string or atom)
type : type of the property (string or atom)
cb : function(err, result), where result is the decoded property value
```

### Encode


```
x11prop.encode(type, data [, null_terminated ])

type : string with one of the supported types
data : 1 - Array of strings for string properties: STRING, UTF8_STRING
       2 - Array of integers for ATOM, INTEGER, CARDINAL, WINDOW
       3 - For WM_STATE: { state : integer [, icon : integer ]}
       4 - For _XSETTINGS_SETTINGS: { serial: integer, setting1 : { type:
                                      integer, serial: integer, value: {}}, ... }
           See: https://github.com/sidorares/x11-xsettings
null_terminated : (optional AND only for string properties) if true, the strings will be null terminated.
                  Otherwise, they will be null separated
```

### Decode

```
x11prop.decode(type, data)

type : string with one of the supported types
data : data field of the property object returned by *X.GetProperty*
```

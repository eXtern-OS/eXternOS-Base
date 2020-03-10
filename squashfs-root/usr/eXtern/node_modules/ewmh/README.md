node-ewmh
================

This module allows a window manager to implement the Extended Window Manager Hints. See: http://standards.freedesktop.org/wm-spec/wm-spec-1.3.html


Example
=======

Install x11 and ewmh modules
```
npm install x11 ewmh
```

```
var x11 = require('x11');
var EWMH = require('ewmh');

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
```

HINTS - API relationship
=======
This is a work in progress.

\_NET\_SUPPORTED - ewmh.set\_supported(hints_list, cb)

\_NET\_NUMBER\_OF\_DESKTOPS - ewmh.set\_number\_of\_desktops

\_NET\_CURRENT\_DESKTOP - ewmh.set\_current\_desktop

\_NET\_CLIENT\_LIST - ewmh.update\_window\_list(list, cb)

\_NET\_CLIENT\_LIST\_STACKING - ewmh.update_window_list_stacking(list_stacking, cb)

\_NET\_WM\_PID - emwh.set_pid(windowId, cb)

WM\_CLIENT\_MACHINE - emwh.set_hostname(windowId, cb)

\_NET\_ACTIVE\_WINDOW - ewmh.set_active_window(windowId, cb)

\_NET\_WM\_CM\_S0 - emwh.set_composite_manager_owner(windowId, screenNo, cb)

\_NET\_CLOSE\_WINDOW - ewmh.close_window(windowId, delete_protocol);

\_NET\_WM\_DESKTOP - ewmh.set_desktop(windowId, desktop, cb);

=======

EVENTS
=======

Events are generated whenever a client requests the modification of a HINT.

**Events - Hint relationship**

*ActiveWindow* - \_NET\_ACTIVE\_WINDOW

*Close Window* - \_NET\_CLOSE\_WINDOW

*CurrentDesktop* - \_NET\_CURRENT\_DESKTOP

*Desktop* - \_NET\_WM\_DESKTOP


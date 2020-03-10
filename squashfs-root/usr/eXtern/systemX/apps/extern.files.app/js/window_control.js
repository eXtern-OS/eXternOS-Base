          var gui = require('nw.gui');
    var win = gui.Window.get();

var close_but = document.getElementById("close_button");
        var min_but = document.getElementById("minimize_button");

function close_app(evt) {
    win.close();
}
        
        function minimize_app(evt) {
    win.minimize();
}

        document.getElementById("close_button").onclick = function() {
            win.close();
        }
//close_but.addEventListener("click", close_app, false);
        //min_but.addEventListener("click", minimize_app, false);
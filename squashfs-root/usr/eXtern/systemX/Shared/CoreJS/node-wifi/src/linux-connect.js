var exec = require('child_process').exec;
var util = require('util');
var env = require('./env');

var escapeShell = function(cmd) {
    return '"'+cmd.replace(/(["\s'$`\\])/g,'\\$1')+'"';
};


module.exports = function (config) {

    return function(ap, callback) {


    	var commandStr = "nmcli dev wifi connect '" + ap.ssid + "'" +
    	    " password " + "'" + ap.password + "'" ;
console.log("AP",ap);

    	if (config.iface) {
    	    commandStr = commandStr + " iface " + config.iface;
    	}

        // commandStr = escapeShell(commandStr);

    	exec(commandStr, env, function(err, resp) {
console.log("RESPONSE",resp);
if (err)
    	    callback && callback(err);
else
callback;
    	});
    }
}

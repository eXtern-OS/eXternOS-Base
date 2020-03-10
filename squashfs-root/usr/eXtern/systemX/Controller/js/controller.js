//var proc = require('child_process').spawn('/usr/NodeJs/nw /usr/eXtern/iXAdjust');
var win = nw.Window.get();
//(nouveau|Intel).*Mesa 8.0
//sudo -u extern -H /usr/NodeJs/nw /usr/eXtern/iXAdjust
var UI_PID;
function runDesktop() {

var exec = require('child_process').exec;
var child = exec('/usr/eXtern/NodeJs/nw /usr/eXtern/systemX');
child.stdout.on('data', function(data) {
    //console.log('stdout: ' + data);
});
child.stderr.on('data', function(data) {
    //console.log('stdout: ' + data);
});
child.on('close', function(code) {
    //console.log('closing code: ' + code);

//App.quit();
  
runDesktop();
});

    child.stdout.on('end', function(data) {
        //console.log('stdout: ' + data);
    });

/*
var childB = exec('gnome-terminal');
childB.stdout.on('data', function(data) {
    console.log('stdout: ' + data);
});
childB.stderr.on('data', function(data) {
    console.log('stdout: ' + data);
});
childB.on('close', function(code) {
    console.log('close: ', code);
});*/

UI_PID = child.pid;

}
runDesktop();

var psTree = require('ps-tree');

var kill = function (pid, signal, callback) {
    signal   = signal || 'SIGINT';
    callback = callback || function () {};
    var killTree = true;
    if(killTree) {
        psTree(pid, function (err, children) {
            [pid].concat(
                children.map(function (p) {
                    return p.PID;
                })
            ).forEach(function (tpid) {
                try { process.kill(tpid, signal) }
                catch (ex) { }
            });
            callback();
        });
    } else {
        try { process.kill(pid, signal) }
        catch (ex) { }
        //callback();
    }
};

const ioHook = require('iohook');

ioHook.on("keyup", event => {
	if (event.rawcode == 114 && event.metaKey) {
		kill(UI_PID,'SIGKILL'); //.runDesktop //,runDesktop
	}
  // {keychar: 'f', keycode: 19, rawcode: 15, type: 'keypress'}
});

ioHook.start();

//http://krasimirtsonev.com/blog/article/Nodejs-managing-child-processes-starting-stopping-exec-spawn

//sudo -H -u extern /usr/NodeJs/nw /usr/eXtern/iXAdjust

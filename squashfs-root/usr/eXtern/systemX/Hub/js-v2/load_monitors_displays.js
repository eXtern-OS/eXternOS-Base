function load_all_monitors()
{

function ScreenToString(screen) {
  var string = "";
  string += "screen " + screen.id + " ";
  var rect = screen.bounds;
  string += "bound{" + rect.x + ", " + rect.y + ", " + rect.width + ", " + rect.height + "} ";
  rect = screen.work_area;
  string += "work_area{" + rect.x + ", " + rect.y + ", " + rect.width + ", " + rect.height + "} ";
  string += " scaleFactor: " + screen.scaleFactor;
  string += " isBuiltIn: " + screen.isBuiltIn;
  string += "<br>";
  return string;
}
var gui = require('nw.gui');
//init must be called once during startup, before any function to gui.Screen can be called
gui.Screen.Init();
var string = "";
var screens = gui.Screen.screens;
// store all the screen information into string
for (var i=0; i<screens.length; i++) {
  string += ScreenToString(screens[i]);
}
    
    console.log(string);
    
    //updateDisplay();
    //https://askubuntu.com/questions/639495/how-can-i-list-connected-monitors-with-xrandr


}

function updateDisplay() {
        //https://askubuntu.com/questions/121014/how-do-i-list-connected-displays-using-the-command-line
    //https://stackoverflow.com/questions/37048439/removing-lines-containing-specific-words-in-javascript
   
    
    
    
    /*var exec = require('child_process').exec,
                   child;
            //child = exec("xrandr --query",function (error, stdout, stderr)
            child = exec('xrandr | grep " connected "'+" | awk '{ print$1 }'",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       var lines = stdout.split("\n").filter( function(val){ 
    return val.indexOf( " connected" ) == -1;
  });
        console.log("SPLIT LINES",lines);
        
        //console.log("Displays",lines[0].substr(0, lines[0].indexOf('connected')));
        
      
        
        
        
        
        if (lines.length != allDisplays.length) { 
            enableThisDisplayOnly(lines,lines.length-1);
        
        if (allDisplays.length != 0) {
            setTimeout(function(){ chrome.runtime.reload(); }, 2000);
            }
        }
        
        allDisplays = lines;
        
        
        
        
       
        
    }       
});*/
    
     /*runningApps[0].windowObject.repositionWindow();*/ 
}



function enableThisDisplayOnly(displayID) {
//FIXME: Remove this and where it's called
/*
    si.graphics(function(data) {
    console.log("Reconnect Display",data);
        var disabledDisplays = false;
    for (var i=0; i < data.displays.length; i++) {
        if (data.displays[i].connection == displayID)
            execCommand = "xrandr --output "+data.displays[i].connection+" --auto";
        else {
            execCommand = "xrandr --output "+data.displays[i].connection+" --off";
            disabledDisplays = true;
        }
            
        
        console.log('SUCCESS: ' + execCommand);
        
        var exec = require('child_process').exec,
                   child;
            child = exec(execCommand,function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: ' + execCommand);
	reAdjustSystemAppsResolution();
        
        
        
        
        
    }       
});
    }
        if (disabledDisplays)
            setTimeout(function(){ chrome.runtime.reload(); \}, 1000);
});*/
}


setTimeout(function(){ load_all_monitors() }, 5000);
//var win = nw.Window.get(); 
//win.setShowInTaskbar(false);
//win.x = 0;
//win.y = screen.height-win.height+15;//screen.height-win.height-exploreBarHeight;
//console.log("Screen height:"+screen.width);

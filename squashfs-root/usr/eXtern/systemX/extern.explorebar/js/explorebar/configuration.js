var win = nw.Window.get();
//win.showDevTools();
//console.log("win.showDevTools();");
//win.canOpenHub = false;
var modeOpen = false;
var extrabarOpen = false;
var toggleMode  = "time"; //store id of currently displayed side details
var wifi = require('/usr/eXtern/systemX/Shared/CoreJS/node-wifi'); //Use custom one instead because the one that comes from the modules tries to change LC and screws everything up because it fails to do so.
var volumes = require('volumes');
var si = require('systeminformation');
var noOfDrives = 0
var screenshot = require('desktop-screenshot');
//var monitor = require('node-usb-detection');
var monthNames = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];
//https://www.npmjs.com/package/node-usb-detection
var stopCheckingForRecordingTIme = false;
var screenRecordingLive = false;
var wifiConnections = [];
function convertBytes(input) {
    current_filesize = input.toFixed(2);
    var size_reduction_level = 0;
    while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
          /*Check if its a whole number or not*/
          if (current_filesize % 1 !== 0)
      current_filesize = current_filesize.toFixed(2);
          
      
      switch(size_reduction_level){
          case 0: current_filesize +=" B"; break;
          case 1: current_filesize +=" KB"; break;
          case 2: current_filesize +=" MB"; break;   
          case 3: current_filesize +=" GB"; break;
          case 4: current_filesize +=" TB"; break;
          case 5: current_filesize +=" PB"; break;
          case 6: current_filesize +=" EB"; break;
          case 7: current_filesize +=" ZB"; break;
      }
    
    return current_filesize;
}

setTimeout(function() {
 
/*
console.log("Process jsHeapSizeLimit",convertBytes(window.performance.memory.jsHeapSizeLimit));
console.log("Process totalJSHeapSize",convertBytes(window.performance.memory.totalJSHeapSize));
console.log("usedJSHeapSize",convertBytes(window.performance.memory.usedJSHeapSize));
*/
    
    }, 10000);

var playerID = "";

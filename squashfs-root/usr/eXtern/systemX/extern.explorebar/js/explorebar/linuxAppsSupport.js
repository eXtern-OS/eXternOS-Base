//nw.Window.get().evalNWBin(null, '/usr/eXtern/iXAdjust/apps/extern.photos.app/js/binary.bin');

//https://www.npmjs.com/package/get-gtk-icon

//temp: paste <(cat /sys/class/thermal/thermal_zone*/type) <(cat /sys/class/thermal/thermal_zone*/temp) | column -s $'\t' -t | sed 's/\(.\)..$/.\1°C/'

var x11 = require('x11');

var fs = require('fs');


// function to encode file data to base64 encoded string
function base64_encode(file) {
    // read binary data
    var bitmap = fs.readFileSync(file);
    // convert binary data to base64 encoded string
    return new Buffer(bitmap).toString('base64');
}

/* Function: Get differences between arrays and return the difference*/
Array.prototype.diff = function (a) {
    return this.filter(function (i) {
        return a.indexOf(i) === -1;
    });
};

//win.showDevTools();
//console.log("win.showDevTools();");

//var base64str = base64_encode('icon.pam');

//var base64str = fs.readFileSync('icon.pam', 'base64');

//$("#appIcon").attr("src","data:image/pam;base64,"+base64str);


function functionb(err, tree) {
  //console.log("root2",tree);
  
  X.GetWMName(tree.children[10], function(err, treeb) {
        //console.log("treeb",treeb);
      });
}


function getIcon(windowID,pid) {



	
  var strx = 'xprop -id '+windowID+' -notype 32c _NET_WM_ICON |   perl -0777';
  var stra = " -pe '@_=/\\d+/g;";
  var strb = ' printf "P7\\nWIDTH %d\\nHEIGHT %d\\nDEPTH 4\\nMAXVAL 255\\nTUPLTYPE RGB_ALPHA\\nENDHDR\\n", splice@_,0,2; $_=pack "N*", @_;';
  var strc = " s/(.)(...)/$2$1/gs' > Shared/ProccessIcons/"+pid+".pam";
  
  var fullString = strx+stra+strb+strc;
  fullString = String.raw`${fullString}`;
  
  //console.log("command: "+fullString);
  
    var exec = require('child_process').exec,
                   child;
            child = exec("export LC_ALL=C && "+fullString,function (error, stdout, stderr)
    {
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
      

      iconToPng('Shared/ProccessIcons/'+pid+'.pam', pid);

      
      
    }
    });
}

//Just realised might as well have this and stop copying and pasting code haha

function runLinuxCommand(command) {
  
  var exec = require('child_process').exec,
                   child;
            child = exec(command,function (error, stdout, stderr)
    {
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
      
	

      
      
    }
    });

}

function linuxSetAppActive(windowID) {
  
  var exec = require('child_process').exec,
                   child;
            child = exec("wmctrl -ia "+windowID,function (error, stdout, stderr)
    {
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
      
	
	$(".runningApp").removeClass("activeApp");
		$("#app"+windowID).addClass("activeApp");
	

      
      
    }
    });

}


function getActiveLinuxWIndow() {
  
    var exec = require('child_process').exec,
                   child;
            child = exec("xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW",function (error, stdout, stderr)
    {
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
      
	var activeLinuxWin = stdout.replace("_NET_ACTIVE_WINDOW(WINDOW)	","");
      //console.log("window:."+activeLinuxWin+".");

	//console.log("sys window ids:",systemWindowsIDs);
	

	var iseXternOSApp = false;

	for (var i = 0; i < systemWindowsIDs.length; i++) {
		//Parsing to int because there is usually an additional 0 in hex difference between these.
		if (parseInt(activeLinuxWin, 16) == parseInt(systemWindowsIDs[i], 16)) {
			iseXternOSApp = true;
		}
			
	}

	if (!iseXternOSApp) {
		if ($("#app"+activeLinuxWin.replace("x","x0")).hasClass("activeApp")) {

		} else {
			$(".runningApp").removeClass("activeApp");
			$("#app"+activeLinuxWin.replace("x","x0")).addClass("activeApp");
		}
	} else {
		//console.log("window ss a system one:"+activeLinuxWin);
	}
	
	

      
      
    }
    });
}



function iconToPng(iconPath, PID) {
    var exec = require('child_process').exec,
                   child;
            child = exec("ffmpeg -i "+iconPath+" Shared/ProccessIcons/"+PID+".png",function (error, stdout, stderr)
    {
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {

	var base64Icon = "data:image/png;base64,"+fs.readFileSync("Shared/ProccessIcons/"+PID+".png", 'base64');//base64_encode("Shared/ProccessIcons/"+PID+".png");

	fs.unlink("Shared/ProccessIcons/"+PID+".png", (err) => {
  		if (err) throw err;
	  });
	
	  fs.unlink("Shared/ProccessIcons/"+PID+".pam", (err) => {
  		if (err) throw err;
	  });
      
      for (var m = 0; m < allActiveWindows.length; m++) {
        if (allActiveWindows[m].PID == PID) {
          allActiveWindows[m].icon = base64Icon;
	  $("#app"+allActiveWindows[m].id+" > .appIcon").attr("src",allActiveWindows[m].icon);
	  //fs.unlink("Shared/ProccessIcons/"+PID+".png");
	  
	  $("#appIcon").attr("src",allActiveWindows[m].icon);
        }
      }
      
    }
    });
}



function meme() {

  x11.createClient(function(err, display) {
    X = display.client;
    root = display.screen[0].root;
    
    ////console.log("root",root);
    
    
    
    X.GetInputFocus(root, function(err, winds) {
      
      //console.log("winds",winds);
      
      X.GetWMName(winds.focus, function(err, wind_name) {
        
        //console.log("got here");
        
        if (err) {
    		throw err;
    	}
        
        //console.log("wind_name",wind_name);
        
      });
      
    });
    
    
/*
    X.QueryTree(root, function(err, tree) {
        console.log(tree.children); //output all windows tree
      
      X.FetchName(tree.children[5], function(err, treeb) {
        console.log("treebs",treeb);
      });
      
      
      
      
    },functionb);*/
});
  
  /*for (var i = 0; i < tree.children.length; i++) {
        
        X.ChangeWindowAttributes(tree.children[i], { eventMask: x11.eventMask.EnterWindow|x11.eventMask.KeyPress });
    X.on('event', function(ev) {
        console.log(ev);
    });
        
      }*/
  
}

/*
var EWMH = require('ewmh');

  function meme() {
    
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
    	} else console.log("success desktop");

    	ewmh.set_current_desktop(2);
    });
     
     var list = [];
     
     ewmh.update_window_list(list, function(err) {
    	if (err) {
    		throw err;
    	} else console.log("success windows",list);

    	//ewmh.set_current_desktop(2);
    });
  
  

  





  });
    
  }*/

var allActiveWindows = [];
var allActiveWIndowsPIDs = [];
var allUnfilteredNumberOfWindows = [];
var mainDesktopPID = -1;
var systemWindowsIDs = [];
//win.showDevTools();

function loadWIndows() {
  var exec = require('child_process').exec,
                   child;
            child = exec("wmctrl -l -p -G",function (error, stdout, stderr)
    {
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
      
	var unfilteredSplit = stdout.split("\n");

	//Check if any changes to avoid unecessary processing
      if (unfilteredSplit.length > allUnfilteredNumberOfWindows.length) { 
        
        allUnfilteredNumberOfWindows = unfilteredSplit;

	//totalUnfilteredNumberOfWindows = unfilteredSplit.length;

	
      stdout.split("\n").forEach(function (allWindows, index) {
        
        if (allWindows.length > 3) { //Safe guard from empty strings
          
          var removeExtendedSpaces = allWindows.replace(/\s\s+/g,' ');
           var item = removeExtendedSpaces.split(' ');

		 windowTitle = removeExtendedSpaces.split(item[6]+" "+item[7]+" ")[1];

		if (windowTitle == "eXtern explorebar3332bn334") //explorebar 
		   mainDesktopPID = item[2]; //set system PID
          
          if (item[1] != -1) { //Not a sticky window i.e a desktop
            
           

 
        
        var windowObject = {
          id: item[0],
          title: windowTitle,
          PID: item[2],
          xOffset: item[3],
          yOffset: item[4],
          width: item[5],
          height: item[6]
        }
            
            var processObject = {
              PID: windowObject.PID,
              sampleWindowID: windowObject.id
            }

		



		allActiveWindows.map(function(e) { return e.id; }).indexOf(windowObject.id) === -1 ? allActiveWindows.push(windowObject) : console.log("Window already exists");
                
                allActiveWIndowsPIDs.map(function(e) { return e.PID; }).indexOf(processObject.PID) === -1 ? allActiveWIndowsPIDs.push(processObject) : console.log("PID already exists");
            
            //allActiveWIndowsPIDs.indexOf(processObject) === -1 ? allActiveWIndowsPIDs.push(processObject) : console.log("PID already exists");
            
          }
        

          
          
            
            
        }

        
      });
	
      
      /*var singleWindowSplit = activeWindowsRaw[0].split(" ");
      
      
      
      console.log("trial title",result);
      
      console.log("id: ",singleWindowSplit);*/
      //console.log("window Objects",allActiveWindows);
      //console.log("window PIDs",allActiveWIndowsPIDs);



	for (var k = 0; k < allActiveWindows.length;k++) {
		if (allActiveWindows[k].PID != mainDesktopPID && !$("#app"+allActiveWindows[k].id).length) {

			var winTitle = allActiveWindows[k].title;

			if (allActiveWindows[k].title.length > 14) {
				winTitle = allActiveWindows[k].title.substring(0, 14)+"...";
			}
			$("#runningApps").append('<a id="app'+allActiveWindows[k].id+'" class="runningApp tooltips" data-placement="right" data-original-title="'+allActiveWindows[k].title+'" href="javascript:void(0);" onclick="linuxSetAppActive(&quot;'+allActiveWindows[k].id+'&quot;)"><img class="appIcon" src="../apps/extern.files.app/icons/flash package.png"><span> '+winTitle+'</span></a>');

	if (allActiveWindows[k].title == "Install") {
		win.installerStartedEvent();
	}

console.log("winTitle: ",allActiveWindows[k].title);
      	runLinuxCommand("xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id "+allActiveWindows[k].id); //use blur and transparency
	runLinuxCommand("xprop -id "+allActiveWindows[k].id+" -f _NET_WM_WINDOW_OPACITY 32c -set _NET_WM_WINDOW_OPACITY 3600000000"); //use blur and transparencyr
  
		} else {
			systemWindowsIDs.push(allActiveWindows[k].id);
		}
	 }

        if($('.tooltips')[0]) {
            $('.tooltips').tooltip();
        }
      
      for (var k = 0; k < allActiveWIndowsPIDs.length;k++) {
	if (allActiveWIndowsPIDs[k].PID != mainDesktopPID)
        	getIcon(allActiveWIndowsPIDs[k].sampleWindowID,allActiveWIndowsPIDs[k].PID);
      }

	


      } else if (unfilteredSplit.length < allUnfilteredNumberOfWindows.length){
        
        var n_unfilteredSplit = [];
        
        var n_allUnfilteredNumberOfWindows = [];
        
        for (var i = 0; i < unfilteredSplit.length; i++) {
          if (unfilteredSplit[i] != "")
          n_unfilteredSplit.push(unfilteredSplit[i].substring(0, unfilteredSplit[i].indexOf(' ')));
        }
        
        for (var i = 0; i < allUnfilteredNumberOfWindows.length; i++) {
          if (allUnfilteredNumberOfWindows[i] != "")
          n_allUnfilteredNumberOfWindows.push(allUnfilteredNumberOfWindows[i].substring(0, allUnfilteredNumberOfWindows[i].indexOf(' ')));
        }
        
        var closedWIndows = n_allUnfilteredNumberOfWindows.diff(n_unfilteredSplit);
        
        //console.log("n_allUnfilteredNumberOfWindows",n_allUnfilteredNumberOfWindows);
        
        //console.log("n_unfilteredSplit",n_unfilteredSplit);
         
      //console.log("TO BE REMOVED closedWIndows: ", closedWIndows);
        
        for (var i = 0; i < closedWIndows.length; i++) {
          
          for (var j = 0; j < allActiveWindows.length; j++) {
            if (allActiveWindows[j].id == closedWIndows[i]) {
              allActiveWindows.splice(j, 1);
              //console.log("SPlicing");
              $("#app"+closedWIndows[i]).remove();
              break;
          }
		}
          
        }
        

	/*for (var i = 0; i < closedWIndows.length; i++) {
      var removeExtendedSpaces = closedWIndows[i].replace(/\s\s+/g,' ');
           	var item = removeExtendedSpaces.split(' ');
      
      console.log("TO BE REMOVED item: ", item);
      
      console.log("TO BE REMOVED id: ", item[0]);
      console.log("TO BE REMOVED Pid: ", item[2]);
      //console.log("TO BE REMOVED Pid: ", item[2]);

		if (item[2] != mainDesktopPID) { //Is PID the eXtern OS desktop PID
			$("#app"+item[0]).remove(); // item[0] is the id of the window
          console.log("REMOVED");
          
          for (var j = 0; j < allActiveWindows.length; j++) {
            if (allActiveWindows[j].id == item[0]) {
              allActiveWindows.splice(j, 1);
              console.log("SPlicing");
          }
		}
    }
	

	}*/
        allUnfilteredNumberOfWindows = unfilteredSplit;
        //console.log("differences: ",allActiveWindows);

	
        
        
        
        
      }
      
    }
    });
}

setTimeout(function(){ loadWIndows(); getActiveLinuxWIndow();

setInterval(function(){ loadWIndows(); getActiveLinuxWIndow();}, 4000);
}, 8000);








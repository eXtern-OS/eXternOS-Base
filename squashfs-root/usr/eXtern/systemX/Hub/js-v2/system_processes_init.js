
var explorebarSysWinId = 0;

const commsChannel = new BroadcastChannel("deskeXternChannel"); //Comms channel between process manager and Desktop
const explorebarCommsChannel = new BroadcastChannel("explorebareXternChannel"); //Comms channel between process manager and explorebar
const extrabarCommsChannel = new BroadcastChannel("extrabareXternChannel");  //Comms channel between process manager and extrabar

win.ignoreFirstBlurTrigger = false;

//FIXME: Enable /usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1


//Hub events
//win.showDevTools();
win.hidingNow = false; //Used to avoid on blur even being called if the user used another way to close the hub

    if (localStorage.getItem('useRealTimeBlur') != null) {
	var useRealTimeBlur = JSON.parse(localStorage.getItem('useRealTimeBlur'));
	console.log("useRealTimeBlur",useRealTimeBlur);

    } else {

var useRealTimeBlur = false;

}
//win.showDevTools();

// Use this to adapt window changes
//compton -b --opengl ..

function installerStartedEvent() {
	for (i = 0; i <  runningApps.length; i++) {
		 if (runningApps[i].realID == "extern.welcome.app") {
			runningApps[i].windowObject.installerStarted();
			break;
		}
	}
}


var posY = screen.height-716-56;

win.outerBodyBackground = window.document.getElementsByTagName("BACKGROUND");
		$(win.outerBodyBackground[0]).css("background-position",-25+"px "+"-"+posY+"px");

console.log("posY",posY);

console.log("posY win",win);





/*
Not relevant to v2 yet
win.on("focus", function () {

setTimeout(function(){ win.ignoreFirstBlurTrigger = false; }, 100);
//win.opened = true;
updateExplorebar();
$("#searchOuter > input").val("");
//console.log("hiiiii");
$("#searchOuter > input").focus();
//setTimeout(function(){ 
$("#searchOuter > input").val("");
$("#searchOuter > input").focus();
win.x = 0;
//$.bgAdjust(win);
console.log("win.window.screenY A",win.window.screenY);
//}, 1000);
});
*/


function moveGTKWindowButtonsToRight() {
    var exec = require('child_process').exec,
                   child;
            child = exec("gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close'",function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        

    }       
});
}

moveGTKWindowButtonsToRight();

function enableNodeDesktopSupport(type) {
    var exec = require('child_process').exec,
                   child;
            child = exec('gsettings set org.compiz.winrules:/org/compiz/profiles/unity/plugins/winrules/ '+type+' "title=eXtern Desktop"',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
    
        //console.log("success",type);
        
        if (type =="below-match")
            enableNodeDesktopSupport("no-focus-match");
        
        if (type =="no-focus-match")
            chrome.runtime.reload(); //Configuration Done, reload
        

    }       
});
}

function getWindowID(winTitle,callback,retryCount) {
    var exec = require('child_process').exec,
                   child;
            child = exec("xdotool search --name '"+winTitle+"'",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);

	if (retryCount == null)
		retryCount = 0;

	retryCount++;

	if (retryCount < 5)
		setTimeout(function(){ getWindowID(winTitle,callback,retryCount) }, 1000);
    } else {

	//console.log("tite: "+winTitle+" result: ",(stdout.replace(/(\r\n\t|\n|\r\t)/gm,""));
    
        callback(stdout.replace(/(\r\n\t|\n|\r\t)/gm,""));

    }       
});
}

function setExplorebarAsPanel(winID) {

//Changed to 25 as thats the maximize level 56 for normal, but no need
    var exec = require('child_process').exec,
                   child;
            child = exec('xprop -id '+winID+' -f _NET_WM_STRUT_PARTIAL 32cccccccccccc -set _NET_WM_STRUT_PARTIAL "0, 0, 0, 25, 0, 0, 0, 0, 0, 0, 0, 0"',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
    

    }       
});
}

function setDeskasDesktop(winID,isDock) {
	var winType = "DESKTOP";
	if (isDock)
		winType = "DOCK";
	console.log("setDeskasDesktop",winID);
    var exec = require('child_process').exec,
                   child;
            child = exec('xprop -id '+winID+' -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_'+winType+' && xprop -id '+winID+' -f _MOTIF_WM_HINTS 32c -set _MOTIF_WM_HINTS 0 && xprop -id '+winID+' -remove _MOTIF_WM_HINTS',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {

	if (isDock)
		executeNativeCommand("qdbus org.kde.KWin /KWin reconfigure");
    

    }       
});
}


function loadCursorIcon() {
    var exec = require('child_process').exec,
                   child;
            child = exec('xsetroot -cursor_name left_ptr',function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
    

    }       
});
}

loadCursorIcon();

//Execute Native command was here


function applyHubBlur(winId) {
  //executeNativeCommand('xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id '+winId); //Not used anymore
  console.log("setting up hud id: ",winId);
  hubId = winId;
}




function getWinIcon(data) {
	//console.log("icon",data);
}

function applyExplorebarWinProperties(winID) {

explorebarSysWinId = winID;

setExplorebarAsPanel(winID);
executeNativeCommand('wmctrl -r explorebar3332bn334 -b add,sticky'); //set it as sticky
executeNativeCommand('wmctrl -r explorebar3332bn334 -b add,skip_taskbar'); // Skip it from task bar
executeNativeCommand('wmctrl -r explorebar3332bn334 -b add,skip_pager'); // Skip it from pager

executeNativeCommand('wmctrl -r "eXtern Desktop" -b add,sticky'); //set it as sticky
executeNativeCommand('wmctrl -r "eXtern Desktop" -b add,skip_taskbar'); // Skip it from task bar
executeNativeCommand('wmctrl -r "eXtern Desktop" -b add,below');
setDeskasDesktop(winID,true); //So that when user selects show desktop, we don't hide this as well (explore bar)
executeNativeCommand('wmctrl -r "explorebar3332bn334" -b add,above'); //get on top

//executeNativeCommand('wmctrl -r "eXtern Desktop" -b add,skip_pager'); // Skip it from pager

//code below was attempt to get icon later
//executeNativeCommand('xprop -id '+winID+" -notype 32c _NET_WM_ICON | perl -0777 -pe '@_=/\d+/g; printf"+' "P7\nWIDTH %d\nHEIGHT %d\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n", splice@_,0,2; $_=pack "N*", @_; s/(.)(...)/$2$1/gs'+"'",getWinIcon); // Skip it from pager

}


//Automount - https://askubuntu.com/questions/342188/how-to-auto-mount-from-command-line

var exec = require('child_process').exec,
                   child;
            child = exec('gsettings get org.compiz.winrules:/org/compiz/profiles/unity/plugins/winrules/ below-match',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
        var supportedDesktopSettings = stdout.replace(/(?:\r\n|\r|\n)/g, '');
    
        //console.log("GSETTINGS:"+supportedDesktopSettings+".");
        
        if (supportedDesktopSettings != "'title=eXtern Desktop'") { //Node Desktop Wallpaper is not enabled
            
            enableNodeDesktopSupport("below-match");
            
        }
        
        
        
        
        
       
        
    }       
});







//"height": 66

/*
win.minimized = false;

win.on('minimize', function() {
    win.minimized = true;
  }); 

win.on('focus', function() {
  win.minimized = false;
    console.log("FOCUSED");
});

win.on('move', function() {
  win.minimized = false;
    console.log("MOVED");
});
*/

var currentBlurIMG = 0; //tackling the caching system.
function loadWinBG(new_win,callback) {

	//This is a dummy function because it's not being used anymore. Delete later once I find out who (where) is calling it
					
				}

var systemAppsLoaded = 0;

function showDesktopAnimated() {
	if (systemAppsLoaded > 1) {


	new Audio("file://"+process.cwd()+"/Shared/CoreAudio/Signed In First Time.mp3").play();
	setTimeout(function(){
		if(systemSetupCompleted) {
			runningApps[0].windowObject.show();
			$(runningApps[0].windowObject.window.document.getElementById("runningApps")).removeClass("hidden");

			$(runningApps[0].desktopObject.window.document.getElementById("deskStacksContainter")).removeClass("hiddenOpacity");
			
		} else {
      
    		}

			$(runningApps[0].desktopObject.window.document.getElementById("mainBg")).removeClass("hiddenOpacity");
	}, 2000);
	}
}


function addAppToExploreBar(AppToAdd) {
			console.log("adding App: ",AppToAdd);
			explorebarCommsChannel.postMessage({
				type: "add-app",
				app: AppToAdd
			});
}

function makeAppVisibleInExploreBar(AppId) {
			explorebarCommsChannel.postMessage({
				type: "show-app",
				appId: AppId
			});
}

function removeAppFromExploreBar(AppToRemove) {
			console.log("remove App: ",AppToRemove);
			explorebarCommsChannel.postMessage({
				type: "remove-app",
				app: AppToRemove
			});
}

function minimizeAppInExploreBar(AppToMinimize) {
			explorebarCommsChannel.postMessage({
				type: "minimize-app",
				app: AppToMinimize
			});
}

function focusAppInExploreBar(AppToFocus) {
			explorebarCommsChannel.postMessage({
				type: "focus-app",
				app: AppToFocus
			});
}

function unfocusAppInExploreBar(AppToUnfocus) {
			explorebarCommsChannel.postMessage({
				type: "unfocus-app",
				app: AppToUnfocus
			});
}

function toggleNetworkOptions() {
			explorebarCommsChannel.postMessage({
				type: "toggle-network-options"
			});
}

function workspaceSwitchedEvent() {
	//console.log("triggering event");
	explorebarCommsChannel.postMessage({
				type: "workspace-switched"
	});
}

function updateExplorebar() {
			if (systemSetupCompleted)
				var canOpenHub = true;
			else
				var canOpenHub = false;

			console.log("sending message");

			explorebarCommsChannel.postMessage({
				type: "init-objects-v2",
				sysWinId: explorebarSysWinId,
				systemSortedApps: systemSortedApps,
				accessedApps: accessedApps,
				canOpenHub: canOpenHub,
				runningApps: runningAppsNew,
				height: win.height,
				width: win.width,
				opened: win.opened,
				apps: allInstalledApps
			});
}

function updateExplorebarGenericInstance() {
		explorebarCommsChannel.postMessage({ type: "update-sys-generic-instance", nextGenericProcessId: currentTempApp.windowObject.sysWinId});
}

function updateExplorebarFilesInstance() {
		explorebarCommsChannel.postMessage({ type: "update-sys-files-instances", nextFilesProcessId: nextFilesProcess.sysWinId});
}

function updateHudInstance() {
//console.log("runningApps[hudInstancePos]: ",runningApps[hudInstancePos]);
		explorebarCommsChannel.postMessage({ type: "update-sys-hud-instance", hudProcessId: runningApps[hudInstancePos].windowObject.cWindow.id});
}

function increaseVolume(increase) {
	if (increase)
		runningApps[hudInstancePos].windowObject.appCommsChannel.postMessage({ type: "increase-volume"});
	else
		runningApps[hudInstancePos].windowObject.appCommsChannel.postMessage({ type: "decrease-volume"});
}

function increaseBrightness(increase) {
	if (increase)
		runningApps[hudInstancePos].windowObject.appCommsChannel.postMessage({ type: "increase-brightness"});
	else
		runningApps[hudInstancePos].windowObject.appCommsChannel.postMessage({ type: "decrease-brightness"});
}



function exploreBar() {

	explorebarCommsChannel.onmessage = function (ev) {
		console.log("evX",ev);

		if (ev.data.type == "explorebarReady-v2") {

			console.log("type: ",typeof ev.data);



			updateExplorebar();

			console.log("runningApps",runningApps);
//				



		} else if (ev.data.type == "function" && ev.data.name == "hideHubView") {
			//win.opened = false;
			win.ignoreFirstBlurTrigger = false;
			//win.hide();
			win.hideFixed();
		} else if (ev.data.type == "function" && ev.data.name == "showHubView") {
			console.log("showing showHubView");
			//win.show(); //toggleHub
			win.showFixed();
			//win.restore();
			win.ignoreFirstBlurTrigger = true;
			//win.opened = true;
			
		} else if (ev.data.type == "function" && ev.data.name == "toggleHub") {
			console.log("toggle showHubView",win.opened);
			 toggleHub();
			
		} else if (ev.data.type == "minimize-this-app") {
			for (var i = 0; i < runningApps.length; i++) {
				if (runningApps[i].id == ev.data.id) {
					runningApps[i].windowObject.minimize();
				}
			}
		} else if (ev.data.type == "new-windows") {
			console.log("update all new-windows: ",ev.data);
			for (var i = 0; i < runningApps.length; i++) { //Maybe limit this to the animation instance
				if (runningApps[i].windowObject.appCommsChannel) {
					console.log("post new-windows");
					runningApps[i].windowObject.appCommsChannel.postMessage(ev.data);
				}
			}
		} else if (ev.data.type == "open-app") {
			var files = [];
			runApp(ev.data.appId,files);
		} else if (ev.data.type == "show-itai") {
			if (ev.data.show) {
				executeNativeCommand("wmctrl -i -R "+runningApps[itaiInstancePos].windowObject.sysWinId,function () {
					runningApps[itaiInstancePos].windowObject.restore();
					executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+runningApps[itaiInstancePos].windowObject.sysWinId);
				});
					
			} else {
				console.log("minimizing ITAI");
				runningApps[itaiInstancePos].windowObject.minimize();
				//runningApps[itaiInstancePos].windowObject.callMinimizeEvent();
			}
			//var files = [];
			//runApp(ev.data.appId,files);
		}


	}

options = {
    "show": false,
    "title": "eXtern explorebar3332bn334",
    "icon": "icon.png",
    "transparent": true,
    "frame": false,
    "always_on_top": true,
    "focus": false,
    "width": screen.width,
    "min_width": screen.width,
    "visible_on_all_workspaces": true,
    "max_height": 49,
    "height": 49
};
    
//Launch explorebar
nw.Window.open('extern.explorebar/main.html',options,function(new_win) {
    new_win.title = "eXtern explorebar3332bn334"; //making this unique
new_win.adaptiveBlurEnabled  = function () {
			return adaptiveBlur;
		}

new_win.installerStartedEvent = installerStartedEvent;

	new_win.adjustHubVolumeSlider = function (percentage) {
		$('#ex1').slider( 'setValue', percentage );
	}


    new_win.on('loaded', function() {


	console.log("explorebar win: ",new_win);

      //new_win.App.argv.push("www.extern.io");
    //console.log('New window is loaded',$( new_win.window.document.body.background ).length);
      if ($( new_win.window.document.body.children[0])[0].nodeName !="BACKGROUND")
          //$(new_win.window.document.body).prepend('<background style="border-radius: 5px 5px 5px; position: absolute; width:100%; height:100%"></background>');
      //console.log('New window BG ELEMENT',$( new_win.window.document.body.children[0])[0].nodeName);
      //new_win.window.document.body.children[0].style.backgroundImage = document.body.children[0].style.backgroundImage;
        
        //new_win.window.document.getElementById("mainBlock").style.backgroundImage = document.body.children[0].style.backgroundImage;


	runningApps[0].windowObject.window.document.getElementById("launcherContainer").style.backgroundImage = document.body.children[0].style.backgroundImage;
              runningApps[0].windowObject.window.document.getElementById("rightPanelContainer").style.backgroundImage = document.body.children[0].style.backgroundImage;
              //runningApps[0].windowObject.window.document.getElementById("actionIconsView").style.backgroundImage = document.body.children[0].style.backgroundImage;
        new_win.window.document.getElementById("extraAiBar").style.backgroundImage = document.body.children[0].style.backgroundImage;
        new_win.window.document.getElementById("extraBar").style.backgroundImage = document.body.children[0].style.backgroundImage;
    
        new_win.bottomBar = true;
	new_win.loadWinBG = loadWinBG;

	systemAppsLoaded += 1; // Prepare to show

	showDesktopAnimated();


        
        new_win.repositionWindow = function () {
            var gui = require('nw.gui');
            //init must be called once during startup, before any function to gui.Screen can be called
            gui.Screen.Init();
            var string = "";
            var screens = gui.Screen.screens;
            //console.log("REPOSITION DONE")
            //new_win.y = window.screen.height-49; //FIXME
            new_win.x = 0;
            new_win.width = screen.width;
        }

	new_win.apps = allInstalledApps;
	new_win.accessedApps = accessedApps;
	new_win.getSystemSortedApps = function () {
					return systemSortedApps;

					}
	new_win.openApp = function (appName,files) {

	runApp(appName,files);

    //setTimeout(function(){ runApp(appName,files); }, 300);
    
    
    
}
 
        
      //FIXME remove: win.hide();
      $( new_win.window.document ).ready(function() {
          
          new_win.y = window.screen.height-49; //FIXME
	  new_win.setResizable(false);
          new_win.x = 0;
          new_win.width = screen.width;
	//win.show();
//$.bgAdjust(win);

//console.log("SCREENWIDTH:",screen.width);
          setTimeout(function(){ new_win.show(); new_win.width = screen.width; new_win.x = 0; new_win.y = window.screen.height-49;

getWindowID(new_win.title,applyExplorebarWinProperties); //Set the explorebar as a panel

	$("body").removeClass("hiddenOpacity"); //Was added so that the wallpaper can allign properly while window is hidden
//win.hide();
}, 2000); //RETURN HERE

          /*setTimeout(function(){ 
		//win.hide();
}, 2000);*/
          
          //added some delay cause for somereason waiting for the whole app/document to load doesn't work
          //setTimeout(function(){ new_win.show(); $.bgAdjust(new_win);}, 1000);

	

          $(new_win.window.document.body ).click(function() { 
          //win.hide(); 
          win.hideFixed();
          });

      });
    new_win.on('focus', function() {
        //win.hide();
        win.hideFixed();
new_win.x = 0;
        //win.minimized = true;
  //console.log("We're triggered");
        //$.bgAdjust(new_win,true);
});
    
    new_win.on('move', function() {
        //FIXME win.hide();
	new_win.setAlwaysOnTop(true);
        win.minimized = true;
    //$.bgAdjust(new_win,true);
	//console.log("explorebar moved",new_win.height);
	//new_win.y = window.screen.height-49;
	//new_win.height = 49;
	//new_win.height = 69; console.log("explorebar height restored");
	setTimeout(function(){new_win.restore(); /*console.log("old height",new_win.height);*/}, 500);
  }); 

new_win.on('close', function() {
  // do nothing
});

new_win.on('blur', function() {
  // do nothing
	console.log("on blur called");
new_win.setAlwaysOnTop(true);
	//win.opened = false;
	//updateExplorebar();
});
    });
    
    
    
           window.exploreBarWin = new_win;
        
        launchProperties = {
            windowObject: new_win,          
}
        
        new_win.runningApps = runningApps;
        new_win.sysWin = win;
        
        //console.log("WE ARE LANCHING PROPS AGAIN FOR SOME REASON
        runningApps.push(launchProperties);
prepareNextProcess();








if (systemSetupCompleted)
 checkOSUpates();

	desktop(); //FIXME
    extrabar();

});
    
    
 
}


function changeDesktopStackStyleTo(newStackStyle) {
	stackStyle = newStackStyle;
	localStorage.setItem('stackStyle', JSON.stringify(stackStyle));
//runningApps[0].desktopObject.changeStackStyle(newStackStyle);

	commsChannel.postMessage({type: "update-stack-style",stackStyle: stackStyle});
}

function addNewStack(stackLocation) {
	commsChannel.postMessage({type: "add-new-stack",stackLocation: stackLocation});
}


function desktop() {

	commsChannel.onmessage = function (ev) {
		console.log("evX",ev);

		if (ev.data == "desktopReady") {
			commsChannel.postMessage({
				type: "init-objects",
				map: map,
				stackStyle: stackStyle
			});

		} else if (ev.data.name == "setMountedDrives") {
			console.log("lolm",ev.data.data);
			detectedMountedDrives = ev.data.data;
			appsUpdateData();
		} else if (ev.data.name == "open-app") {
			openApp(ev.data.appName,ev.data.files);
		}

		

	}

//console.log("desktop() screen width:"+screen.width+" screen height:"+screen.height);

       options = {
    "show": true,
    "title": "eXtern Desktop",
    "icon": "icon.png",
    "frame": false,
    "transparent": true,
    "always_on_top": false,
    "visible_on_all_workspaces": true,
    "width": screen.width,
    "height": screen.height,
    "min_width": screen.width,
    "min_height": screen.height
};
    //['core', 'composite', 'opengl', 'copytex', 'mousepoll', 'imgpng', 'grid', 'commands', 'place', 'regex', 'animation', 'session', 'move', 'compiztoolbox', 'wall', 'resize', 'unitymtgrabhandles', 'snap', 'vpswitch', 'fade', 'workarounds', 'expo', 'winrules', 'ezoom', 'scale', 'unityshell']
    
    //Launch the desktop
nw.Window.open('extern.explorebar/desktop.html',options,function(new_win) {

    new_win.fileTypesIcons = fileTypesIcons;
    new_win.getfileIcon = getfileIcon;
    new_win.resolveFileType = resolveFileType;
	new_win.fileTypesApps = fileTypesApps;
    new_win.stackStyle = stackStyle;

	

	getWindowID("eXtern Desktop",setDeskasDesktop);


    
    new_win.on('loaded', function() {

		

	


     
        new_win.y = 0;
	new_win.x = 0;
new_win.height = screen.height;
new_win.setDrives = function (driveList) {
	detectedDrives = driveList;
}

new_win.setMountedDrives = function (drives) {
//console.log("setMountedDrives",drives);
	detectedMountedDrives = drives;
}

        new_win.openApp = openApp
        runningApps[0].desktopObject = new_win;
    
      $( new_win.window.document ).ready(function() {
	new_win.setResizable(false);

	systemAppsLoaded +=1;

	showDesktopAnimated();


          
            wallpaper.get().then(imagePath => {
                     runningApps[0].desktopObject.window.document.body.children[0].children[0].style.backgroundImage = "url('file://"+imagePath+"')";//"file://"+wallpaperPath;
            runningApps[0].desktopObject.window.document.body.children[0].children[0].style['background-size'] =  screen.width+"px "+screen.height+"px";

        //runningApps[0].desktopObject.window.window.document.getElementById("blurWallpaper").style.backgroundImage = document.body.children[0].style.backgroundImage;
        //runningApps[0].desktopObject.window.window.document.getElementById("blurWallpaper").style['background-size'] =  (screen.width+9)+"px "+screen.height+"px";

});
          
         

      });
        
    new_win.on('focus', function() {
//console.log("focused out");
        new_win.blur();
	//FIXME win.hide();
        win.minimized = true;
});
    
    new_win.on('move', function() {
        //FIXME win.hide();
        win.minimized = true;
	new_win.x = 0;
	new_win.y = 0;
    //$.bgAdjust(new_win,true);
  }); 

new_win.on('minimize', function() {
  new_win.restore();
});

new_win.on('close', function() {
  // do nothing
});
  

    });
    
    


});

}

function openApp(appName,files) {

	runApp(appName,files);

    //setTimeout(function(){ runApp(appName,files); }, 300);
    
    
    
}

var audioCallbackFunction;


function updateAudioInfoNotification(data,appProcess,callback) {
	audioCallbackFunction = callback;
	extrabarCommsChannel.postMessage({
			type: "update-audio-notification",
			data: data,
			appProcess: appProcess
	});
	
}

function updateAudioDeviceExtrabarInfo(deviceName,portIcons,portFriendlyName) {
	extrabarCommsChannel.postMessage({
			type: "update-audio-device",
			deviceName: deviceName,
			portIcons: portIcons,
			portFriendlyName: portFriendlyName,
			enhancedAudio: enhancedAudio
	});
	
}

function updateExtrabarPerfomanceMode() {
	extrabarCommsChannel.postMessage({
			type: "update-improve-perfomance-mode",
			improvePerfomanceMode: improvePerfomanceMode
	});
	
}

//runningApps[0].desktopObject.openApp = openApp;

function runcmd(cmd,args,callback) {
var childProcess = require('child_process');
var spawn = childProcess.spawn;
var child = spawn('cmd', );

child.stdout._handle.setBlocking(true);

////console.log("spawned: " + child.pid);

child.stdout.on('data', function(data) {
  console.log("Child data: " + data);
	if (callback != null)
		callback(null,data);


});
child.on('error', function () {
  console.log("Failed to start child.");
if (callback != null)
		callback("error starting",null);
});
child.on('close', function (code) {
  console.log('Child process exited with code ' + code);
	//enbleFullScreenAdaption();
});
child.stdout.on('end', function () {
  console.log('Finished collecting data chunks.');
	//enbleFullScreenAdaption();
});
}

var extraBarMovedCounter = 0;

function extrabar() {

	extrabarCommsChannel.onmessage = function (ev) {
		if (ev.data.type == "playback-play-trigger") {
			console.log("sending playback controls");
			audioCallbackFunction("playback-play-trigger");
		} else if (ev.data.type == "playback-pause-trigger") {
			console.log("sending playback controls");
			audioCallbackFunction("playback-pause-trigger");
		} else if (ev.data.type == "playback-next-trigger") {
			audioCallbackFunction("playback-next-trigger");
		} else if (ev.data.type == "playback-next-trigger") {
			audioCallbackFunction("playback-next-trigger");
		} else if (ev.data.type == "open-screenshot-app") {
			openApp("extern.photos.app",ev.data.files);;
		} else if (ev.data.type == "request-audio-info") {
			getAudioDevices(setAudioCurrentSettings);
		} else if (ev.data.type == "changed-enahnced-audio") {
			if (enhancedAudio != ev.data.enhancedAudio) {
			enhancedAudio = ev.data.enhancedAudio;
			localStorage.setItem('enhancedAudio', JSON.stringify(enhancedAudio));
			console.log("called here");

			if (enhancedAudio) {
				console.log("setting here"); ///usr/eXtern/systemX/Shared/CoreMsc/audio.sh
				setTimeout(function(){
				executeNativeCommand('pulseeffects --load-preset "Enhanced Audio Experience"', function () {
					//
				});
				}, 1000);
				/*runcmd('pulseeffects',['--load-preset','Enhanced Audio Experience'],function (err,res) {
					if (err)
						console.log("error occurred applying preset: ",err);
					else
						console.log("success applying preset: ",res);
					
				});*/
			} else {
				setTimeout(function(){
				console.log("resetting here");
				executeNativeCommand('pulseeffects --reset');
				}, 1000);
				/*runcmd('pulseeffects',['--reset'],function (err,res) {
					if (err)
						console.log("error occurred resetting: ",err);
					else
						console.log("success reset: ",res);
					
				});*/
			}
		}
		}
}

       options = {
    "show": true,
    "transparent": true,
    "title": "extrabar3332bnx334",
    "icon": "icon.png",
    "frame": false,
    "always_on_top": true,
    "width": 280,
    "max_height" : 310,
    "visible_on_all_workspaces": true,
    "height": 1
};//screen.width
    
    //Launch extrabar
nw.Window.open('extern.explorebar/extrabar.html',options,function(new_win) {

	console.log("hey");



var execSync = require('child_process').execSync;

var allProcesses = execSync("wmctrl -l").toString().split("\n");


		for (var i = allProcesses.length-1; i > -1; i--) {
			if (allProcesses[i].indexOf("extrabar3332bnx334") != -1) {
				new_win.sysWinId = allProcesses[i].split("  ")[0].split(" ")[0];
			}
		}

//executeNativeCommand('wmctrl -i -r '+new_win.sysWinId+' -b add,skip_pager');
//executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NOTIFICATION -id '+new_win.sysWinId);

//applyHubBlur(new_win.sysWinId);
    
    new_win.on('loaded', function() {

var execSync = require('child_process').execSync;

		//var lolll = execSync("xdotool search --name 'extrabar3332bnx334'").toString().split("\n");

		//console.log("allNewAppProcessesxM",lolll);
      //new_win.App.argv.push("www.extern.io");
    //console.log('New window is loaded',$( new_win.window.document.body.background ).length);
      if ($( new_win.window.document.body.children[0])[0].nodeName !="BACKGROUND")
          //$(new_win.window.document.body).prepend('<background style="border-radius: 5px 5px 5px; position: absolute; width:100%; height:100%"></background>');
      //console.log('New window BG ELEMENT',$( new_win.window.document.body.children[0])[0].nodeName);
      //new_win.window.document.body.children[0].style.backgroundImage = document.body.children[0].style.backgroundImage;
          
          new_win.bottomBar = false;

	updateExtrabarPerfomanceMode();
        

        //new_win.window.document.getElementById("extraAiBar").style.backgroundImage = document.body.children[0].style.backgroundImage;

	if (!useRealTimeBlur) {
    //new_win.window.document.getElementById("extraBar").style.backgroundImage = document.body.children[0].style.backgroundImage; //FIXME we are not gonna use this for now
  }
        	
    
        
 //new_win.hide();
        new_win.y = screen.height-420;
	new_win.x = screen.width-320;
    
      $( new_win.window.document ).ready(function() {
          
          //new_win.y = screen.height-166; //FIXME
          $(new_win.window.document.body ).click(function() { 
          
          //win.hide();
          win.hideFixed();
          
          });
          //setTimeout(function(){ new_win.show();}, 2000);
          
          //added some delay cause for somereason waiting for the whole app/document to load doesn't work
          setTimeout(function(){ new_win.show(); $.bgAdjust(new_win); 
                                
                           $(new_win.window.document.getElementById("extraBlockBGS")).click(function() {
              runningApps[0].windowObject.closeAllNotifications(true);
});
                                
                                $(new_win.window.document.getElementById("extraBlockBGS2")).click(function() {
              runningApps[0].windowObject.closeAllNotifications(true);
});    


                               
                               }, 1000);
          
          

      });
        
    new_win.on('focus', function() {
console.log("extrabar focus");
        //win.minimize();
        //win.minimized = true;
  //console.log("We're triggered");
        $.bgAdjust(new_win,true);
        setTimeout(function(){$.bgAdjust(new_win,true);}, 1000);
});
    
    new_win.on('move', function() {
        //FIXME win.hide();
console.log("extrabar move");

	if (extraBarMovedCounter == 1)
		if (new_win.sysWinId != null)
			executeNativeCommand('wmctrl -i -r '+new_win.sysWinId+' -b remove,skip_pager')

	if (extraBarMovedCounter < 1) //adding if because we don't need to keep adding to mem
		extraBarMovedCounter++;

        win.minimized = true;
    //$.bgAdjust(new_win,true);
        //setTimeout(function(){$.bgAdjust(new_win,true);}, 1000);
  }); 

new_win.on('close', function() {
  // do nothing
});
  

    });
    
    //if (webview.currentAtHome) {
    
           window.extraBarWin = new_win;
        

        
        new_win.runningApps = runningApps;
        new_win.sysWin = win;
    runningApps[0].extrabarObject = new_win;
    
    
    //FIXME setTimeout(function(){new_win.hide();}, 2000);
        
        //console.log("WE ARE LANCHING PROPS AGAIN FOR SOME REASON
        //runningApps.push(launchProperties);

});

}





 $(document).ready(function () {
    setTimeout(function(){getWindowID("Hub34334332",applyHubBlur);  exploreBar();}, 8000);
 });


function loadMultitouchGestures() {


        

        //Using "restart" allows us to be able to re-use this function when a user changes gestures

        var exec = require('child_process').exec,
                   child;
            child = exec("libinput-gestures-setup restart",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
        
        
        
        
    }       
});



}

// localStorage.setItem('closeButtonProperties', JSON.stringify(closeButtonProperties));



function changeBrightness(brightness) {


	var brightnessData = {
    		brightness: brightness
	}
	
	displayBrightness = brightness;

	$.post("http://127.0.0.1:8081/system/display/change_brightness",brightnessData, function (data, status) {
		if (status == "success") {
			console.log("success brightness change");
			localStorage.setItem('displayBrightness', JSON.stringify(displayBrightness));
			//console.log("changed brightness: ",JSON.parse(localStorage.getItem('displayBrightness')));
		} else {
			console.log("An error occurred changing brightness");
		}
    		//console.log("got back data: ",data);
    		//console.log("got back status: ",status);
	});



}

function changeGamma(gamma) {
    var gammaVal = gamma;
	 displayGamma = gammaVal;
    //console.log("GammaUpdated",gammaVal);
    
    var exec = require('child_process').exec,
                   child;
            //child = exec("xrandr --query",function (error, stdout, stderr)
            child = exec('xgamma -gamma '+gammaVal,function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
     $("#gammaPercentage").text(((gammaVal*100).toFixed(2)).replace(/\.00$/,'')+"%");
        localStorage.setItem('displayGamma', JSON.stringify(displayGamma));
       
        
        
        
        
        
       
        
    }       
});
}

function setTouchpadDefaults() {
executeNativeCommand("xinput list", function (devicesRaw) {
    var devices = devicesRaw.split("\n");
    //console.log("devices",devices);
    var touchpadDevices = [];

    for (var i = 0; i < devices.length; i++) {
        if (devices[i].toLowerCase().indexOf("touchpad") != -1) {
            console.log("found touchpad",devices[i]);
            var touchpadDevice = {
                id: devices[i].split("id=")[1].split("[")[0].trim(),
                name: devices[i].split("↳")[1].split("id=")[0].trim()
            }
            touchpadDevices.push(touchpadDevice);
            executeNativeCommand('xinput set-prop "'+touchpadDevice.id+'" "libinput Tapping Enabled" 1'); //FIXME: for now auto set tap to click to enabled by default
        }
    }

    //console.log("all:",touchpadDevices);
});
}

loadMultitouchGestures();
setTouchpadDefaults();
changeBrightness(displayBrightness);
changeGamma(displayGamma);

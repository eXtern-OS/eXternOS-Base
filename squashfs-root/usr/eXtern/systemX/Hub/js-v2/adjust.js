/*var option = {
  key : "VolumeUp",
  active : function() {
    console.log("Global desktop keyboard shortcut: " + this.key + " active."); 
  },
  failed : function(msg) {
    // :(, fail to register the |key| or couldn't parse the |key|.
    console.log("faiiled",msg);
  }
};

// Create a shortcut with |option|.
var shortcut = new nw.Shortcut(option);

// Register global desktop shortcut, which can work without focus.
nw.App.registerGlobalHotKey(shortcut);

// If register |shortcut| successfully and user struck "Ctrl+Shift+A", |shortcut|
// will get an "active" event.

// You can also add listener to shortcut's active and failed event.
shortcut.on('active', function() {
  console.log("Global desktop keyboard shortcut: " + this.key + " active."); 
});

shortcut.on('failed', function(msg) {
  console.log("faiiiled",msg);
});
    setTimeout(function(){ 
console.log("un registered");
    nw.App.unregisterGlobalHotKey(shortcut);
    
}, 60000);
// Unregister the global desktop shortcut.
//nw.App.unregisterGlobalHotKey(shortcut);
*/

//Speaker Icon Source: https://www.svgrepo.com/svg/88829/music-speaker

//win.showDevTools();
//console.log("win.showDevTools();");

var aiChatShown = true;
function toggleAiChat() {
    if (aiChatShown) {
        $("#aiResponse").fadeOut("fast");
        $("#hideAiChat")[0].children[0].innerHTML = "Show Replies";
        $("#showConvo").removeClass("hidden");
        $("#hideConvo").addClass("hidden");
        aiChatShown = false;
    } else {
        $("#aiResponse").fadeIn("fast");
        $("#hideAiChat")[0].children[0].innerHTML = "Hide Replies";
        $("#showConvo").addClass("hidden");
        $("#hideConvo").removeClass("hidden");
        aiChatShown = true;
    }
    
    console.log("close chatt: ",$("#hideAiChat"));
}





function refreshCourasel() {
    
   // setTimeout(function(){ 
    $("#myCarousel").carousel("pause").removeData();
        $("#weatherOuter").removeClass("active");
        $("#weatherOuter").removeClass("next");
        $("#weatherOuter").removeClass("left");
    $("#myCarousel").carousel();
    $("#myCarousel").carousel("cycle");
    //$("#myCarousel").carousel("play")
    
//}, 5000);
    
}



//win.showDevTools();



var oldWinWidth = 1156;
var oldWinHeight = 716;
var oldWinX = 0;
var oldWinY = screen.height-oldWinHeight+15;;

var blurTimeout;

/*
win.showFixed = function () {
	
	win.opened = true;
	window.opened = true;
	if (hubId != null) {
		$("background").show();
		
		blurTimeout = setTimeout(function(){
		executeNativeCommand("xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id "+hubId);
		$("background").fadeOut();
		console.log("applied blur for: ",hubId);
		}, 600);
	}
	win.moveTo(oldWinX, oldWinY);
	win.resizeTo(oldWinWidth, oldWinHeight);
	setTimeout(function(){
	win.opened = true;
	window.opened = true;
	//$('#file_context_menu').removeClass('animated fadeInUp');
    	$('#animateOpen').removeClass('hidden');
    	win.focus();
	}, 50);
	
	
}
*/
win.hideFixed = function () {
	/*win.resizeTo(1, 1);
	win.moveTo(0, screen.height);
	
	console.log("hubId: ",hubId);
	clearTimeout(blurTimeout)
	if (hubId != null)
		executeNativeCommand("xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -remove _KDE_NET_WM_BLUR_BEHIND_REGION -id "+hubId);
	//$('#file_context_menu').addClass('animated fadeInDown');
    	$('#animateOpen').addClass('hidden');
	console.log("hideFixed called");
	setTimeout(function(){
	win.opened = false;
	window.opened = false;
	}, 50);*/
}

function toggleHub() {
if (win.opened) {
			//win.hide();
			win.opened = false;
			console.log("here x");
			win.hideFixed();
			console.log("here x2");
		} else {
			win.ignoreFirstBlurTrigger = true;
			//win.show();
			console.log("here xa");
			win.showFixed();
			win.opened = true;
			console.log("here xa2");
		}
}

window.opened = false;

//win.show();
//setTimeout(function(){ win.show(); }, 2000);
//setTimeout(function(){win.hideFixed(); }, 1000);

function loadInfoOnConnection() {
    
    internetCheckInterval = window.setInterval(function(){
  // Constantly check for internet connection
            console.log("CHECK....");
            if (navigator.onLine) { //if online
                console.log("enabledSources",enabledSources);
                if (enabledSources.length != 0) {
                setTimeout(function(){ loadNewsSources(true);}, 5000);
                webInformationLoaded = true;
                } else {
			/*enabledSources.push("The Verge");
			enabledSources.push("CNN : Top Stories");
			enabledSources.push("CNN : World");
			loadNewsSources(true);
                	webInformationLoaded = true;*/
		}
		window.clearInterval(internetCheckInterval);
		    setTimeout(function(){ loadWeatherStats();  }, 5000);
                
                
    }
        }, 5000);
}
var filess = []; //runApp('extern.itai.app',filess);


/*

setTimeout(function(){

prepareNextProcess();








if (systemSetupCompleted)
 checkOSUpates(); 
}, 1000); //Delay to allow the Hub to load first*/


/* To remove spaces at the start of a string*/
function ltrim(str) {
  if(!str) return str;
  return str.replace(/^\s+/g, '');
}
/*
    var childProcess = require('child_process');
var spawn = childProcess.spawn;
var child = spawn('node', ['/usr/eXtern/systemX/Controller/keyEventsListerner.js']);

child.stdout._handle.setBlocking(true);

////console.log("spawned: " + child.pid);

console.log("spawned something");
child.stdout.on('data', function(data) {
  console.log("Child data: " + data);

  if (data.indexOf("volume up") != -1) {
      increaseVolume(true);
  }

   if (data.indexOf("volume down") != -1) {
      increaseVolume(false);
  }

  if (data.indexOf("brightness up") != -1) {
      increaseBrightness(true);
  }

   if (data.indexOf("brightness down") != -1) {
      increaseBrightness(false);
  }
  
  if (data.indexOf("keyPress=XF86HubToggle") != -1) {
  console.log("trying this");
      if (win.opened) {
			//win.hide();
			win.opened = false;
			console.log("here x");
			win.hideFixed();
			console.log("here x2");
		} else {
			win.ignoreFirstBlurTrigger = true;
			//win.show();
			console.log("here xa");
			win.showFixed();
			win.opened = true;
			console.log("here xa2");
		}
  }
  
  if (data.indexOf("Workspace=switched") != -1) {
      //workspaceSwitchedEvent();
  }
//var obj = JSON.parse(data)
  

	//force on dimensio change

});
child.on('error', function () {
  console.log("Failed to start child.");
});
child.on('close', function (code) {
  console.log('Child process exited with code ' + code);
	//enbleFullScreenAdaption();
});
child.stdout.on('end', function () {
  console.log('Finished collecting data chunks.');
	//enbleFullScreenAdaption();
});

var gui = require("nw.gui");
gui.App.on('open', function (argString) {
	console.log("HUB triggered Arguments",argString);
	if (argString.indexOf("keyPress=XF86AudioLowerVolume") != -1)
		increaseVolume(false);

	if (argString.indexOf("keyPress=XF86AudioRaiseVolume") != -1)
		increaseVolume(true);

	if (argString.indexOf("keyPress=XF86HubToggle") != -1)
		if (win.opened) {
			win.hideFixed();
			//win.opened = false;
		} else {
			win.ignoreFirstBlurTrigger = true;
			//win.show();
			win.showFixed();
			win.opened = true;
		}

	if (argString.indexOf("Workspace=switched") != -1)
		workspaceSwitchedEvent();
    // Parse argString to find out what args were passed to the second instance.
//
    if (argString.indexOf("file-url-path-alias=/gen=/usr/eXtern/NodeJs/gen /usr/eXtern/systemX") != -1) {
      var initialSplit = argString.split("file-url-path-alias=/gen=/usr/eXtern/NodeJs/gen /usr/eXtern/systemX")[1];
	var appAOfInterest = ltrim(initialSplit).split(" ")[0];
      var arguments = ltrim(initialSplit.replace(appAOfInterest,""));
      console.log("appAOfInterest: ",appAOfInterest);
      console.log("args check: ",ltrim(arguments).indexOf('"/'));
	if (arguments.indexOf('"/') == 0) {
		arguments = arguments.replace(/^"(.*)"$/, '$1');
		console.log("done",arguments);
	} else if (arguments.indexOf("'/") == 0) {
		arguments = arguments.replace(/^'(.*)'$/, '$1');
	}
      console.log("arguments: ",arguments);
	filesToOpen = [];
	filesToOpen.push(arguments);
	openApp(appAOfInterest,filesToOpen);
    }
});
*/
//const ioHook = require('iohook');
/*ioHook.on("keypress", event => {

	if (event.rawcode == 65299)
		increaseVolume(true);

	if (event.rawcode == 65297)
		increaseVolume(false);


});



win.ignoreMetaKey = false;

ioHook.on("keyup", event => {
  //console.log(event);
	if (event.rawcode != 65515 && event.metaKey) //Note Super key on it's own
		win.ignoreMetaKey = true;

	if (event.rawcode == 65515) //Super key
		if (!win.ignoreMetaKey) {
			window.exploreBarWin.openHubs();
			setTimeout(function(){searchApps();}, 200);
		} else {
			win.ignoreMetaKey = false;
		}
  // {keychar: 'f', keycode: 19, rawcode: 15, type: 'keypress'}
});

ioHook.start();*/

$(document).keyup(function(e) {
		//console.log("triggering this A");
	if (!$("#searchOuter > input").is(':focus')) {
		//console.log("triggering this");
		$("#searchOuter > input").select();
	}
});


win.showFixed = function () {
	
	win.opened = true;
	window.opened = true;
	$("body").removeClass("hiddenOpacity"); //Was added so that the wallpaper can allign properly while window is hidden
	//if (hubId != null) {
		$("background").show();
		
		blurTimeout = setTimeout(function(){
		//executeNativeCommand("xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id "+hubId);
		$("background").fadeOut();
		console.log("applied blur for: ",hubId);
		}, 600);
	//}
	//win.moveTo(oldWinX, oldWinY);
	//win.resizeTo(oldWinWidth, oldWinHeight);
	setTimeout(function(){
	win.opened = true;
	window.opened = true;
	//$('#file_context_menu').removeClass('animated fadeInUp');
    	$('#animateOpen').removeClass('hidden');
    	//win.focus();
	}, 50);
	
	
}


blurTimeout = setTimeout(function(){

	console.log("SHOOOOOWING ");
	win.showFixed();
	}, 10000);



/*

sudo apt-get install xbindkeys
sudo apt-get install xvkbd




xev | grep -A2 --line-buffered '^KeyRelease'     | sed -n '/keycode /s/^.*keycode \([0-9]*\).* (.*, \(.*\)).*$/\1 \2/p'




*/



//gsettings set org.gnome.desktop.background picture-uri "file:///usr/eXtern/iXAdjust/Shared/CoreIMG/wallpaper/4.jpg"


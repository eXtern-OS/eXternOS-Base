var win = nw.Window.get();
//win.zoomLevel = 1.25; //FIXME: remoe, testing scailing capabilities
var internalId;
var detectedMountedDrives;
var App = {};
var AppLoaded = false;
var requestedApp = false;
var ignorePhotosInactive = false;
//win.showDevTools();
var initRestore = false;
var initLoaded = false;
var appLoaded = false;
var Appready = false;
var enableDisableBlurOnMaximize = false;
var disableBlurOnLostFocus = false;
var delayShowingApp = false;
var useRealTimeBlur = false;
var allActiveNews;
const usingKwin = true;
if (usingKwin)
	win.minimize();
else
	win.hide();
var appLocation = "";
var maximized = false;
var _ = require('underscore');
var lodash = require('lodash');
var confirmUserDetailsCallback;
var fWidth = 10;
var fHeight = 10;
var enabledSources = [];
//var robot = require("robotjs");
var imageEditor;
var setAppGeometry;
var ignoreFocusCheck = 0;
var thisAppName = "App";
var doNotTriggerShowWindowEvents = false;
var filesInClipboard = [];
filesInClipboard.isCut = false;
var tabToClose; //temporarily hold tab being closed object while waiting for the callback from the instance App
//var iohook = require("/usr/eXtern/systemX/Shared/CoreWindow/js/iohook");

var wallpaperWidth = screen.width;
var wallpaperheight = screen.height;
var lastPo = -1;

if ((screen.width > 1900) && (screen.width > 900)) {
			var xwidth = 1750-50;
			var xheight = 910-50;

	} else {

			//Same reason as above
			var xwidth = 1319-50;
			var xheight = 725-50;
	}
var finalAppGeometry = { 
			width: xwidth,
			height: xheight
	}
var waitForAppToRespond = false;

document.body.addEventListener('dragover', function(e){
  e.preventDefault();
  e.stopPropagation();
}, false);
document.body.addEventListener('drop', function(e){
  e.preventDefault();
  e.stopPropagation();
}, false);

/* Supported file extensions */
var map = {
  'compressed zip': ['zip'],
    'compressed rar': ['rar'],
    'compressed gz': ['gz'],
    'compressed 7z': ['7z'],
    'compressed tar': ['tar'],
    'compressed bz2': ['bz2'],
    'binary': ['dat','bin','exe'],
    'flash package': ['swf','flash'],
    'compile instructions': ['make','cmake','pak','json'],
    'shared library': ['so','dll'],
    'vector graphics': ['svg'],
    'vector image': ['svg','eps','bmp','gif','tif'],
    'illustrator': ['ai'],
    'font': ['vtt','ttf','eot','woff','ttc','pfb','pfm','otf','dfont','pfa','afm'],
    'executable script': ['sh','bat','cmd','csh','com','ksh','rgs','vb','vbs','vbe','vbscript','ws','wsf'],
  'text': ['txt', 'md','info','nfo', ''],
    'initialization file': ['ini'],
    'logged data': ['log'],
    'c code': ['c'],
    'bit torrent': ['.torrent'],
    'CD-DVD Image': ['iso','img'],
    'debian': ['deb'],
    'c++ code': ['cc', 'cpp', 'c++','cp','cxx'],
    'python code': ['py','pyc','pyo','pyd'],
  'image': ['jpg', 'jpeg', 'png','PNG'],
  'pdf': ['pdf'],
  'css': ['css'],
  'java script': ['js'],
  'web page': ['html'],
    'xml': ['xml'],
    'java': ['java','jar'],
  'document': ['doc', 'docx','odt'],
  'presentation': ['ppt', 'pptx'],
  'video': ['mkv', 'avi', 'rmvb','flv','wmv','mp4','mpeg'],
    'audio': ['mp3', 'wma', 'wav','aiff','m4a','ape','wv','act','aac','au','dss','flac','iklax','ivs','m4p','mmf','mpc','ogg','oga','opus','raw','sln','tta','vox'],
};

/* End of file extensions */


/* Start of Video Playback API */

var duration = 0;

(function () {
    function Xplay (embed, options, callback) {
        var thiz = this;

        var hwdec = options.hwdec == true ? true : false,
            src = options.src || "",
            loop = options.loop == true ? true : false,
            volume = options.volume != null ? options.volume : 100,
            autoplay = options.autoplay == true ? true : false;

        thiz.mpv = embed;
        thiz.mpv.type = 'application/x-mpvjs';

        thiz.mpv.addEventListener("message", function (e) {
            if (e.data.type == 'ready') {
                thiz.loadfile(src);

                if (hwdec) thiz.setProperty("hwdec", "vaapi-copy");
                if (volume != null) thiz.setVolume(volume);
                if (loop) thiz.setProperty("loop-file", "inf");
                if (autoplay) thiz.play();

                thiz.mpv.postMessage({
                    type: 'observe_property',
                    data: "duration"
                });

                thiz.mpv.postMessage({
                    type: 'observe_property',
                    data: "time-pos"
                });

                thiz.mpv.postMessage({
                    type: 'observe_property',
                    data: "pause"
                });

                thiz.mpv.postMessage({
                    type: 'observe_property',
                    data: "eof-reached"
                });

                callback && callback({
                    "name": "ready"
                });
            }
            else if (e.data.type == "property_change"){
                if (e.data.data.name == "duration") {
                    duration = e.data.data.value;
                    callback && callback({
                        "name": "duration",
                        "value": e.data.data.value,
                    });
                }
                else if (e.data.data.name == "time-pos") {
                    callback && callback({
                        "name": "progress",
                        "value": e.data.data.value,
                    });
                }
                else if (e.data.data.name == "pause" && !e.data.data.value) {
                    callback && callback({
                        "name": "play",
                    });
                }
                else if (e.data.data.name == "pause" && e.data.data.value) {
                    callback && callback({
                        "name": "pause",
                    });
                }
                else if (e.data.data.name == "eof-reached" && e.data.data.value) {
                    callback && callback({
                        "name": "ended",
                    });
                }
            }
        });

        return thiz;
    }

    Xplay.prototype.setProperty = function (name, value) {
        this.mpv.postMessage({
            type: 'set_property',
            data: {
                name: name,
                value: value,
            }
        });

        return this;
    };

    Xplay.prototype.sendCommand = function (name, value) {
        var data = [];
        if (name) data.push(name);
        if (value) data.push(value);

        this.mpv.postMessage({
            type: 'command',
            data: data,
        });

        return this;
    };

    Xplay.prototype.loadfile = function (src, autoplay = true) {
        this.sendCommand("loadfile", src);
        if (!autoplay) {
            this.pause();
        }
        else {
            this.play();
        }

        return this;
    };

    Xplay.prototype.play = function () {
        this.setProperty("pause", false);

        return this;
    };

    Xplay.prototype.pause = function () {
        this.setProperty("pause", true);

        return this;
    };

    Xplay.prototype.replay = function () {
        this.setProperty("time-pos", 0);
        this.setProperty("pause", false);

        return this;
    };

    Xplay.prototype.setVolume = function (volume) {
        this.setProperty("volume", volume);

        return this;
    };

    Xplay.prototype.destroy = function () {
        this.pause();
        this.sendCommand("stop", null);
        this.mpv.remove();
        return this;
    };

    Xplay.prototype.keypress = function (key) {
      this.sendCommand("keypress", key);
      return this;
    };

    Xplay.prototype.setPosition = function (seconds) {
      if (duration > 3599)
          var durationCnverted = new Date(parseInt(seconds) * 1000).toISOString().substr(11, 8);
        else
          var durationCnverted = new Date(parseInt(seconds) * 1000).toISOString().substr(14, 5);

          //console.log("duration converted: ",durationCnverted);
          
      this.setProperty('time-pos', durationCnverted);
      return this;
    };

    window.Xplay = Xplay;
    return Xplay;
})();

/* End of Video Playback API */

var AppInstances = [];

function getInstance() {
	
}

/**
 * Hides instance tabs with an animated fade
 *
 * @return null.
 */
function hideInstanceTabs() {
	if ($("#new_tab_instance_button").hasClass("hidden")) {
		console.log("hide now");
		
		$("#tabsBodySelector").fadeOut( "fast", function() {
			$("#tabsBody").removeClass("tab-overview-body");
    			$("#new_tab_instance_button").removeClass("hidden");
  		});
	}
}

/**
 * Toggles instance tabs (show or hide) with a smooth animation.
 *
 * @return null.
 */
function toggleInstanceTabs() {
	if ($("#new_tab_instance_button").hasClass("hidden")) {
		console.log("hide now");
		$("#tabsBodySelector").fadeOut( "fast", function() {
			$("#tabsBody").removeClass("tab-overview-body");
    			$("#new_tab_instance_button").removeClass("hidden");
  		});
	} else {
		console.log("show now");
		$("#new_tab_instance_button").addClass("hidden");
		$("#tabsBody").addClass("tab-overview-body");
		setTimeout(function() {
		$("#tabsBodySelector").fadeIn();
		}, 300);
	}
}

/**
 * Enables tabs. To be called when there is more than 1 instance tab
 *
 * @return null.
 */
function enableTabs() {
	$("#tabsBody").removeClass("tabsBodyNoTabs");
	$("#new_tab_instance_button").fadeIn();
}

/**
 * Disables tabs. To be called when there is more than 1 instance tab
 *
 * @return null.
 */
function disableTabs() {
	$("#tabsBody").addClass("tabsBodyNoTabs");
	$("#new_tab_instance_button").hide();
}

var newInstance; //To be used to temporarily store the last added instance tab

/**
 * Returns the latest added instance.
 * Will automatically set it to null to prevent being called again.
 * It's used for instances wanting to get a handle of their instance on load.
 *
 * @return {instanceTab}.
 */
function getInstance() {
	var returnInstance = newInstance;
	newInstance = null;
	
	return returnInstance;
}

/**
 * Returns Apps relative to the file types they support.
 *
 * @return {fileTypesApps}.
 */
function getFileTypesApps() {
	return App.fileTypesApps;
}

var requestOnCloseCallbacksNo = 0; //stores number of tabs that need to be asked before the whole window is closed

/**
 * Creates a new instance tab.
 *
 * @param {array} Files for argv for the new instance tab.
 * @param {boolean} Do we automatically switch to this new instance tab?
 * @param {boolean} Do we load App into the instance tab? Set to false for the first instance tab.
 * @return {null].
 */
App.addNewInstanceTab = function (files,autoSwitch,noLoad) {
	if (files != null)
		if (!Array.isArray(files)) {
			var filesString = files;
			files = [];
			if (filesString !== undefined)
				files.push(filesString);
		
		}
	
	/* FIXME: Work in progress*/
	App.argv = files;
	
	var newAppInstance = {
		id: "app_tab_"+(lastPo+1),
		po: lastPo+1,
		argv: App.argv,
		addNewInstanceTab: App.addNewInstanceTab,
		disableWindowDraggability: App.disableWindowDraggability,
		enableWindowDraggability: App.enableWindowDraggability,
		getFileTypesApps: getFileTypesApps,
		getMimeType: App.getMimeType,
		getDefaultLegacyApp: App.getDefaultLegacyApp,
		getLegacyFileAssociations: App.getLegacyFileAssociations,
		imageEditor: App.imageEditor,
		disableAdaptiveBlur: App.disableAdaptiveBlur,
		enableAdaptiveBlur: App.enableAdaptiveBlur,
		closeImageEditor: App.closeImageEditor,
		onResize: function (width, height) {  },
		unfocused: function () {  },
		getClipboardFiles: function () { console.log("get new copy here: ",filesInClipboard);
		var duplicatedClipboard = lodash.cloneDeep(filesInClipboard) /*Using this to prevent manipulation*/
		duplicatedClipboard.copyDir = filesInClipboard.copyDir;
		duplicatedClipboard.isCut = filesInClipboard.isCut;
		
		/*for (var i = 0; i < filesInClipboard.length; i++) {
		duplicatedClipboard.push(filesInClipboard[i]);
		}*/
		
		console.log("duplicatedClipboard: ",duplicatedClipboard);
		return  duplicatedClipboard; },
		setClipboardFiles: function (clipboardFiles,isCut) { 
			console.log("setting new copy here: ",clipboardFiles);
			filesInClipboard = clipboardFiles;
			filesInClipboard.isCut = isCut;
			appCommsChannel.postMessage({type: "files-in-clipboard", data: filesInClipboard});
			
		},
		maximize_button: $("#maximize_button")[0],
		close_button: $("#close_button")[0],
		minimize_button: $("#minimize_button")[0],
		loading_animation: $("#loadingAnimation")[0],
		systemEvent: function () {  },
		onMaximize: function () {  },
		isMaximized: false,
		restored: function () { },
		Xplay: Xplay,
		resolveFileType: App.resolveFileType,
		toggleNetworkOptions: App.toggleNetworkOptions,
		sysOptions: App.sysOptions,
		osVersion: App.osVersion,
		fileTypesApps: App.fileTypesApps,
		apps: App.apps,
		legacyApps: App.legacyApps,
		newsSourceModalClosed: function () { },
		closeNewsSourcesModal: App.closeNewsSourcesModal,
		openNewsSourcesModal: App.openNewsSourcesModal,
		closeCustomModal: App.closeCustomModal,
		openCustomModal: App.openCustomModal,
		getModalButtonsDom: function () { return $("#customDialogBoxButtons")[0] },
		getMountedDrives: App.getMountedDrives,
		unmountDrive: unmountDrive,
		updateAudio: App.updateAudio,
		addCustomWallpaper: App.addCustomWallpaper,
		packageApp: App.packageApp,
		openApp: App.openApp,
		addNewStack: App.addNewStack,
		newNotification: App.newNotification,
		RunAppDev: App.RunAppDev,
		devToolsShow: App.devToolsShow,
		getAllNews: App.getAllNews,
		ready: App.ready,
		removeOpacityProperty: function() { executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY"); },
		updateTitle: function (title) {
		console.log("titlem: ",this);
		$("#app_tab_elector_"+this.po+" > a > span").text(title);
		$("#app_tab_elector_"+this.po).attr("title",title);
		$("title").text(title);
		win.title = title;
		},
		setBackground: function (bg) {
		$("#outerBody").css("background",bg);
		},
		updateTrack: App.updateAudio, //Backwards compatibility, delete later
		newsSourceUpdated: App.newsSourceUpdated,
		closeCallback: null,
		requestOnClose: function (callback) {
			readyToClose = false;
			requestOnCloseCallbacksNo++;
			console.log("requestOnCloseCallbacksNo: ",requestOnCloseCallbacksNo);
			this.closeCallback = callback;
		},
		close: App.close,
		onOpenFiles: function () { },
		explorebar: explorebar,
		showWindowEvent: null
		};
	AppInstances.push(newAppInstance);
	newInstance = AppInstances[AppInstances.length-1];
	lastPo++;
	
	App.argv = null;
	
	if (appLocation.indexOf("extern.files.app") != -1)
		AppInstances[AppInstances.length-1].isReady = function () {
			if (AppInstances.length > 1)
				if (files != null) {
					console.log("here A");
					//AppInstances[AppInstances.length-1].onOpenFiles(files);
					AppInstances[AppInstances.length-1].showWindowEvent();
					//setTimeout(function(){ AppInstances[AppInstances.length-1].showWindowEvent(); }, 2000);
				} else
					AppInstances[AppInstances.length-1].showWindowEvent(); //setTimeout(function(){ console.log("here B"); AppInstances[AppInstances.length-1].showWindowEvent(); }, 2000);
		}
	
	console.log("set new instance: ",newInstance);
	//enableTabs();
	console.log("AppInstances.length: ",AppInstances.length);
	
	var hiddenOpacityClass = "";
	
	if (setAppGeometry != null) {
		hiddenOpacityClass = " hiddenOpacity";
	}
		var tabId = newInstance.po;
		if (!noLoad) {
		//$("#tabsBodySelector").append('<li><a href="#app_tab_2">Tab2</a></li>');
		$("#tabsBodySelector").append('<li id="app_tab_elector_'+tabId+'" title="'+thisAppName+'"><a href="#app_tab_'+tabId+'"><i class="fas fa-object-ungroup pull-left"></i> <span class="pull-left">'+thisAppName+'</span></a> <i class="fas fa-circle instanceTabCloser" onclick="closeTab(&quot;'+newInstance.id+'&quot;)"></i></li>');
		
	
	    $('.tab a').click(function(e) {
		e.preventDefault();
		$(this).tab('show');
	    });
	    
	
	$("#tabsBody").append('<div class="tab-pane overflow" style="height: 100%;" id="app_tab_'+tabId+'"> <iframe class="appContainer" src="../../'+appLocation+'" frameborder="0" partition="persist:trusted" allownw class="appInstance '+hiddenOpacityClass+'"> </iframe></div>');
	$("#app_tab_"+tabId+" > iframe").load( function() {
					
					console.log("executed",this);
					$(this).contents().find("head")
      .prepend($("<style type='text/css'>  .btn { border-color: "+winButtonProperties.borderColor+" !important;}  </style> <link href='../../../Shared/CoreCSS/scrollbar.css' rel='stylesheet'> <script> window.instance = parent.newInstance;  console.log('window.instance',window.instance); document.addEventListener('click', function() { console.log('focused iframe'); });</script>"));

	$(this.contentWindow.document.body).click(function() {
		hideInstanceTabs();
	});
	
	console.log("autoswitch: ",autoSwitch);
	
	if (autoSwitch)
	    	$("#app_tab_elector_"+tabId+" > a").click();
	//frameBody.click(function(){ /* ... */ });

	});
	
	}
	
	if (AppInstances.length > 1) {
		enableTabs();
		//console.log("appLocation: ",appLocation);
		//console.log("appLocation2: ",AppInstances[AppInstances.length-1]);
		/*if (appLocation.indexOf("extern.files.app") != -1)
			setTimeout(function(){ AppInstances[AppInstances.length-1].showWindowEvent();}, 1000);*/
	}
	

}

App.disableWindowDraggability = function () {
	$("#windowTitleBar").removeClass("drag_enabled");
};

App.enableWindowDraggability = function () {
	if (!$("#windowTitleBar").hasClass("drag_enabled")) {
		$("#windowTitleBar").addClass("drag_enabled");
	}
	
};

App.setTimeout = setTimeout;

/**
 * Returns mime type of a given file
 *
 * @param {string} File to check.
 * @param {function} Callback function to return the result to.
 * @return {null}.
 */
App.getMimeType = function (file,callback) {
//console.log("monitoring");
var childProcess = require('child_process');
var spawn = childProcess.spawn;
var child = spawn('xdg-mime', ['query','filetype',file]);

child.stdout._handle.setBlocking(true);

////console.log("spawned: " + child.pid);

child.stdout.on('data', function(data) {
  console.log("Child data: " + data);
  if (callback != null) {
	  callback(data.toString());
  }

});
child.on('error', function () {
  console.log("Failed to start child.");
});
child.on('close', function (code) {
  console.log('Child process exited with code ' + code);
});
child.stdout.on('end', function () {
  console.log('Finished collecting data chunks.');
});
}

/**
 * Returns legacy Apps that support the given mime type (file type).
 *
 * @param {string} Mime type to check.
 * @param {function} Callback function to return the result to.
 * @return {null}.
 */
function getDefaultLegacyApp(mimeType, callback) {
		var childProcess = require('child_process');
		var spawn = childProcess.spawn;
		console.log("mimeTypex: ",mimeType);

			executeNativeCommand("xdg-mime query default '"+mimeType+"'", function (res) {
				console.log("res: ",res);
				if (callback != null) {
					callback(res);
				}
			});
		
}

/**
 * Returns legacy Apps that support the given mime type (file type).
 *
 * @param {string} Mime type to check.
 * @param {function} Callback function to return the result to.
 * @return {null}.
 */
App.getDefaultLegacyApp = function (file,callback) {

	App.getMimeType(file, function (mimeType) {
		getDefaultLegacyApp(mimeType, callback);
	});

}

function unmountDrive(driveName) {
	var mountPoint = "/dev/"+driveName;
	console.log("unmounting...",mountPoint);
var exec = require('child_process').exec,
                   child;
            child = exec("udisksctl unmount -b "+mountPoint,function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        if (stdout.indexOf("failed") == -1) {
            console.log("successfully unmounted");

	    

            
        } else
            console.log("failed to unmount");
    }
       
});
}

App.getLegacyFileAssociations = function (file,callback) {
	App.getMimeType(file, function (mimeType) {
		getDefaultLegacyApp(mimeType, function (defaultApp) {
			executeNativeCommand("grep '"+mimeType+"' '/usr/share/applications/mimeinfo.cache'", function (res) {
				console.log("res: ",res);
				if (callback != null) {
					callback(res);
				}
			});
			/*var childProcess = require('child_process');
			var spawn = childProcess.spawn;
			console.log("mimeType: ",mimeType);
			var child = spawn('grep', [mimeType,'/usr/share/applications/mimeinfo.cache']);
			
			child.stdout._handle.setBlocking(true);	
			////console.log("spawned: " + child.pid);
			
			child.stdout.on('data', function(data) {
				console.log("Child data: " + data);
				if (callback != null) {
					callback(data.toString());
				}
			});
			
			child.on('error', function () {
				console.log("Failed to start child.");
			});
			
			child.on('close', function (code) {
				//console.log('Child process exited with code ' + code);
			});
			
			child.stdout.on('end', function () {
				//console.log('Finished collecting data chunks.');
			});*/
		});

	});

}


var defaultTheme = require('/usr/eXtern/systemX/Shared/CoreWindow/js/photo_editor_element/theme/white-theme.js');
var imageEditorCallback;

 App.imageEditor = function(image,name,callback) {
	console.log("image: ",image)
	console.log("name: ",name);
	imageEditorCallback = callback;
	$("iframe").addClass("lowOpacity");
	$(".imageEditorElement").removeClass("hidden");

	setTimeout(function() { //Apparently the remove hidden above is not completely done by now ?
    				
         imageEditor = new tui.ImageEditor('#tui-image-editor', {
             includeUI: {
                 loadImage: {
                     path: image,
                     name: name
                 },
                 theme: defaultTheme,
                 initMenu: 'filter',
                 menuBarPosition: 'left'
             },
             cssMaxWidth: 900,
             cssMaxHeight: 700,
             usageStatistics: false
         });
         window.onresize = function() {
			 console.log("window resized")
             imageEditor.ui.resizeEditor();
         }
	$(".imageEditorElement").removeClass("hiddenOpacity");

	}, 1000);
}

var forceNoBlur = false;
var forceBlur = false;
//For Apps like video players to save resources
App.disableAdaptiveBlur = function(forceState,temporaryForce) {
	console.log("App.disableAdaptiveBlur CALLED");
	if (forceState && !temporaryForce)
		forceNoBlur = true;
		if (!forceBlur)
			executeNativeCommand("xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -remove _KDE_NET_WM_BLUR_BEHIND_REGION -id "+internalId);
}

App.enableAdaptiveBlur = function(forceState,temporaryForce) {
	console.log("App.enableAdaptiveBlur CALLED");
	if (!forceNoBlur || forceState) {
		forceNoBlur = false;

		if (forceState && !temporaryForce)
			forceBlur = true;
		executeNativeCommand('xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id '+internalId);
	}
		
}

App.closeImageEditor = function (saveChanges) {
	if (saveChanges) {
		const myImage = imageEditor.toDataURL();
		if (imageEditorCallback != null) {
			imageEditorCallback(myImage);
		}
	}
	$(".imageEditorElement").addClass("hiddenOpacity");

	setTimeout(function() {
		$(".imageEditorElement").addClass("hidden");
		$("iframe").removeClass("lowOpacity");
	}, 100);
}

App.onResize =  function (width,height) {
	// Override this
}

win.on('resize', function (width,height) {
	App.onResize(width,height);
	if (imageEditor != null) {
		console.log("image Editor resized");
		imageEditor.ui.resizeEditor();
	}
	
    
  });

App.unfocused = function () {

}

var currentlyProcessingIDPos = 0;
var winIdsToProcess = [];
var keepChecking = false;




function checkIfAnotherWindowExistBehindWIndow() {
	if ((currentlyProcessingIDPos < winIdsToProcess.length) && keepChecking) {
		executeNativeCommand('/usr/eXtern/systemX/extern.explorebar/js/windowDimensionsById.sh '+winIdsToProcess[currentlyProcessingIDPos], function(data, err) {
			if (!err) {
				//console.log("data pos: ", data);
				var dataSplit = data.split(" ");
				//console.log("dataSplit: ",dataSplit);
				var x = dataSplit[0];
				var y = dataSplit[1];
				var width = dataSplit[2];
				var height = dataSplit[3];
			}
			if ((((x) > win.x) && (win.x+win.width) > x && ((win.y+win.height) > y && (y+height) > (win.y))) || (y > win.y && (win.y+win.height) > y && ((win.x+win.width) > x && (x+width) > (win.x)))) {
				App.enableAdaptiveBlur();
				$("background").fadeOut( 400, function() {
					App.enableAdaptiveBlur();
				});
			} else {
				currentlyProcessingIDPos++;
				checkIfAnotherWindowExistBehindWIndow();
			}
			
		});
	} else {
		console.log("we are using this")
		$("background").fadeIn( 400, function() {
			App.disableAdaptiveBlur(true,true);
		});

	}
	
}

var itatiFirstTriggered = 0;

var gui = require('nw.gui');

gui.Screen.Init();

var screens = gui.Screen.screens;

var currentScreen = screens[0];

function focusBlurCheck() {
	let continueChecking = true;

	console.log("checking for edge");

	let canAdjustBgInstantly = true;
	if ((win.x+win.width) > currentScreen.work_area.width || (win.y+win.height) > currentScreen.work_area.height) {
		canAdjustBgInstantly = false;
	}

	if ((win.x+win.width > (currentScreen.work_area.x+currentScreen.work_area.width)) || (win.y+win.height > (currentScreen.work_area.y+currentScreen.work_area.height) || (win.x < currentScreen.work_area.x)  || (win.y < currentScreen.work_area.y))) {
		if (win.x > currentScreen.work_area.x || win.y > currentScreen.work_area.y) { //on a new monitor adjust blur size
			for (var i = 0; i < screens.length; i++) {
				if (win.x < screens[i].work_area.width && win.x > (screens[i].work_area.x-1) && win.y < screens[i].work_area.height && win.x > (screens[i].work_area.y-1)) {
					currentScreen = screens[i];
					if (canAdjustBgInstantly)
						setTimeout(function(){ $("background")[0].style.backgroundSize = `${currentScreen.work_area.width}px ${currentScreen.work_area.height}px`; }, 500);
					else {
						$("background")[0].style['background-position'] = "0px 0px";
						App.enableAdaptiveBlur();
						$("background").fadeOut( 400, function() {
							$("background")[0].style.backgroundSize = `${currentScreen.work_area.width}px ${currentScreen.work_area.height}px`;
						});
						
					}
						
					break;
				}
			}
		}

		if (canAdjustBgInstantly) {
			console.log("over edge");
			
			App.enableAdaptiveBlur();
			$("background").fadeOut( 400, function() {
				App.enableAdaptiveBlur();
			});
		}
		continueChecking = false;
		
		keepChecking = false;
	}

	if ((enableDisableBlurOnMaximize || disableBlurOnLostFocus) && continueChecking) {
			//App.enableAdaptiveBlur();
			//$("background").addClass("hidden");
			//$("background").addClass("hiddenOpacity");
			keepChecking = false;
		executeNativeCommand('xdotool search --all --onlyvisible --desktop $(xprop -notype -root _NET_CURRENT_DESKTOP | cut -c 24-) "" 2>/dev/null', function(data, err) {
			if (!err) {
				var currentWorkspaceWindowIds = data.split("\n");
				winIdsToProcess = [];
				currentlyProcessingIDPos = 0;
				for (var i = 0; i < currentWorkspaceWindowIds.length; i++) {
					if (currentWorkspaceWindowIds[i] != "") {
						var hexString = parseInt(currentWorkspaceWindowIds[i]).toString(16);
						hexString = "0x0"+hexString;
						console.log("testing...")
						if (internalId != hexString)
							winIdsToProcess.push(hexString);
					}
					
				}
				console.log("all Apps data",currentWorkspaceWindowIds);
				
				console.log("test hex winIdsToProcess: ",winIdsToProcess);
				keepChecking = true;
				if (disableBlurOnLostFocus) {
					checkIfAnotherWindowExistBehindWIndow(); //Sometimes kinda laggy on startup. Didn't fix this because we aren't using this anymore. Just a heads up as it's not always and you might not notice.
				} else {
					App.enableAdaptiveBlur();
					$("background").fadeOut( 400, function() {
						//App.enableAdaptiveBlur();
					});
				}
				
			}
		});
		}
}


var focusTriggeredCounter = 0;
win.on('focus', function() {
	if (!Appready) {
		//win.blur();
	} else {
		if (focusTriggeredCounter > 0) {
			console.log("coming here A");
			if (disableBlurOnLostFocus)
				focusBlurCheck();
		} else {
			focusTriggeredCounter++;
		}
		
		
		if (itatiFirstTriggered < 4) {
			itatiFirstTriggered++;
			console.log("adding focus");
		} else {
		if (appLocation.indexOf("extern.itai.app") != -1) {
			console.log("itai triggered C");
			executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");
		}
		}
		console.log("checking focus");
		

	}

});

$(document).ready(function() {
console.log("ready!!! hoverDetection");
$('#hoverDetection').on("mouseenter", function() {
	console.log("hover...");
	/*$("background").fadeOut( 400, function() {
       App.enableAdaptiveBlur(true,true);
	});*/
    }).on("mouseleave", function() {
		console.log("leave...");
		/*$("background").fadeIn( 400, function() {
			App.disableAdaptiveBlur(true,true);
		});*/
	   //focusBlurCheck();
    });
    
    });

	var oldWinX = 0; //Used to prevent loops as apparently on("move") randomly keeps triggering until window loses focus
	var oldWinY = 0;

    win.on('move', function() {
		//win.blur();
		//win.focus();

		
		
        
	

	if (Appready && oldWinX != win.x && oldWinY != win.y) {
		const xPos = -(win.x-currentScreen.work_area.x);
		const yPos = -(win.y-currentScreen.work_area.y);
		let moveBg = true;
		if (xPos > 0 || yPos > 0) { //Prevent animation when we are gonna hide it anyway and graphically breaks
			moveBg = false;
		}

		if (moveBg) {
			$("background")[0].style['background-position'] = `${xPos}px ${yPos}px`;
			console.log("We're moving");
		}

		

		oldWinX = win.x;
		oldWinY = win.y;
		console.log("coming here B");
		if (disableBlurOnLostFocus)
			focusBlurCheck();
	}
			//focusBlurCheck();
	
  }); 

win.on('blur', function() {
	console.log("all B: ",window.performance.memory);
	const usedB = window.performance.memory.totalJSHeapSize / 1024 / 1024;
	console.log(`B The instances uses approximately ${Math.round(usedB * 100) / 100} MB`);
	
	let canDisableBlur = true;
	if ((win.x+win.width) > currentScreen.work_area.width || (win.y+win.height) > currentScreen.work_area.height) { //Prevent animation when we are gonna hide it anyway and graphically breaks
		canDisableBlur = false;
	}

if (disableBlurOnLostFocus && canDisableBlur) {
	//$("background").removeClass("hidden");
	//$("background").removeClass("hiddenOpacity");
	//App.disableAdaptiveBlur();
	console.log("disabling blur here")
	keepChecking = false;
	$("background").fadeIn( 400, function() {
    		App.disableAdaptiveBlur();
    	});
}

//Appready = true;



	if (!Appready) {
		//executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");
		
		if (usingKwin)
			win.minimize();
		else
			win.hide();

		setTimeout(function() { 
			if (!Appready) { 
				if (usingKwin)
					win.minimize();
				else
					win.hide();
			} 
	}, 1000); //guarantee we are really minimized as sometimes this is not the case
		
	if (appLocation.indexOf("extern.files.app") != -1) {

	executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId, function () {
		
		if (usingKwin)
			win.minimize();
		else
			win.hide();

executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_DOCK -id '+internalId); })
	console.log("moving window to position");

	//fHeight = height;
	//fWidth = width;
	//executeNativeCommand("wmctrl -i -R "+internalId, function() {
	//win.resizeTo(width,height);
	//var mx = Math.floor(((screen.width/2) - (fWidth/2)));
    //var my = Math.floor(((screen.height/2) - (fHeight/2)) - (20));

	//win.moveTo(mx,my);
	
	
//executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");
	/*executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId, function () { win.minimize();
executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_DOCK -id '+internalId); });*/
	//executeNativeCommand('wmctrl -i -r '+internalId+' -b add,stiky');
	//executeNativeCommand('wmctrl -i -r '+internalId+' -b remove,skip_pager');
			/*setTimeout(function() {
				
    				}, 1000);*/
		
	} else {
		/*win.resizeTo(300,100);
		executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");
		executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId, function () { win.minimize();
executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_DOCK -id '+internalId); });*/
	}
	}
		console.log("xfocused: ");
		App.unfocused();


	});

/*
win.on('focus', function() {
		console.log("focus event: ");


	});*/


function executeNativeCommand(request,callback) {
    var exec = require('child_process').exec,
                   child;
            child = exec(request,function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
	if (callback != null)
		callback(error);
    } else {

	if (callback != null)
		callback(stdout);
    

    }       
});
}

function openNewsCategory(newsCategory) {
	$("#mainNewsCategories").fadeOut( 400, function() {
    		$("#newsCategoryView").fadeIn();
  	});
}

function closeNewsCategoryView() {
	$("#newsCategoryView").fadeOut( 400, function() {
    		$("#mainNewsCategories").fadeIn();
  	});
}

var useRealTimeBlur = false;

$("body").removeClass("hidden");

$("#close_button")[0].onclick = function() {
	win.close();
};

App.maximize_button = $("#maximize_button")[0];
App.close_button = $("#close_button")[0];
App.minimize_button = $("#minimize_button")[0];
App.loading_animation = $("#loadingAnimation")[0];

$("#maximize_button")[0].onclick = function() {
	if (maximized) {
		win.restore();
		maximized = false;
	} else {
		win.maximize();
		maximized = true;
	}
};

	App.onMaximize = function () {

	};

	App.isMaximized = false;

win.on('maximize', function() {
	App.onMaximize();
	if (enableDisableBlurOnMaximize && Appready) {
	maximized = true;
	console.log("maximize called");
	//$("background").removeClass("hidden");
	//$("background").removeClass("hiddenOpacity");
	console.log("disabling blur here2")
	$("background").fadeIn( 400, function() {
    		App.disableAdaptiveBlur();
  	});
	
	}
});

$("#minimize_button")[0].onclick = function() {
	win.minimize();
};
win.on('minimize', function() {

	if (disableBlurOnLostFocus) {
		//$("background").removeClass("hidden");
		//$("background").removeClass("hiddenOpacity");
		console.log("disabling blur here3")
		$("background").fadeIn( 400, function() {
			App.disableAdaptiveBlur();
    		});
	}

	console.log("minimize triggered");

	if (appLocation.indexOf("extern.itai.app") != -1) {
	console.log("itai triggered");
		
		//setTimeout(function() { win.hide(); }, 1000);
		
		//executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_DOCK -id '+internalId);
	}
});

App.restored = function () {

}

function loadWindowVisuals() {

	$(".appContainer").removeClass("hiddenOpacity");
	$("#body_settings").removeClass("zeroOpacity");
	$("#outerBody").addClass("noMargins");
	console.log("restored called");
	executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId);
	executeNativeCommand('wmctrl -i -r '+internalId+' -b add,stiky');
	executeNativeCommand('wmctrl -i -r '+internalId+' -b remove,skip_pager');

	//$("title").text("showShadowBorderMxs");
}


			setTimeout(function() {
				win.lol = "hi";
				console.log("winx: ",win);
    				//win.restore();
				//loadWindowVisuals();
    				}, 10000);

win.on('restore', function() {

	//setTimeout(function() {
		//console.log("cheking maximize");
	if (win.width < screen.width && win.height < (screen.height-10)) {
		//console.log("win restored from maximize");
		App.isMaximized = false;
	}

	//}, 1000);

	App.restored();
maximized = false;
	/*if (enableDisableBlurOnMaximize || disableBlurOnLostFocus) {
		App.enableAdaptiveBlur();
		$("background").fadeOut( 400, function() {
    		App.enableAdaptiveBlur();
    		});
	} else {
		$("background").fadeOut( 400, function() {
    		//App.enableAdaptiveBlur();
    		});
    		//$("background").addClass("hidden");
		//$("background").addClass("hiddenOpacity");
	}*/
	
var currentdate = new Date();
console.log("restored here  at: "+currentdate.getMinutes()+":"+currentdate.getSeconds()+":"+currentdate.getMilliseconds());
	console.log("restore: ",internalId);
	console.log("restore: ",initRestore);
	if (!initRestore)
		initRestore = true
	else {
	if (internalId != null) {
		//loadWindowVisuals();
	}
	}

	if (appLocation.indexOf("extern.itai.app") != -1) {
	console.log("itai triggered B");
		//executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");
		executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId);
	}

});

App.Xplay = Xplay;

App.resolveFileType = function (ext,includeIconExtention) {
var fType = "blank";

if (ext == "*folder*") {
	fType = "folder";
} else {
        for (var key in map) {
	//console.log("hihihi");
          if (_.include(map[key], ext)) {
		fType = key;
		//console.log("result.type",key);
            //cached[ext] = result.type = key;
            break;
          }
        }
}
if (includeIconExtention)
	return fType+".png";
else
	return fType;
}

App.toggleNetworkOptions = function () {
	appCommsChannel.postMessage({type: "toggle-network-options"});
}

App.sysOptions = function (optionToSend) {
	appCommsChannel.postMessage({type: optionToSend});
}

App.newsSourceModalClosed = function () {

}

App.closeNewsSourcesModal = function () {
	$("iframe").removeClass("lowOpacity");
	$("#NewsSourcesSelector").addClass("hiddenOpacity");
	$(".modal").addClass("hidden");
	$("#NewsSourcesSelector").addClass("hidden");
	App.newsSourceModalClosed();
}

App.openNewsSourcesModal = function () {

	$("#NewsSourcesSelector").removeClass("hidden");
	$(".modal").removeClass("hidden");
	setTimeout(function() {
		$("#NewsSourcesSelector").removeClass("hiddenOpacity");
    
    				}, 500);
	
	$("iframe").addClass("lowOpacity");
}

App.closeCustomModal = function () {
	$("iframe").removeClass("lowOpacity");
	$("#customDialogBox").addClass("hiddenOpacity");
	$(".modal").addClass("hidden");
	$("#customDialogBox").addClass("hidden");
}

var currentInputElements = null;
var currentBody = null;

App.openCustomModal = function (body,inputElements) {
	$("#customDialogBoxMessage").empty();
	if (body.data != null) {
		$("#customDialogBoxMessage").append(body.data);
	}

	if (body.title != null) {
		$("#customDialogBoxTitle").text(body.title);
	}

	if (inputElements.closeModal != null)
		$("#closeCustomModal").removeClass("hidden");
	else
		$("#closeCustomModal").addClass("hidden");

	currentBody = $("#customDialogBoxMessage")[0];
	if (inputElements != null) {
		currentInputElements = inputElements;
		if (inputElements.buttons != null && Array.isArray(inputElements.buttons)) {
			$("#customDialogBoxButtons").empty();
			$("#customDialogBoxButtons").removeClass("text-center");
			console.log("inputElements.buttons: ",inputElements.buttons);
			if (inputElements.buttons.centerise) {
				$("#customDialogBoxButtons").addClass("text-center");
			}
			for (var i = 0; i < inputElements.buttons.length; i++) {
				var buttonClass = "";
				if (inputElements.buttons[i].pullLeft)
					buttonClass += " pull-left";

				if (inputElements.buttons[i].pullRight)
					buttonClass += " pull-right";
				
				$("#customDialogBoxButtons").append('<button style="width: 200px;margin-top: 0;" type="button" class="btn btn-alt m-r-5'+buttonClass+'" onclick="handleCustomButton('+i+')">'+inputElements.buttons[i].text+'</button>')
			}
		}
	}

	$("#customDialogBox").removeClass("hidden");
	$(".modal").removeClass("hidden");
	setTimeout(function() {
		$("#customDialogBox").removeClass("hiddenOpacity");
    
    				}, 500);
	
	$("iframe").addClass("lowOpacity");

	return currentBody;
}

function handleCloseCustomModal() {
	if (currentInputElements.closeModal != null && currentInputElements.closeModal.callback != null) {
		console.log("callback called")
		currentInputElements.closeModal.callback(currentInputElements.closeModal.callbackData);
	}
}

function animateOpenApp(delay,scale) {
win.setVisibleOnAllWorkspaces(false);
Appready = true;
console.log("delay: ",delay);
//setTimeout(function(){ 

//win.showDevTools();
executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId);


			var width = finalAppGeometry.width;
			var height = finalAppGeometry.height;

	if (finalAppGeometry.x == null)
		var mx = Math.floor(((screen.width/2) - (finalAppGeometry.width/2)));
	else
		var mx = finalAppGeometry.x;

	if (finalAppGeometry.y == null)
       		var my = Math.floor(((screen.height/2) - (finalAppGeometry.height/2)) - (20));
	else
		var my = finalAppGeometry.y;
	
	oldX = mx;
	oldY = my;

	oldWidth = width;
	oldHeight = height;
	console.log("oldWidth: "+oldWidth+" oldHeight: "+oldHeight)
	//win.x = 900;
	//win.y = 1000;
//Was here
	//win.height = 200;
	//win.width = 200;

	console.log("minx");

	if (scale) {
console.log("using scale");
		//win.restore();
setTimeout(function(){ 
executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");
//$(".appContainer").removeClass("hiddenOpacity");
 }, delay);
 setTimeout(function(){ 

	win.maximize();
	$("#appPreview").addClass("hiddenOpacity");
	appCommsChannel.postMessage({type: "app-opened"});
	setTimeout(function(){  win.setAlwaysOnTop(false); }, 1000);

//openAppAnimation();
 }, delay);

 setTimeout(function(){ 

	$("#appPreview").addClass("hidden");
	enableDisableBlurOnMaximize = true;

 }, (1000+delay));


 setTimeout(function(){ 



	//.x = oldX;
	//win.y = oldY;
	

	console.log("oldX: ",oldX);
	console.log("oldY: ",oldY);

	
	//App.enableAdaptiveBlur();
	win.resizeTo(oldWidth,oldHeight);
	win.moveTo(oldX, oldY);

	$("#close_button").removeClass("hiddenOpacity");
	$("#minimize_button").removeClass("hiddenOpacity");
	$("#maximize_button").removeClass("hiddenOpacity");
	$("#outerBody").addClass("bg_settings");
	
	

//openAppAnimation();
 }, (delay+80));


	} else {

console.log("not using scale");
$("#appPreview").addClass("hidden");
loadWindowVisuals()
if (usingKwin)
	win.minimize();
else
	win.hide();

	console.log("oldX: ",oldX);
	console.log("oldY: ",oldY);

	
	//App.enableAdaptiveBlur();
	win.resizeTo(oldWidth,oldHeight);
	win.moveTo(oldX, oldY);
	if (usingKwin)
		win.minimize();
	else
		win.hide();

if (appLocation.indexOf("extern.itai.app") != -1) {
	$("#close_button").removeClass("hiddenOpacity");
	$("#minimize_button").removeClass("hiddenOpacity");
	$("#maximize_button").removeClass("hiddenOpacity");
	$("#outerBody").addClass("bg_settings");
	appCommsChannel.postMessage({type: "app-opened"});
	enableDisableBlurOnMaximize = true;
	if (usingKwin)
		win.restore(); 
	else
		win.show();
	setTimeout(function(){ executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");}, 2000);
} else
setTimeout(function(){ 
executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY", function () {
//win.minimize();

	


	$("#close_button").removeClass("hiddenOpacity");
	$("#minimize_button").removeClass("hiddenOpacity");
	$("#maximize_button").removeClass("hiddenOpacity");
	$("#outerBody").addClass("bg_settings");

	if (usingKwin)
		win.restore(); 
	else
		win.show();

	appCommsChannel.postMessage({type: "app-opened"});
	setTimeout(function(){  win.setAlwaysOnTop(false); }, 1000);
	enableDisableBlurOnMaximize = true;


});
}, 500);


	}

 //}, 2000);










}

function handleCustomButton(buttonId) {
	console.log("buttonId: ",buttonId);
	console.log("currentInputElements: ",currentInputElements);
	if (currentInputElements.buttons[buttonId] != null && currentInputElements.buttons[buttonId].callback != null) {
		console.log("callback called")
		currentInputElements.buttons[buttonId].callback(currentInputElements.buttons[buttonId].callbackData);
	}
}



App.getMountedDrives = function() {
	return detectedMountedDrives;
}

var audioControlCallback;

App.updateAudio = function (data,callback) {


	console.log("show playback menu");
	appCommsChannel.postMessage({type: "update-audio-notification",data: data});

	if (callback != null)
		audioControlCallback = callback;
}

App.addCustomWallpaper = function(newWallpaper,setAsWallpaper, wallpaperName, wallpaperArtist) {

}

var packageCompiledCallback;

App.packageApp = function(appDirectory,apDestination,callback) {
	packageCompiledCallback = callback;
	appCommsChannel.postMessage({type: "package-app",appDirectory: appDirectory,apDestination: apDestination});
}

App.openApp = function (appName,files,appGeometry) {
	appCommsChannel.postMessage({type: "open-app",appName: appName,files: files,appGeometry: appGeometry });
}

App.addNewStack = function (location) {
	//console.log("add stacks attempt", location);
//runningApps[0].desktopObject.addNewStack(location);
	appCommsChannel.postMessage({type: "add-new-stack",stackLocation: location});
}

App.newNotification = function (notificationText, notificationButtons, notificationTimeOut,notificationIcon) {

	console.log("sending notification");

	appCommsChannel.postMessage({type: "new-notification",
			notificationText: notificationText,
			notificationButtons: notificationButtons,
			notificationTimeOut: notificationTimeOut,
			notificationIcon: notificationIcon
	});
/*
	var appObject = new_win.sys.getInfo("ids");

	if (notificationIcon == null)
		var notificationIcon = appObject.physicalLocation+appObject.realID+"/"+appObject.options.icon;

	runningApps[0].windowObject.newNotification(new_win.sys.getInfo("ids"),notificationText, notificationButtons, notificationTimeOut,notificationIcon);

		*/
			
}

App.RunAppDev = function (appLocation) {
	appCommsChannel.postMessage({type: "run-app-dev",appLocation: appLocation});
}


App.addCustomWallpaper = function(newWallpaper,setAsWallpaper, wallpaperName, wallpaperArtist) {

	appCommsChannel.postMessage({type: "set-as-wallpaper",newWallpaper: newWallpaper,setAsWallpaper: setAsWallpaper,wallpaperName: wallpaperName,wallpaperArtist: wallpaperArtist});

	/*var gui = require('nw.gui');
	var fs = require('fs');

	var thumb_cache = gui.App.dataPath+"/thumbnails/wallpapers/";
	var thumbnail_location = thumb_cache+wallpaperName+customWallpapers.length;

		if (!fs.existsSync(gui.App.dataPath+"/thumbnails/")){
    			fs.mkdirSync(gui.App.dataPath+"/thumbnails/");
		}

		if (!fs.existsSync(thumb_cache)){
    			fs.mkdirSync(thumb_cache);
		}

			const execSync = require('child_process').execSync;
			code = execSync('ffmpeg -deinterlace -an -i "'+newWallpaper+'" -f mjpeg -t 1 -r 1 -y -s 178x130 "'+thumbnail_location+'.jpg" 2>&1');

			//console.log("code",code);


			var customWallpaperObject = {
				name: wallpaperName,
				artist: wallpaperArtist,
				thumbnail: thumbnail_location+".jpg",
				wallpaperImage: newWallpaper
			}

			customWallpapers.push(customWallpaperObject);

			$("#customeWallpapers").empty();


			for (var k = 0; k < customWallpapers.length; k++) {
				$("#customeWallpapers").append('<div class="col-xs-4" style="opacity:1;" onclick="setWallpaperTo(&quot;'+customWallpapers[k].wallpaperImage+'&quot;,&quot;'+customWallpapers[k].name+'&quot;,&quot;'+customWallpapers[k].artist+'&quot;,&quot;file://'+customWallpapers[k].thumbnail+'&quot)"> <img src="file://'+customWallpapers[k].thumbnail+'" alt="'+customWallpapers[k].name+'"> </div>');
			}

	if (setAsWallpaper) {
		setWallpaperTo(customWallpapers[customWallpapers.length-1].wallpaperImage,customWallpapers[customWallpapers.length-1].name,customWallpapers[customWallpapers.length-1].artist,"file://"+customWallpapers[customWallpapers.length-1].thumbnail);
	}*/

			
}

App.devToolsShow = function() {
	win.showDevTools();
}

App.getAllNews = function () {
	return allActiveNews;
}

App.ready = function (newGeometry,faster,scale) {
	if (!Appready) {
	if (newGeometry != null) {
		if (newGeometry.x != null)
			finalAppGeometry.x = newGeometry.x;

		if (newGeometry.y != null)
			finalAppGeometry.y = newGeometry.y;

		if (newGeometry.width != null)
			finalAppGeometry.width = newGeometry.width;

		if (newGeometry.height != null)
			finalAppGeometry.height = newGeometry.height;
	}
	
	if (faster)
		animateOpenApp(1,scale);
	else
		animateOpenApp(1000,scale);
	}
}

App.updateTrack = App.updateAudio; //Backwards compatibility, delete later

var closeCallback;

App.newsSourceUpdated = function () {
	//override this
}

App.requestOnClose = function(callback) {
	readyToClose = false;
	closeCallback = callback;
}

function closeTabNow() {
			var switchTab = false;
			if ($("#app_tab_elector_"+tabToClose.po).hasClass("active")) {
				switchTab = true;
			}
			$("#app_tab_elector_"+tabToClose.po).remove();
			$("#app_tab_"+tabToClose.po).remove();
			for (var i = 0; i < AppInstances.length; i++) {
				if (tabToClose.id == AppInstances[i].id) {
					console.log("inside if: ");
				 	if (switchTab) {
				 		if (i > 0) {
				 			$("#app_tab_elector_"+AppInstances[i-1].po+" > a").click();
				 		} else {
				 			$("#app_tab_elector_"+AppInstances[i+1].po+" > a").click();
				 		}
				 	}
				 	
					AppInstances.splice(i, 1);
				}
			}
			
			tabToClose = null; //not needed anymore
			if (AppInstances.length == 1) {
				hideInstanceTabs();
				disableTabs();
			}
			console.log("AppInstances removed: ",AppInstances);
}

var closeCalls = 0;
App.close = function () {

	if (tabToClose != null) {
		if (tabToClose.closeInProgress) {
			closeTabNow();
		} else {
			console.log("close tB REQUEST");
			tabToClose.closeInProgress = true;
			if (tabToClose.closeCallback != null) {
				requestOnCloseCallbacksNo--;
				tabToClose.closeCallback();
			} else {
				closeTabNow();
			}
			
		}
	} else {
		console.log("requested to close");
		readyToClose = true;
		if (requestOnCloseCallbacksNo != 0) {
			closeCalls++;
		if (requestOnCloseCallbacksNo == closeCalls)
			console.log("you can now close"); 
		win.close();
	}
	}
	
	
}

function closeTab(tabId) {
console.log("close tab called: ",tabId);
	for (var i = 0; i < AppInstances.length; i++) {
		console.log("AppInstances[i].id: ",AppInstances[i].id);
		if (AppInstances[i].id == tabId) {
			console.log("tab to close found");
			tabToClose = AppInstances[i];
			AppInstances[i].close();
		}
	}
}

App.checkInstanceFocus = function() {
  if(document.activeElement == "IFRAME") {
    console.log('iframe has focus: ',document.activeElement.tagName);
  } else {
    console.log('iframe not focused');
  }
}

App.onOpenFiles = function () {};

               var explorebar = {
                   //updateTrack : new_win.updateAudio//runningApps[0].windowObject.updateAudioInfo
               }
               
               
               
               App.explorebar = explorebar;










	var winButtonProperties = { //For Beta 2 we will only use border (running out of time)
		backgroundColor: "rgba(255, 255, 255, 0)",
		hoverBackgroundColor: "rgba(255, 255, 255, 0.8)",
		borderColor: "rgba(255, 255, 255, 0.31)",
		hoverBorderColor: "rgba(255, 255, 255, 0.8)",
		textShadow: "0 0 10px rgba(0, 0, 0, 0.75);",
		color: "rgba(255, 255, 255, 1)"
	}


			setTimeout(function() {
//console.log("element: ",document.getElementsByTagName("IFRAME")[0]);
    
    				}, 10000);

		//position: absolute; width: 100%; height: 100%;" allownw class="appInstance hiddenOpacity"> </iframe>

//win.initWindow

console.log("win.cWindow.id: ",win.cWindow.id);

const appCommsChannel = new BroadcastChannel("eXternOSApp"+win.cWindow.id); //Comms channel between process manager and this App

var readyToClose = true;

win.on('close', function() {
	
	if (readyToClose) {
		appCommsChannel.postMessage({type: "closed"});
		$("#main").empty();
		App = null;
		this.close(true);
	} else if (requestOnCloseCallbacksNo != 0){
	console.log("trying to close");
		for (var i = 0; i < AppInstances.length; i++) {
			if (AppInstances[i].closeCallback != null) {
			console.log("trying to callback: ",AppInstances[i].closeCallback);
				AppInstances[i].closeCallback();
			}
		}
		
	} else {
		appCommsChannel.postMessage({type: "closed"});
		$("#main").empty();
		App = null;
	}
		
});

//const appCommsChannelTemp = new BroadcastChannel("eXternOSAppListerning");
/*
appCommsChannelTemp.onmessage = function (ev) {

			console.log("got a message back",ev);

		if (ev.data.type == "load-id") {

	//const appCommsChannel = new BroadcastChannel("eXternOSApp"+ev.data.id);


}
};*/
		$(".appContainer").removeClass("hiddenOpacity");
		//$("#outerBody").addClass("bg_settings");
	appCommsChannel.postMessage({type: "requesting-init-settings"});
appCommsChannel.onmessage = function (ev) {
			console.log("message recieved: ",ev);



			if (ev.data.type == "confirm-user-details") {
				console.log("got the feedback");
				confirmUserDetailsCallback(ev.data.returnedResults);
			}

			if (ev.data.type == "resore") {

}

			if (ev.data.type == "package-compiled") {
				packageCompiledCallback(ev.data.result);
			}

			if (ev.data.type == "audio-playback-control") {
				console.log("sending playback controls");
				audioControlCallback(ev.data.request);
			}

			if (ev.data.type == "new-windows") {
				console.log("new-windows: ",ev.data);
				AppInstances.forEach(appInstance => {
					appInstance.systemEvent(ev.data)
				});
			}


			
		if (ev.data.type == "wallpaper-data") {
		console.log("found bg data");
			var hideBackgroundClass = "";
			var globalDefaultBgPosition = "";
			if (useRealTimeBlur)
				hideBackgroundClass = "hidden";
		//}
		
		var globalDefaultBgSize = wallpaperWidth+'px '+wallpaperheight+'px';
		
		globalDefaultBgPosition = '0 0';
		
		//height: '+wallpaperheight+'px; width: '+wallpaperWidth+'px;
      if ($( window.document.body.children[0])[0].nodeName !="BACKGROUND")
		if (globalDefaultBgPosition != "") {
		          $(window.document.body).prepend(`<background class="noMargins ${disableBlurOnLostFocus ? '' : 'hidden'}" style="border-radius: 5px 5px 5px; position: absolute; height: calc(100% - 50px); width: calc(100% - 50px); box-shadow: rgba(0, 0, 0, 1) 0px 0px 30px; top: 25px; left: 25px; background-repeat: repeat; background-position: '+globalDefaultBgPosition+'; background-size: '+globalDefaultBgSize+';" class="'+hideBackgroundClass+'"></background>`);
	document.body.children[0].style.backgroundImage = ev.data.data;
//ev.data.data
		//$(new_win.outerBodyBackground[0]).css("background-position",new_win.oldbackgroundPosition);
		console.log("set with.. ",globalDefaultBgPosition);
	} else {
		$(window.document.body).prepend(`<background class="noMargins ${disableBlurOnLostFocus ? '' : 'hidden'}" style="border-radius: 5px 5px 5px; position: absolute; height: calc(100% - 50px); width: calc(100% - 50px); box-shadow: rgba(0, 0, 0, 1) 0px 0px 30px; top: 25px; left: 25px; background-repeat: repeat;" class="'+hideBackgroundClass+'"></background>`);

		if (disableBlurOnLostFocus)
			document.body.children[0].style.backgroundImage = ev.data.data;
	}

      //console.log('New window BG ELEMENT',$( new_win.window.document.body.children[0])[0].nodeName);
      //new_win.window.document.body.children[0].style.backgroundImage = document.body.children[0].style.backgroundImage;
setTimeout(function(){ 


			}, 100);

}



			if (ev.data.type == "init-objects") {
				internalId = ev.data.internalId;
				console.log("whats internal: ",ev.data.internalId);
				win.internalId = ev.data.internalId;
				detectedMountedDrives = ev.data.detectedMountedDrives;
				App.osVersion = ev.data.osVersion;
				App.fileTypesApps = ev.data.fileTypesApps;
				App.apps = ev.data.allInstalledApps;
				App.legacyApps = ev.data.allLegacyApps;
				/*for (var i = 0; i < AppInstances.length; i++) {
				AppInstances[i].osVersion = ev.data.osVersion;
				AppInstances[i].fileTypesApps = ev.data.fileTypesApps;
				AppInstances[i].apps = ev.data.allInstalledApps;
				AppInstances[i].legacyApps = ev.data.allLegacyApps;
				}*/
				if (allActiveNews != ev.data.allActiveNews && allActiveNews != null) {
					console.log("news updated: ",ev.data.allActiveNews);
					console.log("ev.data.enabledSources: ",ev.data.enabledSources);
					App.newsSourceUpdated(ev.data.allActiveNews);
				}
				allActiveNews = ev.data.allActiveNews;
				enabledSources = ev.data.enabledSources;
				improvePerfomanceMode = ev.data.improvePerfomanceMode;
				filesInClipboard = ev.data.filesInClipboard;
				if (improvePerfomanceMode)
					$("#outerBody").addClass("improvePerfomanceModeBody");
				else
					$("#outerBody").removeClass("improvePerfomanceModeBody");

				if (!initLoaded) {
					App.disableAdaptiveBlur();
					executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -set _NET_WM_WINDOW_OPACITY 0");
					initLoaded = true;
				}//addSource

				$('.addNews').empty();

				$('.addNews').each(function(i, obj) {
					console.log("each looping");
    					$(obj).append('<i class="fas fa-plus"></i> Add "'+$(obj).attr("name")+'"');
    					$(this).addClass("addSource");
				});

				console.log("enabledSources: ",enabledSources);
				for (var i = 0; i < enabledSources.length; i++) {
					console.log("finding.... ",$('.addSource[source="'+enabledSources[i]+'"]'));
					 $('.addSource[source="'+enabledSources[i]+'"]').empty();
					 $('.addSource[source="'+enabledSources[i]+'"]').append('<i class="fas fa-times"></i> Remove "'+$('.addSource[source="'+enabledSources[i]+'"]').attr("name")+'"');
					$('.addNews[source="'+enabledSources[i]+'"]').removeClass("addSource");
					console.log("removed lass from: ",$('.addNews[source="'+enabledSources[i]+'"]'));
				}
				//setTimeout(function() { adjustWalpaperPosition();}, 3000);
			}


			if (ev.data.type == "open-files") {
				console.log("open-files: ",ev.data.files);
				doNotTriggerShowWindowEvents = false;
				if (appLocation.indexOf("extern.files.app") != -1) {
					AppInstances[AppInstances.length-1].argv = ev.data.files;
					//AppInstances[AppInstances.length-1].onOpenFiles(ev.data.files);
				} else {
					AppInstances[AppInstances.length-1].onOpenFiles(ev.data.files);
				}
					
			}

			if (ev.data.type == "minimize-window") {
				console.log("minimizing called");
				win.minimize();
			}
			
			if (ev.data.type == "set-volume") {
				AppInstances[AppInstances.length-1].setVolume(ev.data.level);
			}
			
			if (ev.data.type == "increase-volume") {
				AppInstances[AppInstances.length-1].increaseVolume();
			}
			
			if (ev.data.type == "decrease-volume") {
				AppInstances[AppInstances.length-1].decreaseVolume();
			}

			if (ev.data.type == "increase-brightness") {
				AppInstances[AppInstances.length-1].increaseBrightness();
			}
			
			if (ev.data.type == "decrease-brightness") {
				AppInstances[AppInstances.length-1].decreaseBrightness();
			}
			
			if (ev.data.type == "set-brightness") {
				AppInstances[AppInstances.length-1].setBrightnes(ev.data.level);
			}

			if (ev.data.type == "show-window") {

				if (appLocation.indexOf("extern.itai.app") != -1) {
					win.hide();
				}

				//setTimeout(function() { disableBlurOnLostFocus = true;}, 5000);
//loadWindowVisuals(); 
				//win.minimize();
				//executeNativeCommand("wmctrl -i -R "+internalId);
				console.log("window showing",internalId);
//executeNativeCommand("wmctrl -i -R "+internalId, function() {
//setTimeout(function() {
//win.minimize();

				//win.show()

		$(".appContainer").removeClass("hiddenOpacity");
		
 //loadWindowVisuals(); 

if (appLocation.indexOf("extern.files.app") != -1) {
//win.showDevTools();
console.log("restoring files app: ",fWidth);
console.log("restoring files app height: ",fHeight);
console.log("App.argv: ",App.argv);
if (!doNotTriggerShowWindowEvents) {
	console.log("opening from here")
	AppInstances[AppInstances.length-1].showWindowEvent();
	//setTimeout(function(){ AppInstances[AppInstances.length-1].showWindowEvent(); }, 1000);
}
	
	
//win.width = 10;
//win.height = 10;
//win.resizeTo(10,10);
	
	/*$("#outerBody").addClass("bg_settings");
	$("#close_button").removeClass("hiddenOpacity");
	$("#minimize_button").removeClass("hiddenOpacity");
	$("#maximize_button").removeClass("hiddenOpacity");

	win.resizeTo(fWidth,fHeight);
	var mx = Math.floor(((screen.width/2) - (fWidth/2)));
    var my = Math.floor(((screen.height/2) - (fHeight/2)) - (20));

	win.moveTo(mx,my);*/
	
	//App.ready({width: 1700, height: 860},true,false);


//executeNativeCommand('wmctrl -i -R '+internalId, function () { 


win.setVisibleOnAllWorkspaces(false);
appCommsChannel.postMessage({type: "app-opened"});
setTimeout(function(){  win.setAlwaysOnTop(false); }, 1000);
enableDisableBlurOnMaximize = true;


console.log("don't minimize");
//App.enableAdaptiveBlur();

//win.minimize(); 

//setTimeout(function() { 

executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId);

executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY", function () {





Appready = true;
if (usingKwin)
	win.restore();
else
	win.show();
//win.showDevTools();

});
//}, 300);
//});


	//setTimeout(function() { win.restore();}, 800);
} else { //if (appLocation.indexOf("extern.itai.app") == -1)

	/*if (appLocation.indexOf("extern.itai.app") != -1) {
		executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -set _NET_WM_WINDOW_OPACITY 0");
		//executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY"); //come here
	}*/


	if (appLocation.indexOf("extern.itai.app") != -1) {
		win.resizeTo(10,10);
	} else {

	if ((screen.width > 1900) && (screen.width > 900)) {
		if (useRealTimeBlur) {
			var width = 1750-50;
			var height = 910-50;
		} else {
			//We are just gonna do this for consistant shadows to be managed by the WM
			//FIXME: Not removing the redudant if statement incase we need to rollback etc
			var width = 1750-50;
			var height = 910-50;
		}

	} else {
		if (useRealTimeBlur) {
			var width = 1319-50;
			var height = 725-50;
		} else {
			//Same reason as above
			var width = 1319-50;
			var height = 725-50;
		}
	}
	//executeNativeCommand("wmctrl -i -R "+internalId, function() {
	/*win.resizeTo(width,height);
	var mx = Math.floor(((screen.width/2) - (width/2)));
       var my = Math.floor(((screen.height/2) - (height/2)) - (20));

	win.moveTo(mx,my);*/


	//var mouse = robot.getMousePos();
	console.log("mouse: ",mouse);
	var mouse = {x:100, y:100};

	console.log("setAppGeometry: ",setAppGeometry);

	if (setAppGeometry != null) {
		var newX = parseInt(setAppGeometry.x);
		var newY = parseInt(setAppGeometry.y);
	var miniWidth = parseInt(setAppGeometry.width);
	var minHeight = parseInt(setAppGeometry.height);
	if (setAppGeometry.previewImage != null && setAppGeometry.showThumbnailPreview) {
		$("#appPreview > img").attr("src",setAppGeometry.previewImage);
		$("#appPreview").removeClass("hidden");
	}
		console.log("using custom geometry");
	} else {
	var miniWidth = 200;
	var minHeight = 200;
	var newX = mouse.x-(miniWidth/2);
	var newY = mouse.y-(minHeight/2);
	console.log("NOT using custom geometry");

	}
	
	win.resizeTo(miniWidth,minHeight);
	win.moveTo(newX,newY);

	}


	if (!waitForAppToRespond)
		animateOpenApp(950);

	
	//win.minimize();

	//win.width = width;
	//win.height = height;
	//setTimeout(function() { win.minimize(); }, 3000);
				if (delayShowingApp) {
				delayShowingApp = false;
				//loadWindowVisuals();
				//setTimeout(function() {  loadWindowVisuals(); }, 10000);

				} else {
				//win.restore();
				//loadWindowVisuals();
				}
			console.log("end");
		var useLegacyAnimation = false;
		if (useLegacyAnimation) {
setTimeout(function() { 
	if (usingKwin)
		win.restore();
	else
		win.show();

}, 500);
}

	/*setTimeout(function() {
		executeNativeCommand('xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id '+internalId); //RESTORE THIS
	}, 300);*/
//}, 3000);
//});

}
executeNativeCommand('xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id '+internalId); //RESTORE THIS

			} 
//&& ev.data.appLocation != undefined && !appLoaded
			console.log("cjhecking....");
			if (ev.data.type == "load-App") {
appLocation = ev.data.appLocation;
thisAppName = ev.data.appName;
$("#app_tab_elector_0 > a > span").text(thisAppName);
$("#app_tab_elector_0").attr("title",thisAppName);
setAppGeometry = ev.data.appGeometry;
App.argv = ev.data.argv;
if (ev.data.waitForAppToRespond != null)
	waitForAppToRespond = ev.data.waitForAppToRespond;

if (App.argv != null) {
	if (App.argv[0] == "--screnshot-extern\0" && ev.data.appLocation.indexOf("extern.photos.app") != -1) {
		//Screenshot lets do something
		ignorePhotosInactive = true;
		console.log("it's a screenshot");
		if (usingKwin)
			win.restore();
		else
			win.show();
	} else {
		if (usingKwin)
			win.minimize();
		else
			win.hide();
	}
} else {
	if (usingKwin)
		win.minimize();
	else
		win.hide();
}
	console.log("lets go");
//executeNativeCommand("wmctrl -i -R "+internalId, function() {
//win.minimize();
console.log("lets go lol");
			//setTimeout(function() { 
				delayShowingApp = true;   				
				appLoaded = true;



	if (ev.data.appLocation.indexOf("extern.files.app") != -1) {
//Files resize was here
	//win.minimize();

	/*setTimeout(function() { 
	win.width = width;
	win.height = height;
	win.x = Math.floor(((screen.width/2) - (width/2)));
	}, 1000);*/

	//win.minimize();
	//});
	}
	var empty = [];
	console.log("setting blur... :",internalId);
	//executeNativeCommand('xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id '+internalId); //RESTORE THIS
$("#outerBody").addClass("noMargins");
	$("#body_settings").removeClass("zeroOpacity");

		if (ev.data.appLocation.indexOf("extern.welcome.app") != -1) {
			App.setUpForInstall = function() {
				appCommsChannel.postMessage({type: "setup-for-install"});
			}

		}



		if (ev.data.appLocation.indexOf("extern.photos.app") != -1) {
			/*AppInstances[AppInstances.length-1].removeOpacity = function() {
				executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY");
			}*/

		}

		if (ev.data.appLocation.indexOf("extern.tips.app") != -1) {

			App.doneUserSetup = function () {
				appCommsChannel.postMessage({type: "done-user-setup"});
			}

			App.setUserDetails = function (userDetails,pass,callback) {
				confirmUserDetailsCallback = callback;
				appCommsChannel.postMessage({type: "set-user-details",userDetails: userDetails,pass: pass});
			}
		}

var hiddenOpacityClass = "";

if (setAppGeometry != null) {
	hiddenOpacityClass = " hiddenOpacity";
}

App.addNewInstanceTab(App.argv,true,true);
		setTimeout(function() { 
			var tabId = 0;
				$("#app_tab_"+tabId).append('<iframe onclick="App.checkInstanceFocus()" class="appContainer" src="../../'+ev.data.appLocation+'" frameborder="0" partition="persist:trusted" allownw class="appInstance '+hiddenOpacityClass+'"> </iframe>');
				console.log("elementx: ",document.getElementsByTagName("IFRAME")[0]);
				$("#app_tab_"+tabId+" > iframe").load( function() {
					
					console.log("executed",this);
					$(this).contents().find("head")
      .prepend($("<style type='text/css'>  .btn { border-color: "+winButtonProperties.borderColor+" !important;}  </style> <link href='../../../Shared/CoreCSS/scrollbar.css' rel='stylesheet'> <script> window.instance = parent.newInstance; console.log('window.instance',window.instance); document.addEventListener('click', function() { console.log('focused iframe'); });</script>"));
	//console.log("hiii: ",$("#app_tab_1")[0]);

	//console.log("fromae click detection readyA: ",this.contentWindow.document.body);
	//var frameBody = this.contentWindow.document.body;

	//console.log("fromae click detection ready3: ",$(this.contentWindow.document.body));

	$(this.contentWindow.document.body).click(function() {
		hideInstanceTabs();
	});

	//frameBody.onmousedown(function(){ console.log("focused iframe")});
	//frameBody.click(function(){ /* ... */ });
	

if (appLocation.indexOf("extern.itai.app") != -1) {
		executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -set _NET_WM_WINDOW_OPACITY 0");
		//executeNativeCommand("xprop -id "+internalId+" -f _NET_WM_WINDOW_OPACITY 32c -remove _NET_WM_WINDOW_OPACITY"); //come here
	}

if (ev.data.appLocation.indexOf("extern.files.app") != -1) {
				//console.log("elementx: ",document.getElementsByTagName("IFRAME")[0]);
	//win.blur();
	$(".appContainer").removeClass("hiddenOpacity");
	$("#outerBody").addClass("bg_settings");
	$("#close_button").removeClass("hiddenOpacity");
	$("#minimize_button").removeClass("hiddenOpacity");
	$("#maximize_button").removeClass("hiddenOpacity");
	if ((screen.width > 1900) && (screen.width > 900)) {
		if (useRealTimeBlur) {
			var width = 1750-50;
			var height = 910-50;
			//win.resizeTo(1750-50,910-50);
		} else {
			//We are just gonna do this for consistant shadows to be managed by the WM
			//FIXME: Not removing the redudant if statement incase we need to rollback etc
			var width = 1750-50;
			var height = 910-50;
			//win.resizeTo(1750-50,910-50);
		}

	} else {
		if (useRealTimeBlur) {
			var width = 1319-50;
			var height = 715-50;
			//win.resizeTo(1319-50,715-50);
		} else {
			//Same reason as above
			var width = 1319-50;
			var height = 715-50;
			//win.resizeTo(1319-50,715-50);
		}
	}

	fHeight = height;
	fWidth = width;
	//executeNativeCommand("wmctrl -i -R "+internalId, function() {
	
	var mx = Math.floor(((screen.width/2) - (width/2)));
    var my = Math.floor(((screen.height/2) - (height/2)) - (20));

	console.log("mx: ",mx);
	console.log("my: ",my);

	console.log("mheightx: ",height);
	console.log("width: ",width);

	executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId, function () {
		win.resizeTo(width,height);
		win.moveTo(mx,my);
		//loadWindowVisuals();
		if (usingKwin)
			win.minimize();
		else
			win.hide();
		executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_DOCK -id '+internalId);
		//setTimeout(function() {  }, 1000);
	});
	//setTimeout(function() {  }, 1000);
	

	
	

	
}
console.log("app-ready sent");
appCommsChannel.postMessage({type: "app-ready"});  //Give some leeway
	//App.onOpenFiles(empty);
//});
});

if (ev.data.appLocation.indexOf("extern.files.app") != -1) {

//FIXME: remove this
}


}, 100); //1000
			}

			
};

$(".addNews").click(function(){

	enabledSources = [];

    if ($(this).hasClass("addSource")) {
    enabledSources.push($(this).attr("source"));
	appCommsChannel.postMessage({type: "update-news-sources", sources: enabledSources});
    //$(this).addClass("hidden");
    $(this).empty();
    $(this).append('<span class="icon pull-left">&#61918;</span> Remove "'+$(this).attr("name")+'"');
    $(this).removeClass("addSource");
	
    } else {
    //enabledSources.push($(this).attr("source"));
    //$(this).addClass("hidden");
		console.log("vefore enabledSources",enabledSources);
    for (var m = 0; m < enabledSources.length; m++) {
         if (enabledSources[m] == $(this).attr("source")) {
                 enabledSources.splice(m, 1);
                 break;
         }
    }
	appCommsChannel.postMessage({type: "update-news-sources", sources: enabledSources});
		console.log("remoced enabledSources",enabledSources);
    $(this).empty();
    $(this).append('<i class="fas fa-plus"></i> Add "'+$(this).attr("name")+'"');
    $(this).addClass("addSource");
    }
    //$("#nextTab").removeClass("unclickable");
    //console.log("SOURCE",$(this).attr("source"));
    //console.log("SOURCE",this);
});

		
	//appCommsChannelTemp.postMessage({type: "requesting-id"});
console.log("posted");

//document.addEventListener('click', function() { App.checkInstanceFocus(); console.log('focused iframe check'); });




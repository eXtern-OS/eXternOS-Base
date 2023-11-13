//nw.Window.get().evalNWBin(null, '/usr/eXtern/iXAdjust/Hub/js/processes_apps_manager.bin');
var rimraf = require('rimraf');
var ncp = require('ncp').ncp;

var globalDefaultBgPosition = "";
var nextFilesProcess; //Stores the next available files process for fast user experience
var winIdCounter = 0;
var restoreCalls = 0; //used to only blur after initial load times
var urlToLoadNext = "";
var itaiInstancePos; //store app pos of itai for efficiency. Doesn't matter as it's like the second launched instance so won't change position 
var hudInstancePos; //store app pos of the HUD for efficiency. Doesn't matter as it's like the second launched instance so won't change position 
var appsToRunQueue = [];
var readyToRunApp = true;
var configsReady = false;
var currentTempApp;
var currentTempAppNew;
var filesInClipboard = [];
filesInClipboard.isCut = false;

//systemSetupCompleted = false;
//win.showDevTools();
var firstProcessLoaded = false;
//win.showDevTools();
//systemSetupCompleted = true;
//userSetupCompleted = false;

const appCommsChannelTemp = new BroadcastChannel("eXternOSAppListerning");

appCommsChannelTemp.onmessage = function (ev) {
	console.log("requesting ID",ev);
	if (ev.data.type == "requesting-id") {
		var idToUse = winIdCounter-1;
		appCommsChannelTemp.postMessage({
			type: "load-id",
			id: idToUse
		});
		
	}
}


function appsUpdateData(updateDrives) {
	console.log("updating all Apps");
	for (var i = 1; i < runningApps.length; i++) {
		runningApps[i].windowObject.updateAppGlobalVariables(updateDrives);
	}
}

function showDispPieChart(usedSpace,pieChartDiv) {

	var animateTime = 3000;
	if (usedSpace < 20) {
		animateTime = 500;
	} else if (usedSpace < 50) {
		animateTime = 1000;
	} else if (usedSpace < 80) {
		animateTime = 2000;
	}

$(pieChartDiv).find('.pie-chart-med').remove();

$(pieChartDiv).prepend('<div class="pie-chart-med" data-percent="'+usedSpace+'"><span class="percent"></span></div>')
    $(pieChartDiv).find('.pie-chart-med').easyPieChart({
        easing: 'easeOutSine',
        barColor: 'rgba(255,255,255,0.6)',
        trackColor: 'rgba(0,0,0,0.3)',
        scaleColor: false,
        lineCap: 'round',
        lineWidth: 30,
        size: 200,
        animate: animateTime,
        onStep: function(from, to, percent) {
            $(this.el).find('.percent').text(Math.round(percent));
        }
    });

    var charts = window.chart = $(pieChartDiv).find('.pie-chart-med').data('easyPieChart');
    /*$('.pie-chart-tiny .pie-title > i').on('click', function() {
        $(this).closest('.pie-chart-tiny').data('easyPieChart').update(Math.random()*200-100);
    });*/
}

function convertBytes(input) {
if (input != 0) {
    current_filesize = input.toFixed(2);
    var size_reduction_level = 0;
    while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
          /*Check if its a whole number or not*/
          if (current_filesize % 1 !== 0)
      current_filesize = Math.round(current_filesize); /*.toFixed(2);*/

	if (current_filesize < 10)
		current_filesize += ".0";
          
      
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
} else {
	return 0;
}
}

function convertBytesExact(input) {
if (input != 0) {
    current_filesize = input.toFixed(2);
    var size_reduction_level = 0;
    while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
          /*Check if its a whole number or not*/
          //if (current_filesize % 1 !== 0)
      //current_filesize = Math.round(current_filesize); /*.toFixed(2);*/

	//if (current_filesize < 10)
		//current_filesize += ".0";

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
} else {
	return 0;
}
}



function loadStartUpApps() {
runAppX("extern.temp.app",filess);
if (systemSetupCompleted) {
	runApp('extern.itai.app',filess);
	setTimeout(function(){ runApp('extern.hud.app',15000); }, filess); 
}
 

executeNativeCommand("/usr/eXtern/NodeJs45/nw /usr/eXtern/systemX/apps/extern.video.app/main --load-for-cache");

	if (!systemSetupCompleted)
		executeNativeCommand("grep -zq casper /proc/cmdline && echo live",function(res,err) {
		console.log("live check: ",res);
		//console.log("err",err); lol2
		if ( res == null) {
			systemSetupCompleted = true;
			//setTimeout(function(){ runApp("extern.files.app",files); }, 1000);
			localStorage.setItem('systemSetupCompleted', JSON.stringify(systemSetupCompleted));
			executeNativeCommand("cp -r /usr/eXtern/systemX/Shared/CoreSetup/Projects ~/", function () {
				setTimeout(function(){ chrome.runtime.reload(); }, 1000); //FIXME temporary fix
			});
			
		} else {
			runApp("extern.welcome.app",filess);
		}
	})
		

	//if (!userSetupCompleted)
		//setTimeout(function(){ runApp("extern.tips.app",filess); }, 2000);

		if (systemSetupCompleted && !userSetupCompleted) {

	/*console.log("checking password");
	sudo.setPassword("extern"); //check if password has already been changed (i.e setup completed but configs got reset)
		sudo.check(function(valid) {
		console.log("password checked");
        		if (valid) {
				console.log("password valid");
				var userSetupTrigger = [];
			userSetupTrigger.push("trigger");
			runApp("extern.tips.app",userSetupTrigger);
			} else {
				console.log("password invalid");
				userSetupCompleted = true;
				localStorage.setItem('systemSetupCompleted', JSON.stringify(userSetupCompleted));
			}

		});*/

		executeNativeCommand("grep -zq casper /proc/cmdline && echo live",function(res,err) {
		console.log("live check: ",res);
		//console.log("err",err);
		if ( res == null) {
			console.log("try to open tips");
			var userSetupTrigger = [];
			userSetupTrigger.push("trigger");
			runApp("extern.tips.app",userSetupTrigger);
		} else {
			//res.indexOf("live") == -1 
			console.log("set sys complete");
			userSetupCompleted = true;
			localStorage.setItem('systemSetupCompleted', JSON.stringify(userSetupCompleted));
		}
	})
	
	}


	

runApp("extern.files.app",filess);

//setTimeout(function(){ runApp("extern.files.app",filess); }, 3000); //openApp will do the checking




}

function runWelcomeApp() {
	console.log("try welcome App");
	//setTimeout(function(){ runApp('extern.welcome.app',files); }, 5000);
	runApp('extern.welcome.app',filess);
}
//win.showDevTools();

function openNewsInBrowser(link) {
    var webpages = []
    webpages.push(link);
    //console.log("Link clicked: "+link);
    openApp(fileTypesApps.web[0].id,webpages);
    
}

function packageApp(appDirectory,apDestination,packagePass,callback) {


var child = require('child_process')
  .spawn('zip', ['-r',apDestination,appDirectory]);

child.stdout.on('data', function (data) {
       console.log('SUCCESS: compiled');


	var cryptos = require('crypto');
	var cipher = cryptos.createCipher('aes-256-cbc', packagePass);
	var inputs = fs.createReadStream(apDestination);
	var outputs = fs.createWriteStream(apDestination+'.out');

	inputs.pipe(cipher).pipe(outputs);

	outputs.on('finish', function() {

		fs.unlink(apDestination, (err) => {
            		if (err) {
                		console.log("failed to delete file:" + err);
            		} else {
            			console.log("success to delete source file:");
				fs.rename(apDestination+'.out', apDestination, function (err) {
  					if (err) callback(false); else callback(true);
  					//console.log('renamed complete');

				});





			}
        });






	});

});

child.stderr.on('data', function (data) {
  console.log('stderr: ' + data);
});


/*
	    var exec = require('child_process').exec,
                   child;
            child = exec('zip -r "'+apDestination+'" ./',{cwd: appDirectory},function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: compiled');


	var cryptos = require('crypto');
	var cipher = cryptos.createCipher('aes-256-cbc', packagePass);
	var inputs = fs.createReadStream(apDestination);
	var outputs = fs.createWriteStream(apDestination+'.out');

	inputs.pipe(cipher).pipe(outputs);

	outputs.on('finish', function() {

		fs.unlink(apDestination, (err) => {
            		if (err) {
                		console.log("failed to delete file:" + err);
            		} else {
            			console.log("success to delete source file:");
				fs.rename(apDestination+'.out', apDestination, function (err) {
  					if (err) callback(false); else callback(true);
  					//console.log('renamed complete');

				});





			}
        });






	});
        
        
        
        
    }       
});*/
}


function encryptPackage(packagePass,appDirectory,apDestination,callback) {

console.log("we are here: ",packagePass);

var childx = require('child_process')
  .spawn('zip', ['-P',packagePass,"/tmp/compileApp/data.out",appDirectory+"/package.json"]);

childx.stdout.on('data', function (data) {
  console.log('stdout: ' + data);

	     console.log('SUCCESS: compiled');
	var cryptos = require('crypto');
	var cipher = cryptos.createCipher('aes-256-cbc', packagePass);
	var inputs = fs.createReadStream('/tmp/compileApp/data.out');
	var outputs = fs.createWriteStream('/tmp/compileApp/data');

	inputs.pipe(cipher).pipe(outputs);

	outputs.on('finish', function() {
  	console.log('Encrypted file written to disk!');
	fs.unlink('/tmp/compileApp/data.out', (err) => {
            if (err) {
                console.log("failed to delete file:" + err);
            } else {
                ncp(appDirectory+'/package.json', '/tmp/compileApp/package.json', function (err) {
			console.log("hereee");
  		if (err) {
    			console.log("error copying Json",err);
  		} else {
			console.log("copied json before read");

			var pjson = JSON.parse(fs.readFileSync(appDirectory+'/package.json', 'utf8'));
			console.log("copied json");
			ncp(appDirectory+"/"+pjson.window.icon, '/tmp/compileApp/'+pjson.window.icon, function (err) {
  				if (err) {
    				console.error(err);
  				} else {
					console.log("copied icon");
					packageApp("/tmp/compileApp/",apDestination,"eXternOSAppXAPP5M2MMGSB1B234BB",callback);
		}

		});

		}

		});
            }
        });



	});



	//packageApp(appDirectory,apDestination,packagePass,callback);



});

childx.stderr.on('data', function (data) {
  console.log('stderr: ' + data);
});

childx.stdout.on('exit', function (code) {
  console.log('exit: ' + code);
});
}



function compressApp(appDirectory,apDestination,callback) {

var child = require('child_process')
  .spawn('sha256sum', [appDirectory+"/package.json"]);

child.stdout.on('data', function (data) {
  //console.log('stdout: ' + data);

	//packagePass = data;
	if (!fs.existsSync("/tmp/compileApp")){
    		fs.mkdirSync("/tmp/compileApp");
	}
	console.log("B..: ",data.toString().split(" ")[0]);
	//console.log("pass: ",data.split(" "));
	encryptPackage(data.toString().split(" ")[0],appDirectory,apDestination,callback);



});

child.stderr.on('data', function (data) {
  console.log('stderr: ' + data);
});

/*

	var execSync = require('child_process').execSync;
	console.log("what to send",escapeShell('sha256sum "'+appDirectory+'/package.json"'));
	var packagePass = execSync(escapeShell('sha256sum "'+appDirectory+'/package.json"')).toString().split("  ")[0];

if (!fs.existsSync("/tmp/compileApp")){
    fs.mkdirSync("/tmp/compileApp");
}

	    var exec = require('child_process').exec,
                   child;
            child = exec('zip -P '+packagePass+' -r /tmp/compileApp/data.out ./',{cwd: appDirectory},function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: compiled');
	var cryptos = require('crypto');
	var cipher = cryptos.createCipher('aes-256-cbc', packagePass);
	var inputs = fs.createReadStream('/tmp/compileApp/data.out');
	var outputs = fs.createWriteStream('/tmp/compileApp/data');

	inputs.pipe(cipher).pipe(outputs);

	outputs.on('finish', function() {
  	console.log('Encrypted file written to disk!');
	fs.unlink('/tmp/compileApp/data.out', (err) => {
            if (err) {
                console.log("failed to delete file:" + err);
            } else {
                ncp(appDirectory+'/package.json', '/tmp/compileApp/package.json', function (err) {
			console.log("hereee");
  		if (err) {
    			console.log("error copying Json",err);
  		} else {
			console.log("copied json before read");

			var pjson = JSON.parse(fs.readFileSync(appDirectory+'/package.json', 'utf8'));
			console.log("copied json");
			ncp(appDirectory+"/"+pjson.window.icon, '/tmp/compileApp/'+pjson.window.icon, function (err) {
  				if (err) {
    				console.error(err);
  				} else {
					console.log("copied icon");
					packageApp("/tmp/compileApp/",apDestination,"eXternOSAppXAPP5M2MMGSB1B234BB",callback);
		}

		});

		}

		});
            }
        });



	});



	//packageApp(appDirectory,apDestination,packagePass,callback);
        
        
        
        
    }       
});*/
}



//win.showDevTools();

var readyForNextApp = true;

var callbackForAppLoaded;

function prepareNextProcess(callbackForAppLoadedB) {
	console.log("prepareNextProcess called",callbackForAppLoadedB);

	callbackForAppLoaded = callbackForAppLoadedB;

//console.log("prepareNextProcess()");

var files = [];
runAppX("extern.temp.app",files);
}

function attemptLoadApp(appLink,options,files,multi_window,appTitle,appName,appGeometry,waitForAppToRespond,showThumbnailPreview) {

               /*var appObj = {
          id : runningID,
          name : appTitle,
          physicalLocation : "../apps/",
          realID : appName,
          multi_window : multi_window,
          windowObject : new_win,
        options: options
      };*/

var runningAppTemp = currentTempApp;
var appObj = runningAppTemp.windowObject.sys.getInfo("ids");
var appObjNew = currentTempAppNew;
currentTempApp = null;

console.log("runningAppTemp :",runningAppTemp);

appObj.name = appName;
appObj.realID = appTitle;
appObj.multi_window = multi_window;
appObj.options = options;
appObj.options.min_width = 260;
appObj.options.min_height = 580;

console.log("before trying to add things");
appObjNew.name = appName;
appObjNew.title = appName;
appObjNew.realID = appTitle;
appObjNew.multi_window = multi_window;
appObjNew.options = options;
appObjNew.options.min_width = 260;
appObjNew.options.min_height = 580;
appObjNew.sysWinId = runningAppTemp.windowObject.sysWinId;

runningAppTemp.windowObject.sys.setInfo("midsm",appObj);
runningAppTemp.windowObject.sys.setInfo("midsm2",appObjNew);

updateExplorebar();
console.log("trying to add things");
if (appTitle != "extern.itai.app" && appTitle != "extern.hud.app")
	addAppToExploreBar(appObjNew);
else if (appTitle == "extern.itai.app")
	itaiInstancePos = runningApps.length-1;
else {
	hudInstancePos =  runningApps.length-1;
	updateHudInstance();
}
	



console.log("checking for files 2: ",files);
runningAppTemp.windowObject.filesToOpen = files;
runningAppTemp.windowObject.appGeometry = appGeometry;
runningAppTemp.windowObject.waitForAppToRespond = waitForAppToRespond;
runningAppTemp.windowObject.showThumbnailPreview = showThumbnailPreview;
console.log("checking for files 2 App: ",runningAppTemp.windowObject);
//console.log("app object",runningApps[runningApps.length-1].windowObject.sys.getInfo("ids"));

//setTimeout(function(){ //To allow animations to happen


//$( runningApps[runningApps.length-1].windowObject.window.document.getElementById("main")).append('<iframe id="appContainer" src="../../'+appLink+'" frameborder="0" partition="persist:trusted" style="    position: absolute; width: 100%; height: 100%;" allownw class="appInstance hiddenOpacity"> </iframe>');

	urlToLoadNext = "../../"+appLink;
	
	runningAppTemp.windowObject.appName = appName;

	runningAppTemp.windowObject.initWindow("../../"+appLink);

	runningAppTemp.windowObject.showDevToolsX = jQuery.extend( true, {}, runningAppTemp.windowObject.showDevTools);

	//runningApps[runningApps.length-1].windowObject.showDevTools = "";

runningAppTemp.windowObject.showAppDevTools = function() {
	//var test = new_win.window.document.getElementById("appContainer");
	console.log("teest");//,this
	//this.showDevTools = "";

	console.log("teest2",this.showDevTools);

	console.log("teest3",this.showDevToolsX);
		//console.log("teest2",this);//,this

	//this.showDevTools(this.instance);
	//win.showDevTools();
}




			$( runningAppTemp.windowObject.window.document.getElementById("appContainer")).load(function() {

		this.appInstance.windowObject.instance = this;

		if (this.appInstance.realID != "extern.files.app")
			this.appInstance.windowObject.loadedApp = true;


		$(this.appInstance.windowObject.window.frames.document).contents().find("head")
      .append($("<style type='text/css'>  .btn { border-color: "+winButtonProperties.borderColor+" !important;}  </style> <link href='../../../Shared/CoreCSS/scrollbar.css' rel='stylesheet'>"));

		//console.log("ready App",runningApps[runningApps.length-1]);

		//console.log("this.windowInstance",this.windowInstance);

/*runningApps[runningApps.length-1].windowObject.windowInstances = [];

runningApps[runningApps.length-1].windowObject.windowInstances.push(this);*/ //No need for this, waste of memory and resources for now
		var thisAppInstance = this;
		if ((files !=null) && (this.appInstance.realID != "extern.files.app"))
			if (files.length != 0) {
         		thisAppInstance.appInstance.windowObject.onOpenFiles(files);
			thisAppInstance.appInstance.windowObject.focus();
			
			}
		$(thisAppInstance).removeClass("hiddenOpacity");
		//setTimeout(function(){ $(thisAppInstance).removeClass("hiddenOpacity");}, 100);
		//console.log("this app",this);
		//setTimeout(function(){
		$(this.appInstance.windowObject.close_button).removeClass("hiddenOpacity");

	$(this.appInstance.windowObject.minimize_button).removeClass("hiddenOpacity");

	$(this.appInstance.windowObject.maximize_button).removeClass("hiddenOpacity");
		//}, 200);

//console.log("executed IFRAME");

    			});

//console.log("runningApps",runningApps);

			//}, 100);



		if (appLink == "apps/extern.photos.app/index.html") {
		//nw.Window.get().evalNWBin(new_win.window.frames, '/usr/eXtern/iXAdjust/apps/extern.photos.app/js/binary.bin');
		//console.log("imgs attempt");
		}
  
  
  //console.log("APP LINK",appLink);

		var currentWin = runningAppTemp.windowObject;
  
  
  		if (appLink == "apps/extern.itai.app/index.html") {
		  currentWin.runningApps = runningApps;
		  currentWin.adaptiveBlurEnabled  = function () {
			return adaptiveBlur;
		}

		}

		  currentWin.getAllNews = function () {
			return allActiveNews;
		}
  
		//console.log("appName",options);
		currentWin.title = appName;
               
               function reqAcc(pssw) {
                   if (pssw=="awqasddcme,,s") {
                        //Give the Welcome App extra system access. This is a dangerous way FIXME
                           console.log("EXTRA PERMS",currentWin);
                           currentWin.runningApps = runningApps;
                           currentWin.enableNewsSources = enableNewsSources;
			   currentWin.setUpForInstall = function () {
				
				systemSetupCompleted = true;
								localStorage.setItem('systemSetupCompleted', JSON.stringify(systemSetupCompleted));
				}

				currentWin.doneUserSetup = function () {
					console.log("setup done");
					userSetupCompleted = true;
					localStorage.setItem('userSetupCompleted', JSON.stringify(userSetupCompleted));
				}

			   currentWin.finishedSetUp = function () {
				runningApps[0].windowObject.show();
				
				systemSetupCompleted = true;
				//setTimeout(function(){ runApp("extern.files.app",files); }, 1000);
				localStorage.setItem('systemSetupCompleted', JSON.stringify(systemSetupCompleted));
				setTimeout(function(){ chrome.runtime.reload(); }, 1000); //FIXME temporary fix
				
				/*$(runningApps[0].windowObject.window.document.getElementById("mainBar")).removeClass("hidden");
				$(runningApps[0].windowObject.window.document.getElementById("mainBar")).removeClass("hiddenOpacity");
				$(runningApps[0].desktopObject.window.document.getElementById("deskStacksContainter")).removeClass("hiddenOpacity");

				runningApps[0].windowObject.canOpenHub = true;
				runningApps[0].windowObject.loadExplorebar();*/
				
				//runApp("extern.files.app",files);
			};

                           currentWin.setUserDetails = setUserDetails;
				currentWin.confirmUserDetails = function (returnedResults) {
					console.log("chang calledA");
					console.log("chang called",currentWin.appCommsChannel);
					currentWin.appCommsChannel.postMessage({
						type: "confirm-user-details",
						returnedResults: returnedResults
					});
				}
			   
                       
                   }
                   if (pssw=="awqas,,mns") {
                       currentWin.runningApps = runningApps;
                   }
               }
               
               if (appLink == "apps/extern.welcome.app/welcome.html" || appLink == "apps/extern.tips.app/index.html") {
				   currentWin.loadWeatherStats = loadWeatherStats;
                   reqAcc("awqasddcme,,s");
				   if (appLink == "apps/extern.welcome.app/welcome.html") {
					   //currentWin.width = screen.width;
					   //currentWin.height = screen.height;			
					   //runningApps[0].windowObject.hide();
				   }
		}

               if (appLink == "apps/extern.store.app/index.html")
                   reqAcc("awqas,,mns");
  
  
  
  
  

//$(new_win.window.document.getElementsByTagName("IFRAME")[0]).addClass("hidden");




//console.log("iframe",new_win.window.document.getElementsByTagName("IFRAME"));



runningAppTemp.windowObject.appLink = appLink;



		if (options.show) {
			////console.log("trying animating");
			//showApp(new_win);
			//runningApps[runningApps.length-1].windowObject.show();
			//new_win.minimize();
			//new_win.minimized = true;

			//setTimeout(function(){ 

	//console.log("ooptions",options);
	var min_height = 500;
	var min_width = 500;

	if (options.min_width != null)
		min_width = options.min_height;

	if (options.min_height != null)
		min_height = options.min_height;

	/*if (options.width != null)
		runningApps[runningApps.length-1].windowObject.width = options.width;

	if (options.height != null)
		runningApps[runningApps.length-1].windowObject.height = options.height;*/

	if (appLink == "apps/extern.welcome.app/welcome.html"){
		//runningApps[runningApps.length-1].windowObject.width = screen.width;
		//runningApps[runningApps.length-1].windowObject.height = screen.height;
	}

	/*if ((options.min_height != null) || (options.min_width != null))
		runningApps[runningApps.length-1].windowObject.setMinimumSize(min_width,min_height);*/

		//runningApps[runningApps.length-1].windowObject.minimize(); FIXME Restore this

			

	//win.hide();
	

	//new_win.setPosition("centre");

			//new_win.width = setWidth;
			//new_win.height = setHeight;
			//showApp(new_win);
			//new_win.setPosition("centre");
			//}, 100);
			
			/*setTimeout(function(){ 
				//new_win.y = (screen.height - new_win.height) ;
			 runningApps[runningApps.length-1].windowObject.x = Math.floor(((screen.width/2) - (runningApps[runningApps.length-1].windowObject.width/2)));
            		runningApps[runningApps.length-1].windowObject.y = Math.floor(((screen.height/2) - (runningApps[runningApps.length-1].windowObject.height/2)) - (20));
	//console.log("screen.height",screen.height);
	//console.log("new_win.height",runningApps[runningApps.length-1].windowObject.height);
	//console.log("new_win.width",runningApps[runningApps.length-1].windowObject.width);
	$(runningApps[runningApps.length-1].windowObject.window.document.body).removeClass("zeroOpacity");
			//showApp(new_win);
			runningApps[runningApps.length-1].windowObject.setPosition("centre");
			//console.log("centre");
			}, 5);*/

			//setTimeout(function(){ 

			//new_win.outerBodyBackground

			//setTimeout(function(){ $.bgAdjust(new_win); }, 500);

			//$.bgAdjust(runningApps[runningApps.length-1].windowObject);


			//runningApps[runningApps.length-1].windowObject.showDevTools();

			//console.log("appLink",appLink);



			if (appLink == "apps/extern.files.app/index.html") {
			var nextProcessLoaded = false;
				if (nextFilesProcess != null) {
				console.log("next Files process loaded, attempting to show");
				//nextFilesProcess.focus();
				//nextFilesProcess.loadDrives();
				//console.log("nextProcess A",nextFilesProcess);
						//new_win.y = (screen.height - new_win.height) ;
			 //nextFilesProcess.x = Math.floor(((screen.width/2) - (nextFilesProcess.width/2)));
            		//nextFilesProcess.y = Math.floor(((screen.height/2) - (nextFilesProcess.height/2)) - (20));
					//console.log("nextProcess AB",nextFilesProcess);
//var execSync = require('child_process').execSync;
					//console.log("nextFilesProcess.sysWinId",nextFilesProcess.sysWinId);
					//var moveToCuurentDesk = execSync("wmctrl -i -R "+nextFilesProcess.sysWinId);


			var winToOpen = nextFilesProcess;

			

if (nextFilesProcess.sysWinId != null) {
	/*console.log("nextFilesProcess has sysWinId");
    var exec = require('child_process').exec,
                   child;
            child = exec("wmctrl -i -R "+nextFilesProcess.sysWinId,function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        

    }   

	//console.log("nextFilesProcessX",nextFilesProcess.sysWinId);
					//console.log("moveToCuurentDesk",moveToCuurentDesk);

					console.log("trying to show files App");
					
					showApp(winToOpen);
					//setTimeout(function(){showApp(winToOpen);    }, 8000);  
});*/
					console.log("trying to show files App: ",winToOpen);
					
					
}


					
					
					//console.log("nextProcess B",nextFilesProcess);


					if (files !=null) {
						if (files.length != 0) {
							console.log("files A",files);
							console.log("detectedMountedDrives.length",detectedMountedDrives.length);
							nextProcessLoaded = true;
							//setTimeout(function(){
         						winToOpen.onOpenFiles(files);
         						
							nextFilesProcess = runningAppTemp.windowObject;
							nextFilesProcess.filesToOpen = null;
							console.log("nextFilesProcess",nextFilesProcess);
							updateExplorebarFilesInstance();
							//}, 100);
						}
						
					}
					
					showApp(winToOpen);
					console.log("set to true");
					nextFilesProcess.loadedApp = true;

				}
				
				if (!nextProcessLoaded) {
					console.log("nextF= files process not loaded, setting this as next: ",runningAppTemp.windowObject)
					nextFilesProcess = runningAppTemp.windowObject;
					updateExplorebarFilesInstance();
					//console.log("don't show app",appLink);
				}
			} else {
				//new_win.y = (screen.height - new_win.height) ;
			 runningAppTemp.windowObject.x = Math.floor(((screen.width/2) - (runningAppTemp.windowObject.width/2)));
            		runningAppTemp.windowObject.y = Math.floor(((screen.height/2) - (runningAppTemp.windowObject.height/2)) - (20));
			//var execSync = require('child_process').execSync;
			//var moveToCuurentDesk = execSync("wmctrl -i -R "+runningApps[runningApps.length-1].windowObject.sysWinId);

		var winToOpen = runningAppTemp.windowObject;

if (runningAppTemp.windowObject.sysWinId != null) {
/*
console.log("run App called");
    var exec = require('child_process').exec,
                   child;
            child = exec("wmctrl -i -R "+runningAppTemp.windowObject.sysWinId,function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        

    }    
		console.log("nextFilesProcessXA",winToOpen.sysWinId);

		

		//setTimeout(function(){showApp(winToOpen);    }, 2000); //FIXME: PUT THIS BACK
});*/
showApp(winToOpen);
}



			}

	//FIXME Removed from new change 





console.log("lets try hereA",appLink);


			
			//new_win.setPosition("centre");
			//console.log("centre");
			//}, 5);

			setTimeout(function(){ 

		if (appLink != "apps/extern.welcome.app/welcome.html" && appLink != "apps/extern.itai.app/index.html") {


                   //addAppToExploreBar(appObj);
			if (appLink != "apps/extern.files.app/index.html") {
				//runningApps[0].windowObject.loadDrives();
				//runningApps[0].windowObject.makeAppVisible(runningApps[runningApps.length-1].windowObject.sys.getInfo("ids").id);
			}
			prepareNextProcess();
			
			} else {
				prepareNextProcess(runWelcomeApp);
				//runApp('extern.welcome.app',files);
				//console.log("lets try hereB",runningApps);
				//setTimeout(function(){ runApp('extern.welcome.app',files); }, 5000);
			}

			
			console.log("runningApps.length",runningApps.length);// Come here

			}, 400);
			
		} else {

			prepareNextProcess();
		}

//runningApps[runningApps.length-1].windowObject.show();

//runningApps[runningApps.length-1].windowObject.showDevTools();

//showApp(runningApps[runningApps.length-1].windowObject);



			//console.log("runningApps",runningApps);

}


//win.showDevTools();




function RunAppDev(appLocation) {

jsApp = JSON.parse(fs.readFileSync(appLocation+"/package.json", 'utf8'));
jsApp.id = "extern.liverun.app";
appID = jsApp.id;
//openApp(appID);

//console.log("LOADING APP in DEV: "+appLocation,jsApp);

//fs.copy(appLocation, '/usr/eXtern/iXAdjust/apps/'+appID, function (err) {

if (appLocation.indexOf('/usr/eXtern/systemX/apps/') != 0) {
		if (!fs.existsSync("/usr/eXtern/systemX/apps/extern.liverun.app")) {
			fs.mkdirSync("/usr/eXtern/systemX/apps/extern.liverun.app");
		}
ncp(appLocation, '/usr/eXtern/systemX/apps/extern.liverun.app', function (err) {
  		if (err) {
    			console.error(err);
  		} else {
   			 //console.log("success!");
			//getDirs("apps",addDefault);
for (var ax = 0; ax < apps.length; ax++) {
if (apps[ax].id == appID)
apps.splice(ax,1);

}
jsApp.devApp = true;
jsApp.installed = false;
apps.push(jsApp);

openApp(appID);
//console.log("success2",jsApp);
			

  		}
});
} else {
for (var ax = 0; ax < apps.length; ax++) {
if (apps[ax].id == appID)
apps[ax].devApp = true;
}
openApp(appID);
}

}

var currentWinId;

function showApp(new_winss) {
var new_wins = new_winss;
currentWinId = new_wins.sysWinId;
console.log("now in ShowApp",new_winss);
//console.log("currentWinIdA",currentWinId);
$(new_winss.win_main_title).text("showShadowBorderMxs");

//executeNativeCommand('wmctrl -i -R '+new_wins.sysWinId, function () {new_winss.showWindow();});
new_winss.showWindow();


if ((new_winss.appLink != "apps/extern.welcome.app/welcome.html")) {
	//$(new_wins.window.document.body).removeClass("hidden");
}

if ((new_winss.appLink == "apps/extern.files.app/index.html")) {
	//new_winss.loadDrives();
}

//$(new_win.win_main_title).text("hidehadowBorderMxs");



//$(new_winss.win_main_title).text("hidehadowBorderMxs");

setTimeout(function(){ 
    //$(new_winss.win_main_title).text("hidehadowBorderMxs");
	//new_winss.maximize();
    }, 3000);

setTimeout(function(){ 
	//new_winss.restore();
    //$(new_winss.win_main_title).text("showShadowBorderMxs");
    }, 10000);


//new_wins.show();

if (runningApps[0].windowObject.makeAppVisible != null) {
	runningApps[0].windowObject.makeAppVisible(new_winss.sys.getInfo("ids").id);
}

//console.log("showApp() called");
//new_win.showDevTools();


// Apply window visual settings
/*$(new_wins.close_button).css('opacity', closeButtonProperties.opacity);
$(new_wins.outerBodyBackground[0]).next().css('background-color', windowBackgroundColor);
$(new_wins.outerBodyBackground[0]).css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

$(new_wins.outerBodyBackground[0]).next().css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

$(new_wins.outerBodyBackground[0]).next().removeClass("hiddenOpacity");
			$(new_wins.outerBodyBackground[0]).removeClass("hiddenOpacity");
		$(new_wins.outerBodyBackground[0]).parent().removeClass("zeroOpacity");


$(new_wins.window.document.body).removeClass("zeroOpacity");*/

console.log("new_wins.sysWinId",new_wins.sysWinId);
/*
setTimeout(function(){
console.log("currentWinIdXM",currentWinId);
var execSync = require('child_process').execSync;
var removeFromPageSkipper = execSync('wmctrl -i -r '+currentWinId+' -b remove,skip_pager');

}, 1000);*/
/*
setTimeout(function(){

console.log("currentWinIdB",currentWinId);

    var exec = require('child_process').exec,
                   child;
            child = exec('xprop -id '+currentWinId+' -f _NET_WM_NAME 32a -set _NET_WM_NAME "hb"',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
    

    }       
});

    var exec = require('child_process').exec,
                   child;
            child = exec('xprop -id '+currentWinId+' -f WM_NAME 32a -set WM_NAME "hb"',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
    

    }       
});

	}, 5000);*/
//$.bgAdjust(new_wins);

//setTimeout(function(){ $.bgAdjust(new_wins); }, 500);
//setTimeout(function(){ $.bgAdjust(new_wins); }, 5000);
//$(new_win.window.document.body).addClass("opacityAnimation");
//setTimeout(function(){ $(new_win.window.document.body).removeClass("zeroOpacity"); }, 2000);

//console.log("tried to show");
//win.hide();

}


function openApp(appName,files,appGeometry,AppObj) {

	console.log("openApp: ",appName);

if (appName.indexOf("[[{linux.}]") == 0) {

	console.log("appName open",appName);

	//console.log("$(window).scrollTop(): ",$(window).scrollTop());
	//console.log("$(AppObj).offset(): ",$(AppObj).offset())
//win.hide();
	//runApp(appName,files,null,appGeometry);
	console.log("apps: ",apps)
	const appObj = apps.find(appx => appx.id === appName)

	let startPos = AppObj ? $(AppObj).offset() : null;

	$(AppObj).addClass("hiddenOpacity");

	parent.launchApp(appName,files, appGeometry, startPos, appObj, `apps/${appName}/${appObj.main}`, function () {
		$(AppObj).removeClass("hiddenOpacity");
	});



    var exec = require('child_process').exec,
                   child;
            child = exec("LC_ALL=C & "+appName.replace("[[{linux.}]","")+"&",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
    if (error !== null) {
      //console.log('exec error: ' + error);
    } else {
        if (stdout.indexOf("failed") == -1) {
		//win.hide();
		//win.hideFixed();
		win.opened = false;
            //console.log("successfully unmounted");
            //listAvailableDrives();
        } //else
            //console.log("failed to unmount");
    }       
});
/*
//var proc = require('child_process').spawn(appName.replace("[[{linux.}]",""));
var exec = require('child_process').exec;
var child = exec(appName.replace("[[{linux.}]","")+"&");
child.stdout.on('data', function(data) {
    console.log('stdout: ' + data);
});*/
//FIXME -x win.hide();
//setTimeout(function(){ win.show(false); }, 5000);
//win.close();
} else if (appName == "extern.terminal.app"){
	var childProcess = require('child_process');
        var spawn = childProcess.spawn;
var childx = spawn("/usr/eXtern/systemX/apps/extern.terminal.app/main/terminal  --enable-transparent-visuals --disable-gpu");

} else if (appName == "extern.web.app"){
	var childProcess = require('child_process');
        var spawn = childProcess.spawn;
var childx = spawn("/usr/eXtern/systemX/apps/extern.web.app/Nyika-6.0.0-nightly.3.AppImage");

} else if (appName == "extern.video.app"){

	console.log("1. trying to launch video");
	//executeNativeCommand("/usr/eXtern/NodeJs45/nw /usr/eXtern/systemX/apps/extern.video.app/main '/media/extern/Seagate Expansion Drive/Files/Plex Backup/TV Shows/Nikita/Season 1/Nikita.S01E01.Pilot.1080p.10bit.BluRay.AAC5.1.HEVC-Vyndros.mkv'");
	
	var childProcess = require('child_process');
        var spawn = childProcess.spawn;

        if (!Array.isArray(files)) {
	var filesString = files;
	files = [];
	if (filesString !== undefined)
		files.push(filesString);
		
	}
	var splitArgs = ["/usr/eXtern/systemX/apps/extern.video.app/main"];
	splitArgs = splitArgs.concat(files);
	
	console.log("trying to launch video");
var childx = spawn("/usr/eXtern/NodeJs45/nw", splitArgs);

} else {



if (!Array.isArray(files)) {
	var filesString = files;
	files = [];
	if (filesString !== undefined)
		files.push(filesString);
}

	console.log("appName open",appName);

	//console.log("$(window).scrollTop(): ",$(window).scrollTop());
	//console.log("$(AppObj).offset(): ",$(AppObj).offset())
//win.hide();
	//runApp(appName,files,null,appGeometry);
	const appObj = apps.find(appx => appx.id === appName)

	let startPos = AppObj ? $(AppObj).offset() : null;

	$(AppObj).addClass("hiddenOpacity");

	parent.launchApp(appName,files, appGeometry, startPos, appObj, `apps/${appName}/${appObj.main}`, function () {
		$(AppObj).removeClass("hiddenOpacity");
	});

	

}
    
    
    
}

function addRecentApp(appName) {
    realAppName = appName.replace("extern.","").replace(".app","");
//console.log("REAL NAME",realAppName);
if ($( "[name='"+realAppName+"']" ).length != 0) { //be able to run non-installed apps. i.e skip
    if (typeof accessedApps[realAppName] !== 'undefined')
    {
        accessedApps[realAppName] += 1;
    }
    else
    {
        accessedApps[realAppName] = 1;
    }
    //$("#most-accessed-b").empty();
    //console.log("Detected name: #",$( "[name='"+realAppName+"']" ));
    $( "[name='"+realAppName+"']" )[$( "[name='"+realAppName+"']" ).length-1].attributes.Accessed.value = accessedApps[realAppName];
    localStorage.setItem('accessedApps', JSON.stringify(accessedApps));
//console.log("Accessed apps GET",accessedApps);
    //console.log("Accessed apps SET",JSON.parse(localStorage.getItem('accessedApps')));
appsortAppsByAcessList();
}

	
    //appsortAppsByAcessList();
    //appCategoryList(); //FIXME
}

function testingMe() {
    //console.log("IT WORKS!");
}

function checkAppToRunQueue() {
	if (readyToRunApp && configsReady) {
		if (appsToRunQueue.length > 0) {
			var appName = appsToRunQueue[0].appName;
			var files = appsToRunQueue[0].files;
			var notificationID = appsToRunQueue[0].notificationID;
			var appGeometry = appsToRunQueue[0].appGeometry;
			console.log("try this: ",appName);
			console.log("appGeometryC: ",appGeometry);
			appsToRunQueue.shift(); //Remove App from queue
	runAppX(appName,files,notificationID,appGeometry);
			
		}
	}
	console.log("appsToRunQueuex: ",appsToRunQueue);
}

var restoredEvent = new Event('restored');



function runApp(appName,files,notificationID,appGeometry) {
	console.log("appGeometryB: ",appGeometry);
	if (readyToRunApp && appsToRunQueue.length == 0 && configsReady) {
		console.log("fine to launch this",appName);
		runAppX(appName,files,notificationID,appGeometry);
	} else {
		var appToRunObj = {
			appName: appName,
			files: files,
			notificationID: notificationID,
			appGeometry: appGeometry
		}
		appsToRunQueue.push(appToRunObj);
		console.log("appsToRunQueue: ",appName);
	}
}

function runAppX(appName,files,notificationID,appGeometry) {
    
    console.log("runApp: ",appName);
	console.log("appGeometryA: ",appGeometry);
	if (appName == "extern.temp.app") {
		readyToRunApp = false;
		configsReady = false;
		console.log("NOT prepared for the next app");
	}
    
    function directLaunch(appLink,options,files,multi_window,appTitle) {
        if (files !=null) {
        if (files.constructor === Array) {
            //console.log("IT IS AN ARRAY");
        } else {
            //console.log("NOT AN ARRAY");
            
        var filesArray = []
    filesArray.push(files);
            files = filesArray;
            
        }
        }
		//This was supposed to improve animations
		/*var setWidth = options.width;
		var setHeight = options.height;
		options.width = 5;
		options.height = 5;*/

	//var temporaryOptions = _.clone(options);

	console.log("files xp:",files);

	    
    var temporaryOptions = {
  	height: 1,
        width: 1,
        show: true,
        title: "Untitled51453567896"+winIdCounter,
        transparent: true,
        frame: false,
        always_on_top: true,
	/*new_instance: true,*/ //Waiting for nw to fix their bug with this
        show_in_taskbar: false,
	new_instance: true,
	visible_on_all_workspaces: true
};

	//temporaryOptions["visible-on-all-workspaces"] = true;
//win.setShowInTaskbar(show)

	/*console.log("options",options);
	if (temporaryOptions.width != null)
		temporaryOptions.width = 1;

	if (temporaryOptions.height != null)
		temporaryOptions.height = 1;

	if (temporaryOptions.min_width != null)
		temporaryOptions.min_width = 1;

	if (temporaryOptions.min_height != null)
		temporaryOptions.min_height = 1;*/

           nw.Window.open("Shared/CoreWindow/index.html",temporaryOptions,function(new_win) {
               //new_win.show();
		/*Auto maximize and restore fixes the maximize animation
		 that doesn't work on first try. A Bug in compiz :( */
		

          new_win.on('minimize', function() {
		console.log("minimized: ",new_win.sys.getInfo("ids2"));

		//minimizeAppInExploreBar(new_win.sys.getInfo("ids2"));


	});

          new_win.on('focus', function() {
		console.log("focused: ",new_win.sys.getInfo("ids2"));

		focusAppInExploreBar(new_win.sys.getInfo("ids2"));


	});

          new_win.on('blur', function() {
		//console.log("un focused: ",new_win.sys.getInfo("ids2"));

		unfocusAppInExploreBar(new_win.sys.getInfo("ids2"));


	});
		new_win.minimize();
		setTimeout(function(){ new_win.width = 1700; }, 500); //Give time for minimize animation to finish


const appCommsChannel = new BroadcastChannel("eXternOSApp"+new_win.cWindow.id); //Comms channel between process manager and this Aoo


		new_win.appCommsChannel = appCommsChannel;
		function updateAppGlobalVariables (updateDrives) {
	console.log("init send",enabledSources);
			appCommsChannel.postMessage({
				type: "init-objects",
				internalId: new_win.sysWinId,
				detectedMountedDrives: detectedMountedDrives,
				allActiveNews: allActiveNews,
				enabledSources: enabledSources,
				osVersion: sysOs,
				fileTypesApps: fileTypesApps,
				allInstalledApps: allInstalledApps,
				allLegacyApps: allLegacyApps,
				updateDrives: updateDrives,
				improvePerfomanceMode: improvePerfomanceMode,
				filesInClipboard: filesInClipboard
			});
		}

	       //new_win.resolveFileType = resolveFileType;

		function showWindow () {
			console.log("init send");
			appCommsChannel.postMessage({
				type: "show-window"
			});
			//win.hide();
			//win.opened = false;
			//makeAppVisibleInExploreBar(new_win.sys.getInfo("ids").id);
		}

		new_win.callMinimizeEvent = function() {
			appCommsChannel.postMessage({
				type: "minimize-window"
			});
		}

		new_win.showWindow = showWindow;


		new_win.updateAppGlobalVariables = updateAppGlobalVariables;

	new_win.onOpenFiles = function(files) { 

			console.log("on open files: ",files);

			appCommsChannel.postMessage({
				type: "open-files",
				files: files
			});

	};

	new_win.packageCompiledCallback = function(res) {
		appCommsChannel.postMessage({
				type: "package-compiled",
				result: res
			});
	}


	new_win.audioPlaybackControl = function (request) {
		console.log("sending playback controlsx");
		appCommsChannel.postMessage({
				type: "audio-playback-control",
				request: request
			});
	}

	appCommsChannel.onmessage = function (ev) {
		console.log("appCommsChannel",ev);
		
		if (ev.data.type == "files-in-clipboard") {
			filesInClipboard = ev.data.data;
			appsUpdateData();
		}

		if (ev.data.type == "toggle-network-options") {
			toggleNetworkOptions();
		}

		if (ev.data.type == "app-opened") {
			canHideHub = true;
			//win.hide();
			setTimeout(function(){ win.hideFixed(); }, 100);
			makeAppVisibleInExploreBar(new_win.sys.getInfo("ids").id);
		}

		if (ev.data.type == "update-news-sources") {
			enableNewsSources(ev.data.sources);
		}

		if (ev.data.type == "add-new-stack") {
			addNewStack(ev.data.stackLocation);
		}

		if (ev.data.type == "setup-for-install") {
			//reqAcc("awqasddcme,,s");
			new_win.setUpForInstall();
		}

		if (ev.data.type == "done-user-setup") {
			//reqAcc("awqasddcme,,s");
			console.log("done-user-setup")
			new_win.doneUserSetup();
			
		}

		if (ev.data.type == "finished-setup") {
			//reqAcc("awqasddcme,,s");
			console.log("finish-setup");
			new_win.finishedSetUp();
		}

		if (ev.data.type == "set-user-details") {
			//reqAcc("awqasddcme,,s");
			new_win.setUserDetails(ev.data.userDetails,ev.data.pass,new_win.confirmUserDetails);
		}

		if (ev.data.type == "run-app-dev") {
			console.log("run-app-dev: ",ev.data.appLocation);
			RunAppDev(ev.data.appLocation);
		}

		if (ev.data.type == "app-ready") {
			
			console.log("app ready: ",new_win.filesToOpen);
			//console.log("direct: ",filesToOpen);
        			/*if (new_win.filesToOpen !=null)
					if (new_win.filesToOpen.length != 0)
         		 		new_win.onOpenFiles(new_win.filesToOpen);*/
			
		}

		if (ev.data.type == "requesting-init-settings") {
			readyToRunApp = true;
			console.log("prepared for the next app");
			updateAppGlobalVariables();
			appCommsChannel.postMessage({
				type: "wallpaper-data",
				data: document.body.children[0].style.backgroundImage
			});
			checkAppToRunQueue();
		}

		if (ev.data.type == "set-as-wallpaper") {
			addCustomWallpaper(ev.data.newWallpaper,ev.data.setAsWallpaper,ev.data.wallpaperName,ev.data.wallpaperArtist);
		}

		if (ev.data.type == "update-audio-notification") {
			console.log("show playback menu-sys");
			updateAudioInfoNotification(ev.data.data,new_win.sys.getInfo("ids2"),new_win.audioPlaybackControl);
		}

		if (ev.data.type == "open-app") {
			openApp(ev.data.appName,ev.data.files,ev.data.appGeometry);
		}

		if (ev.data.type == "package-app") {
			compressApp(ev.data.appDirectory,ev.data.apDestination,new_win.packageCompiledCallback);
		}

		//new_win.newNotification = function (notificationText, notificationButtons, notificationTimeOut,notificationIcon) {
		if (ev.data.type == "new-notification") {
			console.log("sending notification from system");

			var notificationText = ev.data.notificationText;
			var notificationButtons = ev.data.notificationButtons;
			var notificationTimeOut = ev.data.notificationTimeOut;
			var notificationIcon = ev.data.notificationIcon;

		//notificationAppInfo, 

		var appObject = new_win.sys.getInfo("ids");

		if (notificationIcon == null)
			var notificationIcon = appObject.physicalLocation+appObject.realID+"/"+appObject.options.icon;

		console.log("notificationIcon: ",notificationIcon);

		//runningApps[0].windowObject.newNotification(new_win.sys.getInfo("ids"),notificationText, notificationButtons, notificationTimeOut,notificationIcon);

			console.log("lets send notification");

		var appObject = new_win.sys.getInfo("ids");

		var notificationAppInfo = {
			id: appObject.id,
			name: appObject.name,
			realID: appObject.realID
		}

			extrabarCommsChannel.postMessage({
				type: "new-notification",
				appId: notificationAppInfo,
				notificationText: notificationText,
				notificationButtons: notificationButtons,
				notificationTimeOut: notificationTimeOut,
				notificationIcon: notificationIcon
			});

		
			
		}

		if (ev.data.type == "closed") {
			console.log("closed called");
       			var neededID = new_win.sys.getInfo("ids").id;
			

	if (new_win.sys.getInfo("ids").realID == "extern.liverun.app") {
		rimraf("/usr/eXtern/systemX/apps/extern.liverun.app",function () {
		if (!fs.existsSync("/usr/eXtern/systemX/apps/extern.liverun.app")) {
			fs.mkdirSync("/usr/eXtern/systemX/apps/extern.liverun.app");
		}
	  	
		});
	}

       //runningApps[0].windowObject.removeApp(new_win.sys.getInfo("ids")); FIXME: restore!
       for (var n = 0; n < runningApps.length; n++) {
           if (runningApps[n].id == neededID) {
		removeAppFromExploreBar(runningAppsNew[n-1]);
               runningApps.splice(n,1);
		runningAppsNew.splice(n-1,1);
               //runningAppsNew.splice(n,1);
               updateRunningApps();
               //console.log("FOUND AND REMOVED, final list",runningApps);
               break;
               //lel
           }
       }
      //win.unminimize();

	new_win = null; //Garbage collection
		}
	}

		new_win.initWindow = function (appSRC) {
			canHideHub = false;
			console.log("win.appGeometry: ",appSRC);
			appCommsChannel.postMessage({
				type: "load-App",
				appName: new_win.appName,
				appLocation: appSRC,
				appGeometry: new_win.appGeometry,
				argv: new_win.filesToOpen,
				waitForAppToRespond: new_win.waitForAppToRespond,
				showThumbnailPreview: new_win.showThumbnailPreview
			});
		}

		new_win.setShowInTaskbar(false);
		//new_win.maximize();
		//new_win.restore();
		new_win.minimize();
		//new_win.minimize();

		new_win.fixingMaximizeBug = false; //Used to avoid triggering restore after maximize when auto restore and maximize are called to fix the "black window" bug
		

new_win.minimize();

		var execSync = require('child_process').execSync;

		var allNewAppProcesses = execSync("wmctrl -l").toString().split("\n");

		//console.log("allNewAppProcesses",allNewAppProcesses);
		var foundsss = false;
		for (var i = allNewAppProcesses.length-1; i > -1; i--) {
			if (allNewAppProcesses[i].indexOf("Untitled51453567896"+winIdCounter) != -1) {
				console.log("fouund",allNewAppProcesses[i].split("  ")[0]);
				foundsss = true;
				new_win.sysWinId = allNewAppProcesses[i].split("  ")[0].split(" ")[0];
				executeNativeCommand('wmctrl -i -r '+new_win.sysWinId+' -b add,skip_pager');


				//new_win.minimize();

			//setTimeout(function() {
				executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_DOCK -id '+new_win.sysWinId);
    				//}, 5000);
				//new_win.hide();
				//executeNativeCommand('xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id '+new_win.sysWinId);
			}
		}
		winIdCounter++;

		if (!foundsss) {
			prepareNextProcess(); //lets try again
			win.close();
		}




   /* var exec = require('child_process').exec,
                   child;
            child = exec("wmctrl -l",function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {

		var allNewAppProcesses = stdout.split("\n");
        
		var foundsss = false;
		for (var i = allNewAppProcesses.length-1; i > -1; i--) {
			if (allNewAppProcesses[i].indexOf("Untitled51453567896"+winIdCounter) != -1) {
				//console.log("fouund",allNewAppProcesses[i].split("  ")[0]);
				foundsss = true;
				new_win.sysWinId = allNewAppProcesses[i].split("  ")[0];
			}
		}
		winIdCounter++;


    }       
});*/

		//var addToPageSkipper = execSync('wmctrl -i -r '+new_win.sysWinId+' -b add,skip_pager');

		//var testingd = execSync('wmctrl -i -r Untitled51453567896'+winIdCounter+' -b add,skip_pager');


		/*if (!foundsss) {
			console.log("retrying...");
			for (var i = allNewAppProcesses.length-1; i > -1; i--) {
			if (allNewAppProcesses[i].indexOf("New App") != -1) {
				//console.log("fouund",allNewAppProcesses[i].split("  ")[0]);
				foundsss = true;
				new_win.sysWinId = allNewAppProcesses[i].split("  ")[0];
			}
		}
		}*/

		//console.log("foundsss",foundsss);

		//new_win.hide();
               //console.log("NEW CALL");

		new_win.compressApp = compressApp;
               
               
		//new_win.closeDevTools();
		




		
               
              // new_win.open = function(link){};
  // And listen to new window's focus event
               new_win.fileTypesApps = fileTypesApps;
               new_win.apps = allInstalledApps;
	       new_win.resolveFileType = resolveFileType;


		//new_win.closeAllNotifications = function() { console.log("close notifs");};



		new_win.osVersion  = sysOs;


               

               
               //openApp;
               new_win.openApp = openApp;
	       new_win.RunAppDev = RunAppDev;
               
               

               
               
               
               
            var liveID = {
    get readOnlyProperty() { return runningID; }
};   
               
               new_win.liveID = liveID;
               
               var appObj = {
          id : runningID,
          physicalLocation : "../apps/",
          multi_window : multi_window,
          windowObject : new_win,
        options: options
      };

	var appObjNew = { //For New processes implementation
          id : runningID,
          physicalLocation : "../apps/",
          multi_window : multi_window,
          windowObject : {},
        options: options
      };

/*
appObj.name = appTitle;
appObj.realID = appName;
appObj.multi_window = multi_window;*/
               /*For testing purposes*/
               /*
               if (appName == "extern.files.app") {
                   setTimeout(function(){ 
               
          new_win.selectCustomFiles();
               
                   }, 1000);
               }*/
               
                     function appInfo(obj)
{
    this.getInfo=function(pass){ if (pass == "ids") {return obj;} else if(pass == "ids2") {return appObjNew;} else { return false;}}

    this.setInfo=function(pass,newObj){ if (pass == "midsm") {obj = newObj; return true;} else if (pass == "midsm2") {appObjNew = newObj; return true;} else { return false;}}
}

//var appIDs={id: appName, processID: runningID};

var sys = new appInfo(appObj);
               
               new_win.sys = sys;
      
      //min_but.addEventListener("click", appObj.windowObject.minimize, false);
      runningApps.push(appObj);
	currentTempApp = runningApps[runningApps.length-1];
	runningAppsNew.push(appObjNew);
	currentTempAppNew = runningAppsNew[runningAppsNew.length-1];
	updateExplorebar();
updateExplorebarGenericInstance();
      runningID++;
	configsReady = true;
      updateRunningApps();
	checkAppToRunQueue();
               
      /*console.log("Window object array: ",runningApps);
      console.log("Window APP LINK: ",appName);
      console.log("Window APP OPTIONS: ",options);*/
               
              /* if (appLink != "apps/extern.welcome.app/welcome.html" && appLink != "apps/extern.itai.app/index.html")
                   runningApps[0].windowObject.addApp(appObj);*/

	        new_win.mainWin = new_win;
/*
		var initRestore = false;
		new_win.on('restore', function() {
	console.log("restore: ",new_win.sysWinId);
	console.log("restore: ",initRestore);
		var internalId = new_win.sysWinId;
	if (!initRestore)
		initRestore = true
	else {
	if (internalId != null) {
	//$("#appContainer").removeClass("hiddenOpacity");
	//$("#outerBody").addClass("bg_settings");
	console.log("restored called");
	executeNativeCommand('xprop -f _NET_WM_WINDOW_TYPE 32a -set _NET_WM_WINDOW_TYPE _NET_WM_WINDOW_TYPE_NORMAL -id '+internalId);
	executeNativeCommand('wmctrl -i -r '+internalId+' -b add,stiky');
	executeNativeCommand('wmctrl -i -r '+internalId+' -b remove,skip_pager');
	console.log("setting blur... :",internalId);
	executeNativeCommand('xprop -f _KDE_NET_WM_BLUR_BEHIND_REGION 32c -set _KDE_NET_WM_BLUR_BEHIND_REGION 0 -id '+internalId);
	}
	}

});
	*/	
                   
  new_win.on('loaded', function() {


	


	if (!firstProcessLoaded) {
		firstProcessLoaded = true;
		//loadStartUpApps();
		setTimeout(function(){
		loadStartUpApps();
		}, 1000); //Delay
	}



//$(new_win.window.document.body).addClass("zeroOpacity");
//setTimeout(function(){ $(new_win.window.document.body).addClass("opacityAnimation");}, 100);

//FIXME: RESTORE: Removed for new version
/*
new_win.close_button = new_win.window.document.getElementById("close_button");

new_win.minimize_button = new_win.window.document.getElementById("minimize_button");

new_win.maximize_button = new_win.window.document.getElementById("maximize_button");

new_win.win_main_title = new_win.window.document.getElementById("winTitle");

new_win.drive_properties_win = new_win.window.document.getElementById("driveProperties");

      new_win.window.document.getElementById("closeDrivesPropertiesModalWindow").onclick = function() {
          $(new_win.drive_properties_win).fadeOut();
	$(new_win.drive_properties_win).parent().next().fadeTo( "fast" , 1);
	$(new_win.drive_properties_win).parent().addClass("hidden");
      };

      new_win.window.document.getElementById("closeDrivesPropertiesModalWindowX").onclick = function() {
          $(new_win.drive_properties_win).fadeOut();
	$(new_win.drive_properties_win).parent().next().fadeTo( "fast" , 1);
	$(new_win.drive_properties_win).parent().addClass("hidden");
      };


new_win.outerBodyBackground = new_win.window.document.getElementsByTagName("BACKGROUND");

*/
new_win.showDriveProperties = function (drive) {
	console.log("show drives called",drive);
	$(new_win.drive_properties_win).parent().removeClass("hidden");
	//$(new_win.drive_properties_win).fadeIn();
	console.log("make this transparent",$(new_win.drive_properties_win).parent().next());

	var mountedDrives = new_win.getMountedDrives();
	var driveToMount;

	console.log("all mounted drives",mountedDrives);

	for (var i = 0; i < mountedDrives.length; i++) {
		if (drive == mountedDrives[i].name) {
			console.log("found it ",mountedDrives[i]);
			console.log("lol",$(new_win.drive_properties_win).find( "#drivePieChart" ));
			driveToMount = mountedDrives[i];
			//console.log("do we have percentage",100-driveToMount.freePercentage);
			  $(new_win.drive_properties_win).fadeTo( "fast" , 1, function () {
				  setTimeout(function(){ 

		console.log("driveToMount.freePercentage: ",driveToMount.freePercentage);

showDispPieChart(100-driveToMount.freePercentage,$(new_win.drive_properties_win).find( "#drivePieChart" )); }, 50); //Added delay cos sometimes the pie chart would just not show up. So maybe even though this says it's fully visible it really isn't done?
			  });

			  $(new_win.drive_properties_win).parent().next().fadeTo( "fast" , 0.05);
			$(new_win.drive_properties_win).find("#propertiesDriveName").text(mountedDrives[i].label);
$(new_win.drive_properties_win).find("#propertiesDriveFs").text(mountedDrives[i].fstype);

			if (mountedDrives[i].protocol == "")
				$(new_win.drive_properties_win).find("#propertiesDriveProtocol").parent().addClass("hidden");
			else {
				$(new_win.drive_properties_win).find("#propertiesDriveProtocol").text(mountedDrives[i].protocol);
				$(new_win.drive_properties_win).find("#propertiesDriveProtocol").parent().removeClass("hidden");
			}

			if (mountedDrives[i].name == "sd_extern")
				$(new_win.drive_properties_win).find("#propertiesDriveInternalName").parent().addClass("hidden");
			else {
				$(new_win.drive_properties_win).find("#propertiesDriveInternalName").text(mountedDrives[i].name);
				$(new_win.drive_properties_win).find("#propertiesDriveInternalName").parent().removeClass("hidden");
			}

			$(new_win.drive_properties_win).find("#propertiesDriveSize").text(convertBytes(mountedDrives[i].size));
			

			if (mountedDrives[i].freeSpace == 0) {
				$(new_win.drive_properties_win).find("#propertiesDriveFreeSpace").parent().addClass("hidden");
			} else {
				$(new_win.drive_properties_win).find("#propertiesDriveFreeSpace").text(convertBytesExact(mountedDrives[i].freeSpace));
				$(new_win.drive_properties_win).find("#propertiesDriveFreeSpace").parent().removeClass("hidden");
			}
			
			
		}
	}

	
}

//FIXME: RESTORE: Removed for new version
/*
var mainOuterBody = new_win.window.document.getElementById("outerBody");
*/

/*
if (useRealTimeBlur) {
	$(mainOuterBody).addClass("noMargins");
}*/
//Just do it now anyway lol
//FIXME: RESTORE: Removed for new version
/*
$(mainOuterBody).addClass("noMargins");
$(new_win.outerBodyBackground[0]).addClass("noMargins");

//console.log("new_win.outerBodyBackground 2",new_win.outerBodyBackground);
//new_win.outerBody = $(new_win.outerBodyBackground[0]).next();
new_win.maximize_full = function () {
$(new_win.outerBodyBackground[0]).next().addClass("maximized");
$(new_win.outerBodyBackground[0]).addClass("maximizedBackground");
}

new_win.unmaximize_full = function () {
$(new_win.outerBodyBackground[0]).next().removeClass("maximized");
$(new_win.outerBodyBackground[0]).removeClass("maximizedBackground");
}
*/

		/*console.log("checking for recieved files: ",files);
		console.log("appGeometry: ",appGeometry);
		console.log("appLink: ",appLink);
		console.log("new_win: ",new_win);*/
		

		if (files !=null)
			if (files.length != 0)
         		  	new_win.filesToOpen = files;

setTimeout(function(){ 
//win visuals

/*

$( new_win.window.document.getElementById("main")).append('<iframe id="appContainer" src="../../'+appLink+'" frameborder="0" partition="persist:trusted" style="    position: absolute; width: 100%; height: 100%;" allownw> </iframe>');

		if (appLink == "apps/extern.photos.app/index.html") {
		nw.Window.get().evalNWBin(new_win.window.frames, '/usr/eXtern/iXAdjust/apps/extern.photos.app/js/binary.bin');
		//console.log("imgs attempt");
		}

//$(new_win.window.document.getElementsByTagName("IFRAME")[0]).addClass("hidden");


$(new_win.window.document.getElementsByTagName("IFRAME")[0]).load( function() {
//console.log("append finished",new_win.window.frames.document);


$(new_win.window.frames.document).contents().find("head")
      .append($("<style type='text/css'>  .btn { border-color: "+winButtonProperties.borderColor+" !important;}  </style> <link href='../../../Shared/CoreCSS/scrollbar.css' rel='stylesheet'>"));



    
});

//console.log("iframe",new_win.window.document.getElementsByTagName("IFRAME"));

			$( new_win.window.document.getElementById("appContainer")).load(function() {
        			if (files !=null)
         		 		new_win.onOpenFiles(files);
    			});
*/

//attemptLoadApp(appLink,options,files,multi_window,appTitle,appName);


}, 10000);



if (!new_win.loadedFIrstTime) {
      
      
      //if (sysDevTools)
          //new_win.showDevTools();
          
          
      /*   
          var _show = new_win.show;
var _hide = new_win.hide;
new_win.show = function(){
    new_win.apply(_show);
    console.log('Window is shown',new_win.title);
};
new_win.hide = function(){
    new_win.apply(_hide);
    console.log('Window is hidden',new_win.title);
};
          */
          //new_win.hide();

          
//FIXME: RESTOREHERE
          
  }
  });
               
            
               
               
               
   
       
    
    
  //setTimeout(function(){ console.log("Window object for files: ",new_win.window.document); }, 5000);
  
   
   });
    }
    
    var options = {
  height: 711,
        width: 1294,
        show: false,
        title: "iX Browser",
        transparent: true,
        frame: false,
};
    
    //console.log("GETTING HERE runningApps", runningApps);
    
    /*if (appName == "extern.video.app")
        console.log("RUUUUUUUUUUUUUUUUUUN");*/

	console.log("trying to check files",files);

	console.log("RUUUUUUUUUUUUUUUUUUN: ",appName);
    
    var openNewApp = true;
    
    for (var s = 0; s < runningApps.length; s++) {
        //console.log("GETTING HERE REAL ID", runningApps[s].realID);
        //console.log("GETTING HERE appName", appName);
        if ( runningApps[s].realID == appName) {
            
            if (runningApps[s].multi_window) {
                //console.log("Supports multiwindow");
                openNewApp = true;
            }
            else {
                //console.log("Does not support multiwindow",files);
		
                runningApps[s].windowObject.onOpenFiles(files);
				runningApps[s].windowObject.focus();
                //FIXME -x win.hide();
                openNewApp = false;
            }
        }
    }
    
    if (appName == "extern.welcome.app") {
        if (systemSetupCompleted) {
            openNewApp = false; //Don't open the app. Everything is already set up
		//setTimeout(function(){ runApp("extern.files.app",files); }, 3000); 
//grep -zq casper /proc/cmdline && echo live
	console.log("try live check");
	executeNativeCommand("grep -zq casper /proc/cmdline && echo live",function(res,err) {
		console.log("live check: ",res);
		if (!userSetupCompleted && res.indexOf("live") == -1) {
			var userSetupTrigger = [];
			userSetupTrigger.push("trigger");
			setTimeout(function(){ runApp("extern.tips.app",userSetupTrigger); }, 5000);
		}
	})
/*		if (!userSetupCompleted && !fs.existsSync("/usr/eXtern/live")) {
			var userSetupTrigger = [];
			userSetupTrigger.push("trigger");
			setTimeout(function(){ runApp("extern.tips.app",userSetupTrigger); }, 5000);
		}*/
	} else {
    		// Do something

	console.log("try live 2 check");

	executeNativeCommand("grep -zq casper /proc/cmdline && echo live",function(res,err) {
		console.log("live check: ",res);
		if (res.indexOf("live") == -1) {
		openNewApp = false; //Don't open the app. Everything is already set up
		systemSetupCompleted = true;
		localStorage.setItem('systemSetupCompleted', JSON.stringify(systemSetupCompleted));
		setTimeout(function(){ chrome.runtime.reload(); }, 1000); //FIXME temporary fix
		}
	});

		/*openNewApp = false; //Don't open the app. Everything is already set up
		systemSetupCompleted = true;
		localStorage.setItem('systemSetupCompleted', JSON.stringify(systemSetupCompleted));
		setTimeout(function(){ chrome.runtime.reload(); }, 1000); //FIXME temporary fix*/
	}
    }

        if (appName != "extern.temp.app") {
    //console.log("GETS HERE NOT: extern.temp.app");
    if (openNewApp) {
    for (var j = 0;j < apps.length; j++)
    {
        if (apps[j].id == appName) {
            if (systemSetupCompleted) 
                addRecentApp(appName);


console.log("we have files",files);	attemptLoadApp('apps/'+appName+'/'+apps[j].main,apps[j].window,files,apps[j].multi_window,appName,apps[j].name,appGeometry,apps[j].wait,appGeometry,apps[j].thumbnail_preview);

//directLaunch(appLink,options,files,multi_window,appTitle)

           // directLaunch('apps/'+appName+'/'+apps[j].main,apps[j].window,files,apps[j].multi_window,apps[j].name);
        }
    }
    }
    } else {

	    //console.log("GETS HERE: extern.temp.app");
		
            directLaunch('apps/'+appName+'/index.html',options,files,false,"unknown");


    }
/*if (appName == "extern.webbrowser.app") {
    
    var options = {
  height: 711,
        width: 1294,
        show: false,
        title: "iX Browser",
        transparent: true,
        frame: false,
};
    
    directLaunch('apps/brows/index.html',options);
   
}
    
    
if (appName == "extern.devkit.app") {
    
    var options = {
  height: 660,
        width: 1300,
        show: false,
        title: "iX Browser",
        transparent: true,
        frame: false
};
    
    directLaunch('apps/DevKit/core/index.html',options);
   
}
    
    if (appName == "extern.files.app") {
        
        var options = {
  width: 1260,
        height: 680,
       min_width: 260,
       min_height: 580,
        show: false,
        title: "Files",
        transparent: true,
        frame: false
};
        directLaunch('apps/iX Files/index.html',options);

    
}*/
 /*web.on('closed', function() {
    web = null;
  });
    
    web.on('loaded', function() {
        console.log("LOADED");
    //web = null;
  });*/
    
   // setTimeout(function(){ /*$("#bg_main").trigger( "click" );*/$("#loadingAnim").remove(); }, 1000);
   /* $("#bg_main").zoomTo({
        
    });*/
}
//END of runApp();

var filesApp = {
    id: "iX Files",
    name: "Files",
    size: "53.7 Mb",
    desc: "Browse, view, modify and remove files from filesystems connected to this Computer",
    icon: "icons/system-file-manager.png",
    launchTimes: 5,
}

allApps.push(filesApp);



var bApp = {
    id: "txteditor",
    name: "Text Editor",
    size: "10.2 Mb",
    desc: "Create and modify plain text files",
    icon: "icons/preferences-desktop-filetype-association.png",
    launchTimes: 10,
}

allApps.push(bApp);

var bApp = {
    id: "camera",
    name: "Camera",
    size: "13.7 Mb",
    desc: "View, capture and record content from camera/capture devices connected to this computer.",
    icon: "icons/cheese.png",
    launchTimes: 10,
}

allApps.push(bApp);

var browserApp = {
    id: "brows",
    name: "Web",
    size: "33.7 Mb",
    desc: "Explore the Web!",
    icon: "icons/web-browser.png",
    launchTimes: 10,
}

allApps.push(browserApp);
    //console.log("all Apps",allApps);




function loadApps()
{
    //$("#footer_text").append("You are currently viewing <b>"+total_files+" files</b> and <b>"+total_folders+" folders</b>.");
    //console.log("Testing ",$("#ttest")[0].childNodes[1].attributes[0].nodeValue);
    
    
    
    
    

}

setTimeout(function(){ loadApps() }, 5000);



 /*$( ".appBox" )
  .mouseenter(function() {
    console.log("Testing ",$(this)[0].attributes.description.value);
     $("#appDescId").text($(this)[0].attributes.description.value);
     $("#AppDiskUsage").text($(this)[0].attributes.disk.value);
     $("#AppAccessTimes").text($(this)[0].attributes.Accessed.value+" times");
        $("#AppIconPreview")[0].src = $(this)[0].childNodes[1].src;
        $("#sideBarAppLabel").text($(this)[0].childNodes[5].innerText);
     hoveringOverApp = true;
     if ($("#personalAssistant").hasClass("cActive"))
    {
        $("#appInfo").fadeIn();
        $("#appInfo").addClass("cActive");
        $("#personalAssistant").fadeOut();
        $("#personalAssistant").removeClass("cActive");
        
    }
  })
  .mouseleave(function() {
     hoveringOverApp = false;
     setTimeout(function(){
    if (!$("#personalAssistant").hasClass("cActive") && hoveringOverApp == false)
    {
        
        $("#personalAssistant").fadeIn();
        $("#personalAssistant").addClass("cActive");
        $("#appInfo").fadeOut();
        $("#appInfo").removeClass("cActive");
        hoveringOverApp = false;
            
    }
                   }, 1000);
  });*/


function checkOSUpates()
      {
          
          

          var url = sysOs.url;
var search_request = new XMLHttpRequest();
search_request.onreadystatechange = function() {
    if (search_request.readyState == 4 && search_request.status == 200) {
        var osversion_data = JSON.parse(search_request.responseText);
        if (sysOs.version != osversion_data[0].version || sysOs.name != osversion_data[0].osname) {
setTimeout(function(){ //This delay has been added due to the new way we run Apps, sometimes lauched at the exact same time as I>T>A>I forming some kind of mutant of an App haha. Will fix this issue so that even if Apps launch at the same time, the system should be able to handle it.
var updateRequests = []
    updateRequests.push('extern.update.app');
openApp('extern.store.app',updateRequests);
}, 8000);
}
        //console.log("OS online",osversion_data);
         //console.log("OS local",os);


        
    }
};
      search_request.open("GET", url, true);
      search_request.send();
      }


console.log("using this file");

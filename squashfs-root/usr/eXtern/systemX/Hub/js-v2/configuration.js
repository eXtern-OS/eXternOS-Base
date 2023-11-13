//nw.Window.get().evalNWBin(null, '/usr/eXtern/iXAdjust/Hub/js/configuration.bin');

//nw.Window.get().evalNWBin(null, '/usr/eXtern/iXAdjust/Hub/js/configuration.bin');

var fs = require('fs-extra'),
    path = require('path'),
    async = require('async');
var win = {}; //nw.Window.get();
//win.showDevTools();
//console.log("showDevTools()");
var getSize = require('get-folder-size');
var njds = require('nodejs-disks');
//var screenshot = require('desktop-screenshot');
var _ = require('underscore');
var os = require('os');
//var changeBrightness = require('node-brightness');
//const isOnline = require('is-online');
var currentDisplay = "";
var sysOnline = false; //Internet connection status
var webInformationLoaded = false; //for news and weather. If not, wait until conection is estabilished
const wallpaper = require('wallpaper');
var sysDevTools = true;
var currentMenuMode = 'apps';
var allDisplays = [];
var noOfDisplays = 0;
var allAppsDivs = [];
var allInstalledApps = [];
var allActiveNews = [];
var detectedDrives = [];
var detectedMountedDrives = [];
var systemSetupCompleted = false; //Used to to know if this is the first time boot from Live CD
var userSetupCompleted = false;
var adaptiveBlur = true; //We can now trust real time blur to enable it by default
var enableLinuxNativeApps = false; // Temporary support for Linux GTK native Apps
var enableDesktopStacks = true; // Desktop icons pretty much
var stackStyle = "stack-peekaboo"; //Stores the style class to be used on the stack icons
var customWallpapers = []; //Used to store user defined custom wallpapers in the settings
win.hidingNow = false; //Used to avoid on blur even being caled if the user used another way to close the hub
win.ignoreMetaKey = false;
win.opened = false; //Used by explorebar to track if hub is opened
var allLegacyApps = []; //Store Legaccy (Linux etc) Apps here
const homedir = require('os').homedir();
//win.showDevTools();
var improvePerfomanceMode = false; //For low spec computers
var enhancedAudio = true;
var canHideHub = true;
var displayBrightness = 1;
var displayGamma = 1;
var hubId;

if (localStorage.getItem('displayBrightness') != null)
    displayBrightness = JSON.parse(localStorage.getItem('displayBrightness'));

if (localStorage.getItem('displayGamma') != null)
    displayGamma = JSON.parse(localStorage.getItem('displayGamma'));

if (localStorage.getItem('improvePerfomanceMode') != null)
    improvePerfomanceMode = JSON.parse(localStorage.getItem('improvePerfomanceMode'));

if (localStorage.getItem('enhancedAudio') != null)
    enhancedAudio = JSON.parse(localStorage.getItem('enhancedAudio'));

console.log("homedir: ",homedir);

//Will be used to get weather etc

var volumeSlider = $('#ex1').slider()
		.on('slide', updateallVolumeSliders)
		.data('slider');

$('#ex1').slider({
	formatter: function(value) {
		return 'Current value: ' + value;
	}
});

function updateallVolumeSliders() {
	runningApps[0].windowObject.setSystemVolume(volumeSlider.getValue());
	console.log("vol adjust called");
}


if (localStorage.getItem('user_location') === null) {
    var user_location = {
	city : "",
	country : "",
	region : "",
	zipcode : ""
	};
} else
    var user_location = JSON.parse(localStorage.getItem('user_location'));

var fileTypesApps = {
    audio : [],
    video : [],
    image : [],
    text : [],
    web : [],
    prefferedFileTypesApps : {
        audio : [],
        video : [],
        image : [],
        text : [],
        web : []
}
};

var fileTypesIcons = {
	unknown: "blank.png",
	folder: "folder.png",
	mp3: "audio.png",
	zip: "compressed zip.png",
	pdf: "pdf.png",
	java: "java.png",
	js: "java script.png",
	css: "css.png",
	c: "c code.png",
	"c++": "c++ code.png"
}

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
  'image': ['jpg', 'jpge', 'png','PNG'],
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

function getfileIcon (fileType) {
	if (fileTypesIcons[fileType] != null) {
		return fileTypesIcons[fileType];
	} else {
		return fileTypesIcons.unknown;
	}
}

function resolveFileType(ext,includeIconExtention) {
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
	

const sysOs = {
name: "eXtern OS",
version: "Beta 3D",
url: "https://externos.io/externapps/osupdates/3d/"
};

var systemSortedApps = [];

var adaptiveFocusEnabled = false;
window.InfoBox = "calendarEvents"; //Use this for now cos it's more "proffessional looking"

//credits: RoundIcons -- URL on other PC

//win.showDevTools();
if (localStorage.getItem('systemSetupCompleted') === null)
    systemSetupCompleted = false;
else
    systemSetupCompleted = true;

if (localStorage.getItem('userSetupCompleted') === null)
    userSetupCompleted = false;
else
    userSetupCompleted = true;

if (fs.existsSync("/usr/eXtern/systemX/Shared/temp/xrandr-parse")) {
//console.log("exists");

var ncp = require('ncp').ncp;
 
ncp.limit = 16;
 
ncp("/usr/eXtern/systemX/Shared/temp/xrandr-parse", "/usr/eXtern/node_modules/xrandr-parse", function (err) {
 if (err) {
   return console.error(err);
 }
 //console.log('done!');
var rimraf = require('rimraf');
rimraf("/usr/eXtern/systemX/Shared/temp/xrandr-parse", function () { console.log('done'); chrome.runtime.reload(); });
});

    // Do something
}


//systemSetupCompleted = false; //FIXME delete ths


var runningApps = [];
var runningAppsNew = []; //Without the window object for the new process manager implementation



//console.log("localStorage.getItem('accessedApps')",localStorage.getItem('accessedApps'));

if (localStorage.getItem('accessedApps') === null)
    var accessedApps = {};
else
    var accessedApps = JSON.parse(localStorage.getItem('accessedApps'));

if (localStorage.getItem('enableLinuxNativeApps') != null)
    enableLinuxNativeApps = JSON.parse(localStorage.getItem('enableLinuxNativeApps'));



if (localStorage.getItem('enableDesktopStacks') === null)
    enableDesktopStacks = true;
else
    var enableDesktopStacks = JSON.parse(localStorage.getItem('enableDesktopStacks'));


if (localStorage.getItem('stackStyle') != null)
    stackStyle = JSON.parse(localStorage.getItem('stackStyle'));

if (localStorage.getItem('customWallpapers') != null)
    customWallpapers = JSON.parse(localStorage.getItem('customWallpapers'));



//console.log("stackStyle",stackStyle);

//win.showDevTools();

/*Screen Recorder*/
//https://www.npmjs.com/package/screencap

//https://askubuntu.com/questions/487496/terminal-command-to-record-video

//sudo apt-get install libav-tools

//console.log("CD: ",process.cwd())

//https://github.com/nwjs/nw.js/wiki/Preserve-window-state-between-sessions

if ($("#osDevs").length == 0 || $("#osVersion").length == 0)
    chrome.runtime.reload();

$("#osDevs").text("eXtern OS Developers");
$("#osVersion").text('"Quantum" (In-house)');

exploreBarHeight = 46;
//console.log("File types:",fileTypesApps);


function updateAppSizes() {
    getSize(myFolder, function(err, size) {
  if (err) { throw err; }
 
  //console.log(size + ' bytes');
  //console.log((size / 1024 / 1024).toFixed(2) + ' Mb');
});
}

function clearAllLists() {
    $("#recent-b").empty();
    $("#most-accessed-b").empty();
    $("#txt-editors-b").empty();
    $("#sys-tools-b").empty();
    $("#multimedia-b").empty();
    $("#internet-b").empty();
    $("#img-and-graphics-b").empty();
    $("#developer-tools-b").empty();
    $("#other-apps-b").empty();
    $("#other-apps-a").addClass("hidden");
}

var ost  = require('os-utils');
var os = require("os");
var cpus = os.cpus(); 

/**
 * Returns a random integer between min (inclusive) and max (inclusive)
 * Using Math.round() will give you a non-uniform distribution!
 */
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}



if (window.InfoBox == "motivationalQuotes") {
var json = (function () {
    var json = null;
    $.ajax({
        'async': false,
        'global': false,
        'url': "quotes/motivational.json",
        'dataType': "json",
        'success': function (data) {
            //console.log("quotes: ",data);
            var randomQuote = data[getRandomInt(1, data.quotesTotal)];
            $("#motivationalQuote").text(randomQuote.quote);
            $("#quoteAuthor").text(randomQuote.author);
        }
    });
    
})(); 
}

if (window.InfoBox == "calendarEvents") {
    $("#motivationalQuote").text("You don't have any scheduled events.");
    $("#quoteAuthor").text("Calendar");
}

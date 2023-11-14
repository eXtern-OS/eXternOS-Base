//nw.Window.get().evalNWBin(null, '/usr/eXtern/iXAdjust/apps/extern.web.app/js/binary.bin');
//sudo chfn -f "Anesu Chiodze" extern - Change user name
App = parent.getInstance();
		var fs = require('fs');
	var parser = require('/usr/eXtern/systemX/apps/extern.web.app/ext/abp-filter-parser-modified/abp-filter-parser.js');
	var blockTrackersAndAds = true;
	var transparencySetting = "";//"allowtransparency";
	var useTransparency = false;
	//./apps/extern.web.app/ext/abp-filter-parser-modified/abp-filter-parser.js
	var isLoading = false;
	var isAudioPlaying = false;
	var currentTab = 0;
	var totalTabs = 0;
	var availableTabs = [];
	var imgNmbr = 0; //this is because the app kept catche-ing the image so I have to make it seem like a different one each time.
	var tabsArray = new Array();
	var gui = require('nw.gui');
	var win = gui.Window.get();
	var canGoBack = false;
	var downloadLocation = process.env['HOME']+"/Downloads/";
	var lastOpenedBookmark = "#googleTab0";
	var clipboard = nw.Clipboard.get();
	gui.Screen.Init();
	fs = require('fs');
	//win.showDevTools();
	var currentAtHome = true;
	var lastHomeTab = "test";
	var homeBookMarks = [];
	var browserHistory = [];
	var firstTime = true;
	var currentBookmarkId = -1; //Locaton in the bookmarks aray being modified
	//var request = require('request');
	var needle = require('needle'); // Using needle because request broke with the node update
	var win = nw.Window.get();
	$(App.close_button).css("top","19px"); //move close button to other buttons
	$(App.close_button).css("right","10px"); //move close button to other buttons
	$(App.maximize_button).css("top","19px"); //move maximize button to other buttons
	$(App.maximize_button).css("right","50px"); //move maximize button to other buttons
	$(App.minimize_button).css("top","14px"); //move minimize button to other buttons
	$(App.minimize_button).css("right","85px"); //move minimize button to other buttons

console.log("App.close_button: ",App.close_button);
console.log("App.minimize_button: ",App.minimize_button);
var parsedFilterData = {};
var tabOverflowScrollEnabled = false;
var mouseX = 0;
var mouseY = 0;
var lastHoveredLink = ""; //Using this to get accurate link that user clicked on. If this fails for whatever reason, there is the old way still there haha
var lastTabID = 0; //Use this to go to this tab when user closes the current tab
var fancyRendering = false; //Experimental page adjustments such as if user scrolls contents go below the navigation bar
var sessionStoragePartition = 'partition="persist:trusted"';
var privateMode = false;
var controlsShowing = true; //used to determine if scontrols have been auto hidden
var useZoomAnimations = false;
var recommendedSearches = [];
var allowedLocationPermissions = [];
var deniedLocationPermissions = [];



if (localStorage.getItem('allowedLocationPermissions') != null)
	allowedLocationPermissions = JSON.parse(localStorage.getItem('allowedLocationPermissions'));

if (localStorage.getItem('deniedLocationPermissions') != null)
	deniedLocationPermissions = JSON.parse(localStorage.getItem('deniedLocationPermissions'));

if (localStorage.getItem('recommendedSearches') != null)
	recommendedSearches = JSON.parse(localStorage.getItem('recommendedSearches'));

//win.showDevTools();
var currentSwitchingTimeOut;




	function animatedZoomBox(zoomElement) {
				if ($(zoomElement).hasClass("hiddenOpacity")) {
					console.log("exiting");
					$(zoomElement).toggleClass("fullScreen");
					setTimeout(function(){ 
						$(zoomElement).toggleClass("hiddenOpacity");
					}, 800);
				} else {
					$(zoomElement).toggleClass("fullScreen");
					setTimeout(function(){ 
						$(zoomElement).toggleClass("hiddenOpacity");
					}, 500);
				}
			};

		


  

	
	



/* Track mouse location for context menus etc */
(function() {
    document.onmousemove = handleMouseMove;
    function handleMouseMove(event) {
        var eventDoc, doc, body;

        event = event || window.event; // IE-ism

        // If pageX/Y aren't available and clientX/Y are,
        // calculate pageX/Y - logic taken from jQuery.
        // (This is to support old IE)
        if (event.pageX == null && event.clientX != null) {
            eventDoc = (event.target && event.target.ownerDocument) || document;
            doc = eventDoc.documentElement;
            body = eventDoc.body;

            event.pageX = event.clientX +
              (doc && doc.scrollLeft || body && body.scrollLeft || 0) -
              (doc && doc.clientLeft || body && body.clientLeft || 0);
            event.pageY = event.clientY +
              (doc && doc.scrollTop  || body && body.scrollTop  || 0) -
              (doc && doc.clientTop  || body && body.clientTop  || 0 );
        }

        // Use event.pageX / event.pageY here
				mouseX = event.pageX;
				mouseY = event.pageY;
    }
})();


/* Selects part of an input box. Used when user enters a known input and we are auto suggesting*/

function createSelection(field, start, end) {
    if( field.createTextRange ) {
      var selRange = field.createTextRange();
      selRange.collapse(true);
      selRange.moveStart('character', start);
      selRange.moveEnd('character', end);
      selRange.select();
      field.focus();
    } else if( field.setSelectionRange ) {
      field.focus();
      field.setSelectionRange(start, end);
    } else if( typeof field.selectionStart != 'undefined' ) {
      field.selectionStart = start;
      field.selectionEnd = end;
      field.focus();
    }
  }



(function($) {
    $.fn.hasScrollBar = function() {
        return this.get(0).scrollWidth > this.width();
    }
})(jQuery);

setInterval(function(){ 

	if ($('#tabNav').hasScrollBar()) {
		tabOverflowScrollEnabled = true;
		//console.log("has scrollbar");
	} 


}, 1000);


//$('#allTabs > .searchSuggestions').fadeOut();

$('#allTabs > .searchSuggestions').hide();

console.log("win.getAllNews",App.getAllNews());
//console.log("win.showDevTools();");

//$('#enableTrackersAdsBlocker').val(blockTrackersAndAds);

//$('#enableTrackersAdsBlocker').bootstrapSwitch('setState', blockTrackersAndAds);

// A $( document ).ready() block.

//https://github.com/fronteed/icheck




//https://stackoverflow.com/questions/34102374/bootstrap-switch-setstate-using-a-jquery-function
//localStorage.setItem('browserHistory', JSON.stringify(browserHistory));

if (localStorage.getItem('browserHistory') != null)
	var browserHistory = JSON.parse(localStorage.getItem('browserHistory'));

var firstTime = localStorage.getItem('firstTimeWebApp');

if (firstTime != null) {
  firstTime = false;
} else {
  firstTime = true;
  localStorage.setItem('firstTime', false);
}


function openNewWindow(url,isPrivate) {
	var requiredApps = win.fileTypesApps.prefferedFileTypesApps;

	if (isPrivate) {
		var files = ["--private-session", url];
		win.openApp("extern.web.app",files);
	} else {
		win.openApp("extern.web.app",url);
	}
	
	if (!$("#link_context_menu").hasClass("hidden")) {
			closeAllMenus();
			closeSideBar();
	}
	win.minimize();
}





function initFilterList () {
updateEasyPrivacyList();
  var data = fs.readFile('/usr/eXtern/systemX/apps/extern.web.app/ext/filterLists/easylist+easyprivacy-noelementhiding.txt', 'utf8', function (err, data) {
    if (err) {
      console.log("error occured passing filter list",err);
      return
    }

    // data = data.replace(/.*##.+\n/g, '') // remove element hiding rules

    parser.parse(data, parsedFilterData);
  })
}

document.addEventListener('DOMContentLoaded', function() {
console.log("yo");

/* attemptig to scroll when side bar is active
  $("#contextMenuOverlay").scroll(function() {
    $('#webview'+currentTab).prop("scrollTop", this.scrollTop)
          .prop("scrollLeft", this.scrollLeft);
  });
*/
  
  if (localStorage.getItem('blockTrackersAndAdsWebbApp') != null) {
  blockTrackersAndAds = JSON.parse(localStorage.getItem('blockTrackersAndAdsWebbApp'));
    console.log("blockTrackersAndAdsWebbApp from memory: ",blockTrackersAndAds);
} else {
  blockTrackersAndAds = false;
  localStorage.setItem('blockTrackersAndAdsWebbApp', JSON.stringify(false));
  console.log("blockTrackersAndAdsWebbApp Not from mem:"+blockTrackersAndAds);
}
  
  if (blockTrackersAndAds) {
    console.log("check it");
    $('#enableTrackersAdsBlocker').parent().removeClass("switch-off"); 
    $('#enableTrackersAdsBlocker').parent().addClass("switch-on"); 
    $('#enableTrackersAdsBlocker').iCheck('update');
  }
    
    
    
  
  if (blockTrackersAndAds) {
initFilterList ();
}
  
    if (localStorage.getItem('useTransparencyWebbApp') != null) {
  useTransparency = JSON.parse(localStorage.getItem('useTransparencyWebbApp'));
    console.log("useTransparencyWebbApp from memory: ",useTransparency);
} else {
  useTransparency = false;
  localStorage.setItem('useTransparencyWebbApp', JSON.stringify(false));
  console.log("useTransparencyWebbApp Not from mem:"+useTransparency);
}
  
  if (useTransparency) {

	transparencySetting = "allowtransparency";
	$('#webview'+currentTab).attr("allowtransparency","");
    $('#enableTransparency').parent().removeClass("switch-off"); 
    $('#enableTransparency').parent().addClass("switch-on");
    $('#enableTransparency').iCheck('update');

} else {

	transparencySetting = "";
	$('#webview'+currentTab).removeAttr("allowtransparency");

}


/* Gotta disable this, has a bug where it only works on last added webview
setInterval(function(){ 

//$('webview').each(function(i, obj) {
	for (var i =0; i < availableTabs.length; i++) {
	//console.log("obj_i: ",i);
	//webview = obj;
	var webview = document.querySelector('#webview'+availableTabs[i]);
	//console.log("availableTabs: ",availableTabs);
	//console.log("webview: ",webview);
	console.log("i: ",i);
	console.log("webview.ids A",webview.ids);
    webview.getAudioState(function (audible) {

			console.log("webview.ids",webview.ids);
			console.log("currentTab: ",currentTab);
			
			/*console.log("is audio playing?",audible);
			console.log("webview.ids",webview.ids);
			console.log("currentTab: ",currentTab);
			console.log("webview.id",$(webview).attr("id"));
			console.log("webview.audioIsPlaying: ",webview.audioIsPlaying);
			console.log("audible: ",audible);//
			//var webview = document.querySelector('#webview'+currentTab);
			if (webview.audioIsPlaying != audible) {
				webview.audioIsPlaying = audible;
				//console.log("here A");
				 //if (webview.ids == currentTab) {
					 console.log("here B");
					 if (webview.audioIsPlaying) {
						 //console.log("here C");
						 if (webview.ids == currentTab) {
						 $("#audioPlayingIcon").removeClass("hidden");
						 $("#urlDisplay").addClass("spaceForAudioIcon");
						 }
						$("#audioPlayingIconTab"+webview.ids).removeClass("hidden");
					 } else {
						 console.log("here D");
						  if (webview.ids == currentTab) {
						 $("#audioPlayingIcon").addClass("hidden");
						 $("#urlDisplay").removeClass("spaceForAudioIcon");
							}
						 $("#audioPlayingIconTab"+webview.ids).addClass("hidden");
					 }
				 //}
			}
		});
//});
	}


		}, 10000);*/
  
  
  

});



	$('#enableTrackersAdsBlocker').change(function() {
      
      console.log("Add blocker changed",this.checked);

//$('#adaptiveBlur').bootstrapSwitch('state', false);

//http://bootstrapswitch.com/methods.html

//https://stackoverflow.com/questions/24152240/bootstrap-switch-doesn%C2%B4t-event

blockTrackersAndAds = this.checked;
      
      localStorage.setItem('blockTrackersAndAdsWebbApp', JSON.stringify(blockTrackersAndAds));

if (blockTrackersAndAds) {
	initFilterList ();
}
var webview = document.querySelector('#webview'+currentTab);
webview.reload();  
    });



function autoResizeWindow() {
		win.x = 100;
		win.y = 50;
		win.resizeTo(screen.width-200,screen.height-150);
		//win.width = screen.width-200;
		//win.height = screen.height-150;
		
	}

	if (screen.width > 1366){
		//autoResizeWindow();
		//win.hide();
		setTimeout(function(){ 
				win.show();
			}, 500);
		
		//win.show();
	}

//Used to show the navigations and tabs when they are hidden
console.log("detect hover of: ",$( "#tabNav" ).parent());
$( "#tabNav" ).parent().hover(function() {
	console.log("hoveredb");
	var maxHeight = 55;
	if (!controlsShowing) {
		$("#navigationBar").css("height",maxHeight+"px");
		$("#blur2").css("height",maxHeight+"px");
		$("#allTabsC").css("height","calc(100% - "+(maxHeight-15)+"px)");
		$(".newNavButton").removeClass("hiddenOpacity");
		$(App.minimize_button).removeClass("hidden");
		$(App.maximize_button).removeClass("hidden");
		$(App.close_button).removeClass("hidden");
		$("#tabNav").removeClass("hidden");
		controlsShowing = true;
	}
				

			}, function() {
				//out of hover
				console.log("not hovering")
			});


	$('#enableTransparency').change(function() {

//$('#adaptiveBlur').bootstrapSwitch('state', false);

//http://bootstrapswitch.com/methods.html

//https://stackoverflow.com/questions/24152240/bootstrap-switch-doesn%C2%B4t-event

useTransparency = this.checked;
      
      localStorage.setItem('useTransparencyWebbApp', JSON.stringify(useTransparency));

if (useTransparency) {

	transparencySetting = "allowtransparency";
	$('#webview'+currentTab).attr("allowtransparency","");

} else {

	transparencySetting = "";
	$('#webview'+currentTab).removeAttr("allowtransparency");

}
var webview = document.querySelector('#webview'+currentTab);

webview.reload();
	
//webview.reload();
	/*if (webview.src.slice(-1) != "#") {
		console.log("add #");
		webview.src = webview.src; //Apparently reload is broken?
	} else {
		console.log("remove #");
		webview.src = webview.src.slice(0, -1); //Remove it if we jusr added it or already there
	}*/


console.log("this.checked",this.checked);
        /*if(this.checked) {
            var returnVal = confirm("Are you sure?");
            $(this).prop("checked", returnVal);
        } */    
    });

var storedBookmarks = localStorage.getItem('storedBookmarksWebApp');

	defaultBookMarks = [];

	defaultBookMarks.push({
		name : "Google",
		id: 0,
		url : "https://www.google.com/",
		description: "Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.",
		thumbUrl : "Bookmarks/new/google-com.png"    
	});

	defaultBookMarks.push({
		name : "YouTube",
		id: 1,
		url : "https://www.youtube.com/",
		thumbUrl : "Bookmarks/new/youtube-com.png",
		description: "Enjoy the videos and music you love, upload original content, and share it all with friends, family, and the world on YouTube.",
		animatedThumbUrl : "Bookmarks/bing.com.gif" 
	});

	defaultBookMarks.push({
		name : "Bing",
		id: 2,
		url : "https://www.bing.com/",
		thumbUrl : "Bookmarks/new/bing-com.png",
		description: "Bing helps you turn information into action, making it faster and easier to go from searching to doing.",
		animatedThumbUrl : "Bookmarks/bing.com.gif"  
	});

	defaultBookMarks.push({
		name : "Twitter",
		id: 3,
		url : "https://twitter.com/",
		thumbUrl : "Bookmarks/twitter.com.png",
		description: "From breaking news and entertainment to sports and politics, get the full story with all the live commentary.",
		animatedThumbUrl : "Bookmarks/new/twitter-com.png" 
	});

	defaultBookMarks.push({
		name : "Facebook",
		id: 4,
		url : "https://www.facebook.com/",
		thumbUrl : "Bookmarks/new/facebook-com.png",
		description: "Connect with friends, family and other people you know. Share photos and videos, send messages and get updates.",
		animatedThumbUrl : "Bookmarks/new/facebook-com.png"
	});

	defaultBookMarks.push({
		name : "Yahoo",
		id: 5,
		url : "https://www.yahoo.com/",
		thumbUrl : "Bookmarks/new/yahoo-com.png",
		description: "News, email and search are just the beginning. Discover more every day. Find your yodel.",
		animatedThumbUrl : "Bookmarks/new/yahoo-com.png"
	});

	defaultBookMarks.push({
		name : "The Verge",
		id: 8,
		url : "https://www.theverge.com/",
		thumbUrl : "Bookmarks/new/theverge-com.png",
		description: "The Verge was founded in 2011 in partnership with Vox Media, and covers the intersection of technology, science, art, and culture. Its mission is to offer in-depth reporting and long-form feature stories, breaking news coverage, product information, and community content in a unified and cohesive manner.",
		animatedThumbUrl : "Bookmarks/theverge.com.png"
	});

	defaultBookMarks.push({
		name : "The Next Web",
		id: 9,
		url : "https://thenextweb.com/",
		thumbUrl : "Bookmarks/new/thenextweb-com.png",
		description: "Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.",
		animatedThumbUrl : "Bookmarks/thenextweb.com.png"
	});

	defaultBookMarks.push({
		name : "WIRED",
		id: 10,
		url : "https://www.wired.com/",
		thumbUrl : "Bookmarks/new/wired-com.png",
		description: "Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.",
		animatedThumbUrl : "Bookmarks/wired.com.png"
	});

	defaultBookMarks.push({
		name : "TechCrunch",
		id: 11,
		url : "https://techcrunch.com/",
		thumbUrl : "Bookmarks/new/techcrunch-com.png",
		description: "Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.",
		animatedThumbUrl : "Bookmarks/techcrunch.com.png"
	});

	defaultBookMarks.push({
		name : "Stack Overflow",
		id: 12,
		url : "https://stackoverflow.com/",
		thumbUrl : "Bookmarks/new/stackoverflow-com.png",
		description: "Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.",
		animatedThumbUrl : "Bookmarks/stackoverflow.com.png"
	});

	defaultBookMarks.push({
		name : "GitHub",
		id: 13,
		url : "https://github.com/",
		thumbUrl : "Bookmarks/new/github-com.png",
		description: "Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.",
		animatedThumbUrl : "Bookmarks/Github.com.png"
	});

if (storedBookmarks != null) {
  homeBookMarks = JSON.parse(storedBookmarks);
var homeBookMarks_lastId = JSON.parse(localStorage.getItem('homeBookMarks_lastId'));
	//var homeBookMarks_lastId = JSON.parse(homeBookMarks_lastId);
  //console.log("using custom bookmarks",homeBookMarks);
	

} else {

		homeBookMarks = homeBookMarks.concat(defaultBookMarks); //Add default bookmarks if first time.
	var homeBookMarks_lastId = 14; //Store the last ID to make a unique one when adding a new one
  localStorage.setItem('storedBookmarksWebApp', JSON.stringify(homeBookMarks));
localStorage.setItem('homeBookMarks_lastId', JSON.stringify(homeBookMarks_lastId));

  
}
var ignoreLink = false;
function openNewsSelector() {
	console.log("open news");
	$(".bookmarksOuter").addClass("hiddenOpacity");
	ignoreLink = true;
	App.openNewsSourcesModal();
}

App.newsSourceModalClosed = function () {
	console.log("App.getAllNews: ",App.getAllNews());
	updateNewsSources();
	$(".bookmarksOuter").removeClass("hiddenOpacity");
	$('#view'+currentTab+' > .zoomContainer').trigger( "click" );
	var webview = document.querySelector('#webview'+currentTab);
	webview.currentAtHome = true;
}

	

	$("#allTabs").css("opacity",0);

	function blurThumbs (BlurPos) {
		var canvas = document.getElementById('blurCanvas');
		var context = canvas.getContext('2d');
		var x = 0;
		var y = 0;
		var width = 300;
		var height = 136; 
		var blurEffect = 2;
		var saturationValue = 2.4;
		canvas.width = 300;
		canvas.height = 136;
		context.clearRect(0, 0, canvas.width, canvas.height);
		var imageObj = new Image();
		imageObj.onload = function() {
			//context.drawImage(imageObj, x, y, width, height);
			context.drawImage(imageObj, 0, 0, canvas.width, canvas.height);
			setTimeout(function(){
				context._blurRect(0, 0, canvas.width, canvas.height, blurEffect, saturationValue);
				imgData = canvas.toDataURL('image/jpeg');//context.getImageData(0,0,canvas.width,canvas.height);
			  //$('#bg_main').css("background-image", "url('file:///home/anesu/Pictures/aa/2/02225_cherryflowers_1920x1080.jpg') !important"); 
	   			//$(document.body).prepend('<background style="border-radius: 5px 5px 5px; position: absolute; width:100%; height:100%"></background>');
				//document.body.children[0].style.backgroundImage= "url('"+imgData+"'";
				homeBookMarks[BlurPos].thumbBlurred = imgData;
				$("#T0B"+BlurPos+" > .textBG")[0].src = imgData;
				BlurPos++;
				if (BlurPos < homeBookMarks.length){
					blurThumbs(BlurPos);
				}else{
					//Code below is to fix some weird bug at the last minute of release LOL
					//newTab();
					//closeTab(0);
					$("#allTabs").css("opacity",1);
					setTimeout(function(){
						//win.show();
					}, 500);
				}
			}, 100);
		};
		imageObj.src = homeBookMarks[BlurPos].thumbUrl;
	}

	function universalBlur(imgss,callback,width,height,blurStrengths,blurEffects,saturationValues){
		var canvas = document.getElementById('blurCanvas');
		var context = canvas.getContext('2d');
		
		canvas.width = width;//300;
		canvas.height = height;//136;
		context.clearRect(0, 0, canvas.width, canvas.height);
		var imageObj = new Image();
		imageObj.onload = function(){
			context.drawImage(imageObj, 0, 0, canvas.width, canvas.height);
			setTimeout(function(){ 
				context._blurRect(0, 0, canvas.width, canvas.height, blurEffects, saturationValues);
				imgData = canvas.toDataURL('image/jpeg');
				callback(imgData);
			}, 100);
		};
		imageObj.src = imgss;
	}

	var gui = require('nw.gui');

	var option = {
	  key : "VolumeUp",
	  active : function() {
		////console.log("Global desktop keyboard shortcut: " + this.key + " active."); 
	  },
	  failed : function(msg) {
		// :(, fail to register the |key| or couldn't parse the |key|.
		////console.log(msg);
	  }
	};

	// Create a shortcut with |option|.
	var shortcut = new gui.Shortcut(option);

	// Register global desktop shortcut, which can work without focus.
	gui.App.registerGlobalHotKey(shortcut);

	// If register |shortcut| successfully and user struck "Ctrl+Shift+A", |shortcut|
	// will get an "active" event.

	// You can also add listener to shortcut's active and failed event.
	shortcut.on('active', function() {
	  ////console.log("Global desktop keyboard shortcut: " + this.key + " active."); 
	});

	shortcut.on('failed', function(msg) {
	  ////console.log(msg);
	});

	//https://www.w3.org/TR/DOM-Level-3-Events-code/#key-media
	//https://github.com/nwjs/nw.js/wiki/shortcut

	$('#allTabs > .searchSuggestions').fadeOut();
	function initHome () {
		if (currentAtHome) {
			
			var currentHomeLinks = "";
			for (var i = 0; i < homeBookMarks.length; i++) {
				var simpleUrl = homeBookMarks[i].url.replace("http://","").replace("https://","").replace("file://","");
				currentHomeLinks += '<a id="T'+currentTab+'B'+i+'" class="bookmarkLink shortcut tile zoomTarget" onclick="executeBookmark(&quot;'+homeBookMarks[i].url+'&quot;,&quot;T'+currentTab+'B'+i+'&quot;)" link="'+homeBookMarks[i].url+'" href="#" style="/*width: 320px;*/  /*height: 200px;*/ padding: 0; box-shadow: 0 0px 30px rgba(0, 0, 0, 0.8);"><img src="'+homeBookMarks[i].thumbUrl+'" alt=""><img src="'+homeBookMarks[i].thumbUrl+'" class="textBG" alt=""><small class="homeBookMarkText hoverBlur" style="font-weight: bold; color: rgba(255, 255, 255, 0.9); font-size: 14px;" class="t-overflow">'+homeBookMarks[i].name+' <span> '+simpleUrl+' </span></small></a>'
			}
			//////console.log("CurrentHOME LINKS: ",currentHomeLinks);

			var classToAppend = "";

			if (!fancyRendering)
				classToAppend = "classicWebviewRendering";
			
			$("#allTabsC").append(' <div id="view0" class="item active"><div class="zoomContainer"><div class="bookmarks">'+currentHomeLinks+'</div></div><webview id="webview0" class="topMargin" useragent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36" partition="persist:trusted" src="" style="width:100%; /*width:99.5%;*/ height:100%; /*left: 0.25%;*/" class="'+classToAppend+'"></webview></div>');

	$('.adaptiveSearch').on("click",function(){
		console.log("adaptive search called");
		adaptiveSearchCall(this);
	});

	console.log("setting hover: ",$('#view0 > .box'));

	$('#view0 > .box').hover(function() {
	console.log("hoveredb");
	var maxHeight = 55;
	if (!controlsShowing) {
		$("#navigationBar").css("height",maxHeight+"px");
		$("#blur2").css("height",maxHeight+"px");
		$("#allTabsC").css("height","calc(100% - "+(maxHeight-15)+"px)");
		$(".newNavButton").removeClass("hiddenOpacity");
		$(App.minimize_button).removeClass("hidden");
		$(App.maximize_button).removeClass("hidden");
		$(App.close_button).removeClass("hidden");
		$("#tabNav").removeClass("hidden");
		controlsShowing = true;
	}
				

			}, function() {
				//out of hover
				console.log("not hovering")
			});

//nodeintegration

		//$(".mainResult").zoomTarget();
			
			
			/*allowtransparency*/
			//availableTabs.push(0);
			var webview = document.querySelector('#webview'+currentTab);

			webview.previewImage = "temporary/homepage_preview.png";

			    webview.onmousemove = handleMouseMove;
    function handleMouseMove(event) {
        var eventDoc, doc, body;

        event = event || window.event; // IE-ism

        // If pageX/Y aren't available and clientX/Y are,
        // calculate pageX/Y - logic taken from jQuery.
        // (This is to support old IE)
        if (event.pageX == null && event.clientX != null) {
            eventDoc = (event.target && event.target.ownerDocument) || document;
            doc = eventDoc.documentElement;
            body = eventDoc.body;

            event.pageX = event.clientX +
              (doc && doc.scrollLeft || body && body.scrollLeft || 0) -
              (doc && doc.clientLeft || body && body.clientLeft || 0);
            event.pageY = event.clientY +
              (doc && doc.scrollTop  || body && body.scrollTop  || 0) -
              (doc && doc.clientTop  || body && body.clientTop  || 0 );
        }

        // Use event.pageX / event.pageY here
				mouseX = event.pageX;
				mouseY = event.pageY;
    }

		
			webview.currentAtHome = true;
			webview.canGoToHome = true;
			//webview.loadingFromHome = true;
			//$('#webview'+currentTab).fadeOut();
			//$('#webview'+currentTab).addClass("noOpacity");
			$("#reloadButton").hide();
			//setTimeout(function(){document.querySelector('#backButton').disabled = true;}, 2000);
		}
	}
	//initHome();
	//newTab();
	//blurThumbs(0); // We don't need this anymore. We now use live experimental blur	

setTimeout(function(){
						newTab();
						//closeTab(0);
					$("#allTabs").css("opacity",1);
						//win.show();
					}, 1000);

	function extractHostname(url) {
    var hostname;
    //find & remove protocol (http, ftp, etc.) and get hostname

    if (url.indexOf("://") > -1) {
        hostname = url.split('/')[2];
    }
    else {
        hostname = url.split('/')[0];
    }

    //find & remove port number
    hostname = hostname.split(':')[0];
    //find & remove "?"
    hostname = hostname.split('?')[0];

    if (hostname.split('.').length == 3) { //Get just the name if the website
 	hostname = hostname.split('.')[1];
	hostname = hostname.charAt(0).toUpperCase() + hostname.slice(1); //Make first character capital
    }

    return hostname;
}

function changeBookMarkDetails() {

	for (var i = 0; i < homeBookMarks.length; i++) {
		if (homeBookMarks[i].id == currentBookmarkId) {
			homeBookMarks[i].name = $("#favouriteNameInput").val();
			homeBookMarks[i].description = $("#favouriteDescInput").val();
			break;
		}
	}
  
  localStorage.setItem('storedBookmarksWebApp', JSON.stringify(homeBookMarks));
closeSideBar();
	
}

function editFavourites(url) {
	for (var i = 0; i < homeBookMarks.length; i++) {
		if (homeBookMarks[i].url == url) {
			$("#favouriteNameInput").val(homeBookMarks[i].name);
			$("#favouriteDescInput").val(homeBookMarks[i].description);
			$("#favouritesBgAll").attr("src",homeBookMarks[i].thumbUrl);
			$("#favourites_preview").attr("src",homeBookMarks[i].thumbUrl);
			$("#favourites_preview").removeClass("hidden");
			currentBookmarkId = homeBookMarks[i].id;
			break;
		}
	}
  
  localStorage.setItem('storedBookmarksWebApp', JSON.stringify(homeBookMarks));

}


function addToFavourites(webview,title) {

	homeBookMarks.unshift({
		name : extractHostname(webview.src),
		id: homeBookMarks_lastId+1,
		url : webview.src,
		description: title,
		thumbUrl : "",
		animatedThumbUrl : "" 
	});
	homeBookMarks_lastId = homeBookMarks_lastId+1;
	currentBookmarkId = homeBookMarks_lastId;
	$("#favouriteNameInput").val(homeBookMarks[0].name);
	$("#favouriteDescInput").val(homeBookMarks[0].description);
	localStorage.setItem('storedBookmarksWebApp', JSON.stringify(homeBookMarks));
	localStorage.setItem('homeBookMarks_lastId', JSON.stringify(homeBookMarks_lastId));
	handleLoadCommit();
  
  if (!webview.currentAtHome) { //Let's make sure we aren't home
			webview.captureVisibleRegion(function(img){
				//$('#navBG').attr("src",img);
		resizeBookmark(img,0,0,300,136,webview,title);
              
              
              
				//universalBlur(img,blurredSuggestion,$(webview).width(),$(webview).height(),2,2);
				
				//if (keepBluring)
					//autoBlur();
				
				/*let jpgFile = img.toJPEG(90);
				jetpack.writeAsync(fullPath, jpgFile)
				.then(function() {
					// some other application code after saving
				});*/
			});
  }
  
}


//Later on we want users to enter custom information such as titles, hence why this is split
function createFavourite() {
  var webview = document.querySelector('#webview'+currentTab);
  if (webview.bookmarked)
  	editFavourites(webview.src);
  else
	addToFavourites(webview,webview.documentTitle);
  
}

//Yes I know a bookmark and favourite are the same thing
function deleteBookmark(bookMarkId) {
	$(".Bookmark"+bookMarkId+" > a").addClass("removeBookMark");
	setTimeout(function(){$(".Bookmark"+bookMarkId).remove(); }, 800);
	for (var i = 0; i < homeBookMarks.length; i++) {
		if (homeBookMarks[i].id == bookMarkId) {
			homeBookMarks.splice(i, 1);
			break;
		}
	}
  
  localStorage.setItem('storedBookmarksWebApp', JSON.stringify(homeBookMarks));

}

function deleteCurrentBookMark() {
	deleteBookmark(currentBookmarkId);
	closeSideBar();
	handleLoadCommit();
}

function findBookmarkWithUrl(url) {
	var foundMatch = false;
	for (var i = 0; i < homeBookMarks.length; i++) {
		if (homeBookMarks[i].url == url) {
			foundMatch = true;
			return foundMatch;
			break; //Shouldn't be necessary, but hey why not haha
		}
	}

	return foundMatch;

}

var executeBookmarkLink = "";

function activateBookmark() {
	console.log("we are here A");
	if (ignoreLink) {
		ignoreLink = false;
	} else {
	var webview = document.querySelector('#webview'+currentTab);

	if (useZoomAnimations) {
			$('#view'+currentTab+' > .zoomContainer').addClass("hidden"); $("#tabsNavigator").removeClass("hidden"); 
			if (!$("#allTabs").hasClass("allTabsReseize")){
				$("#navigationBar").addClass("navShadow");
				$(".controlButton").removeClass("active");
				$(win.minimize_button).addClass("active");
				$(win.maximize_button).addClass("active");
				$(win.close_button).addClass("active");
				$("#blur2").removeClass("hidden");
			}
			$(".homeBookMarkText").addClass("hoverBlur");
			if (useZoomAnimations)
				$('#webview'+currentTab).removeClass("noOpacity");
//$('#webview'+currentTab).removeClass("hidden");




	setTimeout(function(){
		webview.src = executeBookmarkLink;
		webview.loadingFromHome = false;
		$('#webview'+currentTab).show();
	}, 500);

		
	
	} else {
		webview.src = executeBookmarkLink;
		webview.loadingFromHome = false;
		setTimeout(function(){
			$('#view'+currentTab+' > .zoomContainer').hide();
			$("#tabsNavigator").removeClass("hidden"); 
			if (!$("#allTabs").hasClass("allTabsReseize")){
				$("#navigationBar").addClass("navShadow");
				$(".controlButton").removeClass("active");
				$(win.minimize_button).addClass("active");
				$(win.maximize_button).addClass("active");
				$(win.close_button).addClass("active");
				$("#blur2").removeClass("hidden");
			}
			$(".homeBookMarkText").addClass("hoverBlur");
			webview.loadingFromHome = false;
			$('#webview'+currentTab).show();

			}, 450);
	}
	console.log("executeBookmarkLink",executeBookmarkLink);
	}

}

	function executeBookmark(urlPassed,id) {

		$("#"+id).addClass("hiddenOpacity");

		var bookmarkPositionX = $("#"+id).offset().left - $(window).scrollLeft();
		var bookmarkPositionY = $("#"+id).offset().top - $(window).scrollTop();

		console.log("bookmarkPositionX: ",bookmarkPositionX);
		console.log("bookmarkPositionY: ",bookmarkPositionY);
		//console.log("div b: ",$("#"+id)[0]);

		if (useZoomAnimations) {
			$(".box").css("left",bookmarkPositionX+160);
		$(".box").css("bottom",win.height - (bookmarkPositionY+100));

		//$('#view'+currentTab+' > .box').click();
		
		animatedZoomBox($('#view'+currentTab+' > .box')[0]);
		}
		

		
		executeBookmarkLink = urlPassed;
		if (!useZoomAnimations) {
			activateBookmark();
		}
		console.log("executeBookmarkLink: ",executeBookmarkLink);
		$(".homeBookMarkText").removeClass("hoverBlur");
	   	//$('#view'+currentTab+' > .zoomContainer').fadeOut(500);


		if (useZoomAnimations)
			$('#view'+currentTab+' > .zoomContainer').addClass("noOpacity");
		currentAtHome = false;
		var webview = document.querySelector('#webview'+currentTab);
		webview.loadingFromHome = true;
		webview.loadingFromSearch = false;
		webview.currentAtHome = false;
		$("#reloadButton").show();
		$('#view'+currentTab+' > .zoomContainer > .bookmarks > .bookmarksOuter > .bookmarkLink').removeClass("currentSelection");
		$('#view'+currentTab+'> .zoomContainer > .searchSuggestions > .blackBgInner > .zoomTarget').removeClass("currentSelection");
		console.log("idss",id);
		$("#"+id).addClass("currentSelection");
		//webview.src = $(this).attr('link');
		var liink = urlPassed;//$(this).attr('link');
		//webview.src = liink;
		
		document.querySelector('#backButton').disabled = false;
		document.querySelector('#forwardButton').disabled = !webview.canGoForward();
		
		setTimeout(function(){//$('#webview'+currentTab).fadeIn(300);
		$('#view'+currentTab+' > .zoomContainer > .bookmarks > .catalogueTitle').addClass("hiddenOpacity");
//$('#webview'+currentTab).removeClass("noOpacity");
//$('#webview'+currentTab).removeClass("hidden");
 }, 300);

	

		console.log("executeBookmarkLink2: ",executeBookmarkLink);

		
	}

	/*
	$('.bookmarkLink').on("click",function(){
		
		////console.log("ACTIVATED");
	   $('#view'+currentTab+' > .zoomContainer').fadeOut(500);
		currentAtHome = false;
		var webview = document.querySelector('#webview'+currentTab);
		webview.loadingFromHome = true;
		webview.loadingFromSearch = false;
		$("#reloadButton").show();
		$('#view'+currentTab+' > .zoomContainer > .bookmarks > .bookmarksOuter > .bookmarkLink').removeClass("currentSelection");
		$('#view'+currentTab+'> .zoomContainer > .searchSuggestions > .blackBgInner > .zoomTarget').removeClass("currentSelection");
		$(this).addClass("currentSelection");
		//webview.src = $(this).attr('link');
		var liink = $(this).attr('link');
		//webview.src = liink;
		
			document.querySelector('#backButton').disabled = false;
		document.querySelector('#forwardButton').disabled = !webview.canGoForward();
		
		setTimeout(function(){$('#webview'+currentTab).fadeIn(300); }, 300);
		setTimeout(function(){$('#view'+currentTab+' > .zoomContainer').addClass("hidden"); $("#tabsNavigator").removeClass("hidden");}, 500);
		setTimeout(function(){webview.src = liink;  webview.loadingFromHome = false;}, 1000);
	});*/

	function gotToSearch(link) {
		//$('#view'+currentTab+' > .zoomContainer').fadeOut(500);

		console.log("check link: ",link);

		if (link.indexOf("nyika://history") == 0) {
			link = "file://"+process.cwd()+"/apps/extern.web.app/control_pages/history_view.html";
		}

		console.log("new link: ",link);


		if (useZoomAnimations)
			$('#view'+currentTab+' > .zoomContainer').addClass("noOpacity");
		currentAtHome = false;
		var webview = document.querySelector('#webview'+currentTab);
		webview.currentAtHome = false;
		webview.loadingFromHome = true;
		webview.loadingFromSearch = true;
		$("#reloadButton").show();
		
		document.querySelector('#backButton').disabled = false;
		
		document.querySelector('#forwardButton').disabled = !webview.canGoForward();
		
		if (useZoomAnimations) {
			setTimeout(function(){
				//$('#webview'+currentTab).removeClass("hidden");
				$('#webview'+currentTab).show();
				$('#webview'+currentTab).removeClass("noOpacity");
			}, 300);
		} else {
			$('#webview'+currentTab).show();
		}
		
		
		setTimeout(function(){
			if (useZoomAnimations)
				$('#view'+currentTab+' > .zoomContainer').addClass("hidden");
			else 
				$('#view'+currentTab+' > .zoomContainer').hide();

			$("#tabsNavigator").removeClass("hidden");
		}, 500);
		
		setTimeout(function(){
			if (link.indexOf("/") == 0) {
				webview.src = "file://"+link;
			} else {
				webview.doNotAddToSuggestions = true;
				webview.src = link;
			}
			
		}, 1000);
		
		setTimeout(function(){
			webview.loadingFromHome = false;
		}, 500);
	}

	$('.mainResult').on("click",function(){
		$(this).addClass("currentSelection");
		var link = $(this).attr('link');
		//$('#view'+currentTab+'> .zoomContainer > .bookmarks > .bookmarksOuter > .bookmarkLink').removeClass("currentSelection");
		//$('#view'+currentTab+'> .zoomContainer > .searchSuggestions > .blackBgInner > .zoomTarget').removeClass("currentSelection");
		//$(this).addClass("currentSelection");
		gotToSearch(link);
	});

	if (localStorage.getItem('searchEngine') == null) {
		var searchEngine = "https://duckduckgo.com/?q="; //default search engine
		$("#searchEnginesDropdown").text('DuckDuckGo');
		var ssearchEngineName = 'DuckDuckGo';
	} else {
		var searchEngine = JSON.parse(localStorage.getItem('searchEngine'));
		var ssearchEngineName = JSON.parse(localStorage.getItem('searchEngineName'));
	}
	$("#searchEnginesDropdown").text(ssearchEngineName);

	//https://www.google.com/?#q=

	function setSearchEngine(engine,name) {
		searchEngine = engine;
		$("#searchEnginesDropdown").text(name);
		localStorage.setItem('searchEngine', JSON.stringify(searchEngine));
		localStorage.setItem('searchEngineName', JSON.stringify(name));
		
	}

	function adaptiveSearchCall(searchDiv) {
		var webview = document.querySelector('#webview'+currentTab);
		console.log("adaptive search called");
		$(this).addClass("currentSelection");
		console.log("valid url not called");
		if (validURL($(searchDiv).attr("searchTerm"))){
			let regexp = /(http|https|file|ftp)/g
			if(regexp.test($(searchDiv).attr("searchTerm"))){
				var link = $(searchDiv).attr("searchTerm");
			}else{
				var link = "http://"+$(searchDiv).attr("searchTerm");
			}

			webview.searchTerm = link;
			webview.searchTermIsUrl = true;
		} else {
			var link = searchEngine+$(searchDiv).attr("searchTerm");
			var webview = document.querySelector('#webview'+currentTab);
			webview.searchTerm = $(searchDiv).attr("searchTerm");
		}

		$(searchDiv).addClass("currentSelection");

		//$('#view'+currentTab+'> .zoomContainer > .bookmarks > .bookmarksOuter > .bookmarkLink').removeClass("currentSelection");
		//$('#view'+currentTab+'> .zoomContainer > .searchSuggestions > .blackBgInner > .zoomTarget').removeClass("currentSelection");
		//$(this).addClass("currentSelection");
		gotToSearch(link);
	}



	/*$('.adaptiveSearch').on("click",function(){
		console.log("adaptive search called");
		adaptiveSearchCall(this);
	});*/

	/*
	$('.searchResult').on("click",function(){
	////console.log("search result clicked");
		$(this).addClass("currentSelection");

		var link = searchEngine+$(this).attr("searchTerm");
		gotToSearch(link);
	});*/

	/*$('.bookmarkLink').onclick = function(e) {
		////console.log("CLICKED BOOKMARK: ",e);
	}*/

	/*$('.bookmarkLink').one('click',function()
	{
		//$(".bookmarkLink").removeClass("currentSelection");
		////console.log("CLICKED BOOKMARK: ",this.getAttribute("link"));
		//$(this).addClass("currentSelection");
	});*/


	function openFromHomeTab(requestedURL) {
		//$('#webview'+currentTab).remove();
		
		//$('#view'+currentTab).append('<webview id="webview'+currentTab+'" partition="trusted" src="'+requestedURL+'" style="width:100%;/*width:99.5%;*/ height:100%; /*left: 0.25%;*/"></webview>');
		//$('#webview'+currentTab).fadeOut(1);
		//$('#webview'+currentTab).removeClass("hidden");
		  
	}

	var screenshot = require('desktop-screenshot');

	function TakeDesktopScreenshot(X,Y,type,callbackfuntion){
		screenshot("screenshot"+imgNmbr+".png", {width: 400}, function(error, complete) {
			/*if(error)
				//console.log("Screenshot failed", error);
			else
			{
				//BlurScreenshot(X,Y,type,callbackfuntion);
			}*/
		});
	}



	var win = nw.Window.get();
	App.onOpenFiles = function(files){
		var webview = document.querySelector('#webview'+currentTab);
			
		if (webview == null) {
			setTimeout(function(){
				App.onOpenFiles(files);
			}, 100);
		} else {
		if (currentTab == 0 && currentAtHome){


			if (files[0] == "--private-session") {
				privateMode = true;
				sessionStoragePartition = 'partition="trusted"';
				$("#privateConnection").removeClass("hidden");
				newTab();
				closeTab(0);
				
				
				if (files.length != 1)
				gotToSearch(files[1]);
				
			} else {
				gotToSearch(files[0]);
			}


			//newWebview(files[0],false);
			
			console.log("used normal");
			//closeTab(currentTab);
			/*
			//$("webview0").remove();
			currentAtHome = false;
		var webview = document.querySelector('#webview'+currentTab);
		webview.loadingFromHome = false;
			webview.currentAtHome = false;
			$("#reloadButton").show();
			document.querySelector('#backButton').disabled = true;
			webview.src = files[0];
			webview.canGoToHome = false;
			setTimeout(function(){ $('#view'+currentTab+' > .zoomContainer').fadeOut(500);
			$('#webview'+currentTab).fadeIn(300);
								 }, 1000);
								 */
			
		}else{
			if (files[0] == "--private-session") {
				privateMode = true;
				sessionStoragePartition = 'partition="trusted"';
				newTab();
				closeTab(0);
				newWebview(files[1],false);
			} else {
				newWebview(files[0],false);
			}
				
			console.log("used other");
			$("#tabNave"+availableTabs[availableTabs.length-1])[0].click();
		}
		}
		
		

	};

	if (App.argv != null) {
		if (App.argv.length != 0) {
			App.onOpenFiles(App.argv);
		}
	}

	nw.App.on('onFileOpen', function() {
	  //////console.log('command line: ' );
	});

	/*win.addEventListener('onFileOpen', function (e) { //////console.log('command line: ' ); }, false);*/

	function BlurScreenshot(X,Y,width,height,callbackfuntion){
		var ScreenshotCanvas = document.createElement('canvas');
		var context = ScreenshotCanvas.getContext('2d');
		context.clearRect(0, 0, ScreenshotCanvas.width, ScreenshotCanvas.height);
		var imageObj = new Image();
		var x = X;//(-win.x);
		var y = Y;//-win.y;
		var blurEffect = 2;
		var saturationValue = 1.4;
		ScreenshotCanvas.width = width;
		ScreenshotCanvas.height = height;
		imageObj.onload = function() {
			context.drawImage(imageObj, x, y, width, height);
			//fs.unlink('screenshot'+imgNmbr+'.png');
			//imgNmbr++;
			callbackfuntion();
		}
		imageObj.src = 'screenshot'+imgNmbr+'.png';
		var context = ScreenshotCanvas.getContext('2d');
		setTimeout(function(){
			context._blurRect(x, y, width, height, blurEffect, saturationValue);
			setMenuBg(ScreenshotCanvas,X,Y);
		}, 100);
	}


	function resizeBookmark(img, X,Y,width,height,webview,title){
		var ScreenshotCanvas = document.createElement('canvas');
		var context = ScreenshotCanvas.getContext('2d');
		context.clearRect(0, 0, ScreenshotCanvas.width, ScreenshotCanvas.height);
		var imageObj = new Image();
		var favIconObj = new Image();
		var x = X;//(-win.x);
		var y = Y;//-win.y;
		var blurEffect = 2;
		var saturationValue = 1.4;
		var iconLoaded = false;
		ScreenshotCanvas.width = width;
		ScreenshotCanvas.height = height;
		imageObj.onload = function() {
			context.drawImage(imageObj, x, y, width, height);

			if (iconLoaded)
				context.drawImage(favIconObj, (width/2)-15, (height/2)-15, 30, 30);
			//fs.unlink('screenshot'+imgNmbr+'.png');
			//imgNmbr++;
			imgData = ScreenshotCanvas.toDataURL('image/jpeg');
				//callback(imgData);
		$("#favouritesBgAll").attr("src",imgData);
		$("#favourites_preview").attr("src",imgData);
		$("#favourites_preview").removeClass("hidden");
		if (currentBookmarkId != -1)
				for (var i = 0; i < homeBookMarks.length; i++) {
					if (homeBookMarks[i].id == currentBookmarkId) {
						homeBookMarks[i].thumbUrl = imgData;
						break;
					}
				}
          localStorage.setItem('storedBookmarksWebApp', JSON.stringify(homeBookMarks));
			
			/*homeBookMarks.unshift({
		name : title,
		url : webview.src,
		thumbUrl : imgData,
		animatedThumbUrl : "" 
	});*/
		console.log("Bookmark added: ",homeBookMarks);
		}

		if (webview.favIcon != "undefined"){
			favIconObj.src = webview.favIcon;
			favIconObj.onload = function() {
				iconLoaded = true;
				imageObj.src = img;
				}
		} else {
			imageObj.src = img;
		}

	}

	$('#tabx1').click(function(e){
		e.stopPropagation();
		var goTo = $(this).data('slide-to');
	  	$('.carousel-inner .item').each(function(index){
			if($(this).data('id') == "view"+goTo){
		  		goTo = index;
		  		return false;
			}
	  	});
		$('#myCarousel').carousel(goTo);
	});

	//This funvtion is designed to detect whether it's a url or a search term and act accordingly
	//Thanks to: http://stackoverflow.com/questions/5717093/check-if-a-javascript-string-is-a-url
	function validURL(str){
		if (str == "file://"+process.cwd()+"/apps/extern.web.app/control_pages/history_view.html") {
			return true;
		} else {
			// var regexp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/
		var regexp = /([a-zA-Z0-9]*\.)?[a-zA-Z0-9]*\.(fr|com|eu|io|co|org|uk|net|int|edu|gov|mil|ai|ae|be|nl|bz|ci|ca|cn|cz|us|eu|es|au|html)(\.(fr|com|eu|co|io|org|net|int|edu|uk|gov|mil|ai|ae|be|nl|bz|ci|ca|cn|cz|us|eu|es|au|html))?/g
		return regexp.test(str);
		}
		
	}

	function goToRequest(request){
		if (validURL(request)){
			console.log("it's a valid url: ",request);
			navigateTo(document.querySelector('#urlInput').value,currentTab);
		}	
	}

	function searchFocusIn(divx) {
		//this = div;
		var webview = document.querySelector('#webview'+currentTab);
			closeSideBar();
		
			keepBluring = true;
			//autoBlur();
			$("#secureConnection2-text").fadeIn();
			$("#secureConnection2").addClass("hidden");
			
			$(divx).select();

				if (webview.currentAtHome){
					var suggestionsDiv = '#suggestionsHomePage'+currentTab;
				}else{
					var suggestionsDiv = '#allTabs > .searchSuggestions';
				}

				$(suggestionsDiv +' > .blackBgInner > .adaptiveSearch').attr("searchterm",$(divx).val());

				
			
			if (!adaptiveFaded) {
				//$('#suggestionsHomePage'+currentTab+' > .blackBgInner > .adaptiveSearch').fadeOut();
				adaptiveFaded = true;
			}

			

			if(webview.currentAtHome) {
				$('#view'+currentTab+' > .zoomContainer > .searchSuggestions').fadeIn();

			//$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .mainResult').fadeOut();
			if ($('#searchFromHomePage'+currentTab).val() == "")
				$('#suggestionsHomePage'+currentTab+' > .blackBgInner > .mainResult').css("display","none");
				
			$('#suggestionsHomePage'+currentTab+' > .blackBgInner > .mainResult').addClass('hiddenOut');

			$('#suggestionsHomePage'+currentTab).css("display","none");
				
			$('#suggestionsHomePage'+currentTab).addClass('hiddenOut');
			//$('#suggestionsHomePage'+currentTab+' > .blackBgInner > .adaptiveSearch').fadeOut();

	

			}else{
				//$('#allTabs > .searchSuggestions').fadeIn();

			$('#allTabs > .searchSuggestions > .blackBgInner > .mainResult').hide();
	$('#allTabs > .searchSuggestions > .blackBgInner > .mainResult').addClass('hiddenOut');
			//$('#suggestionsHomePage'+currentTab+' > .blackBgInner > .adaptiveSearch').fadeOut();
			}

			$(suggestionsDiv).fadeIn();

			$(suggestionsDiv +' > .blackBgInner').show();
			$('#allTabs > .searchSuggestions > .blackBgInner > .adaptiveSearch').hide();
				$('#suggestionsHomePage'+currentTab).show();
				
			$('#suggestionsHomePage'+currentTab).removeClass('hiddenOut');


			console.log("current text is now: ",$(divx).val());
			//console.log("current text in adaptive: ",$(suggestionsDiv +' > .blackBgInner > .adaptiveSearch'));
	}

	function searchFocusOut() {
		var webview = document.querySelector('#webview'+currentTab);
			keepBluring = false;
			$("#secureConnection2").removeClass("hidden");
			//$('#allTabs > .searchSuggestions > .blackBgInner > .adaptiveSearch').fadeOut();
			//$('#suggestionsHomePage'+currentTab+' > .blackBgInner > .adaptiveSearch').fadeOut();
			adaptiveFaded = false;
			setTimeout(function(){
				var webview = document.querySelector('#webview'+currentTab);
				if (webview.currentAtHome) {
					//$('#view'+currentTab+' > .zoomContainer > .searchSuggestions').fadeOut();
					$('#suggestionsHomePage'+currentTab).css("display","none");
					$('#suggestionsHomePage'+currentTab+' > .blackBgInner > .mainResult').css("display","none");
				}else {
					//$('#allTabs > .searchSuggestions').fadeOut();
					$('#allTabs > .searchSuggestions').css("display","none");
				}
			}, 500);
	}

	function loadRecommendedSearches(suggestionsDiv) {

		//console.log("suggestions loaded");
		

		/*Sample recommendedSearches formatting
		{ 
				id: 0,
				name: "eXtern OS",
				icon: "",
				accessedTimes: 0,
				isSearch: true
			},
			{
				id: 1,
				name: "eXtern OS",
				icon: "",
				accessedTimes: 0,
				url: "https://externos.io",
				isSearch: false
			}
			*/

		var recommendedSuggestions = [
			{
				id: 0,
				name: "Veel",
				icon: "Bookmarks/recommendations/veel.png",
				url: "https://veel.tv"
			},
			{
				id: 1,
				name: "eXtern OS",
				icon: "Bookmarks/recommendations/externos.io",
				url: "https://externos.io"
			},
			{
				id: 2,
				name: "DuckDuckGo",
				icon: "Bookmarks/recommendations/duckduckgo.com",
				url: "hhttps://duckduckgo.com"
			},
		];

		//console.log("div options: ",$(suggestionsDiv+' > .blackBgInner > .searchHistoryOptions'));

		$(suggestionsDiv+' > .blackBgInner > .searchHistoryOptions').empty();
		$(suggestionsDiv+' > .blackBgInner > .defaultSearchSuggestions > .suggestionsBody').empty();

		for (var i = 0; i < recommendedSuggestions.length; i++) {
			$(suggestionsDiv+' > .blackBgInner > .defaultSearchSuggestions > .suggestionsBody').append('<a href="#" class="suggestedWeb" suggestionUrl="'+recommendedSuggestions[i].url+'"><img src="'+recommendedSuggestions[i].icon+'"> <p>'+recommendedSuggestions[i].name+'</p></a>');
		}

		for (var i = recommendedSearches.length-1; i > -1; i--) {
			if (recommendedSearches[i].isSearch) {
				$(suggestionsDiv+' > .blackBgInner > .searchHistoryOptions').append('<div class="p-l-5 zoomTarget searchResult" title="'+recommendedSearches[i].name+'" searchTerm="'+recommendedSearches[i].name+'"><div class="pull-left"><span class="icon searchIcon">&#61788;</span></div><div class="media-body"><p class="searchMainX">'+recommendedSearches[i].name+'</p></div></div>');
			} else if (recommendedSearches[i].icon != "") {
				$(suggestionsDiv+' > .blackBgInner > .searchHistoryOptions').append('<div class="p-l-5 zoomTarget searchResult directLink" title="'+recommendedSearches[i].name+'" searchTerm="'+recommendedSearches[i].name+'"><div class="pull-left"><span class="icon searchIcon">&#61788;</span></div><div class="media-body"><p class="searchMainX">'+recommendedSearches[i].name+'</p></div></div>');
			} else {
				if (recommendedSearches[i].name != "")
					$(suggestionsDiv+' > .blackBgInner > .searchHistoryOptions').append('<div class="p-l-5 zoomTarget searchResult directLink" title="'+recommendedSearches[i].url+'" searchTerm="'+recommendedSearches[i].url+'"><div class="pull-left"><span class="icon searchIcon">&#61838;</span></div><div class="media-body"><p class="searchMainX">'+recommendedSearches[i].url+' - '+recommendedSearches[i].name+'</p></div></div>');
				else
					$(suggestionsDiv+' > .blackBgInner > .searchHistoryOptions').append('<div class="p-l-5 zoomTarget searchResult directLink" title="'+recommendedSearches[i].url+'" searchTerm="'+recommendedSearches[i].url+'"><div class="pull-left"><span class="icon searchIcon">&#61838;</span></div><div class="media-body"><p class="searchMainX">'+recommendedSearches[i].url+'</p></div></div>');
			}

			if (i == recommendedSearches.length-3)
				break;
		}

		$('.searchResult').on("click",function(){
			var webview = document.querySelector('#webview'+currentTab);
				$(this).addClass("currentSelection");

				if ($(this).hasClass("directLink")) {
					var link = $(this).attr("searchTerm");
					webview.searchTerm = $(this).attr("searchTerm");
					webview.searchTermIsUrl = true;
				} else {
					var link = searchEngine+$(this).attr("searchTerm");
					webview.searchTerm = $(this).attr("searchTerm");
				}
				
				gotToSearch(link);
			}); 


			$('.suggestedWeb').on("click",function(){
				var webview = document.querySelector('#webview'+currentTab);
				$(this).addClass("currentSelection");

				var link = $(this).attr("suggestionUrl");
				webview.searchTerm = link;
				webview.searchTermIsUrl = true;
				
				gotToSearch(link);
			}); 

				$(suggestionsDiv +' .defaultSearchSuggestions').show();
				$(suggestionsDiv +' .searchHistoryOptions').show();
		
	}

	//$('#view'+currentTab+' > .zoomContainer > .searchSuggestions').fadeOut();
	//$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .mainResult').fadeOut();
	$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .mainResult').css("display","none");
	$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .mainResult').addClass('hiddenOut');

	$('#allTabs > .searchSuggestions > .blackBgInner > .mainResult').hide();
	$('#allTabs > .searchSuggestions > .blackBgInner > .mainResult').addClass('hiddenOut');
	var keepBluring = false;



	$('#urlInput')
		.focusin(function() {
			loadRecommendedSearches(".searchSuggestions");
			var rect = $("#urlWrap")[0].getBoundingClientRect();
		$(".searchSuggestions").css("left",rect.left+2);
			searchFocusIn(this);
		})
		.focusout(function() {
			searchFocusOut(); //FIXME: restore this
		});

	win.on('resize', function (width,height) {
		setTimeout(function() {
		var rect = $("#urlWrap")[0].getBoundingClientRect();
		$(".searchSuggestions").css("left",rect.left+2);
		}, 100);
	});

	function goToHome(){
		console.log("we are going home A")
      var webview = document.querySelector('#webview'+currentTab);
		if ($('#view'+currentTab+' > .zoomContainer > .bookmarks > .bookmarksOuter > .bookmarkDiv > .currentSelection').length || $('#suggestionsHomePage'+currentTab+' > .blackBgInner .currentSelection').length){
			$('#view'+currentTab+' > .zoomContainer > .bookmarks > .catalogueTitle').removeClass("hiddenOpacity");
			//$('#view'+currentTab+' > .testZoomBox').click();
			console.log("we are going home B");
			if (useZoomAnimations)
				animatedZoomBox($('#view'+currentTab+' > .box')[0]);
			$('#view'+currentTab+' > .zoomContainer > .bookmarks > .bookmarksOuter > .bookmarkDiv > .currentSelection').removeClass("hiddenOpacity");
			$(".homeBookMarkText").removeClass("hoverBlur");
			currentAtHome = true;
			webview.currentAtHome = true;
			$("#reloadButton").hide();
			document.querySelector('#backButton').disabled = !webview.canGoBack();
			document.querySelector('#forwardButton').disabled = webview.canGoBack();
			//$("#tabsNavigator").addClass("hidden");
			//document.querySelector('#backButton').disable = true;
			//$('#webview'+currentTab).fadeOut(300);
			if (useZoomAnimations)
				$('#webview'+currentTab).addClass("noOpacity");
			//$('#webview'+currentTab).addClass("hidden");
			$('#webview'+currentTab).hide();
			$("#navigationBar").removeClass("navShadow");
			$(".controlButton").removeClass("active");
			$("#navigationBar").removeClass("active");
			$(win.minimize_button).removeClass("active");
			$(win.maximize_button).removeClass("active");
			$(win.close_button).removeClass("active");
			$("#blur2").addClass("hidden");

			setTimeout(function(){
				//$('#view'+currentTab+" > .zoomContainer").fadeIn(300);
				if (useZoomAnimations)
					$('#view'+currentTab+' > .zoomContainer').removeClass("noOpacity");
			}, 300);

			setTimeout(function(){
				$(".homeBookMarkText").addClass("hoverBlur");
				if ($("#searchFromHomePage"+currentTab).val() != "")
				 	$("#searchFromHomePage"+currentTab).focus(); 
			}, 1000);
			
			if (useZoomAnimations)
				$('#view'+currentTab+" > .zoomContainer").removeClass("hidden");
			else
				$('#view'+currentTab+" > .zoomContainer").show();

			setTimeout(function(){
				$('#view'+currentTab+' > .zoomContainer').trigger( "click" );
			}, 50);
			
			setTimeout(function(){
				//$('#view'+currentTab+' > .zoomContainer > .searchSuggestions').fadeOut();
				$('#view'+currentTab+' > .zoomContainer > .searchSuggestions').css("display","none");
			}, 100);		
		} else {
          if (webview.canGoForward()) {
						console.log("closed tab from here");
            closeTab(currentTab); //This originated from a bookmark that has been removed
	}
        }
	}

	function reloadWebView(){
		var webview = document.querySelector('#webview'+currentTab);
		if (webview.loading) {
	  		webview.stop();
		} else {
	  		webview.reload();
		}
	}

	function loadControls(){
		document.querySelector('#backButton').onclick = function() {
			closeMenu();
			console.log("go back clicked");
			var webview = document.querySelector('#webview'+currentTab);
			if (canGoBack){
				console.log("it thinks it can go back");
				webview.back();
				document.querySelector('#backButton').disabled = !webview.canGoBack();
				$("#reloadButton").show();	
			}else{
				console.log("trigger go home");
				goToHome();
			}
	  	};

	  	document.querySelector('#forwardButton').onclick = function() {
			var webview = document.querySelector('#webview'+currentTab);

		 	if (webview.currentAtHome){
			  	document.querySelector('#backButton').disabled = false;
			  	document.querySelector('#forwardButton').disabled = !webview.canGoForward();
			  	$("#reloadButton").show();
			  	currentAtHome = false;
			  	webview.currentAtHome = false;
			  	//$('#view'+currentTab+' > .bookmarks > .bookmarksOuter > .currentSelection').trigger( "click" );
			  	if ($('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .currentSelection').length) {
				  	$('#view'+currentTab+' > .zoomContainer > .searchSuggestions').show();
				  	$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .currentSelection').click ();
				  
				  //setTimeout(function(){$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .currentSelection').click ();}, 10);
			  	}else{
				  	$('#view'+currentTab+' > .zoomContainer > .bookmarks > .bookmarksOuter > .currentSelection').click ();
			  	}
		  	}else {
				webview.forward();
		  	}
	  	};

	  	document.querySelector('#home').onclick = function() {
			var webview = document.querySelector('#webview'+currentTab);
			navigateTo('http://www.github.com/',currentTab);
	  	};

	  	document.querySelector('#reloadButton').onclick = function() {
			reloadWebView()
	  	};

	  	document.querySelector('#reload').addEventListener('webkitAnimationIteration', function() {
			if (!webview.loading) {
				document.body.classList.remove('loading');
		  	}
		});

	  	$("#urlInput").keyup(function (e) {
			if (e.keyCode == 13) { //Press ENTER

				var webview = document.querySelector('#webview'+currentTab);

				if (webview.currentAtHome){
					var suggestionsDiv = '#suggestionsHomePage'+currentTab;
				}else{
					var suggestionsDiv = '#allTabs > .searchSuggestions';
				}


				console.log("trying to click adaptive");
				console.log("here is clicked adaptive",$(suggestionsDiv +' > .blackBgInner > .adaptiveSearch'));

				if ($(suggestionsDiv +' > .blackBgInner > .mainResult').hasClass("hiddenOut"))
					$(suggestionsDiv +' > .blackBgInner > .adaptiveSearch').click();
				else
					$(suggestionsDiv +' > .blackBgInner > .mainResult').click();
			}
		});
		
		document.querySelector('#zoom-form').onsubmit = function(e) {
			e.preventDefault();
		  	var zoomText = document.forms['zoom-form']['zoom-text'];
		  	var zoomFactor = Number(zoomText.value);
		  	if (zoomFactor > 5) {
				zoomText.value = "5";
				zoomFactor = 5;
		  	} else if (zoomFactor < 0.25) {
				zoomText.value = "0.25";
				zoomFactor = 0.25;
		  	}
		  	webview.setZoom(zoomFactor);
		}
		

		document.querySelector('#zoom-in').onclick = function(e) {
			e.preventDefault();
		  	increaseZoom();
		}

		document.querySelector('#zoom-out').onclick = function(e) {
		  	e.preventDefault();
		  	decreaseZoom();
		}
		
		var findMatchCase = false;

		document.querySelector('#zoom').onclick = function() {
		  	if(document.querySelector('#zoom-box').style.display == '-webkit-flex') {
				closeZoomBox();
		  	} else {
				openZoomBox();
		  	}
		};

		document.querySelector('#find').onclick = function() {
			if(document.querySelector('#find-box').style.display == 'block') {
				document.querySelector('#webview'+currentTab).stopFinding();
				closeFindBox();
		  	} else {
				openFindBox();
		  	}
		};

		document.querySelector('#find-text').oninput = function(e) {
			var webview = document.querySelector('#webview'+currentTab);
		  	webview.find(document.forms['find-form']['find-text'].value,{matchCase: findMatchCase});
		}

		document.querySelector('#find-text').onkeydown = function(e) {
			var webview = document.querySelector('#webview'+currentTab);
		  	if (event.ctrlKey && event.keyCode == 13) {
				e.preventDefault();
				webview.stopFinding('activate');
				closeFindBox();
		  	}
		}

		document.querySelector('#match-case').onclick = function(e) {
		  	e.preventDefault();
			var webview = document.querySelector('#webview'+currentTab);
		  	findMatchCase = !findMatchCase;
		  	var matchCase = document.querySelector('#match-case');
		  	if (findMatchCase) {
				matchCase.style.color = "blue";
				matchCase.style['font-weight'] = "bold";
		  	} else {
				matchCase.style.color = "black";
				matchCase.style['font-weight'] = "";
		  	}
		  	webview.find(document.forms['find-form']['find-text'].value,{matchCase: findMatchCase});
		}

		document.querySelector('#find-backward').onclick = function(e) {
			e.preventDefault();
			var webview = document.querySelector('#webview'+currentTab);
			webview.find(document.forms['find-form']['find-text'].value,{backward: true, matchCase: findMatchCase});
		}

		document.querySelector('#find-form').onsubmit = function(e) {
			e.preventDefault();
			var webview = document.querySelector('#webview'+currentTab);
			webview.find(document.forms['find-form']['find-text'].value,{matchCase: findMatchCase});
		}
	}

//var tabId = 0;

const times = [];
let fps;

var minFps = 0;

var loadedNewsSources;


function refreshLoop() {
  window.requestAnimationFrame(() => {
    const now = performance.now();
    while (times.length > 0 && times[0] <= now - 1000) {
      times.shift();
    }
    times.push(now);
    fps = times.length;
	$("#fpsDebug").text(fps);
	if (fps < minFps) {
		$("#fpsDebugMin").text(fps);
		minFps = fps;
	}
	
    refreshLoop();
  });
}

function updateNewsSources() {
	var webview = document.querySelector('#webview'+currentTab);
	console.log("try updating news: ",allNewsSources);
	if (webview.loadedNewsSources != App.getAllNews()) {
		webview.loadedNewsSources = App.getAllNews();
		console.log("news div: ",$("#view"+currentTab+" .Bookmarkx"));
		
		loadedNewsSources = App.getAllNews();
		var allNewsSources = [];

		for (var i = 0; i < loadedNewsSources.length; i++) {
			//We can do a nested loop here because we have a max of 2 items before the third item anyway
			var alreadyAdded = false; //We do't want the same source all the time
			for (var j = 0; j < allNewsSources.length; j++) {
				if (allNewsSources[j].Source == loadedNewsSources[i].Source) {
					alreadyAdded = true;
					break; // No need to continue
				}
			}
			if (!alreadyAdded)
				allNewsSources.push(loadedNewsSources[i]);
		}

		if (allNewsSources.length < 3)
			allNewsSources = loadedNewsSources; //They most likely have 1 source selected (or two)... or none, but we take care of that in the next line anyway

		var currentHomeTopLinks = "";
		var tabId = currentTab;
		$("#topBookMarks"+currentTab).empty();
		if (allNewsSources.length >= 3) {
			
			

		//currentHomeTopLinks += '<div class="bookmarksOuter>'; //This is to make sure it's all centered
		//currentHomeTopLinks += '<div class="bookmarkDiv Bookmarkx"> <a id="TTop'+tabId+'BBXM" title="'+allNewsSources[0].title+'" class="bookmarkLink bookmarkTopLink shortcut tile" onclick="executeBookmark(&quot;'+allNewsSources[0].link+'&quot;,&quot;TTop'+tabId+'B'+i+'&quot;)" link="'+allNewsSources[0].link+'" href="#" style="width: auto; /*background-image:url(&quot;'+allNewsSources[0].link+'&quot;);*/   height: 250px; padding: 0; box-shadow: 0 0px 30px rgba(0, 0, 0, 0.8);"><img style="max-width: 375px;" src="'+allNewsSources[0].image+'" alt=""><small class="homeBookMarkText hoverBlur" style="/*font-weight: bold;*/ color: rgba(255, 255, 255, 0.9); font-size: 14px;" class="t-overflow">'+allNewsSources[0].Source+'</small><small class="detailedName"> '+allNewsSources[0].title+'</small></a></div>';
		for (var i = 0; i < 3; i++){

		var bookmarkWidth = 320;

		if (i == 1)
			bookmarkWidth = 520;

			//currentHomeTopLinks += '<div class="bookmarkDiv Bookmarkx"> <a id="TTop'+tabId+'B'+i+'" data-placement="top" data-original-title="'+allNewsSources[i].title+'" class="bookmarkLink bookmarkTopLink shortcut tile" onclick="executeBookmark(&quot;'+allNewsSources[i].link+'&quot;,&quot;TTop'+tabId+'B'+i+'&quot;)" link="'+allNewsSources[i].link+'" href="#" style="width: auto; /*background-image:url(&quot;'+allNewsSources[i].link+'&quot;);*/   height: 250px; padding: 0; box-shadow: 0 0px 30px rgba(0, 0, 0, 0.8);"><img style="max-width: 375px;" src="'+allNewsSources[i].image+'" alt=""><small class="homeBookMarkText hoverBlur" style="/*font-weight: bold;*/ color: rgba(255, 255, 255, 0.9); font-size: 14px;" class="t-overflow">'+allNewsSources[i].Source+'</small><small class="detailedName"> '+allNewsSources[i].title+'</small></a></div><div class="row" style="text-align: center;"><div class="row" style="text-align: center;"><input id="searchFromHomePage'+tabId+'" type="text" class="win-textbox custom-search" placeholder="Search or enter a web address" autocomplete="off" /></div><div id="suggestionsHomePage'+tabId+'" style="display:none;" class="searchSuggestions custom-search-suggestions"><div class="blackBgInner"><div class="p-l-5 zoomTargetB mainResult" link=""><div class="pull-left mainSearchIage"><img width="100" src="" alt="" style="-webkit-filter: drop-shadow(0 0 3px rgba(0,0,0,0.5));"></div><div class="media-body searchMedia"><p class="searchMain"></p><small class="mainSearchOverflow searchDesc"></small></div><div class="moreInfo"><button class="fromWikipedia">View on Wikipedia</button></div></div><div class="adaptiveSearch p-l-5 zoomTargetB" searchTerm=""><div class="pull-left"><span class="icon searchIcon">&#61788;</span></div><div class="media-body"><p class="searchMainX"></p></div></div>   </div></div></div></div>';

			if (allNewsSources[i].image != undefined)
				currentHomeTopLinks += "<div class='bookmarkDiv Bookmarkx'><a id='TTop"+tabId+"B"+i+"'; href='#' data-original-title="+allNewsSources[i].title+" class='bookmarkTopLink bookmarkTopMain shortcut tile' onclick='executeBookmark(&quot;"+allNewsSources[i].link+"&quot;,&quot;TTop"+tabId+"B"+i+"&quot;)' link='"+allNewsSources[i].link+"'> <img style='max-width: 375px;' src='"+allNewsSources[i].image+"' alt=''>   <small class='homeBookMarkText hoverBlur' style='/*font-weight: bold;*/ color: rgba(255, 255, 255, 0.9); font-size: 14px;' class='t-overflow'>"+allNewsSources[i].Source+"</small><small class='detailedName'> "+allNewsSources[i].title+"</small>    </a></div>"
		}
		currentHomeTopLinks += "<br><a href='#' class='m-r-5 pull-right' onclick='openNewsSelector()'><span class='icon'>&#61886;</span> Manage News</a>";
		
	} else {
		currentHomeTopLinks = "<div class='bookmarkDiv Bookmarkx'><a id='TTop"+tabId+"B0'; href='#' class='bookmarkTopLink bookmarkTopMain shortcut tile' onclick='openNewsSelector()' link='https://externos.io'> <section> <figure id='newsStack"+tabId+"' class='stack stack-sideslide active'> <img src='../../Shared/CoreIMG/news-thumbnails/suggestions/breaking_news.png' alt='img0'/> <img src='../../Shared/CoreIMG/news-thumbnails/suggestions/lifestyle_news.png' alt='img06'/> <img src='../../Shared/CoreIMG/news-thumbnails/suggestions/entertainment_news.png' alt='img04'/> </figure> </section> </a></div> <div class='row' style='text-align: center;'><div class='row' style='text-align: center;'><input id='searchFromHomePage"+tabId+"' type='text' class='win-textbox custom-search' placeholder='Search or enter a web address' autocomplete='off'/></div><div id='suggestionsHomePage"+tabId+"' style='display:none;' class='searchSuggestions custom-search-suggestions'><div class='blackBgInner'><div class='defaultSearchSuggestions'><div style='text-align: left; margin-left: 10px;'><h3 class='block-title'>Suggested</h3></div><br><div class='suggestionsBody'><!--Suggestions body--></div></div><div class='searchHistoryOptions'></div><div class='p-l-5 zoomTargetB mainResult' link=''><div class='pull-left mainSearchIage'><img width='100' src='' alt='' style='-webkit-filter: drop-shadow(0 0 3px rgba(0,0,0,0.5));'></div><div class='media-body searchMedia'><p class='searchMain'></p><small class='mainSearchOverflow searchDesc'></small></div><div class='moreInfo'><button class='fromWikipedia'>View on Wikipedia</button></div></div><div class='adaptiveSearch p-l-5 zoomTargetB' searchTerm=''><div class='pull-left'><span class='icon searchIcon'>&#61788;</span></div><div class='media-body'><p class='searchMainX'></p></div></div>  </div> </div></div <h3> Select News Sources </h3></div>";
	}
	$("#topBookMarks"+currentTab).append(currentHomeTopLinks);
			
}
}

//setTimeout(function(){ refreshLoop(); }, 3000);

//setTimeout(function(){ minFps = 60; }, 8000);
//refreshLoop(); //Measure perfomance for debugging

var hoverTImeout;
var tabHoverPreventPreview;
	function newWebview(requestedURL,hide) {
		
		if (!$("#link_context_menu").hasClass("hidden")) {
			closeAllMenus();
			closeSideBar();
		}

		var currentHomeLinks = "";
		var currentHomeTopLinks = ""; //Default will store news to be dislayed at the top,
						// But will be customizable to be other bookmarks
		
		if(availableTabs.length !=0){
			var tabPos = availableTabs.length
		}else{
			var tabPos = 0;
		}

		/*if (totalTabs == 0){
			
			$("#tabNav").append('<li class="tabNavs active"><span id="tabNave'+tabId+'" class="tabsLi" data-target="#allTabs" data-slide-to="'+tabPos+'" class=""><span><img id="tabicon'+tabId+'" class="tabIcon" src="" /></span><span id="newTabText'+tabId+'" class="ntabText">New Tab</span></span> <span class="closeTabB"><a href="#" class="closeTabLi" onclick="closeTab('+tabId+')"><img src="../../Shared/CoreIMG/icons/actions/close-icon.png"></a></span></li>');
		}else{*/
			var tabId = totalTabs;
			$("#tabNav").append('<li class="tabNavs"><span id="tabNave'+tabId+'" class="tabsLi" data-target="#allTabs" data-slide-to="'+tabPos+'" ><span><img id="tabicon'+tabId+'" class="tabIcon" src="" /></span><span id="audioPlayingIconTab'+tabId+'" class="tabAudioIcon icon hidden">&#61849;</span><span id="newTabText'+tabId+'" class="ntabText">New Tab</span></span> <span class="closeTabB"><a href="#" class="closeTabLi" onclick="closeTab('+tabId+')"><img src="../../Shared/CoreIMG/icons/actions/close-icon.png"></a></span></li>');
			//$("#hoverTabPreview").fadeOut();
			tabHoverPreventPreview = tabId;
			$( ".tabNavs" ).hover(function() {
				var selectedId = $(this).find( ".tabsLi" ).attr("id").replace("tabNave","");
				if (tabHoverPreventPreview == selectedId) {
					tabHoverPreventPreview = "";
				} else {
					clearTimeout(hoverTImeout);
				$("#hoverTabPreview").show();
				$("#hoverTabPreview").addClass("showing");
				var webview = document.querySelector('#webview'+selectedId);
				if ( webview.previewImage != null) { //Let's make sure we aren't home
			//webview.captureVisibleRegion(function(img){
				//$('#navBG').attr("src",img);
		//resizeBookmark(img,0,0,300,136,webview,title);
		$("#hoverTabPreview > img").attr("src",webview.previewImage);
		$("#hoverTabPreview > h4").text(webview.documentTitle);
		$("#hoverTabPreview > p").text(webview.src);
              
			//});
			}
				var tabWidth = this.getBoundingClientRect().width;
				var leftPos = (this.getBoundingClientRect().left+(tabWidth/2))-200;
				//console.log("hoverx: ",leftPos);
				if (leftPos > 10)
					$("#hoverTabPreview").css("left",leftPos+"px");
				else
					$("#hoverTabPreview").css("left","5px");
				}
				

			}, function() {
				if ($("#hoverTabPreview").hasClass("showing")) {
					clearTimeout(hoverTImeout);
					hoverTImeout = setTimeout(function(){ $("#hoverTabPreview").hide(); }, 100);
				}
				
			});



			
			






			$( ".tabNavs" ).click(function() {
				console.log("clicked tab");
			});
			
		//}

		lastTabID = currentTab;

var objDiv = document.getElementById("tabNav");
	setTimeout(function(){ objDiv.scrollLeft = objDiv.scrollWidth; }, 200);

	loadedNewsSources = App.getAllNews();
		var allNewsSources = [];

		if (hide) {

		

		for (var i = 0; i < loadedNewsSources.length; i++) {
			//We can do a nested loop here because we have a max of 2 items before the third item anyway
			var alreadyAdded = false; //We do't want the same source all the time
			for (var j = 0; j < allNewsSources.length; j++) {
				if (allNewsSources[j].Source == loadedNewsSources[i].Source) {
					alreadyAdded = true;
					break; // No need to continue
				}
			}
			if (!alreadyAdded)
				allNewsSources.push(loadedNewsSources[i]);
		}

		if (allNewsSources.length < 3)
			allNewsSources = loadedNewsSources; //They most likely have 1 source selected (or two)... or none, but we take care of that in the next line anyway

		if (allNewsSources.length >= 3) {

		//currentHomeTopLinks += '<div class="bookmarksOuter>'; //This is to make sure it's all centered
		//currentHomeTopLinks += '<div class="bookmarkDiv Bookmarkx"> <a id="TTop'+tabId+'BBXM" title="'+allNewsSources[0].title+'" class="bookmarkLink bookmarkTopLink shortcut tile" onclick="executeBookmark(&quot;'+allNewsSources[0].link+'&quot;,&quot;TTop'+tabId+'B'+i+'&quot;)" link="'+allNewsSources[0].link+'" href="#" style="width: auto; /*background-image:url(&quot;'+allNewsSources[0].link+'&quot;);*/   height: 250px; padding: 0; box-shadow: 0 0px 30px rgba(0, 0, 0, 0.8);"><img style="max-width: 375px;" src="'+allNewsSources[0].image+'" alt=""><small class="homeBookMarkText hoverBlur" style="/*font-weight: bold;*/ color: rgba(255, 255, 255, 0.9); font-size: 14px;" class="t-overflow">'+allNewsSources[0].Source+'</small><small class="detailedName"> '+allNewsSources[0].title+'</small></a></div>';
		for (var i = 0; i < 3; i++){

		var bookmarkWidth = 320;

		if (i == 1)
			bookmarkWidth = 520;

			//currentHomeTopLinks += '<div class="bookmarkDiv Bookmarkx"> <a id="TTop'+tabId+'B'+i+'" data-placement="top" data-original-title="'+allNewsSources[i].title+'" class="bookmarkLink bookmarkTopLink shortcut tile" onclick="executeBookmark(&quot;'+allNewsSources[i].link+'&quot;,&quot;TTop'+tabId+'B'+i+'&quot;)" link="'+allNewsSources[i].link+'" href="#" style="width: auto; /*background-image:url(&quot;'+allNewsSources[i].link+'&quot;);*/   height: 250px; padding: 0; box-shadow: 0 0px 30px rgba(0, 0, 0, 0.8);"><img style="max-width: 375px;" src="'+allNewsSources[i].image+'" alt=""><small class="homeBookMarkText hoverBlur" style="/*font-weight: bold;*/ color: rgba(255, 255, 255, 0.9); font-size: 14px;" class="t-overflow">'+allNewsSources[i].Source+'</small><small class="detailedName"> '+allNewsSources[i].title+'</small></a></div><div class="row" style="text-align: center;"><div class="row" style="text-align: center;"><input id="searchFromHomePage'+tabId+'" type="text" class="win-textbox custom-search" placeholder="Search or enter a web address" autocomplete="off" /></div><div id="suggestionsHomePage'+tabId+'" style="display:none;" class="searchSuggestions custom-search-suggestions"><div class="blackBgInner"><div class="p-l-5 zoomTargetB mainResult" link=""><div class="pull-left mainSearchIage"><img width="100" src="" alt="" style="-webkit-filter: drop-shadow(0 0 3px rgba(0,0,0,0.5));"></div><div class="media-body searchMedia"><p class="searchMain"></p><small class="mainSearchOverflow searchDesc"></small></div><div class="moreInfo"><button class="fromWikipedia">View on Wikipedia</button></div></div><div class="adaptiveSearch p-l-5 zoomTargetB" searchTerm=""><div class="pull-left"><span class="icon searchIcon">&#61788;</span></div><div class="media-body"><p class="searchMainX"></p></div></div>   </div></div></div></div>';
			if (allNewsSources[i].image != undefined)
				currentHomeTopLinks += "<div class='bookmarkDiv Bookmarkx'><a id='TTop"+tabId+"B"+i+"'; href='#' data-original-title="+allNewsSources[i].title+" class='bookmarkTopLink bookmarkTopMain newsFound shortcut tile' onclick='executeBookmark(&quot;"+allNewsSources[i].link+"&quot;,&quot;TTop"+tabId+"B"+i+"&quot;)' link='"+allNewsSources[i].link+"'> <img style='max-width: 375px;' src='"+allNewsSources[i].image+"' alt=''>   <small class='homeBookMarkText hoverBlur' style='/*font-weight: bold;*/ color: rgba(255, 255, 255, 0.9); font-size: 14px;' class='t-overflow'>"+allNewsSources[i].Source+"</small><small class='detailedName'> "+allNewsSources[i].title+"</small>    </a></div>"
		}

		currentHomeTopLinks += "<br><a href='#' class='m-r-5 pull-right' onclick='openNewsSelector()'><span class='icon'>&#61886;</span> Manage News</a>"
        } else {
					var searchElements = "<div class='row' style='text-align: center;'><input id='searchFromHomePage"+tabId+"' type='text' class='win-textbox custom-search' placeholder='Search or enter a web address' autocomplete='off'/></div><div id='suggestionsHomePage"+tabId+"' style='display:none;' class='searchSuggestions custom-search-suggestions'><div class='blackBgInner'><div class='defaultSearchSuggestions'><div style='text-align: left; margin-left: 10px;'><h3 class='block-title'>Suggested</h3></div><br><div class='suggestionsBody'><!--Suggestions body--></div></div><div class='searchHistoryOptions'></div><div class='p-l-5 zoomTargetB mainResult' link=''><div class='pull-left mainSearchIage'><img width='100' src='' alt='' style='-webkit-filter: drop-shadow(0 0 3px rgba(0,0,0,0.5));'></div><div class='media-body searchMedia'><p class='searchMain'></p><small class='mainSearchOverflow searchDesc'></small></div><div class='moreInfo'><button class='fromWikipedia'>View on Wikipedia</button></div></div><div class='adaptiveSearch p-l-5 zoomTargetB' searchTerm=''><div class='pull-left'><span class='icon searchIcon'>&#61788;</span></div><div class='media-body'><p class='searchMainX'></p></div></div>  </div> </div>";
          currentHomeTopLinks = "<div class='bookmarkDiv Bookmarkx'><a id='TTop"+tabId+"B0'; href='#' class='bookmarkTopLink bookmarkTopMain shortcut tile' onclick='openNewsSelector()' link='https://externos.io'> <section> <figure id='newsStack"+tabId+"' class='stack stack-sideslide'> <img src='../../Shared/CoreIMG/news-thumbnails/suggestions/breaking_news.png' alt='img0'/> <img src='../../Shared/CoreIMG/news-thumbnails/suggestions/lifestyle_news.png' alt='img06'/> <img src='../../Shared/CoreIMG/news-thumbnails/suggestions/entertainment_news.png' alt='img04'/> </figure> </section> <h3> Select News Sources </h3></a></div> <div class='row' style='text-align: center;'>"+searchElements+"</div>"
        }

	//currentHomeTopLinks += '</div>';

		for (var i = 0; i < homeBookMarks.length; i++){
			currentHomeLinks += '<div class="bookmarkDiv Bookmark'+homeBookMarks[i].id+'"> <a id="T'+tabId+'B'+homeBookMarks[i].id+'" data-placement="top" data-original-title="'+homeBookMarks[i].description+'" class="bookmarkLink shortcut" onclick="executeBookmark(&quot;'+homeBookMarks[i].url+'&quot;,&quot;T'+tabId+'B'+homeBookMarks[i].id+'&quot;)" link="'+homeBookMarks[i].url+'" href="#" style="/*width: 320px;*/ /*background-image:url(&quot;'+homeBookMarks[i].url+'&quot;);*/   /*height: 200px;*/ padding: 0; /*box-shadow: 0 0px 30px rgba(0, 0, 0, 0.8);*/"><img style="margin-top: 30px; border-radius: 20px;" src="'+homeBookMarks[i].thumbUrl+'" alt=""><small class="homeBookMarkText hoverBlur" style="/*font-weight: bold;*/ color: rgba(255, 255, 255, 0.9); font-size: 14px;" class="t-overflow">'+homeBookMarks[i].name+'</small><small class="detailedName" style="bottom: 25px;"> '+homeBookMarks[i].description+'</small></a><a class="deleteBookmark" href="#" class="" onclick="deleteBookmark('+homeBookMarks[i].id+')"><img src="../../Shared/CoreIMG/icons/actions/close-icon.png"></a></div>'
		}

						

		} 

		/*setTimeout(function(){ 
			$("#view"+tabId+" > .zoomContainer > .bookmarks").niceScroll();
		}, 5000);*/
		
		$('#tabNave'+tabId)[0].addEventListener('click', function(e) {
			var webview = document.querySelector('#webview'+currentTab);
			if (!webview.currentAtHome && webview.id == "webview"+currentTab) { //Let's make sure we aren't home
			webview.captureVisibleRegion(function(img){ //Update preview to the latest before we switch
				//console.log("seeing img to",webview.id);
				webview.previewImage = img;
		//console.log("which webview: ",webview); 
              
			});
				}
			console.log("old currenttab: ",currentTab);
			clearTimeout(currentSwitchingTimeOut);
			//$("#webview"+currentTab).addClass("hiddenX");
			var tabm = currentTab;
			currentSwitchingTimeOut = setTimeout(function(){
				/*if (tabm != currentTab)
					$("#webview"+tabm).addClass("hiddenX"); //Reducing elements that are on "screen" to reduce workload on GPU
			*/}, 500);
			lastTabID = currentTab;
			
			if (e.target.className.indexOf("fa") == -1 && e.target.className.indexOf("closeTabB") == -1 && e.target.className.indexOf("closeTabLi") == -1) {
				currentTab = $(this).attr("id").replace("tabNave","");
				
				$("#webview"+currentTab).removeClass("hiddenX");
				console.log("new currenttab: ",currentTab);
				$(".tabNavs").removeClass("active");
				$(this).parent().addClass("active");
              $("#contextMenuOverlay").addClass("hidden");
				handleLoadCommit();
				var webview = document.querySelector('#webview'+currentTab);
			if (!webview.currentAtHome && webview.id == "webview"+currentTab) {
				console.log("tab focus");
				setTimeout(function(){ webview.focus(); }, 500);
			}
			}else {
				e.preventDefault();
			}

			
				
			/*for (var i=0; i < e.path.length-1; i++) {
				if (e.path[i].className.indexOf("tabNavs") !=-1)
					////console.log("NAVVVVV Found",e.path[i]);
			}*/
		});
		
		//tabsArray.push(tabId);
		if (tabId == 0)
			var activeClass = "active";
		else
			var activeClass = "";

			var homeLink = "file://"+process.cwd()+"/apps/extern.web.app/temporary/Welcome.html";

			var classToAppend = "";

			if (!fancyRendering) {
				classToAppend = " classicWebviewRendering";
				console.log("triggered here");
			}

			var privateSessionNote = '';

			if (privateMode)
			privateSessionNote = '<div class="privateMode"><h1><span class="fa fa-user-secret" style="color: #ffffffbf;" aria-hidden="true"></span> Private Session </h2><h4>  You are currently in a private session. This means that your session will not be linked to your personal session including your browsing history. </h1></div>';
			//var searchElements = "<div class='row' style='text-align: center;'><input id='searchFromHomePage"+tabId+"' type='text' class='win-textbox custom-search' placeholder='Search or enter a web address' autocomplete='off'/></div><div id='suggestionsHomePage"+tabId+"' style='display:none;' class='searchSuggestions custom-search-suggestions'><div class='blackBgInner'><div class='p-l-5 zoomTargetB mainResult' link=''><div class='pull-left mainSearchIage'><img width='100' src='' alt='' style='-webkit-filter: drop-shadow(0 0 3px rgba(0,0,0,0.5));'></div><div class='media-body searchMedia'><p class='searchMain'></p><small class='mainSearchOverflow searchDesc'></small></div><div class='moreInfo'><button class='fromWikipedia'>View on Wikipedia</button></div></div><div class='adaptiveSearch p-l-5 zoomTargetB' searchTerm=''><div class='pull-left'><span class='icon searchIcon'>&#61788;</span></div><div class='media-body'><p class='searchMainX'></p></div></div>  </div> </div></div";
			var searchElements = "";
			$("#allTabsC").append('<div id="view'+tabId+'" class="item '+activeClass+''+classToAppend+'"><div class="box testZoomBox">CLICK</div><div class="zoomContainer animated fadeInDown"><div class="bookmarks">'+privateSessionNote+'<h4 id="topBookmarksTitle" style="margin-top: 0; margin-bottom: 20px;" class="catalogueTitle block-title">News for you</h4> <br> <div id="topBookMarks'+tabId+'" class="bookmarksOuter topBookmarks" style="text-align: center;">'+currentHomeTopLinks+'</div>'+searchElements+'<br><h4 style="margin-top: 0; margin-bottom: 20px;" class="catalogueTitle block-title">Bookmarks</h4> <br> <div class="bookmarksOuter">'+currentHomeLinks+'</div></div></div><webview id="webview'+tabId+'" '+sessionStoragePartition+' src="'+homeLink+'" class="topMargin animated fadeInUp" style="width:100%;/*width:99.5%;*/ height:100%; /*left: 0.25%;*/" '+transparencySetting+'></webview><div id="loadingStatusView'+tabId+'" class="loadingStatus"></div></div>');
			//$("#allTabsC").append('<div id="view'+tabId+'" class="item '+activeClass+''+classToAppend+'"><div class="box testZoomBox">CLICK</div><div class="zoomContainer"><div class="searchSuggestions" style="display:none;"><div class="blackBg"></div><div class="blackBgInner"><div class="p-l-5 zoomTarget mainResult" link=""><div class="pull-left mainSearchIage"><img width="100" src="" alt="" style="-webkit-filter: drop-shadow(0 0 3px rgba(0,0,0,0.5));"></div><div class="media-body searchMedia"><p class="searchMain"></p><small class="mainSearchOverflow searchDesc"></small></div><div class="moreInfo"><button class="fromWikipedia">View on Wikipedia</button></div></div><div class="adaptiveSearch p-l-5 zoomTarget" searchTerm=""><div class="pull-left"><span class="icon searchIcon">&#61788;</span></div><div class="media-body"><p class="searchMainX"></p></div></div>   </div></div><div class="bookmarks"><h4 id="topBookmarksTitle" style="margin-top: 0; margin-bottom: 20px;" class="catalogueTitle block-title">News for you</h4> <br> <div class="bookmarksOuter" style="text-align: center;">'+currentHomeTopLinks+'</div><br><h4 style="margin-top: 0; margin-bottom: 20px;" class="catalogueTitle block-title">Bookmarks</h4> <br> <div class="bookmarksOuter">'+currentHomeLinks+'</div></div></div><webview id="webview'+tabId+'" '+sessionStoragePartition+' src="'+homeLink+'" class="topMargin" style="width:100%;/*width:99.5%;*/ height:100%; /*left: 0.25%;*/" '+transparencySetting+'></webview><div id="loadingStatusView'+tabId+'" class="loadingStatus"></div></div>');

			var webview = document.querySelector('#webview'+tabId);
			webview.loadedNewsSources = loadedNewsSources;

			

			$('#view'+tabId+' > .testZoomBox').hover(function() {
	console.log("hoveredb");
	var maxHeight = 55;
	if (!controlsShowing) {
		$("#navigationBar").css("height",maxHeight+"px");
					$("#blur2").css("height",maxHeight+"px");
					$("#allTabsC").css("height","calc(100% - "+(maxHeight-15)+"px)");
					$(".newNavButton").removeClass("hiddenOpacity");
					$(App.minimize_button).removeClass("hidden");
					$(App.maximize_button).removeClass("hidden");
					$(App.close_button).removeClass("hidden");
					$("#tabNav").removeClass("hidden");
					controlsShowing = true;
	}
				

			}, function() {
				//out of hover
				console.log("not hovering")
			});
/*
(function() {
	[].slice.call( document.querySelectorAll( '.stack' ) ).forEach( function( el ) {
		var togglebtt = el.previousElementSibling,
			togglefn = function() {
				if( classie.hasClass( el, 'active' ) ) {
					classie.removeClass( el, 'active' );
				}
				else {
					classie.addClass( el, 'active' );
				}
			};

		togglebtt.addEventListener( 'click', togglefn );
	} );
})();*/






			$(".custom-search").keyup(function (e) {

				var webview = document.querySelector('#webview'+currentTab);

				if (webview.currentAtHome){
					var suggestionsDiv = '#suggestionsHomePage'+currentTab;
				}else{
					var suggestionsDiv = '#allTabs > .searchSuggestions';
				}

				

			if (e.keyCode == 13) { //Press ENTER

				

				

				console.log("trying to click adaptive");
				console.log("here is clicked adaptive",$(suggestionsDiv +' > .blackBgInner > .adaptiveSearch'));

				if ($(suggestionsDiv +' > .blackBgInner > .mainResult').hasClass("hiddenOut"))
					$(suggestionsDiv +' > .blackBgInner > .adaptiveSearch').click();
				else if ($(suggestionsDiv +' > .blackBgInner .highlightedOption').length != 0)
					$(suggestionsDiv +' > .blackBgInner .highlightedOption').click();
				else
					$(suggestionsDiv +' > .blackBgInner > .mainResult').click();
			} else if (e.keyCode == 38) { //Press Up
				//Go up here
			} else if (e.keyCode == 40) { //Press down
				//Go down here
				var searchItems = $(suggestionsDiv +' > .blackBgInner .p-l-5');
				if ($(suggestionsDiv +' > .blackBgInner .highlightedOption').length == 0) {
					console.log("first item: ",$($(suggestionsDiv +' > .blackBgInner .p-l-5')[0]));
					if ($(searchItems[0]).hasClass("hiddenOut")) { //Skip first main url box if it's not shown
						if (searchItems.length > 1) {
							$(searchItems[1]).addClass("highlightedOption");
						}
					} else {
						$(searchItems[0]).addClass("highlightedOption");
					}
					
				} else {
					console.log("not first item: ",searchItems);
					for (var i = 0; i < searchItems.length; i++) {
						console.log("check this: ",searchItems[i]);
						if ($(searchItems[i]).hasClass("highlightedOption")) {
							console.log("found");
							$(searchItems[i]).removeClass("highlightedOption");
							if (i < (searchItems.length-1) && !$(searchItems[i+1]).hasClass("hiddenOut")) {
								console.log("move down");
								$(searchItems[i+1]).addClass("highlightedOption");
								break;
							} else {
								console.log("reset");
								if ($(searchItems[0]).hasClass("hiddenOut")) {  //Skip first main url box if it's not shown
									if (searchItems.length > 1) {
										$(searchItems[1]).addClass("highlightedOption");
									}
								} else {
									$(searchItems[0]).addClass("highlightedOption");
								}
								break;
							}
						}
					}
				}
				
			} else {
				if (webview.currentAtHome){
					var suggestionsDiv = '#suggestionsHomePage'+currentTab;
				}else{
					var suggestionsDiv = '#allTabs > .searchSuggestions';
				}

				console.log("hide defaultSearchSuggestions");

				$(suggestionsDiv +' .defaultSearchSuggestions').hide();
				$(suggestionsDiv +' .searchHistoryOptions').hide();
				$(suggestionsDiv+' > .blackBgInner > .searchHistoryOptions').empty();
				console.log($(this).val());
				$("#urlInput").val($(this).val());
				$("#urlInput").trigger('input');
			}
		});

			$(".custom-search")
		.focusin(function(ev) {
			searchFocusIn(this);
			loadRecommendedSearches(".searchSuggestions");
		})
		.focusout(function() {
			console.log("unfocused")
			searchFocusOut();
		});

		$(".adaptiveSearch").hide();

		

		setTimeout(function(){ loadRecommendedSearches(".searchSuggestions"); $("#newsStack"+tabId).addClass("active"); win.focus(); $("#searchFromHomePage"+tabId).focus(); }, 1000);


function isOnScreen(element)
{
    var curPos = $(element).offset();
    var curTop = curPos.top;
    var screenHeight = $(element).parent().parent().parent().height();
    return (curTop > (screenHeight-200)) ? false : true;
}

if (useZoomAnimations) {
	$( ".bookmarkLink" ).hover(function() {
	if (!$('#view'+tabId+' > .box').hasClass("fullScreen")) {
		var bookmarkPositionX = $(this).offset().left - $(this).parent().parent().parent().scrollLeft();//$(window).scrollLeft();
	var bookmarkPositionY = $(this).offset().top - $(this).parent().parent().parent().scrollTop();
	$('#view'+tabId+' > .box').css("left",bookmarkPositionX+160);
	$('#view'+tabId+' > .box').css("bottom",win.height - (bookmarkPositionY+100));
	if (!isOnScreen(this))
		this.scrollIntoView({ block: 'end',  behavior: 'smooth' });
	}
	
});
}



if (!hide) {
	var webview = document.querySelector('#webview'+tabId);
		webview.src = requestedURL;
	//requestedURL lllol
}

			if (!hide) {
			console.log("gets here",$('#view'+tabId+' > .zoomContainer > .bookmarks > .catalogueTitle'));
		
			$('#view'+tabId+' > .zoomContainer > .bookmarks > .catalogueTitle').addClass("hiddenOpacity");
		}
			settings = {

    // use browser native animation in webkit, provides faster and nicer
    // animations but on some older machines, the content that is zoomed
    // may show up as pixelated.
    nativeanimation: false,
    easing: "ease",
	animationendcallback: activateBookmark
}

//easing: "ease",
			if (useZoomAnimations) {
				$(".bookmarkLink").zoomTarget(settings);
				$(".bookmarkTopLink").zoomTarget(settings);
				$(".zoomTargetB").zoomTarget(settings);
			}
			


		if($('.tooltips')[0]) {
        $('.tooltips').tooltip();
      }

//http://jaukia.github.io/zoomooz/
		//}
			  //$(".adaptiveSearch").zoomTarget(); 
		//$("#view"+tabId).fadeIn(); //fixing some strange bug
				   

		$('.adaptiveSearch').on("click",function(){
			adaptiveSearchCall(this);
		});

		$('.mainResult').on("click",function(){
			$(this).addClass("currentSelection");
			var link = $(this).attr('link');
			webview.searchTerm = link;
			webview.searchTermIsUrl = true;
			//$('#view'+currentTab+'> .zoomContainer > .bookmarks > .bookmarksOuter > .bookmarkLink').removeClass("currentSelection");
			//$('#view'+currentTab+'> .zoomContainer > .searchSuggestions > .blackBgInner > .zoomTarget').removeClass("currentSelection");
			//$(this).addClass("currentSelection");
			gotToSearch(link);
		});

		/*
		$('.searchResult').on("click",function(){
		////console.log("search result clicked");
			$(this).addClass("currentSelection");

			var link = searchEngine+$(this).attr("searchTerm");
			gotToSearch(link);
		});*/
			   
			   /*for (var i = 0; i < homeBookMarks.length; i++) {
			//////console.log("DIVS ZOOM",$("#T"+currentTab+"B"+i));
		//$("#T"+currentTab+"B"+i).zoomTarget();
		}*/
	   	var webview = document.querySelector('#webview'+tabId);
	   	webview.currentAtHome = true;
	   	webview.canGoToHome = true;
			 webview.previewImage = "temporary/homepage_preview.png";

			 	    webview.onmousemove = handleMouseMove;
    function handleMouseMove(event) {
        var eventDoc, doc, body;

        event = event || window.event; // IE-ism

        // If pageX/Y aren't available and clientX/Y are,
        // calculate pageX/Y - logic taken from jQuery.
        // (This is to support old IE)
        if (event.pageX == null && event.clientX != null) {
            eventDoc = (event.target && event.target.ownerDocument) || document;
            doc = eventDoc.documentElement;
            body = eventDoc.body;

            event.pageX = event.clientX +
              (doc && doc.scrollLeft || body && body.scrollLeft || 0) -
              (doc && doc.clientLeft || body && body.clientLeft || 0);
            event.pageY = event.clientY +
              (doc && doc.scrollTop  || body && body.scrollTop  || 0) -
              (doc && doc.clientTop  || body && body.clientTop  || 0 );
        }

        // Use event.pageX / event.pageY here
				mouseX = event.pageX;
				mouseY = event.pageY;
    }
	   
	   	//$(".zoomTarget").zoomTarget();
	   	if(hide){
		   	//$('#webview'+tabId).fadeOut();
				 if (useZoomAnimations)
				 	$('#webview'+tabId).addClass("noOpacity");
			//$('#webview'+tabId).addClass("hidden");
			$('#webview'+tabId).hide();
		   	webview.loadingFromHome = false;
	   	}else{
		   	webview.canGoToHome = false;
		   	webview.loadingFromHome = false;
	   	}
		   // }
		//$('#view'+tabId+'> .zoomContainer > .searchSuggestions').addClass("hidden"); //FIXME REMOVE THIS
		$('#view'+tabId+'> .zoomContainer > .searchSuggestions').fadeOut();
		//$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .mainResult').fadeOut();
		$('#view'+currentTab+' > .zoomContainer > .searchSuggestions > .blackBgInner > .mainResult').css("display","none");
		availableTabs.push(tabId);

		totalTabs++;

		//$("#addTab").remove();
		
		
		//$("#tabsNavigator").append('<div id = "newTab'+tabId+'" class="browserTab"><a href="#" data-target="#allTabs" data-slide-to="'+tabId+'" class="active tabText" style="padding: 45% 58%; padding-left: 0;"><img id="tabicon'+tabId+'" class="tabIcon" src="" /> <span  class="icon" id = "newTabSound'+tabId+'" style="font-size: 15px;margin-right: 3px;margin-top: 4px;">&#61849;</span><span id = "newTabText'+tabId+'" class="tabTextStyle"> Loading...</span></a><a href="#" onclick="closeTab('+tabId+')" class="tabCloseButton"><i style="font-size: 14px;font-weight: bold;text-shadow: 0 0 10px rgba(0, 0, 0, 1);" class="fa fa-circle-thin" aria-hidden="true"></i></a></div>');
		//$("#tabsNavigator").append('<div id="addTab" onclick="newTab()" class="browserTab" style="width: 20px" ><a href="#" style="padding: 45% 28%;" class="tabText">+</a></div>');
		
		if(tabId == 0){
			$("#newTab"+tabId).addClass("browserTabSelected");
			$("#tabsNavigator").addClass("oneTabHide");
		}else{
			$("#tabsNavigator").removeClass("oneTabHide");
		}
		
		$('.carousel').carousel()
		$("#newTabSound"+tabId).fadeOut();
		
		var webview = document.querySelector('#webview'+tabId);
		//webview.ids = tabId;
		//.indexOf("2");
		//$("#allTabs").carousel(tabId+1);
		navigateTo(requestedURL,tabId);
		doLayout(tabId);
		webview.ids = tabId;
		
		webview.addEventListener('close', handleExit);
		webview.addEventListener('loadstart', handleLoadStart);
		webview.addEventListener('loadstop', handleLoadStop);
		webview.addEventListener('loadabort', handleLoadAbort);
      	webview.addEventListener('loadcommit', handleRealLoadCommit);
		webview.addEventListener('loadredirect', handleLoadRedirect);
		webview.addEventListener('did-finish-load', handleLoadCommit);
		webview.addEventListener('did-get-response-details', handleResponseDetails);
		webview.addEventListener('consolemessage', checkConsole);
		webview.addEventListener('newwindow', openInNewTab);
		webview.addEventListener('webkitfullscreenchange', toggleFullsecreen);
		webview.addEventListener('permissionrequest', handlePermmision);
      	webview.addEventListener('dialog', handleDialog);
		webview.addEventListener('download', handleDownload);
		//webview.addEventListener('contextmenu', handleMenu); //Not working anymore in the latest Nw.js. Leaving it here just incase it was a bug and it returns in later versions
		webview.addEventListener('playing', playss);
		webview.addEventListener('play', playss);
		webview.addEventListener('pause', playss);
      
     
      
      	webview.request.onBeforeRequest.addListener(handleRequest,{urls: ["<all_urls>"]},
  ["blocking"]); //blocking
      
		webview.style.webkitTransition = 'opacity 250ms';
		webview.addEventListener('unresponsive', function() {
		  //webview.style.opacity = '0.5';
		});
		webview.addEventListener('responsive', function() {
		  //webview.style.opacity = '1';
		});
		webview.contextMenus.onShow.addListener(function(e){
			e.preventDefault();
			handleMenu(e);
setTimeout(function(){win.focus(); $('#rightclickoption').focus(); console.log("try now"); }, 2000);
			 //$("#rightclickoptions").click(); // Fix for the "click" event bug mentioned below
		});

		//webview.onfocus = function () { console.log("clicked!!!")};
		//console.log("webview",$(webview));

//win.showDevTools();
      
      function handleRealLoadCommit(event) {
	console.log("handle events",event);
        webview = event.srcElement;
		if (webview.insertedCSSCodeUrl != event.url) {
			console.log("inserted");
			webview.insertedCSSCodeUrl = event.url;
			webview.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'});
			webview.insertCSS({file: 'apps/extern.web.app/css/adjustMargin.css'});


		

			if (webview.src.indexOf("file://") != 0) {

		var docTitle = webview.documentTitle;

		if (webview.documentTitle == '')
			docTitle = webview.src.replace("https://","").replace("http://","");

			if (!privateMode) {

				if (webview.searchTerm != "" && webview.searchTerm != null) {
					
					if (webview.searchTermIsUrl) {
						var siteName = webview.documentTitle;
						webview.searchTermIsUrl = false;
						isSearch = false;
						var siteUrl = webview.searchTerm;
					} else {
						var siteName = webview.searchTerm;
						isSearch = true;
						webview.searchTerm = "";
						var siteUrl = "";
					}
					
				

				var recommendedSearchesExists = recommendedSearches.filter(function (el) {
					if (el.isSearch)
            return el.name == siteName;
					else
					  return el.url == siteUrl;
        });

				console.log("recommendedSearchesExists: ",recommendedSearchesExists);
				

				
					if (recommendedSearchesExists.length != 0) {
						recommendedSearchesExists[0].accessedTimes++;
					} else {
						recommendedSearches.push({
							id: recommendedSearches.length,
							name: siteName,
							url: siteUrl,
							icon: "",
							accessedTimes: 0,
							isSearch: isSearch
						});
				}

				

				//Reorder things

				recommendedSearches.sort((a,b) => (a.accessedTimes > b.accessedTimes) ? 1 : ((b.accessedTimes > a.accessedTimes) ? -1 : 0));
				console.log("recommendedSearches: ",recommendedSearches);

				if (recommendedSearches.length > 10) {
					recommendedSearches.splice(1, 1); //Remove second to last most searched/typed url (last one being the one we just added)
				}
				
				localStorage.setItem('recommendedSearches', JSON.stringify(recommendedSearches));
				}
				

				var historyObject = {
					title: docTitle,
					url: webview.src,
					favIcon: webview.favIcon,
					time: + new Date()
				}

				console.log("add to history: ",historyObject);
				
				browserHistory.push(historyObject);
				localStorage.setItem('browserHistory', JSON.stringify(browserHistory));
				//console.log("browserHistory",browserHistory);
				}
			}

		
			
		}
        var webviewIdNo = $(webview).attr("id").replace("webview","");
        $("#loadingStatusView"+webviewIdNo).text("Waiting for "+event.url);
          $("#loadingStatusView"+webviewIdNo).removeClass("hidden");
        
        //console.log("handleRealLoadCommit",event);
        
      }
      
      
       //https://developer.chrome.com/apps/tags/webview
      
      //https://developer.mozilla.org/en-US/Add-ons/WebExtensions/API/webRequest/onBeforeRequest
      
      function handleRequest(details) {
        //console.log("details",this);
        $("#loadingStatusView"+currentTab).text("Waiting for "+details.url);
        
        if (blockTrackersAndAds) {
        if (parser.matches(parsedFilterData, details.url, {
        domain:parser.getUrlHost(details.url),
        elementType: details.type
      })) { 
          return {cancel: true};
        } else {
          return {cancel: false};
        }
        } else {
          return {cancel: false};
        }
        
        /*callback({
          cancel: false,
          requestHeaders: details.requestHeaders
        })
          return;*/
        
      }

			var delayedHide;
      
      function handleDialog(event) {
        //console.log("handleDialog",event);
        webview = event.srcElement;
        var webviewIdNo = $(webview).attr("id").replace("webview","");
        if (event.messageText.indexOf("extern-command: a: mouseenter:") == 0) {
          if (event.messageText.replace("extern-command: a: mouseenter:","") != "") {
            $("#loadingStatusView"+webviewIdNo).text(event.messageText.replace("extern-command: a: mouseenter:",""));
						lastHoveredLink = event.messageText.replace("extern-command: a: mouseenter:","");
            $("#loadingStatusView"+webviewIdNo).removeClass("hidden");
          }
        }

				if (event.messageText.indexOf("extern-new-title-xp:") == 0) {
          //$("#loadingStatusView"+webviewIdNo).addClass("hidden");
					//lastHoveredLink = "";
					console.log("title changed")
        }
        
        if (event.messageText.indexOf("extern-command: a: mouseleave:") == 0) {
          $("#loadingStatusView"+webviewIdNo).addClass("hidden");
					lastHoveredLink = "";
        }

        if (event.messageText.indexOf("extern-command: status:ready") == 0) {
          $(webview).removeClass("reducedOpacity");
	$(webview).removeClass("topMargin");
        }

				if (event.messageText.indexOf("extern-command: cs-move: x:") == 0) {
          var cursorPos = event.messageText.split("extern-command: cs-move: x:")[1].split(" y:");
					mouseX = cursorPos[0];
					mouseY = cursorPos[1];
					//console.log("updated");
        }

				if (event.messageText.indexOf("extern-command-hide-bar:") == 0) {
          var hideBarPercentage = parseInt(event.messageText.split("extern-command-hide-bar:")[1])/10;

					if (hideBarPercentage > 0.2) {
						var maxHeight = 0;
						//clearTimeout(delayedHide);
						/*delayedHide = setTimeout(function(){
							$("#navigationBar").hide();
							$("#blur2").hide();
						}, 500);*/
						$(".newNavButton").addClass("hiddenOpacity");
						console.log("win.minimize_button: ",win.minimize_button);
						$(App.minimize_button).addClass("hidden");
						$(App.maximize_button).addClass("hidden");
						$(App.close_button).addClass("hidden");
						$("#tabNav").addClass("hidden");
					} else {
						var maxHeight = 55-(hideBarPercentage*55);
					}
					

					$("#navigationBar").css("height",maxHeight+"px");
					$("#blur2").css("height",maxHeight+"px");
					$("#allTabsC").css("height","calc(100% - "+(maxHeight-25)+"px)");
					controlsShowing = false;
					//console.log("updated");
        }

				if (event.messageText.indexOf("extern-command-show-bar:") == 0) {
          var hideBarPercentage = parseInt(event.messageText.split("extern-command-show-bar:")[1])/10;

					//console.log("hideBarPercentage: ", hideBarPercentage);
					if (hideBarPercentage > 0.2) {
						var maxHeight = 55;
					} else {
						var maxHeight = (hideBarPercentage*55);
					}

					//clearTimeout(delayedHide);
					$("#navigationBar").css("height",maxHeight+"px");
					$("#blur2").css("height",maxHeight+"px");
					$("#allTabsC").css("height","calc(100% - "+(maxHeight-15)+"px)");
					$(".newNavButton").removeClass("hiddenOpacity");
					$(App.minimize_button).removeClass("hidden");
					$(App.maximize_button).removeClass("hidden");
					$(App.close_button).removeClass("hidden");
					$("#tabNav").removeClass("hidden");
					controlsShowing = true;
					//console.log("updated");
        }
          
      }

		
		
		function playss(event) {
			////console.log("PLAYING DETECTED");
		}
		
		webview.addEventListener('mousedown', handleClick); //Stopped woring on nwjs 0.30.0

		win.on('blur', function() {
                handleClick(this); //quick fix for the click event issue above
            });
		//monitorAudioPlaying(webview,webview.ids);
		
		// Test for the presence of the experimental <webview> zoom and find APIs.
		if (typeof(webview.setZoom) == "function" && typeof(webview.find) == "function") {
			webview.addEventListener('findupdate', handleFindUpdate);
			window.addEventListener('keydown', handleKeyDown);
		}else{
			var zoom = document.querySelector('#zoom');
			var find = document.querySelector('#find');
			zoom.style.visibility = "hidden";
			zoom.style.position = "absolute";
			find.style.visibility = "hidden";
			find.style.position = "absolute";
		}

		$('#tabNave'+tabId)[0].click();
		
		//handleLoadCommit();
	};

	function switchToTab(tabID){
		
		var goTo = $("#view"+tabID).index();
		$("#view"+currentTab).removeClass('active'); 
		$("#newTab"+currentTab).removeClass("browserTabSelected");
		lastTabID = currentTab;
		console.log("switching tab old currentTab: ",currentTab);
		currentTab = tabID;
		console.log("switching tab new currentTab: ",currentTab);
		$("#view"+tabID).addClass('active'); 
		$("#newTab"+currentTab).addClass("browserTabSelected");
		console.log("done switching");
		handleLoadCommit();
		
		return false;
	   /* 
	  $('.carousel-inner .item').each(function(index){
		  //////console.log("checked: view"+tabID);
		  ////console.log("SEARCHING IDS: ",$(this)[0].id);
		   ////console.log("SEARCHING IINDEX: ",index);
		if($(this)[0].id == "view"+tabID){
		  var goTo = index;
			////console.log("success goZto: "+goTo);
		$("#allTabs").carousel(goTo);
			$("#newTab"+currentTab).removeClass("browserTabSelected");
		currentTab = tabID;
		$("#newTab"+currentTab).addClass("browserTabSelected");
		handleLoadCommit();
		  return false;
		}
	  });*/	
	}


	//creating a new tab and opening it
	function newTab(){
		newWebview("file://"+process.cwd()+"/apps/extern.web.app/temporary/Welcome.html",true);
	//$('#urlInput').focus();
	}

	function closeTab(tabId){
		var webview = document.querySelector('#webview'+tabId);
	/*
		for (var i=0;i<availableTabs.length;i++)
			if (availableTabs[i] == tabId)
				var tabPos = i;
		if (tabPos !=0) {
		switchToTab(availableTabs[tabPos-1]);
			////console.log("REMOVED ELEMENT BEFORE:"+availableTabs[tabPos-1]);
			availableTabs.splice(tabPos, 1);
			
			////console.log("REMOVED ELEMENT LATER:",availableTabs);
		$("#view"+tabId).remove();
		$("#newTab"+tabId).remove();
		$("#tabsNavigator").addClass("oneTabHide");
		}*/
		//availableTabs
		
		
		//$( "#tabNave1" ).attr("data-slide-to", 10);

		console.log("lastTabID: ",lastTabID);

		for (var i=0; i<availableTabs.length;i++){	
			console.log("availableTabs[i]: ",availableTabs[i]);
			if (availableTabs.length > 1 && availableTabs[i] == lastTabID) {
				console.log("lastTabID).length: ",$('#webview'+lastTabID).length);
				if ($('#webview'+lastTabID).length == 1) {
					
					//console.log("set tabpos: ",tabPos);
					if (currentTab == tabId)
						$("#tabNave"+lastTabID)[0].click();
					console.log("clicked to lastTabID: ",lastTabID);
					break;
				}
			} else if ("#tabNave"+availableTabs[i] == "#tabNave"+tabId) {
				var tabPos = i;
				if (i !=0) {
					var clickID = availableTabs[i-1];
					//setTimeout(function(){$("#tabNave"+clickID ).trigger('click');}, 2000);
					if (currentTab == tabId)
						$("#tabNave"+clickID )[0].click();
					//$('#myCarousel').carousel(); 
				}else {
					if (availableTabs.length == 1){
						win.close();
					}else {
						var clickID = availableTabs[i+1];
					//setTimeout(function(){$("#tabNave"+clickID ).trigger('click');}, 2000);
						$("#tabNave"+clickID )[0].click();
						//$("#tabNave"+(i+1)).trigger('click');
					}
				}
				break;
			}	
		}
		
		
		
		for (var i=0; i<availableTabs.length;i++){
			if (availableTabs[i] == tabId) {
				var tabPos = i;
				console.log("using tabpos: ",tabPos);
				availableTabs.splice(tabPos, 1);
				break;
			}
		}
		
		
		for (var i=0; i<availableTabs.length;i++){
			$( "#tabNave"+availableTabs[i] ).attr("data-slide-to", i);
		}

		//var goTo = $("#view"+tabID).index();
		//$("#view"+tabId).remove(); 
		$("#tabNave"+tabId).parent().fadeOut();
		setTimeout(function(){console.log("tabId",tabId); $("#tabNave"+tabId).parent().remove();$('#webview'+tabId).remove(); $("#view"+tabId).remove(); }, 1000);
		;
		//$("#newTab"+tabId).remove();
	}

	//$("#sideBar").fadeOut(); //Sidebar init

	//var currentSideBarMode = 'settings';

	function toggleSideBar() {
		var webview = document.querySelector('#webview'+currentTab);
		
		if (!$("#allTabs").hasClass("allTabsReseize")) {
			$("#allTabs").addClass("allTabsReseize");
			//$("#navigationBar").removeClass("navShadow");
			$("#navigationBar").addClass("active");
			$(".controlButton").removeClass("active");
			$(win.minimize_button).removeClass("active");
			$(win.maximize_button).removeClass("active");
			$(win.close_button).removeClass("active");
			//$("#blur2").addClass("hidden");
			$("#sideBar").fadeIn();
		} else {
			$("#allTabs").removeClass("allTabsReseize");
			if (!webview.currentAtHome)
			//$("#navigationBar").addClass("navShadow");
			$("#navigationBar").removeClass("active");
			$(".controlButton").addClass("active");
			$(win.minimize_button).addClass("active");
			$(win.maximize_button).addClass("active");
$(win.close_button).addClass("active");
			//$("#blur2").removeClass("hidden");

			$("#sideBar").fadeOut();
		}
	}

	function closeSideBar() {
		var webview = document.querySelector('#webview'+currentTab);
		
		if ($("#allTabs").hasClass("allTabsReseize")) {
			$("#contextMenuOverlay").addClass("hidden");
			$("#allTabs").removeClass("allTabsReseize");
				closeAllMenus();
			if (!webview.currentAtHome) {
				$("#navigationBar").addClass("navShadow");
				$("#navigationBar").removeClass("active");
				$(".controlButton").addClass("active");
				$(win.minimize_button).addClass("active");
				$(win.maximize_button).addClass("active");
$(win.close_button).addClass("active");
			}
			$("#blur2").removeClass("hidden");

			$("#sideBar").fadeOut();
			//$("#urlWrap").removeClass("searchCoverTop"); //Note needed anymore
		}
	}

	function openSideBar() {
		var webview = document.querySelector('#webview'+currentTab);
		
		if (!$("#allTabs").hasClass("allTabsReseize")) {
			$("#contextMenuOverlay").removeClass("hidden");
			$("#allTabs").addClass("allTabsReseize");
			//$("#navigationBar").removeClass("navShadow");
			$("#navigationBar").addClass("active");
			$(".controlButton").removeClass("active");
			$(win.minimize_button).removeClass("active");
			$(win.maximize_button).removeClass("active");
			$(win.close_button).removeClass("active");
			//$("#blur2").addClass("hidden");
			$("#sideBar").fadeIn();
			//$("#urlWrap").addClass("searchCoverTop"); //Not needed anymore
		}
	}

	function openDownloads() {
		/*$("#downloadsContainer").css("background-position","46% -100px");
		$("#downloadsContainer").css("background-image",$('background').css("background-image"));
		$("#downloadsContainer").css("background-size",$('background').css("background-size"));
		$("#downloadsContainer").fadeIn();*/
		if (!$("#downloadsContainer").hasClass("hidden")) {
			$("#downloadsContainer").addClass("hidden");
			closeAllMenus();
			closeSideBar();
		} else {
			closeSideBar();
			closeAllMenus();
			$("#downloadsContainer").removeClass("hidden");
			openSideBar();
		}
	}

	function closeAllMenus() {
		$("#link_context_menu").addClass("hidden"); //Lets make sure this is hidden
		$("#downloadsContainer").addClass("hidden"); //And this one
		$("#settingsContainer").addClass("hidden");
		$("#favourites_context_menu").addClass("hidden");
		$("#devToolsContainer").addClass("hidden");
		$("#historyContainer").addClass("hidden");
		//$("#urlWrap").removeClass("searchCoverTop"); //Not needed anymore
		$("#contextMenuBG").addClass("hidden");
		$("#sideBar").removeClass("expandedSidebar");
	}

	function openSettings() {
		var webview = document.querySelector('#webview'+currentTab);

		if (!$("#settingsContainer").hasClass("hidden")) {
			$("#settingsContainer").addClass("hidden");
			closeAllMenus();
			closeSideBar();
		} else {
			closeAllMenus();
			$("#settingsContainer").removeClass("hidden");
			openSideBar();
		}
		//toggleSideBar();
			

		/*
		if (!$("#devToolsContainer").hasClass("hidden")) {
		$("#devToolsContainer").addClass("hidden");
		} else {
		$("#devToolsContainer").removeClass("hidden");
		}
		toggleSideBar();

		var devtools = document.createElement('webview');
		devtools.setAttribute('style', 'height:300px;width:100%;position:absolute;top:300px');
		devtools.setAttribute('partition', 'trusted');
		var container = document.getElementById('devToolsInner');
		container.appendChild(devtools);
		webview.showDevTools(true, devtools);


		$("#devToolsInner").empty();
		//https://github.com/nwjs/nw.js/issues/6004
		webview.showDevTools(true, document.getElementById("devToolsInner"))
		*/

	}

	function openFavourites() {
		var webview = document.querySelector('#webview'+currentTab);
		//createFavourite()
		if (!$("#favourites_context_menu").hasClass("hidden")) {
			$("#favourites_context_menu").addClass("hidden");
			closeAllMenus();
			closeSideBar();
		} else if (!webview.currentAtHome) {
			closeAllMenus();
			$("#favourites_context_menu").removeClass("hidden");
			createFavourite();
			openSideBar();
		}


	} //HistoryInner

	function openHistoryItem(link) {
		var webview = document.querySelector('#webview'+currentTab);
		webview.src = link;
		//closeAllMenus();
		//closeSideBar();
	}


	function loadHistoryB() {
		$("#historyList").empty();

		for(var i = browserHistory.length-1; i > -1; i--) {
			$("#historyList").append('<div class="media p-l-5"><div class="pull-left"><img width="40" src="'+browserHistory[i].favIcon+'" alt=""></div><div class="media-body"><small class="text-muted t-overflow">'+browserHistory[i].url+'</small><br/><a class="t-overflow" href="#" onclick="openHistoryItem(&quot;'+browserHistory[i].url+'&quot;)">'+browserHistory[i].title+'</a></div></div>');
		}
	}

	function loadHistory() {
		var webView = document.querySelector('#webview'+currentTab);
		console.log("webview to send to: ",webView);

		var sendObject = [{
			id: "lol",
			me: "hello, webpage!"
		}]
		// Initialize communications
webView.contentWindow.postMessage(browserHistory, 'file:///usr/eXtern/systemX/apps/extern.web.app/control_pages/history_view.html');
document.addEventListener('message', function(e) {

    // I expect this check to work, but I have not tested it.
    if (e.source != webView.contentWindow)
        return;

    // Handle e.data however you want.
});
	}

	function openHistory() {
		var webview = document.querySelector('#webview'+currentTab);

		closeAllMenus();
		closeSideBar();

		if (webview.src == "file://"+process.cwd()+"/apps/extern.web.app/temporary/Welcome.html") {
			gotToSearch("file://"+process.cwd()+"/apps/extern.web.app/control_pages/history_view.html");
		} else {
			newWebview("file://"+process.cwd()+"/apps/extern.web.app/control_pages/history_view.html",false);
		}

		/*if (!$("#historyContainer").hasClass("hidden")) {
			$("#historyContainer").addClass("hidden");
			closeAllMenus();
			closeSideBar();
		} else if (!webview.currentAtHome) {
			closeAllMenus();
			$("#historyContainer").removeClass("hidden");
			loadHistory();
			openSideBar();
		}*/		
	}

	function openDevTools() {
		var webview = document.querySelector('#webview'+currentTab);

		closeAllMenus();
		$("#sideBar").addClass("expandedSidebar");
		
		$("#devToolsContainer").removeClass("hidden");
		//$("#urlWrap").addClass("searchCoverTop"); //Not needed anymore
		openSideBar();
		cdt = document.getElementById('devToolsWebview');
		webview.showDevTools(true,cdt);
		webview.addEventListener('loadstart', function(event) {
		if (cdt.insertedCSSCodeUrl != cdt.src) {
		cdt.insertedCSSCodeUrl = cdt.src;
		cdt.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'});
		cdt.insertCSS({file: 'apps/extern.web.app/css/dev.css'});
		cdt.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'});
		/*cdt.executeScript({file: 'Shared/CoreJS/jquery.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});
		cdt.insertCSS({file: 'apps/extern.web.app/css/dev.css'});
		cdt.executeScript({file: 'apps/extern.web.app/js/inject_dev.js'});*/
		}
		});

		cdt.addEventListener('loadstop', function(event) {
		console.log("load stop webview");
		//cdt.showDevTools(true);

		cdt.executeScript({file: 'Shared/CoreJS/jquery.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});

		//setTimeout(function(){
		cdt.insertCSS({file: 'apps/extern.web.app/css/dev.css'});
 		cdt.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'}); //}, 5000);
		cdt.executeScript({file: 'apps/extern.web.app/js/inject_dev.js'});

		});
		cdt.addEventListener('did-finish-load', function(event) {
			console.log("did-finish-load webview");
		

				/*if (cdt.insertedJSCodeUrl != cdt.src) {
		cdt.insertedJSCodeUrl = cdt.src;
		cdt.executeScript({file: 'Shared/CoreJS/jquery.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});
		cdt.executeScript({file: 'apps/extern.web.app/js/inject_dev.js'});

		}*/


		/*cdt.executeScript({file: 'Shared/CoreJS/jquery.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});
		cdt.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});
		cdt.executeScript({file: 'apps/extern.web.app/js/inject_dev.js'});
		cdt.insertCSS({file: 'apps/extern.web.app/css/dev.css'});
		cdt.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'});*/});
		/*setTimeout(function(){
		cdt.insertCSS({file: 'apps/extern.web.app/css/dev.css'});
 		cdt.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'}); }, 5000);*/
		//cdt.insertCSS({file: 'apps/extern.web.app/css/dev.css'});
		//cdt.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'});
		$("#contextMenuOverlay").addClass("hidden");
		//closeMenu();

		
	}


	function blurredSuggestion(img) {
		var webview = document.querySelector('#webview'+currentTab);
		if (!webview.currentAtHome) {
			var suggestionsDiv = '#allTabs > .searchSuggestions';
		
			//$(suggestionsDiv).css("background-image",'url("'+img+'"');
			//$(suggestionsDiv).css("background-position","-"+(($(webview).width()/2.85))+"px 0");
			//$(suggestionsDiv).css("background-size",$(webview).width()+"px "+$(webview).height()+"px");
		}
	}

	function getSearchSuggestions(keyword) {
		var webview = document.querySelector('#webview'+currentTab);
		if (webview.currentAtHome){
			var suggestionsDiv = '#suggestionsHomePage'+currentTab;
		}else{
			var suggestionsDiv = '#allTabs > .searchSuggestions';
		}

		if (keyword == "nyika://history") {
				$(suggestionsDiv+' > .blackBgInner > .mainResult > .searchMedia > .searchMain').text("Your Browsing History");
				$(suggestionsDiv+' > .blackBgInner > .mainResult > .searchMedia > .searchDesc').text("View your browsing history in Nyika");
				
				$(suggestionsDiv+' > .blackBgInner > .mainResult > .pull-left > img').attr("src","icon.svg");
				$(suggestionsDiv+' > .blackBgInner > .mainResult').attr("link","nyika://history");
			
			
			if ($(suggestionsDiv+' > .blackBgInner > .mainResult').hasClass('hiddenOut')) {
				$(suggestionsDiv+' > .blackBgInner > .mainResult').removeClass('hiddenOut');
				$(suggestionsDiv+' > .blackBgInner > .mainResult').show();
				setTimeout(function(){
					console.log("lolx: ",$(suggestionsDiv+' > .blackBgInner > .mainResult'));
				$(suggestionsDiv+' > .blackBgInner > .mainResult').trigger('mouseenter');
				}, 1000);
			}
		} else {
		/*setTimeout(function(){
			
		$('#view'+currentTab+'> .zoomContainer > .searchSuggestions').css("background-position","46% -100px");
		 $('#view'+currentTab+'> .zoomContainer > .searchSuggestions').css("background-image",$('background').css("background-image"));
		  $('#view'+currentTab+'> .zoomContainer > .searchSuggestions').css("background-size",$('background').css("background-size"));
							  }, 10000);*/
		//$(suggestionsDiv).css("background-position","46% -100px");
		//$(suggestionsDiv).css("background-position","-"+(($(webview).width()/2.85))+"px 0");

		 //$(suggestionsDiv).css("background-image",$('background').css("background-image"));
		  //$(suggestionsDiv).css("background-size",$('background').css("background-size"));
		  //$(suggestionsDiv).css("background-size",$(webview).width()+"px "+$(webview).height()+"px");
		
		$.getJSON("https://ac.duckduckgo.com/ac/?t=min&q="+keyword, function(datax){
			$(suggestionsDiv+' > .blackBgInner > .searchResult').remove();
			console.log("datax",datax);
			if (datax.length != 0) {
				for(var i=0;i < 4;i++) {
					if ($(suggestionsDiv+' > .blackBgInner > .adaptiveSearch > .media-body > .searchMainX').text() != datax[i].phrase){
						$(suggestionsDiv+' > .blackBgInner').append('<div class="p-l-5 zoomTarget searchResult" searchTerm="'+datax[i].phrase+'"><div class="pull-left"><span class="icon searchIcon">&#61788;</span></div><div class="media-body"><p class="searchMainX">'+datax[i].phrase+'</p></div></div>');
					}
				}
			}
			
			
			$('.searchResult').on("click",function(){
				$(this).addClass("currentSelection");

				var link = searchEngine+$(this).attr("searchTerm");

				webview.searchTerm = $(this).attr("searchTerm");
				gotToSearch(link);
			}); 
		});

		settings = {

    // use browser native animation in webkit, provides faster and nicer
    // animations but on some older machines, the content that is zoomed
    // may show up as pixelated.
    nativeanimation: false,
    easing: "ease",
	animationendcallback: activateBookmark
}

	if (useZoomAnimations) {
		$(".searchResult").zoomTarget(settings);
	}
		

		$.getJSON("https://api.duckduckgo.com/?t=min&skip_disambig=1&no_redirect=1&format=json&q="+keyword, function(data){
			console.log("main bar data",data);
			if (data.Results.length != 0 && data.Results[0].Text == "Official site"){
				$(suggestionsDiv+' > .blackBgInner > .mainResult').attr("link",data.Results[0].FirstURL);
			} else {
				$(suggestionsDiv+' > .blackBgInner > .mainResult').attr("link",searchEngine+keyword);
			}

console.log("AUTO SUGGEST DATA",data);


//request(data.Image).pipe(fs.createWriteStream('doodle.png'))
if (data.AbstractText != "") {
			$(suggestionsDiv+' > .blackBgInner > .mainResult > .searchMedia > .searchMain').text(data.Heading);
			$(suggestionsDiv+' > .blackBgInner > .mainResult > .searchMedia > .searchDesc').text(data.AbstractText);

$(suggestionsDiv+' > .blackBgInner > .mainResult > .pull-left > img').attr("src","icon.svg");
getImageDuckduckgo(data.Image,function (imageData) {
		$(suggestionsDiv+' > .blackBgInner > .mainResult > .pull-left > img').attr("src",imageData);
});
			
			
			if ($(suggestionsDiv+' > .blackBgInner > .mainResult').hasClass('hiddenOut')) {
				$(suggestionsDiv+' > .blackBgInner > .mainResult').removeClass('hiddenOut');
				$(suggestionsDiv+' > .blackBgInner > .mainResult').fadeIn();
			}


}
			//$('#view'+currentTab+'> .zoomContainer > .searchSuggestions').addClass("hii");	
		});	  
		}
	}

	var waitingToGetSuggestions = false;
	var adaptiveFaded = false;

	$('#urlInput').change(function(){
		console.log("input changed");
	});

	$('#urlInput').on('input', function() {
		console.log("input detected");
		var webview = document.querySelector('#webview'+currentTab);
		closeSideBar();
		//$('#allTabs > .searchSuggestions').fadeOut();
		if (webview.currentAtHome){
			var suggestionsDiv = '#suggestionsHomePage'+currentTab;
		}else{
			var suggestionsDiv = '#allTabs > .searchSuggestions';
		}

				$(suggestionsDiv +' .defaultSearchSuggestions').hide();
				$(suggestionsDiv +' .searchHistoryOptions').hide();

		$(suggestionsDiv).fadeIn();
		
		if (!$(suggestionsDiv+' > .blackBgInner > .mainResult').hasClass('hiddenOut')) {
			$(suggestionsDiv+' > .blackBgInner > .mainResult').addClass('hiddenOut');
			$(suggestionsDiv+' > .blackBgInner > .mainResult').fadeOut();
			/*if (validURL($('#urlInput').val())) {
				////console.log("URLIS VALID");
			}*/
			//currentAtHome
		}

		if ($('#urlInput').val() == '') {
			$(suggestionsDiv+' > .blackBgInner > .adaptiveSearch').hide();
			adaptiveFaded = true;
			//$(suggestionsDiv).$(suggestionsDiv).css("display","none"); No need to hide anymore there is suggestions now
					$(suggestionsDiv+' > .blackBgInner > .mainResult').hide();

					//loadRecommendedSearches(".searchSuggestions");

			/*if (webview.currentAtHome) {
					//$('#view'+currentTab+' > .zoomContainer > .searchSuggestions').fadeOut();
					$(suggestionsDiv).css("display","none");
					$(suggestionsDiv+' > .blackBgInner > .mainResult').css("display","none");
				}else {
					//$('#allTabs > .searchSuggestions').fadeOut();
					$('#allTabs > .searchSuggestions').css("display","none");
				}*/
		} else if (privateMode) {
			$(suggestionsDiv+' > .blackBgInner > .adaptiveSearch').attr("searchTerm",$('#urlInput').val());
			$(suggestionsDiv+' > .blackBgInner > .adaptiveSearch > .media-body > .searchMainX').text($('#urlInput').val());
				if (adaptiveFaded) {
			  	$(suggestionsDiv+' > .blackBgInner > .adaptiveSearch').show();
				adaptiveFaded = false;
			}
		} else {
			if (adaptiveFaded) {
			  	$(suggestionsDiv+' > .blackBgInner > .adaptiveSearch').show();
				adaptiveFaded = false;
			}

			$(suggestionsDiv+' > .blackBgInner > .adaptiveSearch > .media-body > .searchMainX').text($('#urlInput').val());
			$(suggestionsDiv+' > .blackBgInner > .adaptiveSearch').attr("searchTerm",$('#urlInput').val());

			if (!waitingToGetSuggestions) {
				waitingToGetSuggestions = true;
				
				setTimeout(function(){
					getSearchSuggestions($('#urlInput').val()); waitingToGetSuggestions = false;
				}, 1000);
			}
		}
	});

	onload = function() { //load first tab
		loadControls();
		//$("#audioPlayingIcon").fadeOut();
		//newWebview("file://"+process.cwd()+"/apps/extern.web.app/temporary/Welcome.html",true);
		//getSearchSuggestions("bing");		
	};

	function navigateTo(url,tabId) {
		resetExitedState();
		document.querySelector('#webview'+tabId).src = url;
	}

	function doLayout(tabId) {
		var webview = document.querySelector('#webview'+tabId);
		var controls = document.querySelector('#controls');
		var controlsHeight = controls.offsetHeight;
		var windowWidth = document.documentElement.clientWidth;
		var windowHeight = document.documentElement.clientHeight;
		var webviewWidth = windowWidth;
		var webviewHeight = windowHeight - controlsHeight;

		var sadWebview = document.querySelector('#sad-webview');
		sadWebview.style.width = webviewWidth + 'px';
		sadWebview.style.height = webviewHeight * 2/3 + 'px';
		sadWebview.style.paddingTop = webviewHeight/3 + 'px';
	}

	function handleExit(event) {
		document.body.classList.add('exited');
	  	if (event.type == 'abnormal') {
			document.body.classList.add('crashed');
	  	}else if (event.type == 'killed') {
			document.body.classList.add('killed');
	  	}
	}

	function resetExitedState() {
	  	document.body.classList.remove('exited');
	  	document.body.classList.remove('crashed');
	  	document.body.classList.remove('killed');
	}

	function handleFindUpdate(event) {
	  	var findResults = document.querySelector('#find-results');
	  	if (event.searchText == "") {
			findResults.innerText = "";
	  	}else {
			findResults.innerText =
			event.activeMatchOrdinal + " of " + event.numberOfMatches;
	  	}

	  	// Ensure that the find box does not obscure the active match.
	  	if (event.finalUpdate && !event.canceled) {
			var findBox = document.querySelector('#find-box');
			findBox.style.left = "";
			findBox.style.opacity = "";
			var findBoxRect = findBox.getBoundingClientRect();
			if (findBoxObscuresActiveMatch(findBoxRect, event.selectionRect)) {
				// Move the find box out of the way if there is room on the screen, or
			  	// make it semi-transparent otherwise.
			  	var potentialLeft = event.selectionRect.left - findBoxRect.width - 10;
			  	if (potentialLeft >= 5) {
					findBox.style.left = potentialLeft + "px";
			  	} else {
					findBox.style.opacity = "0.5";
			  	}
			}
	  	}
	}

	function savePage(currentWebview){

		//let page = webview.src;

		if (currentWebview == null) {
			let webview = document.querySelector('#webview'+currentTab);
			getPageBody(webview,savePage);
		} else {

		let webview = currentWebview;


			/*console.log("webview src extension",webview.src.split('.').pop());
			//console.log("webview src lastchar",rightClickedDiv.getElementsByTagName("HEAD")[0].innerHTML);
//webview.src[webview.src.length-1] == "/" &&
		if (rightClickedDiv.getElementsByTagName("HEAD")[0].innerHTML != "") { //it's a nrmal webpage
			    fs.writeFile(downloadLocation+webview.documentTitle.replace(/[/\\?%*:|"<>]/g, '-')+".html", rightClickedDiv.outerHTML, function(err) {
				if(err) {
        				return console.log(err);
    				}

    				console.log("The file was saved of the DOM!");
			});
		} else { //It's a file!
			console.log("saving file....");
			customDownload(webview.src);
		}*/
		
			
		}

		

		/*// use a timeout value of 10 seconds
		let timeoutInMilliseconds = 5*1000;

		let opts = {
		  url: page,
		  timeout: timeoutInMilliseconds
		}

		request(opts, function (err, res, body) {
		  if (err) {
		    alert(err);
		    return
		  }else{

			let temp = new Date();

			let file = (temp.getFullYear()) + "_" +
				(temp.getMonth()) + "_" +
				(temp.getDate()) + "_" +
				(temp.getHours()) + "_" +
				(temp.getMinutes()) + "_" +
				(temp.getSeconds())+".html";

			let path = process.env['HOME']+"/extern/Downloads/"+file;

			fs.writeFile(path, body, (err) => {
				console.log("saved at: "+path);
			});
		  }
		})*/
	}

	function findBoxObscuresActiveMatch(findBoxRect, matchRect) {
		return findBoxRect.left < matchRect.left + matchRect.width &&
			findBoxRect.right > matchRect.left &&
			findBoxRect.top < matchRect.top + matchRect.height &&
			findBoxRect.bottom > matchRect.top;
	}

	function handleKeyDown(event) {
		if (event.ctrlKey) {
			switch (event.keyCode) {
		  
				case 70:// Ctrl+F
					event.preventDefault();
					openFindBox();
					break;
		  
				case 87:// Ctrl+W
					event.preventDefault();
					closeTab(currentTab);
					break;

				case 84: // Ctrl+T
					event.preventDefault();
					newTab();
					break;

				case 82: // Ctrl+R
					event.preventDefault();
					reloadWebView();
					break;

				case 83: // Ctrl+S
					event.preventDefault();
					savePage();
					break;


				case 107: // Ctrl++.
				case 187:
					event.preventDefault();
					increaseZoom();
					break;

				case 109: // Ctrl+-.
				case 189:
					event.preventDefault();
					decreaseZoom();
			}
		}
	}

	function checkLoading () {
		var webview = document.querySelector('#webview'+currentTab);
		
		if (webview.loading) {
			$("#favicon").addClass("hidden");
			$("#loadingRing").removeClass("hidden");
		  	document.body.classList.add('loading');
			$("#reloadButton").empty();
			$("#reloadButton").append('<i style="text-shadow: 0 0 20px rgba(0, 0, 0, 0.8);" class="fas fa-circle" aria-hidden="true">');
			$("#reloadButton").attr('data-original-title',"Stop loading");
			$("#reloadButton").addClass('currentlyLoading');
		} else {
			$("#loadingRing").addClass("hidden");
			$("#favicon").removeClass("hidden");
	  
			$("#reloadButton").empty();
			$("#reloadButton").append('<span class="icon">&#61910;</span>');
			$("#reloadButton").removeClass('currentlyLoading');
			$("#reloadButton").attr('data-original-title',"Refresh");
			checkSecure(webview);
		}
	}

	function handleLoadCommit() {
		resetExitedState();
		var webview = document.querySelector('#webview'+currentTab);
		checkLoading ();
		if (!$("#urlInput").is(':focus'))
			if (webview.src == "file://"+process.cwd()+"/apps/extern.web.app/control_pages/history_view.html")
				document.querySelector('#urlInput').value = "nyika://history";
			else
				document.querySelector('#urlInput').value = webview.src;

		if (webview.src.indexOf("file:///usr/eXtern/systemX/apps/extern.web.app") == 0) {
			console.log("is history");
			var forceTransparency = true;
			$('#webview'+currentTab).addClass("noBgOnPage");
		} else {
			console.log("is not history: ",webview.src);
			var forceTransparency = false;
			$('#webview'+currentTab).removeClass("noBgOnPage");
		}

		if (useTransparency || forceTransparency) {
			$('#webview'+currentTab).attr("allowtransparency","");
		} else {
			$('#webview'+currentTab).removeAttr("allowtransparency");
		}
		
		if (webview.src.indexOf("extern.web.app/temporary/Welcome.html") == -1) {
			webview.currentAtHome = false;
			$(".hideOnHome").fadeIn();
			if (findBookmarkWithUrl(webview.src)) {
				$("#favouritesButton").addClass("bookmarked");
				webview.bookmarked = true;
			} else {
				$("#favouritesButton").removeClass("bookmarked");
				webview.bookmarked = false;
			}
		} else {
			$("#favouritesButton").removeClass("bookmarked");
			webview.bookmarked = false;
			$(".hideOnHome").fadeOut();
		}
		
		document.querySelector('#backButton').disabled = false;
	  	canGoBack = webview.canGoBack();
		if (webview.currentAtHome){
			document.querySelector('#backButton').disabled = true;
		}
		
		if ((!$('#view'+currentTab+' > .bookmarks > .bookmarksOuter > .currentSelection').length) && !canGoBack){
			document.querySelector('#backButton').disabled = true;
		}
		
		if (!webview.canGoToHome && !canGoBack){
			document.querySelector('#backButton').disabled = true;
		}
		
	  	document.querySelector('#forwardButton').disabled = !webview.canGoForward();
		if (webview.favIcon != "undefined"){
			document.querySelector('#favicon').src = webview.favIcon;
			if (browserHistory[browserHistory.length-1].url == webview.src) {
					browserHistory[browserHistory.length-1].favIcon = webview.favIcon;
					localStorage.setItem('browserHistory', JSON.stringify(browserHistory));

				console.log("changed favIcon");
			}
		}
	  
	  	document.querySelector('#tabicon'+currentTab).src = webview.favIcon;
	  
		if (webview.currentAtHome) {
			//document.querySelector('#settingsButton').disabled = true;
			
			if (!$('#webview'+currentTab).hasClass("animated fadeInUp"))
				$('#webview'+currentTab).addClass("animated fadeInUp");
			$("#navigationBar").removeClass("navShadow");
			$(".controlButton").removeClass("active");
			$(win.minimize_button).removeClass("active");
			$(win.maximize_button).removeClass("active");
			$(win.close_button).removeClass("active");
			$("#blur2").addClass("hidden");
			$("#urlDisplay").text('');
			win.title = 'Nyika';
			$("#newTabText"+currentTab).text("New Tab");
          	$("#tabNave"+currentTab).parent().attr("title","New Tab");
		} else {
			document.querySelector('#settingsButton').disabled = false;
			setTimeout(function() {
				if ($('#webview'+currentTab).hasClass("animated fadeInUp"))
					$('#webview'+currentTab).removeClass("animated fadeInUp");
			}, 500);
			
			if (!$("#allTabs").hasClass("allTabsReseize")){
				$("#navigationBar").addClass("navShadow");
				$(".controlButton").addClass("active");
				$(win.minimize_button).addClass("active");
				$(win.maximize_button).addClass("active");
				$(win.close_button).addClass("active");
				$("#blur2").removeClass("hidden");
			}
			$("#urlDisplay").text(webview.documentTitle);
			console.log("2 webview.documentTitle",webview.documentTitle);

			win.title = webview.documentTitle;

			if ((browserHistory[browserHistory.length-1].url == webview.src) && webview.documentTitle != '')
				browserHistory[browserHistory.length-1].title = webview.documentTitle;
				localStorage.setItem('browserHistory', JSON.stringify(browserHistory));

			//if ((webview.favIcon != "search.png") && ())

			if (webview.documentTitle == ''){
				$("#newTabText"+currentTab).text(webview.src.replace("https://","").replace("http://",""));
              $("#tabNave"+currentTab).parent().attr("title",webview.src.replace("https://","").replace("http://",""));
			}else{
				$("#newTabText"+currentTab).text(webview.documentTitle);
              	$("#tabNave"+currentTab).parent().attr("title",webview.documentTitle);
			}
			
			webview.getZoom(function(zoomFactor) {
				$('#zoom-text').val(zoomFactor);
			});
		}
		
		if ($('#urlInput').val().indexOf("extern.web.app/temporary/Welcome.html") != -1) {
			$('#urlInput').val('');
			
		}

		var objDiv = document.getElementById("tabNav");
	objDiv.scrollLeft = objDiv.scrollWidth;
		
	}

	function setAudioStatus(){
		var webview = document.querySelector('#webview'+currentTab);
		if (webview.audioPlaying && !isAudioPlaying){
			$("#audioPlayingIcon").fadeIn();
			$("#urlDisplay").addClass("audioPlayingTitleAdjust");
			isAudioPlaying = true;
		}else if (isAudioPlaying){
			$("#audioPlayingIcon").fadeOut();
			$("#urlDisplay").removeClass("audioPlayingTitleAdjust");
			isAudioPlaying = false;
		}
	}

	function monitorAudioPlaying(webview,ids){
		//checking if our webview still exists..
		if ($("#webview"+ids).length){
			webview.executeScript({code: `JSON.stringify(Array.from(document.getElementsByTagName('video')).map(video => video.paused))`}, function(results) {
				if (results) {
					// Parse result add fallbacks
					isPaused = JSON.parse(results);
			
					if (isPaused.length != 0){
						var tempPlayingAudioStatus = false;
						
						for (var i = 0; i < isPaused.length; i++){
							if (!isPaused[i]){
								tempPlayingAudioStatus = true;
							}
						}
						
						if (tempPlayingAudioStatus){
							if (!webview.audioPlaying){
								$("#newTabSound"+webview.ids).fadeIn();
							}
							
							webview.audioPlaying = true;
							setAudioStatus();
						} else{
							if (webview.audioPlaying){
								$("#newTabSound"+webview.ids).fadeOut();
							}

							webview.audioPlaying = false;
							
							setAudioStatus();
						}
					}
				} else {
					//////console.log("error VIDEO");
				}

			});
		}else{
			//////console.log("It's gone...");
		}
	}

	function openInNewTab(event){
		if (event.windowOpenDisposition == "new_foreground_tab")
			newWebview(event.targetUrl,false);
		
		if (event.windowOpenDisposition == "new_background_tab")
			newWebview(event.targetUrl,false);
		
		if (event.windowOpenDisposition == "new_window")
			newWebview(event.targetUrl,false);
	}

	function handleLoadStart(event) {
		var webview = event.srcElement;
		console.log("loadStopEvent",webview);

		if (useTransparency && event.isTopLevel) {
			console.log("loadstart",event);
			$(webview).addClass("reducedOpacity");
		}

		if (event.isTopLevel) {
			$(webview).addClass("topMargin");
			webview.insertedJSCodeUrl = "";
			webview.insertedCSSCodeUrl = "";
		}

		webview.loading = true;
		webview.documentTitle = '';
		$("#urlDisplay").text(webview.documentTitle);
		win.title = webview.documentTitle;

		console.log("webview.documentTitle",webview.documentTitle);
      
		//console.log("load start",event);
      
		$("#newTabText"+webview.ids).text(webview.src.replace("https://","").replace("http://",""));
		checkSecure(event.srcElement);
		event.srcElement.audioPlaying = false;
		isAudioPlaying = false;
		//$("#audioPlayingIcon").fadeOut();
		$("#urlDisplay").removeClass("audioPlayingTitleAdjust");
		setTimeout(function(){ handleLoadCommit();}, 500);
		
	  	isLoading = true;

		resetExitedState();
		if (!event.isTopLevel) {
			return;
		}
		if (event.url.indexOf("extern.web.app/temporary/Welcome.html") == -1) {
			if (!$("#urlInput").is(':focus'))
          document.querySelector('#urlInput').value = event.url;
          var webviewIdNo = $(webview).attr("id").replace("webview","");
          $("#loadingStatusView"+webviewIdNo).text("Waiting for "+event.url);
          $("#loadingStatusView"+webviewIdNo).removeClass("hidden");
        } else {
          $("#loadingStatusView"+webviewIdNo).addClass("hidden");
        }
	}


	function getPageTitle(webview){
		//var webview = document.querySelector('#webview'+currentTab);
		// Asynchronously check for a favicon in the web page markup
		webview.executeScript({code: `JSON.stringify(Array.from(document.title))`}, function(results) {
			if (results) {
				var titleData = JSON.parse(results[0]);
				var pageTitle = "";
				
				for (var i = 0; i < titleData.length; i++){
					pageTitle += titleData[i];
				}

				webview.documentTitle = pageTitle;
				$("#newTabText"+webview.ids).text(webview.documentTitle);
				handleLoadCommit();
							
			} else {
				//////console.log("error");
			}
		});
	}


	function getPageBody(webview,callback){
		//var webview = document.querySelector('#webview'+currentTab);
		// Asynchronously check for a favicon in the web page markup
		webview.executeScript({code: `JSON.stringify(Array.from(document..getElementsByTagName("html")))`}, function(results) {
			if (results) {
				webview.fullBody = JSON.parse(results[0]);
				callback(webview);
							
			} else {
				//////console.log("error");
			}
		});
	}

//win.showDevTools();

	function getPageIcon(webview,retry){
		//var webview = document.querySelector('#webview'+currentTab);
		if (retry) {
			var iconClass = `'icon'`;
		} else {
			var iconClass = `'shortcut icon'`;
		}
					webview.favIcon = "file://"+process.cwd()+"/apps/extern.web.app/icon.svg";
document.querySelector('#tabicon'+webview.ids).src = webview.favIcon;
		// Asynchronously check for a favicon in the web page markup
		webview.executeScript({code: `JSON.stringify(Array.from(document.getElementsByTagName('link'))
			.filter(link => link.rel.includes('icon'))
			.map(link => link.href))
		`}, function(results) {
			if (results) {
				// Parse result add fallbacks
				favicon = JSON.parse(results[0]);
				//document.querySelector('#favicon').src = favicon[0];
				//webview.favIcon = favicon[0];
				if (favicon != "undefined" && (favicon.length > 0)){
					webview.favIcon = favicon[0];
					document.querySelector('#tabicon'+webview.ids).src = webview.favIcon;

					if (browserHistory[browserHistory.length-1].url == webview.src) {
						browserHistory[browserHistory.length-1].favIcon = webview.favIcon;
						localStorage.setItem('browserHistory', JSON.stringify(browserHistory));

				console.log("changed favIcon");
				handleLoadCommit();
			}
				} else {

					if (!retry) {
						getPageIcon(webview,true);
				} else {
					if (webview.src.indexOf("google.com") != -1) { //FIXME: Do this fall all sites if favicon fails. Not doing right now as that needs to check if it exists
						webview.favIcon = "http://google.com/favicon.ico";
						document.querySelector('#tabicon'+webview.ids).src = webview.favIcon;
						
						if (browserHistory[browserHistory.length-1].url == webview.src) {
							browserHistory[browserHistory.length-1].favIcon = webview.favIcon;
							localStorage.setItem('browserHistory', JSON.stringify(browserHistory));
							handleLoadCommit();
						}
					}
				}
				
				}
							
			} else {
				//////console.log("error");
			}
			
		});
	}

	function getPageVideos(webview){
		//var webview = document.querySelector('#webview'+currentTab);
		
		// Asynchronously check for a favicon in the web page markup
		webview.executeScript({code: `
			JSON.stringify(Array.from(document.getElementsByTagName('video'))
			.map(video => video.paused))
		`}, function(results) {
			if (results) {
				// Parse result add fallbacks
				favicon = JSON.parse(results);
				//document.querySelector('#favicon').src = favicon[0];
							//webview.favIcon = favicon[0];
							////////console.log("setting icon for :"+webview.ids);
							//document.querySelector('#tabicon'+webview.ids).src = webview.favIcon;
							//////console.log("videos playing");
					//////console.log(favicon[0]);
			  //handleLoadCommit();
							
			} else {
				//////console.log("error VIDEO");
			}
			
		});
	}


	function setScrollBar(webview){

	var injectCode = `var actualCode = '(' + function() {
	function loadScript(url, callback)
	{
		// Adding the script tag to the head as suggested before
		var head = document.getElementsByTagName('head')[0];
		var script = document.createElement('script');
		script.type = 'text/javascript';
		script.src = url;

		// Then bind the event to the callback function.
		// There are several events for cross browser compatibility.
		script.onreadystatechange = callback;
		script.onload = callback;

		// Fire the loading
		head.appendChild(script);
	}


	//loadScript("https://code.jquery.com/jquery-2.2.4.min.js", loadNiceScroll);
	//loadScript("https://code.jquery.com/jquery-2.2.4.min.js", $("embed").niceScroll({mousescrollstep: 80, smoothscroll: true, zindex:2999999999, bouncescroll: true, enabletranslate3d:true}););
	$("html").niceScroll({mousescrollstep: 80, smoothscroll: true, zindex:2999999999, bouncescroll: true, enabletranslate3d:true});
	$("embed").niceScroll({mousescrollstep: 80, smoothscroll: true, zindex:2999999999, bouncescroll: true, enabletranslate3d:true});

	var videos = document.getElementsByTagName('video');

	for (var i = 0; i < videos.length; i++)
	{
	//videos[i].setAttribute('onpause','//////console.log("MediaPa - Ignore this was generated by the web browser")');
	//videos[i].setAttribute('onplay','//////console.log("MediaPl - Ignore this was generated by the web browser")');
	}
	//End
	} + ')();';
	var script = document.createElement('script');
	script.textContent = actualCode;
	(document.head||document.documentElement).appendChild(script);
	/*script.parentNode.removeChild(script);*/`;

		webview.executeScript({file: 'Shared/CoreJS/jquery.min.js'});
		webview.executeScript({file: 'Shared/CoreJS/jquery-ui.min.js'});

		if (webview.src.indexOf("file:///usr/eXtern/systemX/apps/extern.web.app") == 0) {
			console.log("is history");
			var forceTransparency = true;
		} else {
			console.log("is not history: ",webview.src);
			var forceTransparency = false;
		}
		//webview.executeScript({file: 'js/scroll.min.js'});
		if (useTransparency || forceTransparency) {
			console.log("using blur")
			if (fancyRendering)
				webview.executeScript({file: 'apps/extern.web.app/js/inject_transparency.js'});
			else
				webview.executeScript({file: 'apps/extern.web.app/js/inject_transparency_classic.js'});
		} else {
			console.log("not using blur");
			if (fancyRendering)
				webview.executeScript({file: 'apps/extern.web.app/js/inject.js'});
			else
				webview.executeScript({file: 'apps/extern.web.app/js/inject_classic.js'});
		}
		//webview.insertCSS({file: 'Shared/CoreCSS/scrollbar-native.css'});
                //webview.insertCSS({file: 'apps/extern.web.app/css/adjustMargin.css'});
	//webview.executeScript({ code: injectCode });
	}

	function checkConsole(event){
		if (event.message == "MediaPl - Ignore this was generated by the web browser"){
			$("#audioPlayingIcon").fadeIn();
			$("#urlDisplay").addClass("audioPlayingTitleAdjust");
		}
		
		if (event.message == "MediaPa - Ignore this was generated by the web browser"){
			$("#audioPlayingIcon").fadeOut();
			$("#urlDisplay").removeClass("audioPlayingTitleAdjust");
		}
	}

	function handleResponseDetails(event) {
		console.log("handleResponseDetails",event);
	}

	function handleLoadStop(event){
	  // We don't remove the loading class immediately, instead we let the animation
	  // finish, so that the spinner doesn't jerkily reset back to the 0 position.
		var webview = event.srcElement;
		webview.loading = false;
		isLoading = false;

				if (!webview.currentAtHome && webview.id == "webview"+currentTab) { //Let's make sure we aren't home

				console.log("is it history check: ",webview.src.indexOf("file:///usr/eXtern/systemX/apps/extern.web.app/control_pages/history_view.html"));
					if (webview.src == "file:///usr/eXtern/systemX/apps/extern.web.app/control_pages/history_view.html") {
						console.log("is history: ")
						loadHistory();
					}
			webview.captureVisibleRegion(function(img){
				//console.log("seeing img to",webview.id);
		webview.previewImage = img;
		//console.log("which webview: ",webview);
              
			});
				}


		console.log("loadstop A");

		if (!webview.currentAtHome && webview.id == "webview"+currentTab && !$("#urlInput").is(':focus'))
			webview.focus();


		

	//console.log("loadstop",event);
      
      var webviewIdNo = $(webview).attr("id").replace("webview","");
      $("#loadingStatusView"+webviewIdNo).addClass("hidden");
		
		var webview = document.querySelector('#webview'+currentTab);
		if (webview.insertedJSCodeUrl != webview.src) {
		webview.insertedJSCodeUrl = webview.src;
		setScrollBar(event.srcElement);
		console.log("js sent");
		}
		getPageTitle(event.srcElement);
		getPageIcon(event.srcElement);
		getPageVideos(event.srcElement);
		
		if (useZoomAnimations) {
			console.log("loadstop B canGoBack: ",webview.canGoBack());
			console.log("loadstop B loadingFromHome: ",webview.loadingFromHome);
			
			////console.log("WEBVIEW LOADING HOME: "+webview.loadingFromHome)
		if (!webview.canGoBack() && !webview.loadingFromHome){
			console.log("going home from here")
			goToHome();
		}
		} else {
			
				console.log("loadstop B canGoBack: ",webview.canGoBack());
			console.log("loadstop B loadingFromHome: ",webview.loadingFromHome);
			console.log("loadstop B src: ",webview.src);
			////console.log("WEBVIEW LOADING HOME: "+webview.loadingFromHome)
		if (!webview.canGoBack() && !webview.loadingFromHome){
			console.log("going home from here")
			goToHome();
		}
			
		}
		
	//$(webview).removeClass("reducedOpacity"); //FIXME Test to make sure no clashes
	}

	function handleLoadAbort(event) {
	  ////console.log('LoadAbort');
	  ////console.log('  url: ' + event.url);
	  ////console.log('  isTopLevel: ' + event.isTopLevel);
	  ////console.log('  type: ' + event.type);
	}

	function handleLoadRedirect(event) {
		resetExitedState();
		if (!$("#urlInput").is(':focus'))
		if (event.srcElement.src == "file://"+process.cwd()+"/apps/extern.web.app/control_pages/history_view.html")
			document.querySelector('#urlInput').value = "nyika://history";
		else
			document.querySelector('#urlInput').value = event.srcElement.src;
		checkSecure(event.srcElement);
	}

	function checkSecure(webview){
		if (webview.src.indexOf("https") == 0)
		{
			//removeClass("hidden");
			$("#secureConnection2-text").fadeIn();
			$("#secureConnection2").fadeIn();
			setTimeout(function() {
				$("#secureConnection2-text").fadeOut();
			}, 1500);
			$("#urlDisplay").addClass("secureResize");
		}
		else
		{
			$("#secureConnection2").fadeOut();//addClass("hidden");
			$("#urlDisplay").removeClass("secureResize");
		}
	}

	var inFullscreen = false;
	var already_done = false;
	var isMaximized = false;

	function maximizeBrowser(){
		if (isMaximized){
			win.unmaximize();
			//$("#windowTitleBar").fadeIn();
			//$("#allTabsC").css("height","calc(100% - 80px)");
			isMaximized = false;
		}else{
			//$("#windowTitleBar").hide();
			//$("#allTabsC").css("height","calc(100% - 80px)");
			
			win.maximize();
			isMaximized = true;
		}
	}

	function fullscreenRequest(){
		var webview = $('#webview'+currentTab);
		if (inFullscreen)
		{
			////console.log("exiting fullscreen");
			//webview.removeClass("overrideHeight");
			//$("#windowTitleBar").removeClass("hidden");
			//$("#navigationBar").removeClass("hidden");
			//win.unmaximize();
			inFullscreen = false;
			/*if (chrome.app.window.current().isMaximized()) {
				console.log("YES WE ARE MAXIMIZED -- inFulscreen");
				win.restore();
				win.maximize();
			}*/
		}
		else
		{
			////console.log("getting in fullscreen");
			//$("#webView"+$.currentTab).addClass("overrideHeight");
			//webview.addClass("overrideHeight");
			//$("#windowTitleBar").addClass("hidden");
			//$("#navigationBar").addClass("hidden");
			//win.maximize();
			/*if (chrome.app.window.current().isMaximized())
				console.log("YES WE ARE MAXIMIZED -- NOT inFulscreen");
			else
				console.log("No WE ARE NOT MAXIMIZED -- NOT inFulscreen");*/
			inFullscreen = true;
		}
	}

	function returnToWebviewFocus(){
		//$("#link_context_menu").addClass("hidden");
		
		if ($("#allTabs").hasClass("allTabsReseize"))
			closeSideBar();

			$("#contextMenuBG").addClass("hidden");
			$("#contextMenuOverlay").addClass("hidden");
			$('#link_context_menu').removeClass('animated fadeInDown');
			$('#link_context_menu').addClass('hidden');
		//}
		//$("#right_click_preview").addClass("hidden");
	}

	function handleClick(event){
		//$("#link_context_menu").addClass("hidden");
		
		/*if ($("#allTabs").hasClass("allTabsReseize")) {
			closeSideBar();
			$('#link_context_menu').removeClass('animated fadeInDown');
			$('#link_context_menu').addClass('hidden');
		}*/
		//$("#right_click_preview").addClass("hidden");
	}

	function closeMenu() {
		if (!$("#link_context_menu").hasClass("hidden")) {
			$('#link_context_menu').removeClass('animated fadeInDown');
			  $('#link_context_menu').addClass('hidden');
				$('#contextMenuBG').addClass('hidden');
			
		}
		closeSideBar();
	}

	function handleMenu(event){
		console.log("handling MENU",event);
		//event.defaultPrevented = true;
		////console.log("CONTEXT MENU:",event);
		//TakeDesktopScreenshot(event.clientX,event.clientY,'ContextMenu',setMenuBg);
		/*var webshot = require('webshot');

	webshot('amazon.com', 'amazon.png', function(err) {
	  if (err) return ////console.log(err);
	  ////console.log('OK');
	});*/

	$("#contextMenuOverlay").removeClass("hidden");

		var webview = document.querySelector('#webview'+currentTab);

		console.log("mouseX: ",mouseX);

		console.log("mouseY: ",mouseY);

		if (mouseY > (win.height-465)) {
			if (mouseY > (win.height-235)) {
				console.log("using higher posx")
				$("#link_context_menu").css("left",mouseX-110);
				$("#link_context_menu").css("top",mouseY-440);
				
				$("#contextMenuBG").css("left",mouseX-110);
				$("#contextMenuBG").css("top",mouseY-440);
			} else {
				console.log("using higher pos")
			$("#link_context_menu").css("left",mouseX-110);
			$("#link_context_menu").css("top",mouseY-233);
			
			$("#contextMenuBG").css("left",mouseX-110);
			$("#contextMenuBG").css("top",mouseY-233);
			}

			/*$("#link_context_menu").css("left",mouseX-110);
			$("#link_context_menu").css("top",mouseY-233);
			
			$("#contextMenuBG").css("left",mouseX-110);
			$("#contextMenuBG").css("top",mouseY-233);*/
			

		} else {
			console.log("using this part",mouseY);
			$("#link_context_menu").css("left",mouseX-110);
			$("#link_context_menu").css("top",parseInt(mouseY)+20);
			
			$("#contextMenuBG").css("left",mouseX-110);
			$("#contextMenuBG").css("top",parseInt(mouseY)+20);
		}

		

		
		
		getTagName(webview);
		////console.log("click Event",event);
		
		
		
		
		/*var imageObj = new Image();
		imageObj.onload = function() {
			destCtx.drawImage(imageObj, 0, 0, cWidth, cHeight);
		  };
		  imageObj.src = 'file:///home/anesu/Pictures/Any%20Wallpapers/iIGVK5F.jpg';*/
		//destCtx.drawImage(sourceCanvas, 0, 0, cWidth, cHeight);
		//$("#link_context_menu").css("left",event.clientX-110);
		//$("#link_context_menu").css("top",event.clientY);
		


		
			////console.log("Rightclick info: ",event);

		  //$('#contextMenuBgCover').css("background-position","-"+event.clientX+"px -"+event.clientY+"px");
		  //$('#contextMenuBgCover').css("background-image",$('background').css("background-image"));
		  //$('#contextMenuBgCover').css("background-size",$('background').css("background-size"));
	   // $("#link_context_menu").removeClass("hidden");
		
		//getRightClick(webview)
		return false;
	}

	function setMenuBg(sourceCanvas,X,Y){
		//var sourceCanvas = document.getElementById("bg_cover");
		/*var sourceCtx = sourceCanvas.getContext('2d');
		var destinationCanvas = document.getElementById("contextMenuBgCover");
		var destCtx = destinationCanvas.getContext('2d');
		var cWidth = 225;
		var cHeight = 270;
		var gui = require('nw.gui');
		var win = gui.Window.get();
		var winX = -win.x;
		var winY = -win.y;
		var imgData=sourceCtx.getImageData(X-110,Y,cWidth,cHeight);
		destCtx.putImageData(imgData,0,0);*/
			
	}

	function getRightClick(webview){
		//var webview = document.querySelector('#webview'+currentTab);
		// Asynchronously check for a favicon in the web page markup
		//document.elementFromPoint(`+x+`,`+y+`);
		////console.log("x: "+x+" y: "+y);
		getTagName(webview);
		/*JSON.stringify(Array.from(document.elementFromPoint(`+x+`,`+y+`))
	.map(a => a.href))*/
		/*webview.executeScript({code: `
				JSON.stringify(document.elementFromPoint(`+x+`,`+y+`).href)
			`}, function(results) {
						if (results) {
							////console.log("RESULTS");
							////console.log(results);
							
						} else {
							////console.log("error");
						}
			
					});*/
	}

	function checkForDataHref(){
		webview.executeScript({code: `
			////console.log(document.elementFromPoint(`+x+`,`+y+`));
			JSON.stringify(document.elementFromPoint(`+x+`,`+y+`).tagName.toLowerCase())
		`}, function(results) {
			if (results) {
				return results[0];
			} else {
				////console.log("error");
			}
		});
	}

	function get_web_data(domainName){
		var web_search = new XMLHttpRequest();
		////console.log("Searched Domain: "+domainName.replace("www.",""));
		var url = "https://en.wikipedia.org/w/api.php?action=query&titles="+domainName.replace("www.","")+"&prop=pageimages&redirects&pithumbsize=215&indexpageids=&format=json";
			  
		web_search.onreadystatechange = function() {
			if (web_search.readyState == 4 && web_search.status == 200) {
				var webPreviewSearch = JSON.parse(web_search.responseText);
				var wikiID = webPreviewSearch.query.pageids[0].toString();
				if (wikiID != -1){
					if (typeof webPreviewSearch.query.pages[wikiID].thumbnail != 'undefined')
					  	var backupThumbnail = webPreviewSearch.query.pages[wikiID].thumbnail.source;
					else{
					  	var backupThumbnail = null;
					}
				  
				  	var websiteTitle = webPreviewSearch.query.pages[wikiID].title;
				  
					getWebsiteLogoID(websiteTitle,backupThumbnail);
				}else{
				  	//Lets retry, this time it's a ditch effort XD
				  	domainNameOnly = domainName.replace("www.","").split(".");
				  	if (domainName !=domainNameOnly[0]){
						get_web_data(domainNameOnly[0]);
				  	}
				}
			}
		};
		
		web_search.open("GET", url, true);
		web_search.send();
	}

	function youtubeThumbnails(fullUrl) {
		var vidId = fullUrl.match(/youtube\.com.*(\?v=|\/embed\/)(.{11})/).pop();
		document.getElementById('rightclick_bg').src = "http://img.youtube.com/vi/"+vidId+"/0.jpg";
		document.getElementById('right_click_preview').src = "http://img.youtube.com/vi/"+vidId+"/0.jpg";
		$("#right_click_preview").removeClass("hidden");
		var url_fix = fullUrl.slice(0, fullUrl.lastIndexOf('/'))+'/watch?v='+vidId;
		
		setRightClickOptions (url_fix); // A temporary fix for a bug
	}

	//Making it ready to use extensions for right clic menu

	var youtubeExt = {
		name: "YouTube Thumbnails",
		domain: "youtube.com",
		checkFor: "watch?v=",
		functions: youtubeThumbnails
	}

	var rightClickExtensions = [];

	rightClickExtensions.push(youtubeExt);

	function websiteLogo(domainName,fullUrl) {
		var supportedExtensionFound = false;

		//Set default image
		document.getElementById('rightclick_bg').src = "icon.svg";
		document.getElementById('right_click_preview').src = "icon.svg";
		$("#right_click_preview").addClass("hidden");

		if (privateMode) {
			$("#right_click_preview").removeClass("hidden");
		} else {
			//Do we have extensions that handle this specific domain?
		for (var i = 0; i < rightClickExtensions.length; i++) {
			if (rightClickExtensions[i].domain == domainName.replace("www.","") && fullUrl.indexOf(rightClickExtensions[i].checkFor) != -1) {
				rightClickExtensions[i].functions(fullUrl);//////console.log("FOUND IT!");
				supportedExtensionFound = true;
			}	
		}
		
		if (!supportedExtensionFound) {

		//Set default image
		document.getElementById('rightclick_bg').src = "icon.svg";
		document.getElementById('right_click_preview').src = "icon.svg";
		$("#right_click_preview").addClass("hidden");

		console.log("getting icon data here"); //https://api.duckduckgo.com/i/4bf16782.png

			$.getJSON("https://api.duckduckgo.com/?t=min&skip_disambig=1&no_redirect=1&format=json&q="+domainName.replace("www.",""), function(data){
				if (data.length != 0){
					console.log("recieved data: ",data.Image);
				   	getImageDuckduckgo(data.Image,function (imageData) {
							 console.log("icon data b")
	document.getElementById('rightclick_bg').src = imageData;
					document.getElementById('right_click_preview').src = imageData;
					$("#right_click_preview").removeClass("hidden");
});
				}
				//$('#view'+currentTab+'> .zoomContainer > .searchSuggestions').addClass("hii");
				
			});


		}
		//document.getElementById('rightclick_bg').src = "https://logo.clearbit.com/"+domainName.replace("www.","");
						  //document.getElementById('right_click_preview').src = "https://logo.clearbit.com/"+domainName.replace("www.","");
		//$("#right_click_preview").removeClass("hidden");
		}
		
	}



function getImageDuckduckgo(imageUrl,callback) {
$.getJSON("https://externos.io/apps/web/imagetobase642.php?image="+imageUrl, function(data){

		console.log("IMG DATA",data);

				if (data.success){
					callback(data.base64);
				   	//document.getElementById('rightclick_bg').src = data.base64;
					//document.getElementById('right_click_preview').src = data.base64;
					//$("#right_click_preview").removeClass("hidden");
				}

		});
}

	function getWebsiteLogo(ID,backupThumbnail){
		var web_search = new XMLHttpRequest();

		var url = "http://logos.wikia.com/api/v1/Articles/Details/?ids="+ID;

		web_search.onreadystatechange = function() {
			if (web_search.readyState == 4 && web_search.status == 200) {
				var webLogoSearch = JSON.parse(web_search.responseText);

			  	companyLogo = webLogoSearch.items[ID].thumbnail;

			  	if (companyLogo != null){
				  	document.getElementById('rightclick_bg').src = companyLogo;
				  	document.getElementById('right_click_preview').src = companyLogo;
				  	$("#right_click_preview").removeClass("hidden");
			  	}else if (backupThumbnail != null){
					  document.getElementById('rightclick_bg').src = backupThumbnail;
					  document.getElementById('right_click_preview').src = backupThumbnail;
					  $("#right_click_preview").removeClass("hidden");
				}
				/*var wikiID = webPreviewSearch.query.pageids[0].toString();
				////console.log(webPreviewSearch);
				if (wikiID != -1)
				{
				var thumbnailSource = webPreviewSearch.query.pages[wikiID].thumbnail.source;

				//////console.log("Source: "+thumbnailSource);
				document.getElementById('rightclick_bg').src = thumbnailSource;
				document.getElementById('right_click_preview').src = thumbnailSource;
				$("#right_click_preview").removeClass("hidden");
				}*/
		  	}
		};
		  
		web_search.open("GET", url, true);
		web_search.send();
	}


	function getWebsiteLogoID(websiteTitle,backupThumbnail){
		var web_search = new XMLHttpRequest();
		//////console.log("Searched Domain: "+domainName.replace("www.",""));
		var url = "http://logos.wikia.com/api/v1/Search/List/?query="+websiteTitle+"&limit=25&namespaces=0%2C14";
			  
		web_search.onreadystatechange = function() {
		  	if (web_search.readyState == 4 && web_search.status == 200) {
			  	var webLogoSearch = JSON.parse(web_search.responseText);
			  	logoID = webLogoSearch.items[0].id;
			  	getWebsiteLogo(logoID,backupThumbnail);
			  	/*var wikiID = webPreviewSearch.query.pageids[0].toString();
			  	if (wikiID != -1)
			  {
			  var thumbnailSource = webPreviewSearch.query.pages[wikiID].thumbnail.source;
			  
			  document.getElementById('rightclick_bg').src = thumbnailSource;
			  document.getElementById('right_click_preview').src = thumbnailSource;
			  $("#right_click_preview").removeClass("hidden");
			  }*/
		  	}
		};

		web_search.open("GET", url, true);
		web_search.send();
	}


	function toDOM(obj) {
	  	if (typeof obj == 'string') {
			obj = JSON.parse(obj);
	  	}
	  	var node, nodeType = obj.nodeType;
	  	switch (nodeType) {
			case 1: //ELEMENT_NODE
		  		node = document.createElement(obj.tagName);
		  		var attributes = obj.attributes || [];
		  		for (var i = 0, len = attributes.length; i < len; i++) {
					var attr = attributes[i];
					node.setAttribute(attr[0], attr[1]);
		  		}
		  		break;
			case 3: //TEXT_NODE
			  	node = document.createTextNode(obj.nodeValue);
			  	break;
			case 8: //COMMENT_NODE
			  	node = document.createComment(obj.nodeValue);
			  	break;
			case 9: //DOCUMENT_NODE
			  	node = document.implementation.createDocument();
			  	break;
			case 10: //DOCUMENT_TYPE_NODE
			  	node = document.implementation.createDocumentType(obj.nodeName);
			  	break;
			case 11: //DOCUMENT_FRAGMENT_NODE
			  	node = document.createDocumentFragment();
			  	break;
			default:
			  	return node;
	  	}
	  
	  	if (nodeType == 1 || nodeType == 11) {
			var childNodes = obj.childNodes || [];
			for (i = 0, len = childNodes.length; i < len; i++) {
		  		node.appendChild(toDOM(childNodes[i]));
			}
	  	}
	  	
	  	return node;
	}

	function setRightClickOptions (tempUrl) {

		$($("#rightclickSubOptions").children()[0]).attr("onclick","newWebview('"+tempUrl+"',false); closeMenu();");
		$("#copyLinkLocation").attr("onclick","clipboard.set('"+tempUrl+"', 'text'); closeMenu();");
									
		$("#openNewTab").attr("onclick","newWebview('"+tempUrl+"',false)");
		$("#openNewWindow").attr("onclick","openNewWindow('"+tempUrl+"')");
		$("#openNewWPrivateindow").attr("onclick","openNewWindow('"+tempUrl+"',true)");
	}

	function setupRightClick(rightClickedDiv) {
		var webview = document.querySelector('#webview'+currentTab);
		var showMenu = false; 
		console.log("rightClickedDiv.tagName.toLowerCase()",rightClickedDiv);

		$("#downloadLink").addClass("hidden");
		$("#downloadLink2").addClass("hidden");

		if (rightClickedDiv.tagName.toLowerCase() == "a" || lastHoveredLink != ""){
			/*Checking for "data-href" for google related links*/
			if (lastHoveredLink != "")
				var tempUrl = lastHoveredLink;
			else
				var tempUrl = rightClickedDiv.getAttribute("data-href");
			showMenu = false;

			console.log("detected the right click is a link");

			if (tempUrl != null){
				setRightClickOptions (tempUrl);
				var dataHrefSplit = tempUrl.split("/");
				var domainRealName = tempUrl.split(".");
				console.log("outside here");
				if (rightClickedDiv.tagName.toLowerCase() == "img"){ //If there is a thumbnail inside the link, use that instead
				console.log("gets in here");
				$("#rightclick_bg").attr("src",$(rightClickedDiv).attr("src"));
				$("#right_click_preview").attr("src",$(rightClickedDiv).attr("src"));
				$("#right_click_preview").removeClass("hidden");
				$("#downloadLink2").attr("onclick","customDownload('"+$(rightClickedDiv).attr('src')+"');");
				$("#downloadLink2").removeClass("hidden");
				showMenu = true;
				} else if (dataHrefSplit[2] !="") {
					console.log("using here instead");
					websiteLogo(dataHrefSplit[2],tempUrl);//get_web_data(dataHrefSplit[2]);
					showMenu = true;
				}					
			} else if (rightClickedDiv.href != ""){
				tempUrl = "";
				if (rightClickedDiv.href.indexOf("chrome-extension://") == 0) { //suport direct local urls
				   	//tempUrl = webview.src;
				   	tempUrl = rightClickedDiv.href.replace("chrome-extension://","");
					tempUrl = webview.src+tempUrl.substring(tempUrl.indexOf("/") + 1);

				} else {
					tempUrl = rightClickedDiv.href;
				}

				var dataHrefSplit = tempUrl.split("/");
				var domainRealName = tempUrl.split(".");

				if (dataHrefSplit[2] != "www.youtube.com") {
					setRightClickOptions (tempUrl); //I am excluding YouTube cos there is a weird bug where there is 2 v= arguments. This is literally a fix applied on the same day of release, hence why thats dodgy as :P I call this when it's youtube under the youtube thumbnail extension.
				}
				
				if (dataHrefSplit[2] !="") {
					websiteLogo(dataHrefSplit[2],tempUrl);//get_web_data(dataHrefSplit[1]);
					showMenu = true;
				}
			}
		} else if (rightClickedDiv.tagName.toLowerCase() == "img"){
			console.log("detected the right click is an image");
			$("#downloadLink").attr("onclick","customDownload('"+$(rightClickedDiv).attr('src')+"');");
			
			$("#rightclick_bg").attr("src",$(rightClickedDiv).attr("src"));
			$("#right_click_preview").attr("src",$(rightClickedDiv).attr("src"));
			$("#right_click_preview").removeClass("hidden");
            console.log("removelink called");
			$("#downloadLink").removeClass("hidden");
			showMenu = true;
		}

		if (showMenu && $("#link_context_menu").hasClass("hidden") && !webview.currentAtHome) {
			closeAllMenus();
			//openSideBar(); Context menu not in the side bar anymore
			$('#textSelectionOption').addClass('hidden');
			//$("#downloadLink").addClass("hidden");
			$('#rightClickText').addClass('hidden');
			$('#right_click_preview').removeClass('hidden');
			$('#rightclick_bg').removeClass('hidden');
			$('#normalLinkOption').removeClass('hidden');
			$('#link_context_menu').addClass('animated fadeInDown');
			$('#link_context_menu').removeClass('hidden');
			$('#contextMenuBG').removeClass('hidden');
		}
	}

	function oldCodes () {
		var menuData = results[0].replace("[","").replace("]","").split('","');
		//menuDataTest = menuData[0].replace(new RegExp('["]', 'g'), '');
		for (var i = 0; i < menuData.length; i++){
			menuData[i] = menuData[i].replace(new RegExp('["]', 'g'), '');
		}
		
		//////console.log(menuData);//////console.log(menuData);
		var showMenu = false; 
		/*For a link aka "a" tag*/
		if (menuData[0] == "a"){
			showMenu = true;
		}
		
		/*Checking for "data-href" for google related links*/
		if (menuData[2] != ""){
			$($("#rightclickSubOptions").children()[0]).attr("onclick","newWebview('"+menuData[2]+"',false); closeMenu();");
			$("#copyLinkLocation").attr("onclick","clipboard.set('"+menuData[2]+"', 'text'); closeMenu();");
			
			$("#openNewTab").attr("onclick","newWebview('"+menuData[2]+"',false)");
			var dataHrefSplit = menuData[2].split("/");
			var domainRealName = menuData[2].split(".");
			if (dataHrefSplit[2] !=""){
				websiteLogo(dataHrefSplit[2],menuData[2]);//get_web_data(dataHrefSplit[2]);
			}
		}else if (menuData[1] != ""){
				var dataHrefSplit = menuData[1].split("/");
				var domainRealName = menuData[1].split(".");
				if (dataHrefSplit[1] !=""){
					websiteLogo(dataHrefSplit[1],menuData[1]);//get_web_data(dataHrefSplit[1]);
				}
		}
							
		/*For an image aka an "img" tag*/
		if (menuData[0] == "img"){
			showMenu = true;
			if (menuData[1] != ""){
				//console.log("IMAGE URL: "+menuData[1]);
				document.getElementById('rightclick_bg').src = menuData[1];
				document.getElementById('right_click_preview').src = menuData[1];
				$("#right_click_preview").removeClass("hidden");
			}
		}			
	}

	function isElement(obj) {
	  	try {
			//Using W3 DOM2 (works for FF, Opera and Chrom)
			return obj instanceof HTMLElement;
	  	}catch(e){
			//Browsers not supporting W3 DOM2 don't have HTMLElement and
			//an exception is thrown and we end up here. Testing some
			//properties that all elements have. (works on IE7)
			return (typeof obj==="object")
				&& (obj.nodeType===1) && (typeof obj.style === "object")
				&& (typeof obj.ownerDocument ==="object");
	  	}
	}

	var clipboardtext = "";

function setTextToClipboard() {
	clipboard.set(stringWithoutQuotes, 'text');
	closeMenu();
}

	function showTextRightClick(string) {
		if ($("#link_context_menu").hasClass("hidden")) {
			$('#right_click_preview').addClass('hidden');
			$("#normalLinkOption").addClass("hidden");
			var stringWithoutQuotes = string.slice(1, -1);
			var textToDisplay = stringWithoutQuotes;
			if (stringWithoutQuotes.length > 75) {
				textToDisplay = stringWithoutQuotes.substring(0,75)+"...";
			}
			$("#rightClickText > span").text(textToDisplay);
			console.log("stringWithoutQuotes",stringWithoutQuotes.length);
			clipboardtext = stringWithoutQuotes;
			$("#copyText").attr("onclick",`clipboard.set('`+stringWithoutQuotes+`', 'text'); closeMenu();`);
			$("#textSelectionOption").removeClass("hidden");
			$("#rightclick_bg").addClass("hidden");
			$("#rightClickText").removeClass("hidden");
			$('#contextMenuBG').removeClass('hidden');
			//openSideBar();
			$('#link_context_menu').addClass('animated fadeInDown');
			$('#link_context_menu').removeClass('hidden');
		}
	}

	function getTagName(webview){

		var x = 0;
		var y = 0;
		webview.executeScript({code: `
		////console.log(document.elementFromPoint(`+x+`,`+y+`));
		//var currentElement = document.elementFromPoint(`+x+`,`+y+`);
		var elementData = [];



		function toJSON(node) {
		  node = node || this;
		  var obj = {
			nodeType: node.nodeType
		  };
		  if (node.tagName) {
			obj.tagName = node.tagName.toLowerCase();
		  } else
		  if (node.nodeName) {
			obj.nodeName = node.nodeName;
		  }
		  if (node.nodeValue) {
			obj.nodeValue = node.nodeValue;
		  }
		  var attrs = node.attributes;
		  if (attrs) {
			var length = attrs.length;
			var arr = obj.attributes = new Array(length);
			for (var i = 0; i < length; i++) {
			  attr = attrs[i];
			  arr[i] = [attr.nodeName, attr.nodeValue];
			}
		  }
		  var childNodes = node.childNodes;
		  if (childNodes) {
			length = childNodes.length;
			arr = obj.childNodes = new Array(length);
			for (i = 0; i < length; i++) {
			  arr[i] = toJSON(childNodes[i]);
			}
		  }
		  return obj;
		}

		//elementData.push("customX");
		//elementData = toJSON(currentElement);


		 if (window.getSelection().toString() != "") {
		elementData = JSON.stringify(window.getSelection().toString());
		//console.log("HMMMM["+window.getSelection().toString()+"]");
		//console.log(window.getSelection().toString());
		} else {
		elementData = toJSON(window.rightClickedElement);
		console.log("RIGHT CLICKED EL",window.rightClickedElement);
		}

				JSON.stringify(elementData);
			`}, function(results) {
				if (results) {
					var jsonCheck =  JSON.parse((results[0]));
					var domCheck = toDOM(results[0]);

					console.log("jsonCheck",jsonCheck);
							
					if (isElement(domCheck))
						setupRightClick(toDOM(results[0]));
					else if (typeof jsonCheck !== 'object')
						showTextRightClick(jsonCheck);
								
						   ////console.log("ALL RESULTS",toDOM(results[0]));
				//setupRightClick(toDOM(results[0]));

				} else {
					////console.log("error");
				}
			});
	}

	//console.log("HOME IS: ",downloadLocation);
	

function sleep(milliseconds) {
  const date = Date.now();
  let currentDate = null;
  do {
    currentDate = Date.now();
  } while (currentDate - date < milliseconds);
}

var wasMaximized = false;

	function handlePermmision(event){
		console.log("event triggered",event);
		if (event.permission === "fullscreen") {
			fullscreenRequest();
			already_done = true;
			//win.maximize();
			sleep(1000); //Wait for maximize animation to finish (to avoid lag)
			event.request.allow();
			
		}
		
		if (event.permission === "download") {
			console.log("event triggered dl",event);
			//event.request.allow();
			if (dlCounts == 0){
				$("#downloadsInner").empty();
			}

		  	//$("#downloadsInner").append('<div id="dl'+dlCounts+'" class="downloadDiv"><div id="divProgress'+dlCounts+'" class="dlProgressDiv"></div><div id="dl'+dlCounts+'Text" class="dlTextDiv"><p id="dl'+dlCounts+'label" class="dlText dlTextName">Downloading test file</p><p id="dl'+dlCounts+'speed" class="dlText">0 Mb/s</p><p id="dl'+dlCounts+'eta"class="dlText" >About <span id="dl'+dlCounts+'eta">Estimating...</span> remaining</p><p id="dl'+dlCounts+'downloading"class="dlText hidden" >Getting there....</p></div><i class="fas fa-circle cancelDl" aria-hidden="true"></i><div class="cancelDownload"><a id="dl'+dlCounts+'cancelDownloadText" class="cancelDownloadText" href="#">Cancel Download</a></div></div>');
				
			handleDownload(event.url,downloadLocation,dlCounts);
		   	dlCounts++;
		
			//$("#allTabsC").addClass("showDownloads");
			//$("#allTabsC").animate({'height':'81%'}, 500);
			//event.request.allow();
		}

		if (event.permission === "geolocation") {
			
			var locationAllowedPermissionExists = allowedLocationPermissions.filter(function (el) {
            return el == event.url;
        });


			var locationDeniedPermissionExists = deniedLocationPermissions.filter(function (el) {
            return el == event.url;
        });

			

				if (locationAllowedPermissionExists.length == 0) {
					if (locationDeniedPermissionExists.length != 0) {
						event.request.deny();
					} else
						locationPermissionRequest(event);
				} else {
					event.request.allow();
				}
					
		}


	}




	

	

	

	

	


	


	


	



	function toggleFullsecreen(event){
		if (!already_done)
			fullscreenRequest();
		else
			already_done = false;
	}

	function getNextPresetZoom(zoomFactor) {
		var preset = [0.25, 0.33, 0.5, 0.67, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5];
		var low = 0;
		var high = preset.length - 1;
		var mid;
		
		while (high - low > 1) {
			mid = Math.floor((high + low)/2);
			if (preset[mid] < zoomFactor) {
			  	low = mid;
			} else if (preset[mid] > zoomFactor) {
			  	high = mid;
			} else {
			  	return {low: preset[mid - 1], high: preset[mid + 1]};
			}
	  	}
	  	
	  	return {low: preset[low], high: preset[high]};
	}

	function increaseZoom() {
	  	var webview = document.querySelector('#webview'+currentTab);
	  
	  	webview.getZoom(function(zoomFactor) {
			var nextHigherZoom = getNextPresetZoom(zoomFactor).high;
			webview.setZoom(nextHigherZoom);
			document.forms['zoom-form']['zoom-text'].value = nextHigherZoom.toString();
	  	});
	}

	function decreaseZoom() {
		var webview = document.querySelector('#webview'+currentTab);
		webview.getZoom(function(zoomFactor) {
			var nextLowerZoom = getNextPresetZoom(zoomFactor).low;
			webview.setZoom(nextLowerZoom);
			document.forms['zoom-form']['zoom-text'].value = nextLowerZoom.toString();
		});
	}

	function openZoomBox() {
		document.querySelector('#webview'+currentTab).getZoom(function(zoomFactor) {
			var zoomText = document.forms['zoom-form']['zoom-text'];
			zoomText.value = Number(zoomFactor.toFixed(6)).toString();
			document.querySelector('#zoom-box').style.display = '-webkit-flex';
			zoomText.select();
		});
	}

	function closeZoomBox() {
	  	document.querySelector('#zoom-box').style.display = 'none';
	}

	function openFindBox() {
	  	//document.querySelector('#find-box').style.display = 'block';
		openSettings();
	 	document.forms['find-form']['find-text'].select();
	}

	function closeFindBox() {
	  /*var findBox = document.querySelector('#find-box');
	  findBox.style.display = 'none';
	  findBox.style.left = "";
	  findBox.style.opacity = "";
	  document.querySelector('#find-results').innerText= "";*/
	}

	function closeBoxes() {
	  	closeZoomBox();
	  	closeFindBox();
	}




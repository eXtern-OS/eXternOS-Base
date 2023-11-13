function appsortAppsByAcessList() {
    
    //clearAllLists();
    $("#most-accessed-b").empty();
    var sortedApps = sortAppsByAcess(accessedApps);
	//console.log("sortedApps",sortedApps);
	systemSortedApps = sortedApps;
    //$("#most-accessed-b").append($( "[name='"+sortedApps[i][0]+"']" ).next().clone());
    if (sortedApps.length !=0)
    {
        for (var i=sortedApps.length-1; i>=0;i--)
    {
        for (var j = 0; j < allAppsDivs.length; j++)
            if (allAppsDivs[j].name == sortedApps[i][0])
            {
                var cloned = $( "[name='"+allAppsDivs[j].name+"']" ).clone(true);
                //console.log("ALL DIVS NAME RECENT:",cloned[0]);
                $("#most-accessed-b").append(cloned[0]);
            }
        //var originalApp = $( "[name='"+sortedApps[i][0]+"']" ).clone(true);
        //$("#most-accessed-b").append(originalApp);
    }
        $("#most-accessed-a").removeClass("hidden");
    }
}

$( ".nav-tabs > li > a" ).click(function() {
  $("#searchOuter > input").val(""); //reset search
});

var toBeProcessedAppDiv;
var lastSearch = "";

function searchApps() {
	//$(".appBox").removeClass("hidden");
    if (($("#searchOuter > input").val() != "") &&  (lastSearch !=$("#searchOuter > input").val()))  {
	lastSearch = $("#searchOuter > input").val();
	//setTimeout(function(){ console.log("in herez: ",$("#searchOuter > input").val())}, 2000);
      console.log("in here: ",$("#searchOuter > input").val());
      //$( ".appBox" ).addClass("hidden");zeroWidth

	$( ".appBox" ).each(function( index ) {
  		//console.log( index + ": " + $( this ).text() );
		var foundMatch  = false;

		//Search Name
		if ($(this).find(".appTextOverflow").text().toLowerCase().search($("#searchOuter > input").val().toLowerCase()) != -1) {
			foundMatch = true;
		}

		//Search Real Name
		if ($( this ).attr("name").toLowerCase().search($("#searchOuter > input").val().toLowerCase()) != -1) {
			foundMatch = true;

		}

		//Search Description
		if ($( this ).attr("description").toLowerCase().search($("#searchOuter > input").val().toLowerCase()) != -1) {
			foundMatch = true;

		}

		//Search developer
		if ($( this ).attr("developer").toLowerCase().search($("#searchOuter > input").val().toLowerCase()) != -1) {
			foundMatch = true;
		}
      
      if (!foundMatch) {
        //$( this ).removeClass("hidden");
	$( this ).addClass("hidden");
	toBeProcessedAppDiv = this;
      } else {
		$(this).removeClass("hidden");
		//$(this).addClass("animateApp");
	}

		
		
	});

	//setTimeout(function(){$( ".appBox.animateApp" ).removeClass("zeroWidth"); $( ".appBox.animateApp" ).removeClass("animateApp");$(".appBox.zeroWidth").addClass("hidden");}, 300);

    } else {
	if ($("#searchOuter > input").val() == "") {
	console.log("out here");
	$(".appBox").removeClass("hidden");
	//$( ".appBox.animateApp" ).removeClass("animateApp");
	//setTimeout(function(){ $( ".appBox" ).removeClass("zeroWidth");}, 100);
	}
     
	//setTimeout(function(){ $(".appBox.zeroWidth").addClass("hidden");}, 450);
    }

	



}

function unfocusSearch() {
	$("#searchOuter > input").trigger( "blur" );
}

$(document).ready(function() {
    $("#searchOuter > input").on('change keydown paste input', function(){
    console.log("YEYEYE");
	//$(".appBox").removeClass("hidden");
	setTimeout(function(){searchApps();}, 500);
	//setTimeout(function(){searchApps();}, 3000);
	setTimeout(function(){searchApps();}, 100);
    });

});

function appCategoryList() {

//console.log("appCategoryList");
    
    clearAllLists();

	if (enableLinuxNativeApps)
    		loadLinuxNativeApps();
    //$("#sys-tools-b").append(allAppsDivs[0].div.clone(true));
    var appended = false;
    //$("#most-accessed-b").append($( "[name='"+sortedApps[i][0]+"']" ).next().clone());
    for (var i=0; i < allAppsDivs.length; i++)
    {
        appended = false; //To check if we found the correct section, otherwise place into "other" sections
        if (allAppsDivs[i].category == "System & Tools")
        {
            
            $("#sys-tools-a").removeClass("hidden");
            //var cloned = allAppsDivs[i].div.clone(true);
            $("#sys-tools-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            //allAppsDivs[i].div.replaceWith(cloned);
            appended = true;
            //setTimeout(function(){ $("#sys-tools-b").append(allAppsDivs[i].div.clone(true)); }, 10000);
            //allAppsDivs[i].div = allAppsDivs[i].div.clone(true);
            //$("#sys-tools-b").empty();
           // $("#sys-tools-b").append(allAppsDivs[i].div.clone(true));
        }
        
        if (allAppsDivs[i].category == "Multimedia")
        {
            $("#multimedia-a").removeClass("hidden");
            $("#multimedia-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            appended = true;
        }
        
        if (allAppsDivs[i].category == "Text Editors")
        {
            $("#txt-editors-a").removeClass("hidden");
            $("#txt-editors-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            appended = true;
        }
        
        if (allAppsDivs[i].category == "Internet")
        {
            $("#internet-a").removeClass("hidden");
            $("#internet-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            appended = true;
        }
        
        if (allAppsDivs[i].category == "Images & Graphics")
        {
            $("#img-and-graphics-a").removeClass("hidden");
            $("#img-and-graphics-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            appended = true;
        }

        if (allAppsDivs[i].category == "Video" || allAppsDivs[i].category == "Audio")
        {
            $("#multimedia-a").removeClass("hidden");
            $("#multimedia-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            appended = true;
        }
        
        if (allAppsDivs[i].category == "Developer Tools")
        {
            $("#developer-tools-a").removeClass("hidden");
            $("#developer-tools-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            appended = true;
        }
        
        if (!appended) {
            $("#other-apps-a").removeClass("hidden");
            $("#other-apps-b").append($( "[name='"+allAppsDivs[i].name+"']" ).clone(true));
            appended = true;
        }
    }
    
    appsortAppsByAcessList();
}

function sortAppsByAcess(obj)
{
  // convert object into array
    var sortable=[];
    for(var key in obj)
        if(obj.hasOwnProperty(key))
            sortable.push([key, obj[key]]); // each item is an array in format [key, value]

    // sort items by value
    sortable.sort(function(a, b)
    {
      return a[1]-b[1]; // compare numbers
    });
    return sortable; // array in format [ [ key1, val1 ], [ key2, val2 ], ... ]
}

function ordinal_suffix_of(i) {
    var j = i % 10,
        k = i % 100;
    if (j == 1 && k != 11) {
        return i + "st";
    }
    if (j == 2 && k != 12) {
        return i + "nd";
    }
    if (j == 3 && k != 13) {
        return i + "rd";
    }
    return i + "th";
}

function readSizeRecursive(item, cb) {
  fs.lstat(item, function(err, stats) {
    if (!err && stats.isDirectory()) {
      var total = stats.size;

      fs.readdir(item, function(err, list) {
        if (err) return cb(err);

        async.forEach(
          list,
          function(diritem, callback) {
            readSizeRecursive(path.join(item, diritem), function(err, size) {
              total += size;
              callback(err);
            }); 
          },  
          function(err) {
            cb(err, total);
          }   
        );  
      }); 
    }   
    else {
      cb(err);
    }   
  }); 
}   

var getDirs = function(rootDir, cb) { 
    fs.readdir(rootDir, function(err, files) { 
        var dirs = []; 
        for (var index = 0; index < files.length; ++index) { 
$("#all-apps-b").empty();
            var file = files[index]; 
		//console.log("loading APP",file);
        if (file != "extern.liverun.app") { //Skip the devkit temp App running directory
            if (file[0] !== '.') { 
                var filePath = rootDir + '/' + file; 
                fs.stat(filePath, function(err, stat) {
                    if (stat.isDirectory()) { 
                        dirs.push(this.file);
                        jsApp = JSON.parse(fs.readFileSync("apps/"+this.file+"/package.json", 'utf8'));
			console.log("jsApp: ",jsApp);
                        apps.push(jsApp);
                        loadApp(jsApp);
                        //appCategoryList();
                    } 
                    if (files.length === (this.index + 1)) {
                        

                        //appCategoryList();
                        //console.log("FOUND APPS DIRS",dirs);
                        return cb(dirs); 
                    } 
                }.bind({index: index, file: file})); 
            }
        }
        }


    });
}




var apps = [];



//require('./file-name');

function addDefault(dirs) {
    appCategoryList();
    //console.log("DIRS: ",dirs);
    var totalLoaded = 0;
    const dirsx = dirs;
    //console.log("DIRSx: ",dirsx);
    
    /*console.log("PUSHEDs"+dirs.length);
        console.log("PUSHEDs"+dirsx.length);
        var json = JSON.parse(fs.readFileSync("apps/"+dirsx[ix]+"/package.json", 'utf8'));
        console.log("PUSHED",json);
        
        loadApp(json);
        appCategoryList();*/
    
    /*
    for (var ix = 0; ix < dirsx.length; ix++) {
        

       
    var json = (function () {
    var json = null;
    $.ajax({
        'async': false,
        'global': false,
        'url': "apps/"+dirsx[ix]+"/package.json",
        'dataType': "json",
        'success': function (data) {
            apps.push(data);
            console.log("PUSHED",data);
            loadApp(data);
            totalLoaded++;
            if (totalLoaded == dirsx.length) {
                setTimeout(function(){
                    //appCategoryList(); //This is to fix a glitch where some apps don't show up
                   }, 8000);
                //appCategoryList();
                //console.log("Apps: ",apps);
            }
                
        }
    });
    
})(); 
    }*/
    
   /* $(document).on('mouseenter', '.appBox', function(e) {
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
});

$(document).on('mouseleave', '.appBox', function(e) {
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
    
    $('.appBox').on({
    mouseenter: function () {
        //console.log("Testing ",$(this)[0].attributes.description.value);
     $("#appDescId").text($(this)[0].attributes.description.value);
     $("#appDevs").text($(this)[0].attributes.developer.value);
     $("#appVersion").text($(this)[0].attributes.version.value);
     $("#AppDiskUsage").text($(this)[0].attributes.disk.value);
var appAccessTimes = accessedApps[$(this)[0].attributes.name.value];
if (typeof accessedApps[$(this)[0].attributes.name.value] !== 'undefined') {
        //appCategoryList();
        if (appAccessTimes < 2 ) {
            if (appAccessTimes == 1)
                $("#AppAccessTimes").text("Once.");
        } else {
     $("#AppAccessTimes").text(appAccessTimes+" times.");
        }
} else {
$("#AppAccessTimes").text("Not yet accessed.");
}
    //console.log("TEST SELECT APPS::",$( "[name='devkit']" ).next());
if (typeof accessedApps[$(this)[0].attributes.name.value] !== 'undefined')
{
    var sortedApps = sortAppsByAcess(accessedApps);
	systemSortedApps = sortedApps;
    for (var i=0; i<sortedApps.length;i++)
        if (sortedApps[i][0] == $(this)[0].attributes.name.value)
        {
            if ((sortedApps.length - i) == 1)
                $("#AppUsageRanking").text("This is your most accessed App!");
            else
                $("#AppUsageRanking").text(ordinal_suffix_of(sortedApps.length - i)+" Most Accessed App!");
        }
            //console.log("aceessed apps:::",sortedApps.length - i);
                }
        else
            $("#AppUsageRanking").text("You haven't accessed this app yet!");
        $("#AppIconPreview")[0].src = $(this).find( "img" )[0].src;
        $("#sideBarAppLabel").text($(this).find( ".appTextOverflow" )[0].innerText);
     hoveringOverApp = true;
     if ($("#personalAssistant").hasClass("cActive"))
    {
        $("#appInfo").fadeIn();
        $("#appInfo").addClass("cActive");
        $("#personalAssistant").fadeOut();
        $("#personalAssistant").removeClass("cActive");
        
    }
    },
    mouseleave: function () {
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
    }
});
    
}

//$( document ).ready(function() {
     /*Clear Apps Menu*/
$("#all-apps-b").empty();
    
    setTimeout(function(){ getDirs("apps",addDefault);}, 2000);

//});


//addDefault();


function getBase64Image(imgs,AppId) {
    
  function  convertImg(img) {
    // Create an empty canvas element
    var canvas = document.createElement("canvas");
    canvas.width = img.width;
    canvas.height = img.height;
      //console.log("CANV width: "+canvas.width+" Canv Height: "+canvas.height);

    // Copy the image contents to the canvas
    var ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);

    // Get the data-URL formatted image
    // Firefox supports PNG and JPEG. You could check img.src to
    // guess the original format, but be aware the using "image/jpg"
    // will re-encode the image.
    var dataURL = canvas.toDataURL("image/png");
      
      //console.log("ICON APP ID",AppId);
      for (var k=0; k < apps.length; k++) {
          if (apps[k].id == AppId) {
              apps[k].iconBase64 = dataURL;
              //console.log("ICON APP FOUND!");
          }
      }

    //console.log("ICON: ",dataURL);
      //console.log("ALL APPS",apps);
    }
    setTimeout(function(){
        var newImg = new Image();

    newImg.onload = function() {
      //var height = newImg.height;
      //var width = newImg.width;
      //alert ('The image size is '+width+'*'+height);
        convertImg(newImg)
    }

    newImg.src = imgs.src; // this must be done AFTER setting onload

}, 500);
    
}



function updateRunningApps() {
console.log("runningApps",runningApps);
    $("#runningAppsManager").empty();

	var addedApps = false;
    for (var i = 2; i  <  runningApps.length; i++) {
        //runningApps[i].name;
	if (runningApps[i].windowObject.loadedApp != undefined) {
        	$("#runningAppsManager").append('<div class="media p-l-5"><div class="pull-left"><img width="40" src="'+runningApps[i].physicalLocation+runningApps[i].realID+'/'+runningApps[i].options.icon+'" alt=""></div><div class="media-body"><small class="text-muted">Currently Active</small><br/><a class="t-overflow" href="javascript:void(0);">'+runningApps[i].name+'</a></div></div>');
		addedApps = true;
	}
    }

	if (!addedApps)
		$("#runningAppsManager").append('<div class="noAppsRunning">No Apps are curently Running.</div>');
    
}



function loadApp(app) {
    
    var categoryIcon = "";
     if (app.category.toLowerCase().indexOf("system") != -1) {
        categoryIcon = "#61886;";
        //fileTypesApps.other.push(app);
    }
    
    if (app.category.toLowerCase().indexOf("internet") != -1) {
        categoryIcon = "#61838;";
        fileTypesApps.web.push(app);
        if (app.id == "extern.web.app")
            fileTypesApps.prefferedFileTypesApps.web = app; //Make this default for Beta 1
            
    }

        if (app.id == "extern.devkit.app") {
            fileTypesApps.prefferedFileTypesApps.text = app; //Make this default for Beta 1 & 2
            fileTypesApps.prefferedFileTypesApps["c code"] = app; //Make this default for Beta 1 & 2
            fileTypesApps.prefferedFileTypesApps["c++ code"] = app; //Make this default for Beta 1 & 2
            fileTypesApps.prefferedFileTypesApps["java script"] = app; //Make this default for Beta 1 & 2
            fileTypesApps.prefferedFileTypesApps["css"] = app; //Make this default for Beta 1 & 2
	}
 
    if (app.category.toLowerCase().indexOf("text") != -1) {
        categoryIcon = "#61955;";
        fileTypesApps.text.push(app);

    }
    
    if (app.category.toLowerCase().indexOf("developer") != -1) {
        categoryIcon = "#61734;";
        fileTypesApps.text.push(app);
    }
    
    if ((app.category.toLowerCase().indexOf("images") != -1) || (app.category.toLowerCase().indexOf("graphics") != -1)) {
        categoryIcon = "#61765;";
        fileTypesApps.image.push(app);
        if (app.id == "extern.photos.app")
            fileTypesApps.prefferedFileTypesApps.image = app; //Make this default for Beta 1
    }
    
    if (app.category.toLowerCase().indexOf("video") != -1) {
        categoryIcon = "#61931;";
        fileTypesApps.video.push(app);
        if (app.id == "extern.video.app")
            fileTypesApps.prefferedFileTypesApps.video = app; //Make this default for Beta 1
    }
    
    if (app.category.toLowerCase().indexOf("audio") != -1) {
        categoryIcon = "#61859;";
        fileTypesApps.audio.push(app);
        if (app.id == "extern.music.app")
            fileTypesApps.prefferedFileTypesApps.audio = app; //Make this default for Beta 1
    }
    var realAppName = app.id.replace("extern.","").replace(".app","");
    /*console.log("CLEARED APPS");*/
if (typeof accessedApps[realAppName] !== 'undefined')
    var appAccessTimes = accessedApps[realAppName];
    else
        var appAccessTimes = 0;
    
    if (app.id !="extern.welcome.app" && app.id !="extern.itai.app" && app.id !="extern.liverun.app"  && app.id !="extern.hud.app" ) { 
allInstalledApps.push(app);
        $("#all-apps-b").append('<a name="'+realAppName+'" app-id="'+app.id+'" class="appBox shortcut tile" href="javascript:void(0);" version="'+app.version
+'" developer="'+app.author+'" description="'+app.description+'" onclick="openApp(`'+app.id+'`,null,null,this)" disk="Unavailable" Accessed="'+appAccessTimes+'"><img src="../apps/'+app.id+'/'+app.window.icon+'" alt=""><div class="runIconDiv hidden"><span class="icon" style=" color:rgba(255,255,255,0.8);font-weight: bold; text-shadow: 0 0 10px rgba(255, 255, 255, 0.9);">&#61815;</span></div><p class="appTextOverflow">'+app.name+'</p><p class="AppCategoryText"><span class="icon" style=" color:rgba(255,255,255,0.8); text-shadow: 0 0 10px rgba(0, 0, 0, 0.9); font-weight: bold; text-shadow: 0 0 10px rgba(0, 0, 0, 0.9);">&'+categoryIcon+'</span> '+app.category+'</p></a>');
    
    //console.log("REALL APP: ",$( "[name='"+realAppName+"'] img"));
    getBase64Image($( "[name='"+realAppName+"'] img")[0],app.id);
    
    
    var appDiv = {
        name: realAppName,
        div:$( "[name='"+realAppName+"']" ).clone(true),
        category: app.category
    }
    allAppsDivs.push(appDiv);
    }
    //appsortAppsByAcessList();
    
    
/*    
names[0] = prompt("New member name?");
localStorage.setItem("names", JSON.stringify(names));
*/
    //console.log("File types:",fileTypesApps);
}

var runningID = 0;

var allApps = [];
$("#appInfo").fadeOut();
$("#main").fadeOut();
$("#sysAbout").fadeOut();
$("#sysPerfomance").fadeOut();
var hoveringOverApp = false;


$( ".quickButtons" )
  .mouseenter(function() {
      console.log("$(this)[0].childNodes: ",$(this)[0].childNodes);
      $(this).find(".left").fadeTo( 100 , 1);
      $(this).find(".right").fadeTo( 100 , 1);
    //This is a dodgy way to do it, FIXME
    /*
       arrowA = $(this)[0].childNodes[2].id;
        arrowB = $(this)[0].childNodes[3].id;    
          $("#"+arrowA).fadeTo( 100 , 1);
        $("#"+arrowB).fadeTo( 100 , 1);
        */
  })
  .mouseleave(function() {
    $(this).find(".left").fadeTo( 50 , 0);
    $(this).find(".right").fadeTo( 50 , 0);
    //This is a dodgy way to do it, FIXME
       /*arrowA = $(this)[0].childNodes[2].id;
        arrowB = $(this)[0].childNodes[3].id;    
          $("#"+arrowA).fadeTo( 50 , 0);
        $("#"+arrowB).fadeTo( 50 , 0);*/
  });

function openSettings() {
    currentMenuMode = 'settings';
   $("#startMenu").fadeOut(300, function() {
    // Animation complete.
	$("#main").fadeIn(200);
  });
    
    
    
    //setTimeout(function(){$("#main").fadeIn(300);}, 350);
    //setTimeout(function(){   $("#startMenu").addClass("hidden");}, 500);    
}

function openSysAbout() {
    currentMenuMode = 'sysAbout';
   $("#startMenu").fadeOut(500);
    
    
    
    setTimeout(function(){$("#sysAbout").fadeIn(300);}, 350);
    setTimeout(function(){   $("#startMenu").addClass("hidden");}, 500);    
}

var path = require('path'), fs=require('fs');

var foundApps = ""; //Store found icon apps to break loop

var linuxAppsIcons = [];

function fromDir(startPath,filter,callback){

    //console.log('Starting from dir '+startPath+'/');

    if (!fs.existsSync(startPath)){
        console.log("no dir ",startPath);
        return;
    }

    if (foundApps.indexOf(filter) == -1) {
    var files=fs.readdirSync(startPath);
    for(var i=0;i<files.length;i++){
	if (foundApps.indexOf(filter) == -1) {
        var filename=path.join(startPath,files[i]);
        var stat = fs.lstatSync(filename);
        if (stat.isDirectory()){
            fromDir(filename,filter,callback); //recurse
        }
        else {
	
	var output = files[i].substr(0, files[i].lastIndexOf('.')) || files[i];

	 if (filter == output) { //filename.indexOf(filter)>=0
	    //foundApps +=" "+filter;
//https://stackoverflow.com/questions/1818310/regular-expression-to-remove-a-files-extension
	    callback(filename,filter,files[i]);
	    break;
        };
	};
	};
    };
   };
};



//Load Native Linux Apps
const linux_apps = require('/usr/eXtern/systemX/Shared/CoreMsc/linux-app-list')();
var noOfInstalledLinuxApps = linux_apps.list().length;
function loadLinuxNativeApps() {

	noOfInstalledLinuxApps = linux_apps.list().length;

//$("#other-apps-b").empty();

linux_apps.list().forEach(function(app){
    var data = linux_apps.data(app);
    var loadApp = false;

	if(data != undefined){
		console.log("data: ",data);
		if (data.OnlyShowIn != undefined) {
			for (var  k = 0; k < data.OnlyShowIn.length; k++)
				if (data.OnlyShowIn[k] == "GNOME") {
					loadApp = true;
					break;
				}
				//console.log("data.OnlyShowIn");
		} else {
			loadApp = true;
		}

	}

	var doNotLoadApp = false;
	if (data.Exec != undefined) {
		if (data.Exec.indexOf("/usr/eXtern/NodeJs/nw /usr/eXtern/systemX") == 0) {
			doNotLoadApp = true;
		}
	} else {
		doNotLoadApp = true;
	}

    if(data == undefined || doNotLoadApp){
        console.log("    " + app + " - Unable to get info or is an eXtern OS App");
    }else if ((data.Terminal != "true") && (data.NoDisplay != "true") && (data.Exec != "qmlscene --settings") && (data.Exec != "gnome-session-properties") && (data.Exec != "compton") && (data.Exec != "/usr/bin/libinput-gestures") && (data.Exec != "obconf %f") && loadApp && data.Exec.indexOf("/usr/eXtern/NodeJs/nw" == -1) && data.Exec != "pulseeffects" && data.Exec != "systemsettings5"){
	$("#other-apps-a").removeClass("hidden");
        //console.log("    " + app);
        //console.log(data);
	var author = "Unknown";
	var appAccessTimes = 0;
	var categoryIcon = "";

	if (data.Categories != null)
		var appCategory = data.Categories[0];
	else
		var appCategory = "Linux Application";

	if (data.Version != null)
		var appVersion = data.Version;
	else
		var appVersion = "";

	var appIcon = "";

	

	/*if (fs.existsSync("/usr/share/icons/Humanity/apps/128/"+data.Icon+".svg")) {
		
	}*/

	

     if ((appCategory.toLowerCase().indexOf("system") != -1) || (appCategory.toLowerCase().indexOf("settings") != -1) || (appCategory.toLowerCase().indexOf("gtk") != -1) || (appCategory.toLowerCase().indexOf("gnome") != -1) || (appCategory == "Linux Application")) {
        categoryIcon = "#61886;";
    }
    
    if (appCategory.toLowerCase().indexOf("internet") != -1) {
        categoryIcon = "#61838;";         
    }

    if (appCategory.toLowerCase().indexOf("text") != -1) {
        categoryIcon = "#61955;";

    }
    
    if ((appCategory.toLowerCase().indexOf("developer") != -1) || (appCategory.toLowerCase().indexOf("utility") != -1)) {
        categoryIcon = "#61734;";
    }
    
    if ((appCategory.toLowerCase().indexOf("images") != -1) || (appCategory.toLowerCase().indexOf("graphics") != -1)) {
        categoryIcon = "#61765;";
    }
    
    if (appCategory.toLowerCase().indexOf("video") != -1) {
        categoryIcon = "#61931;";
    }
    
    if (appCategory.toLowerCase().indexOf("audio") != -1) {
        categoryIcon = "#61859;";
    }
      
      if (data.Icon != null) {

	$("#other-apps-b").append('<a name="linux.'+app+'" class="appBox shortcut tile" href="javascript:void(0);" version="'+appVersion
+'" developer="'+author+'" description="'+data.Comment+'" onclick="openApp(`[[{linux.}]'+app+'`)" disk="Unavailable" Accessed="'+appAccessTimes+'"><img class="linux-'+data.Icon+'" src="../apps/extern.files.app/icons/flash package.png" alt=""><div class="runIconDiv hidden"><span class="icon" style=" color:rgba(255,255,255,0.8);font-weight: bold; text-shadow: 0 0 10px rgba(255, 255, 255, 0.9);">&#61815;</span></div><p class="appTextOverflow">'+data.Name+'</p><p class="AppCategoryText"><span class="icon" style=" color:rgba(255,255,255,0.8); text-shadow: 0 0 10px rgba(0, 0, 0, 0.9); font-weight: bold; text-shadow: 0 0 10px rgba(0, 0, 0, 0.9);">&'+categoryIcon+'</span> '+appCategory+'</p></a>');

var iconProcessed = false;

if (data.Icon.indexOf("/") != -1) {
    if (fs.existsSync(data.Icon)) {
        console.log("custom icon");
        $('.appBox[name="linux.'+app+'"] > img').attr("src","file://"+data.Icon);
	data.appIcon = "file://"+data.Icon;
        iconProcessed = true;
    }
}

      if (!iconProcessed) {
	linuxAppsIcons[data.Icon] = [];
	linuxAppsIcons[data.Icon]["16x16"] = "";
	linuxAppsIcons[data.Icon]["32x32"] = "";
	linuxAppsIcons[data.Icon]["64x64"] = "";
	linuxAppsIcons[data.Icon]["128x128"] = "";
	linuxAppsIcons[data.Icon]["256x256"] = "";
	linuxAppsIcons[data.Icon]["512x512"] = "";
	linuxAppsIcons[data.Icon]["scalable"] = "";
	linuxAppsIcons[data.Icon]["other"] = "";

	var iconDirs = [];
	iconDirs.push('../../share/icons/gnome');
	iconDirs.push('../../share/icons/hicolor');
	iconDirs.push('../../share/pixmaps');
	iconDirs.push('../../share/app-install/icons');

	//console.log("app-data",data);


executeNativeCommand("python3 /usr/eXtern/systemX/Shared/CoreMsc/get_icon.py "+data.Icon,function (newFilename,error) {
	newFilename = newFilename.replace("\n","");
	var iconName = data.Icon;
console.log("icon processed: ",newFilename);
console.log("iconName: ",iconName);
    if (newFilename.split(".").pop() == "xpm") {
		console.log("is xpm");
		if (!fs.existsSync("/usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png")){
			console.log("processin xpm");
			executeNativeCommand("ffmpeg -i "+newFilename+" /usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png", function () {
				//console.log("processed icon");
				$(".linux-"+iconName).attr("src","file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png");
				data.appIcon = "file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png";
			});
		} else {
			console.log("exists already");
			$(".linux-"+iconName).attr("src","file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png");
			data.appIcon = "file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png";
		}
    } else {
	console.log("applying");
        $(".linux-"+iconName).attr("src","file://"+newFilename);
		data.appIcon = "file://"+newFilename;
    }

    iconProcessed = true;
    
});


/*
	for (var m = 0; m < iconDirs.length; m++) {
        if (iconProcessed) {
            break; // try to stop wasting resources during boot
        } else {
	fromDir(iconDirs[m],data.Icon,function(filename,iconName,filesN){
    //console.log('-- found: ',filename); //filename
	//var newFilename = filename.replace("test","");
	
	var newFilename = filename.replace("../../","file:///usr/");
	if (((filename.indexOf("16x16") != -1) || (filename.indexOf("/16/") != -1)) && linuxAppsIcons[iconName]["16x16"] == "") {
		linuxAppsIcons[iconName]["16x16"] = newFilename;
		iconProcessed = true;
	}

	if (((filename.indexOf("32x32") != -1) || (filename.indexOf("/32/") != -1)) && linuxAppsIcons[iconName]["32x32"] == "") {
		linuxAppsIcons[iconName]["32x32"] = newFilename;
		iconProcessed = true;
	}

	if (((filename.indexOf("64x64") != -1) || (filename.indexOf("/64/") != -1)) && linuxAppsIcons[iconName]["64x64"] == "") {
		linuxAppsIcons[iconName]["64x64"] = newFilename;
		iconProcessed = true;
	}

	if (((filename.indexOf("128x128") != -1) || (filename.indexOf("/128/") != -1)) && linuxAppsIcons[iconName]["128x128"] == "") {
		linuxAppsIcons[iconName]["128x128"] = newFilename;
		iconProcessed = true;
	}

	if (((filename.indexOf("256x256") != -1) || (filename.indexOf("/256/") != -1)) && linuxAppsIcons[iconName]["256x256"] == "") {
		linuxAppsIcons[iconName]["256x256"] = newFilename;
		iconProcessed = true;
	}

	if (((filename.indexOf("512x512") != -1) || (filename.indexOf("/512/") != -1)) && linuxAppsIcons[iconName]["512x512"] == "") {
		linuxAppsIcons[iconName]["512x512"] = newFilename;
		iconProcessed = true;
	}

	if ((filename.indexOf("scalable") != -1) && linuxAppsIcons[iconName]["scalable"] == "") {
		linuxAppsIcons[iconName]["scalable"] = newFilename;
		iconProcessed = true;
	}

	if (newFilename.split(".").pop() == "xpm") {
		console.log("is xpm");
		if (!fs.existsSync("/usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png")){
			console.log("processin xpm");
			executeNativeCommand("ffmpeg -i "+newFilename+" /usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png", function () {
				//console.log("processed icon");
				$(".linux-"+iconName).attr("src","file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png");
				data.appIcon = "file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png";
			});
		} else {
			console.log("exists already");
			$(".linux-"+iconName).attr("src","file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png");
			data.appIcon = "file:///usr/eXtern/systemX/Shared/InstalledAppsIcons/"+data.Icon+".png";
		}
		
	} else {
		$(".linux-"+iconName).attr("src",newFilename);
		data.appIcon = newFilename;
		if (!iconProcessed) {
			linuxAppsIcons[iconName]["other"] = newFilename;
		}
	}

	

	

	
	});

        }
      
    }*/
    
    }
    allLegacyApps.push(data);
	////console.log("appended into here: ",$("#other-apps-b")[0]);
    }
    }
});

//}	
//console.log("linuxAppsIcons",linuxAppsIcons);


}

//Check for newly installed Apps FIXME: Better implimentation that monitors menu trigger might be better
setInterval(function(){
	if (enableLinuxNativeApps) {
		if (noOfInstalledLinuxApps != linux_apps.list().length) {
			console.log("reload Apps something was installed or removed");
			noOfInstalledLinuxApps = linux_apps.list().length;
			appCategoryList();
		}
	}

}, 10000);

//https://stackoverflow.com/questions/25460574/find-files-by-extension-html-under-a-folder-in-nodejs

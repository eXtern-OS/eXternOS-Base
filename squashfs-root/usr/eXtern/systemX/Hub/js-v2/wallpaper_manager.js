//Wallpapers
//console.log("win.showDevTools");
//win.showDevTools();

var stillProcessingWallpaper = false; // avoid overlapping blur processing


addCustomWallpaper = function(newWallpaper,setAsWallpaper, wallpaperName, wallpaperArtist) {

	var gui = require('nw.gui');
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
	}

			
		}



function enableOverview() {
setTimeout(function(){ 
	executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Plugins  --key ParachuteEnabled true", function () {
		console.log("set to true");
		setTimeout(function(){ executeNativeCommand("qdbus org.kde.KWin /KWin reconfigure"); }, 500);
	});
}, 500);
}


function realBlurWin(targetWin, srcImage, callback) {

if (!stillProcessingWallpaper) {
stillProcessingWallpaper = true;					
var canvas = document.createElement('canvas');
      var context = canvas.getContext('2d');
if (localStorage.getItem('wallpaperBlurEffect') === null) {
    var blurEffect = 3.4;
    localStorage.setItem('wallpaperBlurEffect', JSON.stringify(blurEffect));
} else
    var blurEffect = parseInt(JSON.parse(localStorage.getItem('wallpaperBlurEffect')));

if (localStorage.getItem('wallpapersaturationValue') === null)
    var saturationValue = 1;//var saturationValue = 2.4;
else
    var saturationValue = parseInt(JSON.parse(localStorage.getItem('wallpapersaturationValue')));


        var x = 0;
var y = 0;
var width = screen.width*3;
var height = screen.height*2; 
/*var blurEffect = 2.4;
var saturationValue = 2.4;*/
	canvas.width = width;
	canvas.height = height;				
    context.clearRect(0, 0, canvas.width, canvas.height);
      var imageObj = new Image();
      imageObj.onload = function() {
        //context.drawImage(imageObj, x, y, width, height);
		console.log("lol B");
          context.drawImage(imageObj, 0, 0, canvas.width/3, canvas.height);
          context.drawImage(imageObj, canvas.width, 0, canvas.width/3, canvas.height);
          context.drawImage(imageObj, canvas.width*2, 0, canvas.width/3, canvas.height);
          setTimeout(function(){ 
    context._blurRect(0, 0, canvas.width, canvas.height, blurEffect, saturationValue);
    imgData = canvas.toDataURL('image/jpeg');

    targetWin.outerBodyBackground[0].style.backgroundImage = "url('"+imgData+"'";

			  //targetWin.show();
			//targetWin.restore();
			if (callback != null)
			callback(targetWin);

			fs.unlink(srcImage);

			stillProcessingWallpaper = false;
		
			//console.log("BLUR IS BEING CALLED");
			  
			   }
                 , 100);
      };
					imageObj.src = "file://"+srcImage;
}
				}

var actualWallpaper;

jQuery.blurWin = function blurWin(wallpaperPath,blurProcessing)
{
if (!stillProcessingWallpaper) { 


stillProcessingWallpaper = true;        
var win = nw.Window.get();
    //console.log("QINDOWS: ",win.window.document);

//console.log("Is transparent: "+win.isTransparent());
        
    var canvas = document.getElementById('bg_cover');
      
    
        var x = -win.x;
var y = -win.y;

if (localStorage.getItem('wallpaperBlurEffect') === null) {
    var blurEffect = 5.4;
    localStorage.setItem('wallpaperBlurEffect', JSON.stringify(blurEffect));
} else
    var blurEffect = parseInt(JSON.parse(localStorage.getItem('wallpaperBlurEffect')));

if (localStorage.getItem('wallpapersaturationValue') === null)
    var saturationValue = 1.3;//var saturationValue = 2.4;
else
    var saturationValue = parseInt(JSON.parse(localStorage.getItem('wallpapersaturationValue')));

console.log("init canvas.width: ",canvas.width);
console.log("init canvas.height: ",canvas.height);
/*
if (blurProcessing) {
	var width = screen.width;
	var height = screen.height; //FIXME: height = screen.height*2; Something is broken here
} else {
	var width = screen.width*3;
	var height = screen.height*2; //FIXME: height = screen.height*2; Something is broken here
}*/

	var width = screen.width;
	var height = screen.height;

canvas.width = width;
canvas.height = height;
var context = canvas.getContext('2d');

//var blurEffect = 5.4;

//localStorage.setItem('wallpaperBlurEffect', JSON.stringify(blurEffect));

/*
var blurEffect = 2;
var saturationValue = 2.4;*/
//canvas.width = win.width;
//canvas.height = win.height;
    context.clearRect(0, 0, canvas.width, canvas.height);
      var imageObj = new Image();
      imageObj.onload = function() {

	if (blurProcessing) { //FIXME flipped temporarily

        //context.drawImage(imageObj, x, y, width, height);
          context.drawImage(imageObj, 0, 0, canvas.width/3, canvas.height);
          //FIXME: Something is broken here context.drawImage(imageObj, 0, canvas.height/2, canvas.width/3, canvas.height/2);
          context.drawImage(imageObj, canvas.width/3, 0, canvas.width/3, canvas.height);
          //FIXME: Something is broken here context.drawImage(imageObj, canvas.width/3, canvas.height/2, canvas.width/3, canvas.height/2);
          context.drawImage(imageObj, (2*canvas.width)/3, 0, canvas.width/3, canvas.height);
          context.drawImage(imageObj, (2*canvas.width)/3, canvas.height/2, canvas.width/3, canvas.height);
    imgData = canvas.toDataURL('image/jpeg');


	stillProcessingWallpaper = false;
	actualWallpaper = imageObj.src;
	//$.blurWin(imgData,true);

	} else {

	actualWallpaper = imageObj.src;
	console.log("canvas.heightx: ",canvas.height);
context.drawImage(imageObj, 0, 0, canvas.width, canvas.height);

		
          setTimeout(function(){ 
	console.log("canvas.height: ",canvas.height);
    context._blurRect( 0, 0, canvas.width, canvas.height, blurEffect, saturationValue);
	//context._blurRect(canvas.width/3, 0, canvas.width/3, canvas.height, blurEffect, saturationValue);
	//context._blurRect((2*canvas.width)/3, 0, canvas.width/3, canvas.height, blurEffect, saturationValue);
    imgData = canvas.toDataURL('image/jpeg');
	console.log("we are here");
    var data = imgData.replace(/^data:image\/\w+;base64,/, "");
    var buf = new Buffer(data, 'base64');

    fs.writeFile(homedir+'/.local/share/kwin/scripts/Parachute/contents/ui/images/bg.jpg', buf, function (err) {
  if (err) return console.log(err);
	executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Plugins  --key ParachuteEnabled false", function () {
		console.log("set to false");
		setTimeout(function(){ executeNativeCommand("qdbus org.kde.KWin /KWin reconfigure", enableOverview); }, 500); 


	var wallpaperData = {
		username: require("os").userInfo().username,
		wallpaper: homedir+'/.local/share/kwin/scripts/Parachute/contents/ui/images/bg.jpg'
	}

		$.post("http://127.0.0.1:8081/system/change_login_wallpaper",wallpaperData, function (data, status) {
		if (status == "success") {
			console.log("wallpaper set info: "+data);
		} else {
			console.log("An error occurred");
		}
    		//console.log("got back data: ",data);
    		//console.log("got back status: ",status);
	});

		//executeNativeCommand("qdbus org.kde.KWin /KWin reconfigure");
	});
});

    document.body.children[0].style.backgroundImage= "url('"+imgData+"'";
              
               
    for (i = 0; i < runningApps.length; i++)
    {
        
    
        
        if (i == 0) {
            /*explore Bar */
              //runningApps[0].windowObject.window.document.getElementById("mainBlock").style.backgroundImage = document.body.children[0].style.backgroundImage;

             console.log("we are in here B"); runningApps[0].windowObject.window.document.getElementById("launcherContainer").style.backgroundImage = document.body.children[0].style.backgroundImage;

              runningApps[0].windowObject.window.document.getElementById("rightPanelContainer").style.backgroundImage = document.body.children[0].style.backgroundImage;

	//FIXME: This undefined thing going on is strange. This si literally a quick fix since it somehow fixes itself later on or something. Look into it later though. Can't be bothered right now since apparently it fixes itself haha

       //if (runningApps[0].desktopObject != undefined) runningApps[0].desktopObject.window.window.document.getElementById("blurWallpaper").style.backgroundImage = document.body.children[0].style.backgroundImage;

              //runningApps[0].windowObject.window.document.getElementById("miniInfo").style.backgroundImage = document.body.children[0].style.backgroundImage;
              //runningApps[0].windowObject.window.document.getElementById("actionIconsView").style.backgroundImage = document.body.children[0].style.backgroundImage;
//$(runningApps[0].extrabarObject.window.document.getElementById("actionIconsView")).css('background', 'red url(' + document.body.children[0].style.backgroundImage + ')');

//$(runningApps[0].extrabarObject.window.document.getElementById("rightPanelContainer")).css('background', 'red url(' + document.body.children[0].style.backgroundImage + ')');

        //FIXME: remove these since we use real blur, but might be needed for backup. runningApps[0].extrabarObject.window.document.getElementById("extraBar").style.backgroundImage = document.body.children[0].style.backgroundImage;

            
        //runningApps[0].extrabarObject.window.document.getElementById("extraAiBar").style.backgroundImage = document.body.children[0].style.backgroundImage;
       
       if (runningApps[0].desktopObject != undefined) runningApps[0].desktopObject.window.document.body.children[0].children[0].style.backgroundImage = "url('"+actualWallpaper+"')";//"file://"+wallpaperPath;
           
       if (runningApps[0].desktopObject != undefined) runningApps[0].desktopObject.window.document.body.children[0].children[0].style['background-size'] =  width+"px "+height+"px";



	if (useRealTimeBlur)
		break; //no need to apply to the rest of the windows
        } else {
        
        //console.log("RUNNING APPS: "+i,runningApps[i]);
        //runningApps[i].windowObject.window.document.body.style.backgroundImage = document.body.style.backgroundImage;
        //runningApps[i].windowObject.window.document.body.children[0].style.backgroundImage = document.body.children[0].style.backgroundImage;

		if (runningApps[i].windowObject.outerBodyBackground != undefined) //FIXME
	runningApps[i].windowObject.outerBodyBackground[0].style.backgroundImage = document.body.children[0].style.backgroundImage;
       }
        
    }
              console.log("gets here B");
              
    
    window.document.body.children[0].style['background-size'] =  width+"px "+height+"px";
    window.document.body.children[0].style['background-position'] = x+"px "+y+"px";
   // $('#bg_main').css("background-size", width+"px "+height+"px !important"); 
    //"url('file:///home/anesu/Pictures/aa/2/02225_cherryflowers_1920x1080.jpg')";
    //console.log("got here",$('body').css("background-image"));
    //context._blurRect(x, y, width, height, blurEffect, saturationValue);
                  stillProcessingWallpaper = false;
			if (blurEffect != parseInt(JSON.parse(localStorage.getItem('wallpaperBlurEffect')))) { //Check to make sure no changes where done in the mean time
				wallpaper.get().then(imagePath => {
				console.log("WALLPAPER C: ",imagePath);
				$.blurWin(imagePath);
				//console.log("LOL IMG",imagePath);
});
			}
                     }
                 , 100);
	}
      };
    //console.log("file://"+wallpaperPath);
if (wallpaperPath.indexOf("data:image/jpeg") != -1) {
	console.log("found data:image");
	imageObj.src = wallpaperPath; 
} else {
	console.log("did not find data:image");
      imageObj.src = "file://"+wallpaperPath; 
}
    //console.log("x: ",x);
    //console.log("y: ",y);
var context = canvas.getContext('2d');
//context._blurRect(x, y, width, height, blurEffect, saturationValue);

    
  $("#draggableTopBar").mouseenter(function() {
  $("#bg_cover").fadeOut();
});
    
    $("#draggableTopBar").mouseleave(function() {
  $("#bg_cover").fadeIn();
});
    
    }
   
}

//$.blurWin("/home/anesu/extern/Wallpaper/wall272.jpg");

//console.log("WALLPAPER C: ",wallpaper.get());





/*var wallpaperDir = "/home/anesu/extern/Wallpaper/";
wallNo = 1;
lastWallpaper = "/home/anesu/extern/Wallpaper/wall0.jpg"
fs.readdir(wallpaperDir, function(err, filenames) {
    if (err) {
      onError(err);
      return;
    }
    if (filenames.length == 1)
    {
        lastWallpaper = wallpaperDir+filenames[0];
        exte = filenames[0].split('.').pop();
       wallNo = filenames[0].replace("wall","").replace(exte,"");
        wallNo++;
        
        console.log("Wall no: ",+wallNo);
        console.log("Wall last: "+lastWallpaper);
        $.blurWin(lastWallpaper);
        
    }
    console.log(filenames);
});*/

function copyFile(source, target, cb) {
  var cbCalled = false;

  var rd = fs.createReadStream(source);
  rd.on("error", function(err) {
    done(err);
  });
  var wr = fs.createWriteStream(target);
  wr.on("error", function(err) {
    done(err);
  });
  wr.on("close", function(ex) {
    done();
  });
  rd.pipe(wr);

  function done(err) {
    if (!cbCalled) {
      cb(err);
      cbCalled = true;
    }
  }
}

function checkWallpaperSet(err)
{
    console.log("done errors: ",err);
}

function setDefaultWallpapers () {
    
    
}


function setWallpaperTo(wallpaperLink,title,artistName,thumbnailUrl) {
    
    if (wallpaperLink.indexOf("../Shared") == 0) { //we are in local wallpapers
        var fixedUrl = process.cwd()+wallpaperLink.replace("..","");
    } else
        var fixedUrl = wallpaperLink;
    
    //console.log("Fixed Link",fixedUrl);
    
   /* currentWallpaper = "/home/anesu/extern/Wallpaper/wall"+wallNo+"."+wallpaperLink.split('.').pop();
    copyFile(wallpaperLink, currentWallpaper, 
             function (err)
{
    console.log("done errors: ",err);
        setTimeout(function(){ $.blurWin(currentWallpaper); }, 500);
        
});*/
    
    //console.log("WALLPAPER LINK");
    
    wallpaper.set(fixedUrl).then(() => {
	console.log("coming from here");
        $.blurWin(fixedUrl);
        $("#wallpaperPreview")[0].src = thumbnailUrl;//wallpaperLink;
$("#wallpaperTitle").text(title);
$("#wallpaperArtist").text(artistName);

/*
var wallpaperInfo = {
url : fixedUrl,
wallTitle ; title,
artist : artistName
}
*/

//localStorage.setItem('wallpaperInfo', JSON.stringify(wallpaperInfo));
    lastWallpaper = wallpaperLink;
    //console.log('done');
});
    
    
    /*$("#wallpaperPreview")[0].src = wallpaperLink;
    fs.unlink(lastWallpaper);
    lastWallpaper = "/home/anesu/extern/Wallpaper/wall"+wallNo+"."+wallpaperLink.split('.').pop();
    
    wallNo++;*/
}

if (localStorage.getItem('systemSetupCompleted') === null) {
//console.log("New wallpaper");

setWallpaperTo('../Shared/CoreIMG/wallpaper/23.jpg','Sagres, Portugal','Chandler Borris');
} else {


wallpaper.get().then(imagePath => {
	console.log("WALLPAPER C: ",imagePath);
	$.blurWin(imagePath);
	//console.log("LOL IMG",imagePath);
});
}

function reloadWallpaper() {
if (localStorage.getItem('systemSetupCompleted') === null) {
//console.log("New wallpaper");

setWallpaperTo('../Shared/CoreIMG/wallpaper/23.jpg','Sagres, Portugal','Chandler Borris');
} else {


wallpaper.get().then(imagePath => {
	console.log("WALLPAPER C: ",imagePath);
	$.blurWin(imagePath);
	//console.log("LOL IMG",imagePath);
});
}
}


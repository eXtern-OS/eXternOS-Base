var win = nw.Window.get();
var reblurBg = false;

function adjustHubBackground() {
	var posY = screen.height-716;
	//console.log("posY",posY);
	win.outerBodyBackground = window.document.getElementsByTagName("BACKGROUND");
	$(win.outerBodyBackground[0]).css("background-position",-25+"px "+"-"+posY+"px");
	//console.log("posY bg",$(win.outerBodyBackground[0]));
}

onload = function() {


           
          
//console.log("Is transparent: ",gui);
//win.setTransparent(true);
//setTimeout(function(){ console.log("Is transparent: "+win.isTransparent) }, blur_time);

jQuery.bgAdjust = function bgAdjust(window,exploreBar) {
	//console.log("Try using force X", window);
	if (window.forceX != null) {
		console.log("using force X");
    		var x = -window.forceX;
		var y = -window.forceY;
	} else {
    		var x = -window.window.screenX;//window.x; //Bug fixing after moving apps to iframe
		var y = -window.window.screenY;//window.y; //Bug fixing after moving apps to iframe
	}

	if ((window.hidingNow == null) && (window.ignoreMetaKey == null)) { //Stop gap to avoid hub window being called here. No idea who is calling it and from where
var width = (screen.width)*3;
var height = screen.height;
x -=  (width/3);
    if (exploreBar) {
        //var mainBlockHeight = window.window.document.getElementById('mainBlock').clientHeight;
        var xBar = -((width-3)-window.window.document.getElementById('extraBar').clientWidth);
        var yBar = -(screen.height - 46 - window.window.document.getElementById('extraBar').clientHeight);
        
        var xxBar = -60;
        var yyBar = -(screen.height - 46 - window.window.document.getElementById('extraAiBar').clientHeight);
        
        
        if (window.bottomBar) {
            y = -(screen.height - window.window.document.getElementById('mainBlock').clientHeight);
        window.window.document.getElementById("mainBlock").style['background-size'] =  width+"px "+height+"px";
        window.window.document.getElementById("mainBlock").style['background-position'] = x+"px "+y+"px";

window.window.document.getElementById("launcherContainer").style['background-size'] =  width+"px "+height+"px";
        window.window.document.getElementById("launcherContainer").style['background-position'] = (x-51)+"px "+y+"px";

window.window.document.getElementById("rightPanelContainer").style['background-size'] =  width+"px "+height+"px";
        window.window.document.getElementById("rightPanelContainer").style['background-position'] = ((width/3)+192+216+window.additionalIconsPixels)+"px "+y+"px";

//window.window.document.getElementById("actionIconsView").style['background-size'] =  width+"px "+height+"px";
        //window.window.document.getElementById("actionIconsView").style['background-position'] = (width+192)+"px "+y+"px"; //FIXME
        } else {
        window.window.document.getElementById("extraBar").style['background-size'] =  width+"px "+height+"px";
        window.window.document.getElementById("extraBar").style['background-position'] = xBar+"px "+yBar+"px";
        
        window.window.document.getElementById("extraAiBar").style['background-size'] =  width+"px "+height+"px";
        window.window.document.getElementById("extraAiBar").style['background-position'] = xxBar+"px "+yyBar+"px";
        }
    } else {
	if (window.outerBodyBackground != null) {
    		window.outerBodyBackground[0].style['background-size'] =  width+"px "+height+"px";
    		window.outerBodyBackground[0].style['background-position'] = x-25+"px "+y+"px";
            //window.outerBodyBackground[0].style['background-position'] = "-25px "+"-25px";
	}
    }

	adjustHubBackground();
	
 }
}
    

    
    var win = nw.Window.get();
    
    win.bgAdjust = $.bgAdjust;


    
    win.minimized = false;
    
    win.on('minimize', function() {
    win.minimized = true;
        console.log("We're minimized");
    }); 
    
    win.on('focus', function() {

	win.x = 0;
	win.y = window.screen.height-(win.height+59);   //win.heigh is 716

	console.log("we're focused");
	console.log("win.window.screenY B",win.window.screenY);
	console.log("win.window.screenHeight B",win.height);
	//setTimeout(function(){ $.bgAdjust(win); }, 1000);
        //console.log("We're triggered");
        //win.minimized = false;
	
	
        //$.bgAdjust(win);
});
    
    win.on('move', function() {
        //win.minimized = false;
	win.y = window.screen.height-(win.height+59); 
	console.log("We're moving");
	focusOnSearchInput();
        //$.bgAdjust(win);
	//setTimeout(function(){ $.bgAdjust(win); }, 1000);
	win.minimized = false;
	$("#searchOuter > input").val("");
  }); 
    
 //blurWin();
           
           var gui = require('nw.gui');
    var win = gui.Window.get();
          console.log(gui.Window.get().title);
           console.log(gui.App.dataPath);

           function set_blur(){
               var exec = require('child_process').exec,
                   child;
            child = exec("/home/anesu/.blur.sh",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
    if (error !== null) {
      console.log('exec error: ' + error);
        
    }       
});win.showDevTools();// get the system clipboard
var clipboard = nw.Clipboard.get();
var textT = clipboard.get('text');
console.log("clipbpard: ", textT);
           }
           
           function show_window()
           {
               //gui.Window.get().show();
               //setTimeout(function(){ gui.Window.get().setShowInTaskbar(false); set_blur(); }, 300);
           }
           

               setTimeout(function(){ show_window() }, 500);
           
           
           
           
           
        }

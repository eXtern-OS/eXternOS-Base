       onload = function() {
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
});//win.showDevTools();
           }
           
           function show_window()
           {
               gui.Window.get().show();
               setTimeout(function(){ set_blur(); }, 300);
           }
           

               setTimeout(function(){ show_window() }, 500);
           
           
           
           
           
        }
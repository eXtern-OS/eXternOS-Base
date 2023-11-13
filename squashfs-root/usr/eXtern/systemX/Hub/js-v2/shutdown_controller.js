function shutdownSys() {
  //win.hide();
  win.hideFixed();
    var exec = require('child_process').exec,
                   child;
            child = exec('systemctl poweroff',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: shutdown');
        
        
        
        
    }       
});
}


function rebootSys() {
  //win.hide();
  win.hideFixed();
    var exec = require('child_process').exec,
                   child;
            child = exec('systemctl reboot',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: shutdown');
        
        
        
        
    }       
});
}

function logoutSys() {
  //win.hide();
  win.hideFixed();
    var exec = require('child_process').exec,
                   child;
            child = exec('kill -9 -1',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: logout');
        
        
        
        
    }       
});
}

function lockSys() {
  //win.hide();
  win.hideFixed();
    var exec = require('child_process').exec,
                   child;
            child = exec('dm-tool switch-to-greeter',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: logout');
        
        
        
        
    }       
});
}

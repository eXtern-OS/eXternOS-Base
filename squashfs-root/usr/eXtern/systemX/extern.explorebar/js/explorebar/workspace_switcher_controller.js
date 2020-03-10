function openWorkspaceSwitcher() {
win.runningApps[0].windowObject.sysWin.ignoreMetaKey = true;
    var exec = require('child_process').exec,
                   child;
            child = exec('xdotool keydown super key s keyup super',function (error, stdout, stderr)
    {
    console.log('stdout: ' + stdout);
    console.log('stderr: ' + stderr);
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       console.log('SUCCESS: switch');
        
        
        
        
    }       
});
}

//https://askubuntu.com/questions/839768/how-to-connect-to-a-wpa2-enterprise-with-nmcli-in-a-non-interactive-mode

//nmcli c modify <connection_name> 802-1x.eap <eap_mode> 802-1x.identity <username> 802-1x.phase2-auth <auth_type>

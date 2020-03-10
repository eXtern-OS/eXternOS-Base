
// Initialize wifi module 
// Absolutely necessary even to set interface to null 
wifi.init({
    iface : null // network interface, choose a random wifi interface if set to null 
});


function getCOnnections () {
 
// Scan networks 
wifi.scan(function(err, networks) {
    if (err) {
        console.log(err);
    } else {
        //console.log(networks);
        wifiConnections = networks;
        //console.log("ALL CONNECTIONS",wifiConnections);
        
        $(win.runningApps[0].extrabarObject.window.document.getElementById("availableWifiList")).empty();
            for (var i = 0; i < networks.length; i++) {
                if (networks[i].ssid != "--") {
                if (networks[i].security != "") {
                    var securedInfo = "Secured ("+networks[i].security+")";
                    var connectFunction = 'getWirelessPassword(`mPasswordField-'+networks[i].mac+'`)';
                } else
                     var securedInfo = "Open";
        $(win.runningApps[0].extrabarObject.window.document.getElementById("availableWifiList")).append('<div id="m-'+networks[i].mac+'" class="media p-l-5 wifiConnection"><div class="pull-left"><span class="wifiIcon icon">&#61954;</span></div><div class="media-body" style="width: 100px; display: inline-block;"><small class="text-muted">'+securedInfo+'</small><br/><a class="" href="javascript:void(0);">'+networks[i].ssid+'</a></div><div class="pull-right" style="text-align: center; margin-top: 5px;"><button id="mConnect-'+networks[i].mac+'" class="btn-connect btn btn-alt m-r-5">Connect</button><span id="mConnected-'+networks[i].mac+'" class="hidden">Connected</span><button id="mDisconnect-'+networks[i].mac+'" class="btn-disconnect hidden btn btn-alt m-r-5"> Disconnect</button></div><input id="mPasswordField-'+networks[i].mac+'" type="password" class="wifiPassInput form-control m-b-10 hidden" placeholder="Password"><a id="mSecureConnect-'+networks[i].mac+'" href="javascript:void(0);" class="mSecureConnectClass hidden" style="position: absolute; bottom: 16px; right: 10px;"><span class="icon" style="font-size: 22px; text-shadow: 0 0 10px rgba(0, 0, 0, 0.7);">&#61815;</span></a></div>');
                   
                    
                    $(win.runningApps[0].extrabarObject.window.document.getElementById('mPasswordField-'+networks[i].mac)).on('keydown', function(e) {
    if (e.which == 13) {
        console.log("Enter pressed",e);
        trySecureConnect(e.currentTarget);
        
        e.preventDefault();
    }
}); 
                    
                }
    }
        getActiveConnections();
        setConnectButtonEvents();
        
    }
});


}








function setWifiList(lists) {
    console.log("LIST",lists);
}

function getActiveConnections() {
    wifi.getCurrentConnections(function(err, currentConnections) {
    if (err) {
        console.log(err);
    }
    //console.log(currentConnections);
    for (var i = 0; i < currentConnections.length; i++) {
        
        $(win.runningApps[0].extrabarObject.window.document.getElementById("mConnect-"+currentConnections[i].mac)).addClass("hidden"); //Hide connect button
        $(win.runningApps[0].extrabarObject.window.document.getElementById("mDisconnect-"+currentConnections[i].mac)).removeClass("hidden"); //Show disconnect button
        
        $(win.runningApps[0].extrabarObject.window.document.getElementById("mConnect-"+currentConnections[i].mac)).addClass("connected");
        
        $(win.runningApps[0].extrabarObject.window.document.getElementById("mConnected-"+currentConnections[i].mac)).removeClass("hidden"); //Show  connected text
    }

    /*
    // you may have several connections
    [
        {
            iface: '...', // network interface used for the connection, not available on macOS
            ssid: '...',
            mac: '...',
            frequency: <number>, // in MHz
            signal_level: <number>, // in dB
            security: '...' // not available on linux
        }
    ]
    */
});

}

function customWirelessConnect(ssid,password) {
    var exec = require('child_process').exec,
                   child;
            child = exec("nmcli dev wifi connect '"+ssid+"' password '"+password+"'",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        if (stdout.indexOf("failed") == -1) {
$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnectingStatus")).fadeOut( "slow", function() {

$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnections")).fadeIn();
  });
        getCOnnections();
        }else {
            console.log("failed to connect");
$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnectingStatus")).fadeOut( "slow", function() {

$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnectionFailed")).fadeIn();

setTimeout(function(){

$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnectionFailed")).fadeOut( "slow", function() {

$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnections")).fadeIn();
  });

}, 3000);

  });

}
    }       
});
}

function connectToWireless (ssid,password) {
$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnections")).fadeOut( "slow", function() {

$(win.runningApps[0].extrabarObject.window.document.getElementById("networkConnectingStatus")).fadeIn();
  });
    // Connect to a network 
    customWirelessConnect(ssid,password); //Using this cos this module has a bug

    /*wifi.connect({ ssid : "ssid", password : "password"}, function(err) {
    if (err) {
        console.log(err);
    }
    console.log('Connected');
    getCOnnections();
});*/
}

function getWirelessPassword() {
    var classname = win.runningApps[0].extrabarObject.window.document.getElementsByClassName("btn-connect");
    
    for (var i = 0; i < classname.length; i++) {
        if (!$(classname[i]).hasClass("connected")) {
            $(classname[i]).removeClass("hidden");
            $(win.runningApps[0].extrabarObject.window.document.getElementById(classname[i].id.replace("mConnect","mPasswordField"))).addClass("hidden");
             $(win.runningApps[0].extrabarObject.window.document.getElementById(classname[i].id.replace("mConnect","mSecureConnect"))).addClass("hidden");
        }
    
}
    
    //passwordFieldID
    $(win.runningApps[0].extrabarObject.window.document.getElementById(this.id.replace("mConnect","mPasswordField"))).removeClass("hidden"); //Hide connect button
    $(win.runningApps[0].extrabarObject.window.document.getElementById(this.id.replace("mConnect","mSecureConnect"))).removeClass("hidden"); //Show password check and connect button
    
    $(this).addClass("hidden"); //Show password check and connect button
    
    //console.log("THIS",this.id.replace("mConnect","mSecureConnect"))
}

function trySecureConnect(passWordFieldDirect) {
    console.log("TRY SECURE",passWordFieldDirect);
    if (passWordFieldDirect !== null)
        var macAdress = passWordFieldDirect.id.replace("mPasswordField-","");
    else
        var macAdress = this.id.replace("mSecureConnect-","").replace("mPasswordField-","");
    
    console.log("MAC: "+macAdress,wifiConnections);
    
    for (var i = 0; i < wifiConnections.length; i++) {
        if (wifiConnections[i].mac == macAdress) {
            var passwordField = win.runningApps[0].extrabarObject.window.document.getElementById("mPasswordField-"+macAdress);
            console.log("connect to: "+wifiConnections[i].ssid+" password: "+passwordField.value);
            connectToWireless(wifiConnections[i].ssid,passwordField.value);
        }
    }
}

function setConnectButtonEvents() {
    var classname = win.runningApps[0].extrabarObject.window.document.getElementsByClassName("btn-connect");
    
    for (var i = 0; i < classname.length; i++) {
        classname[i].addEventListener('click', getWirelessPassword, false);
        var secureConnect = win.runningApps[0].extrabarObject.window.document.getElementById(classname[i].id.replace("mConnect","mSecureConnect"));
        secureConnect.addEventListener('click', trySecureConnect, false);
    }
    
    //Disconnect
    var classname = win.runningApps[0].extrabarObject.window.document.getElementsByClassName("btn-disconnect");
    
    for (var i = 0; i < classname.length; i++) {
    classname[i].addEventListener('click', disconnectWifi, false);
    }
    
}

function disconnectWifi() {
    // Disconnect from a network 
// not available on all os for now 
wifi.getCurrentConnections(function(err, currentConnections) {
    if (err) {
        console.log(err);
    } else {
        console.log("disconnected");
        getCOnnections();
    }
    //console.log("disconnected",currentConnections);
    /*
    // you may have several connections
    [
        {
            iface: '...', // network interface used for the connection, not available on macOS
            ssid: '...',
            mac: '...',
            frequency: <number>, // in MHz
            signal_level: <number>, // in dB
            security: '...' // not available on linux
        }
    ]
    */
});
}

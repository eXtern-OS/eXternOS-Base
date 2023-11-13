
//FIXME move this out of here
function executeNativeCommand(request,callback) {
    var exec = require('child_process').exec,
                   child;
            child = exec(request,function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
    if (error !== null) {
      //console.log('exec error: ' + error);
	if (callback != null)
		callback(null,error);
    } else {

	if (callback != null)
		callback(stdout);
    

    }       
});
}
//win.showDevTools();

/*Apply Virtual Desktops Options*/
executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Desktops --key Number 3");
executeNativeCommand('kwriteconfig5 --file ~/.config/kwinrc --group Desktops --key Name_1 "Main Desktop"');
executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Desktops --key Rows 1");
/*End of Apply Desktops Options*/ 

/*Apply Blur Options*/
executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Effect-Blur --key BlurStrength 12");
/*End of Apply Blur Options*/

/*Apply Alt+Tab Cover Switch view options*/
executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Effect-CoverSwitch --key TabBox true");
executeNativeCommand('kwriteconfig5 --file ~/.config/kwinrc --group Effect-CoverSwitch --key TabBoxAlternative false');
executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Effect-CoverSwitch --key WindowTitle false");
executeNativeCommand("kwriteconfig5 --file ~/.config/kwinrc --group Effect-CoverSwitch --key zPosition 1640");
/*End of Apply Desktops Options*/ 

executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/kcminputrc ~/.config/kcminputrc");
executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/kdeglobals ~/.config/kdeglobals");
executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/kglobalshortcutsrc ~/.config/kglobalshortcutsrc");
	if (improvePerfomanceMode) {
		$("#bg_main").addClass("improvePerfomanceModeBody");
		executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/light_perfomance/kwinrc ~/.config/kwinrc");
	} else {
		$("#bg_main").removeClass("improvePerfomanceModeBody");
		executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/kwinrc ~/.config/kwinrc");
	}
executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/kwinrulesrc ~/.config/kwinrulesrc");
executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/breezerc ~/.kde/share/config/breezerc");
executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/breeze/kdeglobals ~/.kde/share/config/kdeglobals");

executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/Enhanced Audio Experience.json ~/.config/PulseEffects/Enhanced Audio Experience.json");

//executeNativeCommand("gsettings set  org.gnome.desktop.interface cursor-theme 'Quintom_Ink'");
executeNativeCommand("gsettings set  org.gnome.desktop.interface cursor-theme 'Breeze'");

executeNativeCommand("qdbus org.kde.KWin /KWin reconfigure");

executeNativeCommand("sudo /usr/lib/policykit-1/polkitd --replace &");


//Audio Effects

//pulseeffects -q
//setTimeout(function(){ 
//executeNativeCommand("pulseeffects -q", function () {

setTimeout(function(){ 
console.log("executing the rest....");
//executeNativeCommand("pulseeffects --gapplication-service", function () {
console.log("applying effects");
if (enhancedAudio) {
	executeNativeCommand('pulseeffects --load-preset "Enhanced Audio Experience"');
} else {
	executeNativeCommand('pulseeffects --reset');
}
//});
}, 5000);
//});
//}, 20000);



/*Notification*/
executeNativeCommand("dunst -config /usr/eXtern/systemX/Shared/CoreMsc/dunstrc");


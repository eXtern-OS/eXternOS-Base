

function showContextMenu(contextMenuX,contextMenuY) {
	console.log("context menu triggered");
	if (contextMenuY > ((win.height)-245)) {
		$("#appsContextMenu").css("top",contextMenuY-165);
	} else {
		$("#appsContextMenu").css("top",contextMenuY);
	}

		$("#appsContextMenu").css("left",contextMenuX);

	$("#appsContextMenu").removeClass("hidden");
	
}

function contextMenuInit() {

$("#bg_main").prepend('<div id="contextMenuCover" class="hidden"></div><div id="appsContextMenu" class="contextMenu dropdown open hidden">'
			+'<div style="height: 185px; width: 160px; position: absolute;     backdrop-filter: blur(15px); z-index: 100;"></div>'
                        +'<ul style="height: 187px;" class="dropdown-menu dropdown-menu-alt zeroHeight" role="menu">'
                            +'<li id="openAppOption" role="presentation" class="driveMenuItem"><a class="filesOption" role="menuitem" tabindex="-1" href="javascript:void(0);" onclick="openInDriveNewFilesInstance()"><span class="icon randomResize">&#61881;</span> <span id="contextMenuAppName">Photos</span></a></li>'
                            +'<li role="presentation" class="driveMenuItem"><a role="menuitem" tabindex="-1" href="javascript:void(0);" class="driveMenuItem"><span class="icon randomResize">&#61886;</span> Settings</a></li>'
                            +'<li id="appsContextMenuProperties" role="presentation" class="driveMenuItem"><a role="menuitem" tabindex="-1" href="javascript:void(0);" class="driveMenuItem" onclick="showDrivePropertiesWindow()"><span class="icon randomResize">&#61918;</span> Uninstall</a></li>'
                            //+'<li role="presentation" class="divider driveMenuItem"></li>'
                        +'</ul>'
                    +'</div>');

$(".appBox").contextmenu(function(event)  {

console.log("right clicked app",event);

			var bodyRect = document.body.getBoundingClientRect(),
    			elemRect = $('.appBox:hover')[0].getBoundingClientRect(),
    			topOffset   = elemRect.top - bodyRect.top,
			leftOffset   = (elemRect.left - bodyRect.left)+210;

			$(".appOptionsItem").remove();

			console.log("divxx: ",$("#appsContextMenu > ul"));

			$("#appsContextMenu > ul").css("height","187px");

			$("#contextMenuCover").removeClass("hidden");
			$(".selectedApp").removeClass("selectedApp");
			$(".appBox").addClass("notActiveApp");
			$("#contextMenuAppName").text("Open "+$(event.currentTarget).find(".appTextOverflow").text());
			$("#contextMenuAppName").parent().attr("onclick",$(event.currentTarget).attr("onclick"));
			console.log("allApps: ",allInstalledApps);
			console.log("app-name: ",$(event.currentTarget).attr("app-id"));

			for (var i = 0; i < allInstalledApps.length; i++) {
				if (allInstalledApps[i].id == $(event.currentTarget).attr("app-id")) {
					console.log("found the app",allInstalledApps[i]);
					if (allInstalledApps[i].menu != null) {
						if (allInstalledApps[i].menu.options != null) {
							for (var j = 0; j < allInstalledApps[i].menu.options.length; j++) {
									$( '<li role="presentation" class="driveMenuItem appOptionsItem"><a role="menuitem" tabindex="-1" href="javascript:void(0);" class="driveMenuItem" onclick = "openApp(`'+allInstalledApps[i].id+'`,`'+allInstalledApps[i].menu.options[j].argument+'`)" ><span class="'+allInstalledApps[i].menu.options[j].icon+'" style="color: #ffffffbf; font-size: 22px; margin-right: 8px;" aria-hidden="true"></span> '+allInstalledApps[i].menu.options[j].name+'</a></li>' ).insertAfter( $("#openAppOption") );
							}


						if (allInstalledApps[i].menu.options.length < 4) {
							$("#appsContextMenu > ul").css("height",(187+(43*allInstalledApps[i].menu.options.length))+"px");
						} else if (allInstalledApps[i].menu.options.length > 4) {
							$("#appsContextMenu > ul").css("height",(187+(43*4))+"px");
						}


						}
					}
				}
			}

			$(event.currentTarget)
			.addClass("selectedApp")
			.removeClass("notActiveApp");

			if (leftOffset > 800)
				leftOffset -= 380; //Icon (ish) + context menu width
			console.log("leftOffset: ",leftOffset);

			showContextMenu(leftOffset,topOffset);
});

$("#contextMenuCover").click(function(event)  {
	$("#contextMenuCover").addClass("hidden");
	$(".selectedApp").removeClass("selectedApp");
	$("#appsContextMenu").addClass("hidden");
	$(".appBox").removeClass("notActiveApp");
});
}



setTimeout(function() {

contextMenuInit();

}, 10000);

//win.showDevTools();
var cssToAppendToApps = [];

var selectedDisplayResolution;
var oldSelectedResolutionDiv;

if (localStorage.getItem('resolutionManuallySetByUser') != null) {
	var resolutionManuallySetByUser = JSON.parse(localStorage.getItem('resolutionManuallySetByUser')); 
} else {
	var resolutionManuallySetByUser = false;
}

//var resolutionManuallySetByUser = false;

function openSysMonitor() {
    currentMenuMode = 'sysMonitor';
   $("#startMenu").fadeOut(500);

        //setTimeout(function() {
    //$('#cpuUsage').data('easyPieChart').update(cpuPercentage);
         //}, 1000);

   
    
    //console.log("CPUS: ",os.cpus());
    
    
    updateSysMonitor();
    setTimeout(function() {
            updateDiskSpace(); //Delay to avoid lag during animation
}, 1000); 
    
    
    
    
    
   /* 
    //Grab first CPU Measure
var startMeasure = cpuAverage();

//Set delay for second Measure
setTimeout(function() { 

  //Grab second Measure
  var endMeasure = cpuAverage(); 

  //Calculate the difference in idle and total time between the measures
  var idleDifference = endMeasure.idle - startMeasure.idle;
  var totalDifference = endMeasure.total - startMeasure.total;

  //Calculate the average percentage CPU usage
  var percentageCPU = 100 - ~~(100 * idleDifference / totalDifference);

  //Output result to console
  console.log(percentageCPU + "% CPU Usage.");
    $('#cpuUsage').data('easyPieChart').update(percentageCPU);

}, 100);*/
    
    setTimeout(function(){$("#sysPerfomance").fadeIn(300);}, 350);
    setTimeout(function(){   $("#startMenu").addClass("hidden");}, 500);    
}

	if($('#ex1')[0]) {
	    $('#ex1').slider().on('slide', function(ev){
		$(this).closest('.slider-container').find('.slider-value').val(ev.value);
	    });
	}



function initMap(mapName,latitude,longitude,city,country) {
    /* --------------------------------------------------------
 Map
 -----------------------------------------------------------*/
//mapName: world_mill_en latitude: -32.167 longitude: 147.013 city: Alexandria country:Australia

console.log("mapName: "+mapName+" latitude: "+latitude+" longitude: "+longitude+" city: "+city+" country:"+country);

$('#Location-map').empty();
//$(function(){
    if($('#Location-map')[0]) {
	$('#Location-map').vectorMap({
            map: mapName,
            backgroundColor: 'rgba(0,0,0,0.25)',
            regionStyle: {
                initial: {
                    fill: 'rgba(255,2552,255,0.7)'
                },
                hover: {
                    fill: '#fff'
                },
            },
    
            zoomMin:0.88,
            /*focusOn:{
                x: 5,
                y: 1,
                scale: 1.8
            },*/
            markerStyle: {
                initial: {
                    fill: '#e80000',
                    stroke: 'rgba(0,0,0,0.4)',
                    "fill-opacity": 2,
                    "stroke-width": 7,
                    "stroke-opacity": 0.5,
                    r: 4
                },
                hover: {
                    stroke: 'black',
                    "stroke-width": 2,
                },
                selected: {
                    fill: 'blue'
                },
                selectedHover: {
                }
            },
        
    
            markers :[
                {latLng: [latitude,longitude], name: city+", "+country},
            ],
        });
        
        
    }
    
//});
}



function applyNewLocation() {

	user_location.city = searchAll.split(",")[0].replace(" ","");
	user_location.country = searchAll.split(",")[1].replace(" ","");
	user_location.region = ""; //Temporary, we don't know the user region yet

	console.log("apply new location",user_location);

	$("#applyChangeLocationButton").addClass("hidden");
	$("#changeLocationOuter").addClass("hidden");
	$("#changeTimezoneOuter").addClass("hidden");
	$("#cancelChangeLocationButton").addClass("hidden");
	$("#changeLocationButton").removeClass("hidden");

	find({search:user_location.city+', '+user_location.country, degreeType: 'C'});

	var regionText = "";

	if (user_location.region != "") {
		regionText = user_location.region+", ";
	}


	console.log("user_location.city:"+user_location.city+".");
	console.log("user_location.country:"+user_location.country+".");


	if (user_location.city == "" && user_location.country == "")
		$("#locationLabel").text(" currently not yet set. Please add it below");
	else
		$("#locationLabel").text(user_location.city+", "+regionText+user_location.country);
	$("#locationTimezoneLabel").text(user_location.timezone);

	    setTimeout(function() { 
		initMap('world_mill_en',user_location.lat,user_location.long,user_location.city,user_location.country); //world

    }, 2000); 
	
}


Object.filterx = function( obj, predicate) {
    var result = {}, key;
    // ---------------^---- as noted by @CMS, 
    //      always declare variables with the "var" keyword

    for (key in obj) {
        if (obj.hasOwnProperty(key) && !predicate(obj[key])) {
            result[key] = obj[key];
        }
    }

    return result;
};


var allCountries;

var searchAll = "";
var searchCity = "";
var searchCountry = "";
var foundMatches = [];
var allCountriesTimezones = [];
var selectedTimezone = "";

function checkIfLocationInputIsValid() {
	searchAll = $( "#changeLocationInput" ).val();
	searchCity = searchAll.split(",")[0];
	if (searchAll.split(",").length > 1)
		searchCountry = searchAll.split(",")[1].replace(" ","");
	else
		searchCountry = "";
	var found = foundMatches.find(function(element) {
  	return element == searchAll;
	});

	if (found !== undefined && found !== null) {
		$('#applyChangeLocationButton').prop("disabled", false);
		getTimezones();
	} else {
		$('#applyChangeLocationButton').prop("disabled", true);
	}

	console.log("founds",found);
}

function cityInput(e) {
	console.log("city Input",e.target.value);
	searchAll = e.target.value;
	searchCity = searchAll.split(",")[0];
	console.log("searchCity",searchCity);

	checkIfLocationInputIsValid();


	if (searchAll.length > 1) {
		foundMatches = [];
		$.each(allCountries, function(k, v) {
        //display the key and value pair
	/*if (k.indexOf("Zim") > -1) {
        	console.log(k + ' is ',v);*/

	var citiesAsString = v.toString();

	findCity = citiesAsString.toLowerCase().indexOf(searchCity.toLowerCase());

	//console.log("city index",findCity);

	if (findCity != -1) {

	var cityWithTheRest = citiesAsString.substr(findCity);

	var foundCity = cityWithTheRest.substr(0,cityWithTheRest.indexOf(","));

	console.log("city found is :"+foundCity+", "+k);

	foundMatches.push(foundCity+", "+k);

	$( "#changeLocationInput" ).autocomplete({
      		source: foundMatches,
		select:checkIfLocationInputIsValid
    	});

	$(".ui-corner-all").click(function() {
  		checkIfLocationInputIsValid();
	});

	if (foundMatches.length > 3) {

		return false;

	}
	}

	


    });

	}
	
	//e.target.value;
}


//FIXME: Needs root!
function updateSystemTimezone() {
    var exec = require('child_process').exec,
                   child;
            child = exec('sudo dpkg-reconfigure --frontend noninteractive tzdata',function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
    
	console.log("timezone added!");
        

    }       
});
}


//FIXME: Needs root!
function addTimezoneToSystem() {
    var exec = require('child_process').exec,
                   child;
            child = exec('echo "'+selectedTimezone+'" | sudo tee /etc/timezone',function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
    
	console.log("timezone added!");
        

    }       
});
}

function selectTimeZone(timezoneSelected) {
	selectedTimezone = timezoneSelected;
	
	$("#selectedTimezone").text(selectedTimezone);
}

function getTimezones() {

		var findCountryTimezones = allCountriesTimezones.find(function(currentCountry) {
  			return currentCountry.name == searchCountry;
		});

		console.log("findCountryTimezones",findCountryTimezones);

		$("#timeZones").empty();

		$("#selectedTimezone").text(findCountryTimezones.timezones[0]); //Just set the timezone to be the first one. Need to do an automatic find thing without violating people's privacy etc

		for (var i = 0; i < findCountryTimezones.timezones.length; i++)
			$("#timeZones").append('<li><a href="javascript:void(0);" onclick="selectTimeZone(&quot;'+findCountryTimezones.timezones[i]+'&quot;)" >'+findCountryTimezones.timezones[i]+'</a></li>');
}




function activateFindLocation() {

var locationInputBox = document.querySelector('#changeLocationInput');

locationInputBox.addEventListener('input', cityInput) // register for oninput

	$("#changeLocationButton").addClass("hidden");
	$("#changeLocationOuter").removeClass("hidden");
	$("#changeTimezoneOuter").removeClass("hidden");
	$("#applyChangeLocationButton").removeClass("hidden");
	$("#cancelChangeLocationButton").removeClass("hidden");
	$("#changeLocationInput").focus();
	var fs = require('fs');
	var obj;
	fs.readFile('/usr/eXtern/systemX/Shared/CoreJS/countries.min.json', 'utf8', function (err, data) {
  		if (err) throw err;
  		allCountries = JSON.parse(data);

		console.log("allCountries",allCountries);

		var elementPos = Object.keys(allCountries).indexOf("Zim");

		var resA = Object.keys(allCountries)[elementPos];

		console.log("allCountries resultA",resA);

		var resB = allCountries[resA];

		console.log("allCountries resultB",resB);

	$.each(allCountries, function(k, v) {
        //display the key and value pair
	if (k.indexOf("Zim") > -1) {
        	console.log(k + ' is ',v);

	var citiesAsString = v.toString();

	findCity = citiesAsString.indexOf("H");

	console.log("city index",findCity);

	var cityWithTheRest = citiesAsString.substr(findCity);

	var foundCity = cityWithTheRest.substr(0,cityWithTheRest.indexOf(","));

	console.log("city",foundCity);

	}


    });

		
	});

	fs.readFile('/usr/eXtern/systemX/Shared/CoreJS/countries-coordinates-timezones.json', 'utf8', function (err, data) {
  		if (err) throw err;
  		allCountriesTimezones = JSON.parse(data);
	});
}


function cancelChangeLocationButton() {
	$("#changeLocationButton").removeClass("hidden");
	$("#changeLocationOuter").addClass("hidden");
	$("#changeTimezoneOuter").addClass("hidden");
	$("#applyChangeLocationButton").addClass("hidden");
	$("#cancelChangeLocationButton").addClass("hidden");
}





var currentSysSettingsMenu = "sys_main";
var mapLoaded = false;

function open_date_time() {

    if (currentSysSettingsMenu !="sys_date_time")
    {

	var regionText = "";

	if (user_location.region != "") {
		regionText = user_location.region+", ";
	}


	if (user_location.region != "") {
		regionText = user_location.region+", ";
	}


	console.log("user_location.city:"+user_location.city+".");
	console.log("user_location.country:"+user_location.country+".");


	if (user_location.city == "" && user_location.country == "")
		$("#locationLabel").text(" currently not yet set. Please add it below");
	else
		$("#locationLabel").text(user_location.city+", "+regionText+user_location.country);

	$("#locationTimezoneLabel").text(user_location.timezone);
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_date_time").fadeIn( 400, function() {

		if (!mapLoaded) {
	    		setTimeout(function() { 
				initMap('world_mill_en',user_location.lat,user_location.long,user_location.city,user_location.country); //world

   			}, 1000); 
		}
    			
		mapLoaded = true;
  });


        currentSysSettingsMenu = "sys_date_time";
    }

}



function openWallpaperSettings() {
    if (currentSysSettingsMenu !="sys_wallpapers")
    {
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_wallpapers").fadeIn();
        currentSysSettingsMenu = "sys_wallpapers";
    }
}



function focusOnSearchInput() {
    setTimeout(function() { //Delay is to avoid the animation glitch that occurs when returning from settings to Apps view
    	if (currentSysSettingsMenu =="sys_main")
    	{
		$("#searchOuter > input").focus();
    	}
    }, 1500); 
}

function changeTemperatureUnits(newUnits) {

	$("#temperatureUnitsOptionsDropdown").empty();

	systemTemperatureUnit = newUnits;
	if (systemTemperatureUnit == 'c')
		$("#temperatureUnitsOptionsDropdown").append('Celsius <span class="caret"></span>');
	else
		$("#temperatureUnitsOptionsDropdown").append('Fahrenheit <span class="caret"></span>');

	localStorage.setItem('systemTemperatureUnit', JSON.stringify(systemTemperatureUnit));
	loadWeatherStats();

}

let monitorEnaled = $('#monitorEnabled')[0].checked;

$( document ).ready(function() {

	monitorEnaled = $('#monitorEnabled')[0].checked;

	console.log("monitorEnaled: ",monitorEnaled);

	$('#monitorEnabled').change(function() {

		if (this.checked != monitorEnaled) {
			monitorEnaled = this.checked;
			console.log("enabled display?: ",this.checked);

			if (monitorEnaled) {
				let newResolution = $(".res-btn-selected").text().replace(" X ","x").replace("","");
				let newResolutionRefreshRate = $("#refreshRate").text();

				if (allScreenInfo.length > 1) {
					for (let i = 0; i < allScreenInfo.length; i++) {
						if (i == 0 && currentDisplay == allScreenInfo[i].connection) {
							//updateResolution(allScreenInfo[i].connection,newResolution,newRefreshRate,waitForConfirmation,positionCOnfigured)
							console.log("to the left diaply --left-of");
							break;
						} else if (currentDisplay == allScreenInfo[i].connection) {
							console.log("to the right diaply --right-of");
							break;
						}
					}
				} else {
					console.log("lol only 1 display k")
				}

				
				console.log("allScreenInfo: ",allScreenInfo);
				//$('#saveDisplaySettings').prop('disabled', true);
				//updateResolution(selectedDisplayResolution.connection,newResolution,newResolutionRefreshRate,true);
			}
		}

		

	});

if (enableLinuxNativeApps) {
    $('#hubLinuxAppsSupportSwitchInput').parent().removeClass("switch-off"); 
    $('#hubLinuxAppsSupportSwitchInput').parent().addClass("switch-on"); 
    $('#hubLinuxAppsSupportSwitchInput').iCheck('update');
}

if (enableDesktopStacks) {
    $('#desktopStacksSwitchInput').parent().removeClass("switch-off"); 
    $('#desktopStacksSwitchInput').parent().addClass("switch-on"); 
    $('#desktopStacksSwitchInput').iCheck('update');
}

if (improvePerfomanceMode) {
    $('#hubImprovePerfomanceSwitchInput').parent().removeClass("switch-off"); 
    $('#hubImprovePerfomanceSwitchInput').parent().addClass("switch-on"); 
    $('#hubImprovePerfomanceSwitchInput').iCheck('update');
}



});


$('#hubLinuxAppsSupportSwitchInput').change(function() {

enableLinuxNativeApps = this.checked;
localStorage.setItem('enableLinuxNativeApps', JSON.stringify(enableLinuxNativeApps));
setTimeout(function(){ appCategoryList(); }, 1000); //Delay so that the switch animation finishes first

});

$('#desktopStacksSwitchInput').change(function() {

console.log("desktop stacks enable triggered");
enableDesktopStacks = this.checked;

});

$('#hubImprovePerfomanceSwitchInput').change(function() {

	//console.log("improvePerfomanceMode triggered");
	improvePerfomanceMode = this.checked;
	localStorage.setItem('improvePerfomanceMode', JSON.stringify(improvePerfomanceMode));
		if (improvePerfomanceMode) {
			$("#bg_main").addClass("improvePerfomanceModeBody");
			executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/light_perfomance/kwinrc ~/.config/kwinrc");
		} else {
			$("#bg_main").removeClass("improvePerfomanceModeBody");
			executeNativeCommand("cp /usr/eXtern/systemX/Shared/CoreMsc/kwinrc ~/.config/kwinrc");
		}

	updateExtrabarPerfomanceMode();
	executeNativeCommand("qdbus org.kde.KWin /KWin reconfigure");
	appsUpdateData();

});

/*
$('.stackRadio').change(function() {
console.log("input triggered");
    if (this.value == 'Side Slide') {
        changeDesktopStackStyleTo('stack-sideslide')
    }
    else if (this.value == 'Peek-a-bo') {
        changeDesktopStackStyleTo('stack-peekaboo')
    }
});*/




if (stackStyle == "stack-sideslide") {
	$(':radio[name="stackRadio"][value="Side Slide"]').iCheck('check');
}

if (stackStyle == "stack-peekaboo") {
	$(':radio[name="stackRadio"][value="Peek-a-bo"]').iCheck('check');
}

if (stackStyle == "stack-fan") {
	$(':radio[name="stackRadio"][value="Fan"]').iCheck('check');
}

if (stackStyle == "stack-vertspread") {
	$(':radio[name="stackRadio"][value="Vertical Spread"]').iCheck('check');
}

$('input[name="stackRadio"]').on('ifChanged', function(event){
console.log("input triggered");
    if (this.value == 'Side Slide') {
        changeDesktopStackStyleTo('stack-sideslide')
    }
    else if (this.value == 'Peek-a-bo') {
        changeDesktopStackStyleTo('stack-peekaboo')
    }
    else if (this.value == 'Fan') {
        changeDesktopStackStyleTo('stack-fan')
    }
    else if (this.value == 'Vertical Spread') {
        changeDesktopStackStyleTo('stack-vertspread')
    }
});


//fallback: pactl set-default-sink 0 (maybe)


function muteAudioSinkToogle(sinkIndex) {
	var thisAudioDeviceMuteSwitch = $("#muteSwitchFor"+sinkIndex)[0];
	if ($(thisAudioDeviceMuteSwitch).hasClass("mutedAudio")) {
		executeNativeCommand("pactl set-sink-mute "+sinkIndex+" 0", function () {
			console.log("unmuted",thisAudioDeviceMuteSwitch);
			$(thisAudioDeviceMuteSwitch).empty();
			$(thisAudioDeviceMuteSwitch).removeClass("mutedAudio");
			$(thisAudioDeviceMuteSwitch).append(' <span class="icon">&#61849;</span>');
		});
	} else {
		executeNativeCommand("pactl set-sink-mute "+sinkIndex+" 1", function () {
			console.log("muted",thisAudioDeviceMuteSwitch);
			$(thisAudioDeviceMuteSwitch).empty();
			$(thisAudioDeviceMuteSwitch).addClass("mutedAudio");
			$(thisAudioDeviceMuteSwitch).append(' <span class="icon">&#61829;</span>');
		});			
	}
}


function setActiveProfile(sinkIndex,profileIndex,profileSelected) {

//audioDevices[i].profiles.data[j].key+":"+
//audioDevices[i].profiles.data[j].value.split(":")[0]

var profileName = profileSelected;

var profileOfInterest = allAudioDevices[sinkIndex].profiles.data[profileIndex].key+":"+allAudioDevices[sinkIndex].profiles.data[profileIndex].value.split(":")[0];

	console.log("profileOfInterest",profileOfInterest);

    var exec = require('child_process').exec,
                   child;
            child = exec('pactl set-card-profile '+sinkIndex+' '+profileOfInterest,function (error, stdout, stderr)
    {

    if (error !== null) {
      console.log('exec error: ' + error);
    } else {

		

		//activeProfile.icons = profileIcons;
            //$("#audio-device"+sinkIndex+"-selected-profile").empty();
            //$("#audio-device"+i+"-profiles").append('<li><a href="javascript:void(0);" onclick="setActiveProfile('+audioDevices[i].index.replace(" ","")+','+j+',&quot;'+profileName+'&quot;)" title="'+profileName+'">'+profileIcons+" "+profileName+'</a></li>');
            //$("#audio-device"+sinkIndex+"-selected-profile").append(activeProfile.icons+activeProfile.name+' ');
	//console.log("full command: pactl set-card-profile "+sinkIndex+' '+allProfiles[profileIndex].name);
	if (stdout.indexOf("Failed") == -1) {
        console.log("sink successfully set",stdout);

var profileIcons = "";
		if (profileName.indexOf("Output") != -1)
			profileIcons = '<span class="icon">&#61849;</span> ';
		if (profileName.indexOf("Input") != -1)
			profileIcons += '<span class="icon">&#61922;</span> ';
		if (profileName.indexOf("Duplex") != -1)
			profileIcons += '<span class="icon">&#61849;</span> <span class="icon">&#61922;</span> ';

		$("#audio-device"+sinkIndex+"-selected-profile").empty();

		 $("#audio-device"+sinkIndex+"-selected-profile").append(profileIcons+profileName+' ');




	/*$("#audio-device"+sinkIndex+"-selected-port").empty();
	$("#audio-device"+sinkIndex+"-selected-port").append(allPorts[portIndex].portIcons+' '+allPorts[portIndex].portFriendlyName+' ');*/
	} else {
        console.log("FAILED: ",stdout);
		//FIXME Do something, show an error
	}
    }
   });
}



function setActivePort(sinkIndex,portIndex) {

    var exec = require('child_process').exec,
                   child;
            child = exec('pacmd set-sink-port '+sinkIndex+' '+allPorts[portIndex].port,function (error, stdout, stderr)
    {

    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
	console.log("full command: pacmd set-sink-port "+sinkIndex+' '+allPorts[portIndex].port);
	if (stdout.indexOf("Failed") == -1) {
        console.log("sink successfully set",stdout);
	$("#audio-device"+sinkIndex+"-selected-port").empty();
	$("#audio-device"+sinkIndex+"-selected-port").append(allPorts[portIndex].portIcons+' '+allPorts[portIndex].portFriendlyName+' ');
	} else {
		//FIXME Do something, show an error
	}
    }
   });
}


function getActivePorts(callback,callbackData) {
    var exec = require('child_process').exec,
                   child;
            child = exec('pacmd list | grep "active port"',function (error, stdout, stderr)
    {

    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        var allLines = stdout.split("\n");
	var allActivePorts = [];
        
        allLines.forEach(function(entry) {
		var activePort = entry.split(": ")[1];
		if (activePort != null)
			allActivePorts.push(activePort);
	});
	console.log("allPorts",allActivePorts);
	callback(callbackData,allActivePorts);
    }
   });
}

//https://wiki.archlinux.org/index.php/PulseAudio/Examples#Set_the_default_output_source

function getActiveCard() {
    var exec = require('child_process').exec,
                   child;
            child = exec("pacmd list-sinks | grep -e 'index:'",function (error, stdout, stderr)
    {

    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        var allLines = stdout.split("\n");
        
        allLines.forEach(function(entry) {
		if (entry.indexOf("*") != -1)
			console.log("active card found index: ",entry);
	});
    }
   });
}

function deviceMuteStatus(audioDeviceIndex) {
		var thisAudioDeviceMuteSwitch = $("#muteSwitchFor"+audioDeviceIndex)[0];
		console.log("we are here: ",thisAudioDeviceMuteSwitch);
		executeNativeCommand("pacmd list-sinks |grep -A 15 'index: '"+audioDeviceIndex+"'' |awk '/muted/{ print $2}'",function (muteStatus) {
			console.log("muteStatus",muteStatus.indexOf("yes"));
			console.log("thisAudioDeviceMuteSwitch",thisAudioDeviceMuteSwitch);
			if (muteStatus.indexOf("yes") == 0) { //Default is no on audio device selector element creation, so we only need to modify if otherwise (since we only run this check on load)
				console.log("yes it's muted",thisAudioDeviceMuteSwitch);
				$(thisAudioDeviceMuteSwitch).empty();
				$(thisAudioDeviceMuteSwitch).addClass("mutedAudio");
				$(thisAudioDeviceMuteSwitch).append(' <span class="icon">&#61829;</span>');
			}

		});
}

function getAudioDevicesSinks(profileObjects,callback) {

    //https://askubuntu.com/questions/71863/how-to-change-pulseaudio-sink-with-pacmd-set-default-sink-during-playback
    var exec = require('child_process').exec,
                   child;
            child = exec("pacmd list-sinks | grep -e 'name:' -e 'index:'",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        var allLines = stdout.split("\n");

	for (var i = 0; i < allLines.length; i++) {
		if (allLines[i].indexOf("index:") == -1) {
			for (var k = 0; k < profileObjects.length; k++) {
				var profileNameNoClosingArrow = profileObjects[k].name.value.substring(profileObjects[k].name.value.indexOf("."),profileObjects[k].name.value.length-1);
				console.log("processing this line",allLines[i]);
				console.log("processing this lineB",profileNameNoClosingArrow);
				if (allLines[i].indexOf(profileNameNoClosingArrow) != -1) {
					if (allLines[i-1].indexOf("* index:") != -1) {
						profileObjects[k].isFallback = true;
					} else {
						if (profileObjects[k].isFallback == undefined)
						profileObjects[k].isFallback = false;
					}
					
				console.log("found at: ",allLines[i].indexOf(profileObjects[k].name.value));
				console.log("is default? ",allLines[i-1]);
				}
				console.log("processed line",allLines[i]);
			}
		}
		
	}
getActivePorts(callback,profileObjects);
        
 }

	
           
});
    
}


function getAudioDevices(callback) {

    var levels = [];
    var currentRootLevel = {};
    var currentLevelA = {};
    var currentLevelB = {};
    var currentLevelC = {};
    var currentLevelD = {};

    //https://askubuntu.com/questions/71863/how-to-change-pulseaudio-sink-with-pacmd-set-default-sink-during-playback
    var exec = require('child_process').exec,
                   child;
            child = exec("pacmd list-cards",function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        var allLines = stdout.split("\n");
        
        allLines.forEach(function(entry) {
            if (entry.indexOf("				") == 0) {
                if (entry.indexOf(" = ") != -1) {
                    var objectKey = entry.split(" = ")[0].replace("				","");
                    var objectValue = entry.replace("				"+objectKey,"").replace(" = ","");
                } else {
                    var objectKey = entry.split(":")[0].replace("				","");
                    var objectValue = entry.replace("				"+objectKey,"").replace(":","");
                }
                
                var currentLevelDObject = {
                    key: objectKey,
                    value: objectValue,
                    data: []
                }

                currentLevelC[objectKey] = currentLevelDObject;
                currentLevelD = currentLevelC[objectKey];
            } else if (entry.indexOf("			") == 0) {
                if (entry.indexOf(" = ") != -1) {
                    var objectKey = entry.split(" = ")[0].replace("			","");
                    var objectValue = entry.replace("			"+objectKey,"").replace(" = ","");
                } else {
                    var objectKey = entry.split(":")[0].replace("			","");
                    var objectValue = entry.replace("			"+objectKey,"").replace(":","");
                }
                
                var currentLevelCObject = {
                    key: objectKey,
                    value: objectValue,
                    data: []
                }

                currentLevelB[objectKey] = currentLevelCObject;
                currentLevelC = currentLevelB[objectKey];
            } else if (entry.indexOf("		") == 0) {
                if (entry.indexOf(" = ") != -1) {
                    var objectKey = entry.split(" = ")[0].replace("		","");
                    var objectValue = entry.replace("		"+objectKey,"").replace(" = ","");
                } else {
                    var objectKey = entry.split(":")[0].replace("		","");
                    var objectValue = entry.replace("		"+objectKey,"").replace(":","");
                }
                
                var currentLevelBObject = {
                    key: objectKey,
                    value: objectValue,
                    data: []
                }

                /*For Profiles, put everything under data as they all have the same "key"*/
                if (objectKey == "output") {
                    currentLevelA.data.push(currentLevelBObject);
                    currentLevelB = currentLevelA.data[currentLevelA.data.length-1];
                } else {
                    currentLevelA[objectKey] = currentLevelBObject;
                    currentLevelB = currentLevelA[objectKey];
                }
                
            } else if (entry.indexOf("    ") == 0)
            {

                var rootLevelObject = {
                    index: entry.split(":")[1]
                }

                levels.push(rootLevelObject);
                currentRootLevel = levels[levels.length-1]
            } else if (entry.indexOf("	") == 0) {
                var objectKey = entry.split(":")[0].replace("	","");
                var objectValue = entry.replace("	"+objectKey,"").replace(":","").replace(" ","");
                var currentLevelAObject = {
                    key: objectKey,
                    value: objectValue,
                    data: []
                }

                currentRootLevel[objectKey] = currentLevelAObject;
                currentLevelA = currentRootLevel[objectKey];
            }
            //console.log(entry);
        });

	getActiveCard();

        if (callback != null) {
		getAudioDevicesSinks(levels,callback);
            
            //callback(levels);
        }

        //console.log("levels",levels);
        //console.log("allLines",allLines);
    }       
});
    
}

function showMoreAudioDeviceInfo(deviceDiv) {
	//console.log("showMoreAudioDeviceInfo",$(deviceDiv).prev());
	if ($(deviceDiv).prev().hasClass("zeroHeight")) {
		$(deviceDiv).prev().removeClass("zeroHeight");
		$(deviceDiv).children().children().text("VIEW LESS");
	} else {
		$(deviceDiv).prev().addClass("zeroHeight");
		$(deviceDiv).children().children().text("VIEW MORE");
	}
	//console.log("children",);
}

var allPorts = [];
var allAudioDevices;

function setAudioCurrentSettings(audioDevices,allActivePorts) {
	allAudioDevices = audioDevices;
	console.log("audioDevices",audioDevices);
	$("#allAudioHardware").empty();

    for (var i = 0; i < audioDevices.length; i++) {
        var deviceName = audioDevices[i].properties["device.description"].value;
	deviceName = deviceName.substring(1,deviceName.length).substring(0,deviceName.length-2);
	var activeProfileInfoTemp = audioDevices[i]["active profile"].value.split(/:(.+)/)[1];
	console.log("activeProfileInfoTemp",activeProfileInfoTemp);

	var fallBackSelectedClass = "";
	console.log("audioDevices[i]",audioDevices[i]);

	if (audioDevices[i].isFallback)
		fallBackSelectedClass = "fallbackBtnSelected";

            var audioDeviceInfoToAppend = '<h4 class="block-title">'+deviceName+'</h4> <a id="muteSwitchFor'+audioDevices[i].index.replace(/\s/g, '')+'" href="#" class="btn btn-alt fallbackBtn" onclick="muteAudioSinkToogle('+audioDevices[i].index.replace(/\s/g, '')+')"> <span class="icon">&#61849;</span></a> <a href="#" class="btn btn-alt fallbackBtn '+fallBackSelectedClass+'"> <span class="icon">&#61874;</span></a>'+
                                        '<div class="dropdown_container" style="padding-right:5px; position:relative;">'+
                                            '<h5 style="display:inline-block;">Profile: </h5>'+
                                            '<div class="btn-group force_right">'+
                                                '<button class="btn btn-alt dropdown-toggle" type="button" data-toggle="dropdown">'+
                                                    '<span id="audio-device'+i+'-selected-profile"></span>'+
                                                    '<span class="caret"></span>'+
                                                '</button>'+
                                                '<ul id="audio-device'+i+'-profiles" class="dropdown-menu" role="menu">'+
                                                '</ul>'+
                                            '</div>'+
                                        '</div>'+
                                        '<div class="dropdown_container" style="margin-top: 20px; padding-right:5px; position:relative;">'+
                                            '<h5 style="display:inline-block;">Connector: </h5>'+
                                            '<div class="btn-group force_right">'+
                                                '<button class="btn btn-alt dropdown-toggle" type="button" data-toggle="dropdown">'+
                                                    '<span id="audio-device'+i+'-selected-port"></span>'+
                                                    '<span class="caret"></span>'+
                                                '</button>'+
                                                '<ul id="audio-device'+i+'-ports" class="dropdown-menu" role="menu">'+
                                                '</ul>'+
                                            '</div>'+
                                        '</div>'+
					'<div class="tile audioDevicesTile">'+
					'<div class="innerTile zeroHeight">';

				if (audioDevices[i].properties["alsa.card_name"] != null)
				audioDeviceInfoToAppend += '<p><b>Card Name: </b> '+audioDevices[i].properties["alsa.card_name"].value.substring(1,audioDevices[i].properties["alsa.card_name"].value.length-1)+'</p>';

				if (audioDevices[i].properties["device.form_factor"] != null)
				audioDeviceInfoToAppend += '<p><b>Device Form Factor: </b> '+audioDevices[i].properties["device.form_factor"].value.substring(1,audioDevices[i].properties["device.form_factor"].value.length-1)+'</p>';

				if (audioDevices[i].properties["device.bus"] != null)
				audioDeviceInfoToAppend += '<p><b>Device Bus: </b> <span class="text-uppercase" style="text-transform: uppercase;">'+audioDevices[i].properties["device.bus"].value.substring(1,audioDevices[i].properties["device.bus"].value.length-1)+'</span></p>';

				if (audioDevices[i].properties["device.product.name"] != null)
				audioDeviceInfoToAppend += '<p><b>Device Product Name: </b> '+audioDevices[i].properties["device.product.name"].value.substring(1,audioDevices[i].properties["device.product.name"].value.length-1)+'</p>';

				if (audioDevices[i].properties["device.vendor.name"] != null)
				audioDeviceInfoToAppend += '<p><b>Device Ventor Name: </b> '+audioDevices[i].properties["device.vendor.name"].value.substring(1,audioDevices[i].properties["device.vendor.name"].value.length-1)+'</p>';
					audioDeviceInfoToAppend += '</div>'+
                                    '<div class="media p-5 text-center l-100" onclick="showMoreAudioDeviceInfo(this)">'+
                                        '<a href="#"><small>VIEW MORE</small></a>'+
					'</div>'+
                                    '</div>';


			$("#allAudioHardware").append(audioDeviceInfoToAppend);
			deviceMuteStatus(audioDevices[i].index.replace(/\s/g, ''));
			
	var activeProfile = {
				id: activeProfileInfoTemp.substring(0,activeProfileInfoTemp.length-1), //Remove the last ">"
				name: "",
				icons: ""
			}
	//activeProfile = activeProfile.substring(0,activeProfile.length-1); //Remove the last ">"
	console.log("activeProfile",activeProfile);
        console.log("deviceName",deviceName);
        for (var j = 0; j < audioDevices[i].profiles.data.length; j++) {
		var profileName = audioDevices[i].profiles.data[j].value.split(/:(.+)/)[1].split(" (priority")[0];
		var profTest = audioDevices[i].profiles.data[j].value.split(":");
		if (profTest.length == 4) {
			profileName = profileName.split(/:(.+)/)[1];
		}

		if (audioDevices[i].profiles.data[j].value.indexOf(activeProfile.id) == 0)
			activeProfile.name = profileName;

		//console.log("profTest",profTest);
		if (audioDevices[i].profiles.data[j].value.indexOf("available: unknown") > 0) {
			//profileName += " (unplugged)"; //FIXME:Nope apparently this doesn't mean it's unplugged. Figure out another way to find out
		}
		//console.log("test",profileName);
            //var profileNameSplitA = audioDevices[i].profiles.data[j].value.split(":;
		var profileIcons = "";
		if (profileName.indexOf("Output") != -1)
			profileIcons = '<span class="icon">&#61849;</span> ';
		if (profileName.indexOf("Input") != -1)
			profileIcons += '<span class="icon">&#61922;</span> ';
		if (profileName.indexOf("Duplex") != -1)
			profileIcons += '<span class="icon">&#61849;</span> <span class="icon">&#61922;</span> ';

		activeProfile.icons = profileIcons;
            $("#audio-device"+i+"-selected-profile").empty();
            $("#audio-device"+i+"-profiles").append('<li><a href="javascript:void(0);" onclick="setActiveProfile('+audioDevices[i].index.replace(" ","")+','+j+',&quot;'+profileName+'&quot;)" title="'+profileName+'">'+profileIcons+" "+profileName+'</a></li>');
            $("#audio-device"+i+"-selected-profile").append(activeProfile.icons+activeProfile.name+' ');
        }
	if (audioDevices[i].profiles.input != null) {
        for (var j = 0; j < audioDevices[i].profiles.input.length; j++) { //for inputs
		var profileName = audioDevices[i].profiles.input[j].value.split(/:(.+)/)[1].split(" (priority")[0];
		var profTest = audioDevices[i].profiles.input[j].value.split(":");
		if (profTest.length == 4) {
			profileName = profileName.split(/:(.+)/)[1];
		}
		var profileIcons = "";
		if (profileName.indexOf("Output") != -1)
			profileIcons = '<span class="icon">&#61849;</span> ';
		if (profileName.indexOf("Input") != -1)
			profileIcons += '<span class="icon">&#61922;</span> ';
		if (profileName.indexOf("Duplex") != -1)
			profileIcons += '<span class="icon">&#61849;</span> <span class="icon">&#61922;</span> ';
           $("#audio-device"+i+"-profiles").append('<li><a href="javascript:void(0);" onclick="setActiveProfile('+audioDevices[i].index.replace(" ","")+','+(allPorts.length-1)+')" title="'+profileName+'">'+profileIcons+" "+profileName+'</a></li>');

	}
	}



	
	for (var key in audioDevices[i].ports) {
		if (key != "data" && key != "key" && key != "value") {
    		var port = audioDevices[i].ports[key];
		var portFriendlyName = port.value.split(" (priority")[0];
		console.log("port: ",port);
		var portIcons = "";
		if (port.properties["device.icon_name"].value == '"video-display"')
			portIcons = '<span class="icon">&#61729;</span> ';
		if (port.properties["device.icon_name"].value == '"audio-input-microphone"')
			portIcons += '<span class="icon">&#61922;</span> ';
		if (port.properties["device.icon_name"].value == '"audio-speakers"')
			portIcons += '<span class="icon">&#61849;</span> ';
		if (port.properties["device.icon_name"].value == '"audio-headphones"')
			portIcons += '<span class="icon">&#61848;</span> ';
		var portObject = { 
				portFriendlyName: portFriendlyName,
				portIcons: portIcons,
				port: key.replace(" ","")
		}

		allPorts.push(portObject);

	console.log("portFriendlyName:'"+portFriendlyName+"'");
            
            $("#audio-device"+i+"-ports").append('<li><a href="javascript:void(0);" onclick="setActivePort('+audioDevices[i].index.replace(" ","")+','+(allPorts.length-1)+')" title="'+portFriendlyName+'">'+portIcons+' '+portFriendlyName+'</a></li>');
		for (var j = 0; j < allActivePorts.length; j++) {
			var fullKey = "<"+key+">";
			if (fullKey == allActivePorts[j]) {
				$("#audio-device"+i+"-selected-port").empty();
				$("#audio-device"+i+"-selected-port").append(portIcons+' '+portFriendlyName+' ');
				if (fallBackSelectedClass !="")
					updateAudioDeviceExtrabarInfo(deviceName,portIcons,portFriendlyName);
			}
		}
            
		}
	}
	console.log("gets here A");
        
    }

}


function openAppearanceSettings() {
    if (currentSysSettingsMenu !="sys_appearance")
    {
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_appearance").fadeIn();
        currentSysSettingsMenu = "sys_appearance";
    }
}

//win.showDevTools();
//console.log("win.showDevTools();");

var defaultFont = { fontName: "Open Sans light", fontId:"open-sans-light", size: 14, spinnerSelector: '.spinner-1', fontNameDiv: "#defaultFontName"};

var headerOneFont = { fontName: "Open Sans light", fontId:"open-sans-light", size: 14, spinnerSelector: '.spinner-1', fontNameDiv: "#defaultFontName"};


function setFontSize(newFontSize,fontObject) {
 //(function(){
                    //Basic
                    $(fontObject.spinnerSelector).spinedit('setValue', newFontSize);
                    fontObject.size = newFontSize;
                    $(fontObject.fontNameDiv).text(fontObject.fontName);
                    $(fontObject.fontNameDiv).attr("title",fontObject.fontName);			
			
                    
                    $(fontObject.spinnerSelector).on("valueChanged", function (e) {
                        //console.log(e.value);
			fontObject.size = e.value;
			//editor.updateOptions({ fontSize: e.value});
                    });
                    
                //})();
}

//onload = function() {



//}

function openChangeAvatarWindow() {
	$("#changeAvatarWindow").removeClass("hidden");
	$(".selected-btn").removeClass("selected-btn");
	$("#changeAvatar").addClass("selected-btn");
}

function closeChangeAvatarWindow() {
	$("#changeAvatarWindow").addClass("hidden");
	$(".selected-btn").removeClass("selected-btn");
}

$('.avatar-selector').on('click', function() {
    $(".avatar-selector").removeClass("selectedAvatar");
    $(this).addClass("selectedAvatar");
});

function openUserImageSelector() {
	$("#userImageSelector").trigger("click");
}

function applyNewUserImage(imageLocation) {
child = exec('convert "'+imageLocation+'" -thumbnail 300  "/usr/eXtern/systemX/Shared/temp/newUserImage.png"',function (error, stdout, stderr)
    {

//console.log("done..");

     		//console.log("getThumb",getThumb);

		
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {

	console.log("image applied");

	$("#mainAvatarPreview").attr("src","file:///usr/eXtern/systemX/Shared/temp/newUserImage.png");



	}


	});
}

function confirmUserDetails() {

}

function attemptTosetUserDetails() {
        var newUserDetails = userDetails;

	newUserDetails.name = $("#userName").val();

	if ($("#userNewPassword").val() != "")
		newUserDetails.password = $("#userNewPassword").val();

//{username:"extern", name: $("#userName").val(), avatar: $(".selectedAvatar > img").attr("avatarName"),password: $("#userPassword").val()};
        console.log("USER DETAILS",newUserDetails);
	//$("#letsGoButton").attr('disabled','disabled');
        setUserDetails(newUserDetails,$("#userPassword").val(),confirmUserDetails);
}

function checkPassword() {
	//wrong password add class .invalid-password

	var sudo = require('sudo-js');

	sudo.setPassword($("#userPassword").val());

	sudo.check(function(valid) {
		console.log("password valid: ",valid);

		if (valid) {
			$("#incorrectPassword").addClass("hidden");
			$("#updateUserDetails").attr('disabled',true);
			attemptTosetUserDetails();
		} else {
			$("#incorrectPassword").removeClass("hidden");
		}
	});
	
}

function openFontsSettings() {
    if (currentSysSettingsMenu !="sys_fonts")
    {
	//$("#userPassword").text("123456789"); //replace password with fake
	chrome.fontSettings.getFontList(function (fonts) {
	for (var i = 0; i < fonts.length; i++) {
		$(".allFontsList").append('<li> <a href="javascript:void(0);" title="'+fonts[i].displayName+'"> '+fonts[i].displayName+' </a> </li>');
	}
	console.log("fonts",fonts);
});
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_fonts").fadeIn();
        currentSysSettingsMenu = "sys_fonts";
    }
}


function openUserProfileSettings() {
    if (currentSysSettingsMenu !="sys_user_accounts")
    {
	$("#userName").val(userDetails.name);
	//$("#userPassword").text("123456789"); //replace password with fake
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_user_accounts").fadeIn();
        currentSysSettingsMenu = "sys_user_accounts";
    }
}

function openHubAndDesktopSettings() {
    if (currentSysSettingsMenu !="sys_hub_desktop")
    {
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_hub_desktop").fadeIn();
        currentSysSettingsMenu = "sys_hub_desktop";
    }
}

function openAdvancedSettings() {
	if (currentSysSettingsMenu !="sys_advatnced_settings")
    {
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_advatnced_settings").fadeIn();
        currentSysSettingsMenu = "sys_advatnced_settings";
    }
}

function openUnknownSettings() {
if (currentSysSettingsMenu !="sys_unavailable")
    {
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_unavailable").fadeIn();
        currentSysSettingsMenu = "sys_unavailable";
    }
}

function logAudioDevicesSinks(allSinks) {
	console.log("allSinks",allSinks);
}


function openAudioSettings() {
    if (currentSysSettingsMenu !="sys_audio")
    {
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_audio").fadeIn();
        currentSysSettingsMenu = "sys_audio";
	getAudioDevices(setAudioCurrentSettings);
	
    }
}

function getDisplayName (display) {
    var displayName = "";
                
                if (display.model !="")
                    displayName = display.model;
                else
                    displayName = display.resolutionx+" X "+display.resolutiony;


                
                if (display.builtin) {
                    if (displayName != "") {
                        displayName = "Laptop Monitor ("+displayName+")";
                    }
                    else
                        displayName = "Laptop Monitor";
                }
    return displayName;
}


function addDisplayOptions(displays,autoApply) {

console.log("displays!",displays);
     var exec = require('child_process').exec,
                   child;
            //child = exec("xrandr --query",function (error, stdout, stderr)
            child = exec('xrandr --listactivemonitors',function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
       var lines = stdout.split("\n").filter( function(val){ 
    return val.indexOf( "+" ) != -1; //DIsplays only
  });
        //console.log("SPLIT LINES",lines);
        
        //var displayConnection = lines[0].split("  ");
        //console.log("displayConnection "+displayConnection[1]);
        try {
        for (i = 0; i < displays.length; i++) {
            
            if (lines[0].indexOf(displays[i].connection) != -1) {
                $("#mainMonitorDropdown").text(getDisplayName(displays[i]));

				

		selectedDisplayResolution = {
			width: displays[i].work_area.width,
			height: displays[i].work_area.height,
			refreshRate: 0,
			connection: displays[i].connection,
			pos: i
		}

                currentDisplay = displays[i].connection;

		console.log("main monitor set",displays[i]);

		loadDisplayResolutionOptions(currentDisplay);


                if (autoApply && lines.length > 1)
                    enableThisDisplayOnly(currentDisplay);
            }
        }
        } catch (e) {
        console.log("An erro pccured loading display data");
        }
        
        
        
        
        
        
        
       
        
    }       
});
    
}

function pavucontrol() {
    
    var exec = require('child_process').exec,
                   child;
            child = exec('pavucontrol',function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
    }  
    
});
//win.hide();
win.hideFixed();
        win.minimized = true; 
}

function updateBrightness() {
    var brightnessVal = brightnessSlider.getValue();

	//console.log("brightnessVal: ",brightnessVal);

	changeBrightness(brightnessVal);
}

//https://www.npmjs.com/package/node-brightness
function updateGamma() {
    var gammaVal = gammaSlider.getValue();
	changeGamma(gammaVal);
}

    if (localStorage.getItem('closeButtonProperties') != null) {
	var closeButtonProperties = JSON.parse(localStorage.getItem('closeButtonProperties')); 
    } else {
	var closeButtonProperties = {
		xOffset: null,
		yOffset: null,
		opacity: 30,
	}
    }
//console.log("closeButtonProperties.opacity",closeButtonProperties.opacity);
//console.log("parseInt(closeButtonProperties.opacity)",parseInt(closeButtonProperties.opacity));
$('#closeButtonOpacitySlider').slider( 'setValue', closeButtonProperties.opacity );

function updateCloseButtonOpacity() {

closeButtonProperties.opacity = closeButtonOpacitySlider.getValue();
    $("#sample_custom_close_button").css('opacity', closeButtonProperties.opacity);

    for (i = 1; i < runningApps.length; i++)
    {
	$(runningApps[i].windowObject.close_button).css('opacity', closeButtonProperties.opacity);
    }

  localStorage.setItem('closeButtonProperties', JSON.stringify(closeButtonProperties));

}

var closeButtonOpacitySlider = $('#closeButtonOpacitySlider').slider()
		.on('slide', updateCloseButtonOpacity)
		.data('slider');


    if (localStorage.getItem('windowBoxShadow') != null) {
	var windowBoxShadow = JSON.parse(localStorage.getItem('windowBoxShadow')); 
    } else {
	var windowBoxShadow = {
		xOffset: 0,
		yOffset: 0,
		blur: 30,
		color: "rgba(0, 0, 0, 1)"
		
	}
    }

$('#shadowBlur').slider( 'setValue', parseInt(windowBoxShadow.blur) );

function updateShadowBlur() {

windowBoxShadow.blur = shadowBlurSlider.getValue();
    $("#sampleCustomWindow").css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);
   $("#winShadowColourPicker").parent().css("background-color",windowBoxShadow.color);

    for (i = 1; i < runningApps.length; i++)
    {

	$(runningApps[i].windowObject.outerBodyBackground[0]).css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

$(runningApps[i].windowObject.outerBodyBackground[0]).next().css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

    }

  localStorage.setItem('windowBoxShadow', JSON.stringify(windowBoxShadow));

}


var shadowBlurSlider = $('#shadowBlur').slider()
		.on('slide', updateShadowBlur)
		.data('slider');

	$("#winShadowColourPicker").val(windowBoxShadow.color);
	$("#winShadowColourPicker").parent().css("background-color",windowBoxShadow.color);

	$("#sampleCustomWindow").css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

$("#sampleCustomWindow").css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

    if (localStorage.getItem('windowBackgroundColor') != null) {
	var windowBackgroundColor = JSON.parse(localStorage.getItem('windowBackgroundColor')); 
    } else {
	var windowBackgroundColor = "rgba(0,0,0,0.6)";
    }
	$("#winBackgroundColourPicker").val(windowBackgroundColor);
	$("#winBackgroundColourPicker").parent().css("background-color",windowBackgroundColor);
	$("#sampleCustomWindow").css('background-color', windowBackgroundColor);



$(document).ready(function() {

  $("#userImageSelector").change(function(evt) {
	console.log("still triggered");
	if ($(this).val() != "") {
		applyNewUserImage($(this).val());
	}

	choosingNewProjectLocation = false;
  });

    $('#userPassword').on('input', function() {

		console.log("password input changed"); 
	    if ($('#userPassword').val() != "") {
			//FIXME: RESTORE THIS $("#updateUserDetails").removeAttr('disabled');
		} else {
			$("#updateUserDetails").attr('disabled',true);
		}
	});

setFontSize(defaultFont.size,defaultFont);
    $("#winShadowColourPicker").on('change keydown paste input', function(){
    winShadowColourPickerChanged()
});

});

function winBackgroundColorPickerChanged() {
    //console.log("colour changed to: ");
    windowBackgroundColor = $("#winBackgroundColourPicker").val();
    $("#sampleCustomWindow").css('background-color', windowBackgroundColor);
   $("#winBackgroundColourPicker").parent().css("background-color",windowBackgroundColor);

//console.log("win win winA",runningApps[2]);

    for (i = 1; i < runningApps.length; i++)
    {

	$(runningApps[i].windowObject.outerBodyBackground[0]).next().css('background-color', windowBackgroundColor);

    }

  localStorage.setItem('windowBackgroundColor', JSON.stringify(windowBackgroundColor));

}

function winShadowColourPickerChanged() {
    //console.log("bg colour changed to: ");
    windowBoxShadow.color = $("#winShadowColourPicker").val();
    $("#sampleCustomWindow").css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);
   $("#winShadowColourPicker").parent().css("background-color",windowBoxShadow.color);

    for (i = 1; i < runningApps.length; i++)
    {

	$(runningApps[i].windowObject.outerBodyBackground[0]).css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

$(runningApps[i].windowObject.outerBodyBackground[0]).next().css('box-shadow', windowBoxShadow.xOffset+'px '+windowBoxShadow.yOffset+'px '+windowBoxShadow.blur+'px '+windowBoxShadow.color);

    }

  localStorage.setItem('windowBoxShadow', JSON.stringify(windowBoxShadow));

}






var gammaSlider = $('#gammaSlider').slider()
		.on('slide', updateGamma)
		.data('slider');

var brightnessSlider = $('#brightnessSlider').slider()
		.on('slide', updateBrightness)
		.data('slider');

	$('#brightnessSlider').slider( 'setValue', displayBrightness );


//Set correct value on load for the blur options in Hub -> Settings -> Appearance -> Window Background
$('#wallpaperBlur').slider( 'setValue', parseInt(JSON.parse(localStorage.getItem('wallpaperBlurEffect'))) );

function updatewallpaperBlur() {
    var wallpaperBlurVal = wallpaperBlurSlider.getValue();

  localStorage.setItem('wallpaperBlurEffect', JSON.stringify(wallpaperBlurVal));

wallpaper.get().then(imagePath => {
	//console.log("WALLPAPER C: ",imagePath);
	$.blurWin(imagePath);
	//console.log("LOL IMG",imagePath);
});

}



var wallpaperBlurSlider = $('#wallpaperBlur').slider()
		.on('slide', updatewallpaperBlur)
		.data('slider');


    if (localStorage.getItem('winButtonProperties') != null) {
	var winButtonProperties = JSON.parse(localStorage.getItem('winButtonProperties')); 
    } else {
	var winButtonProperties = { //For Beta 2 we will only use border (running out of time)
		backgroundColor: "rgba(255, 255, 255, 0)",
		hoverBackgroundColor: "rgba(255, 255, 255, 0.8)",
		borderColor: "rgba(255, 255, 255, 0.31)",
		hoverBorderColor: "rgba(255, 255, 255, 0.8)",
		textShadow: "0 0 10px rgba(0, 0, 0, 0.75);",
		color: "rgba(255, 255, 255, 1)"
	}
    }
	$("#winButtonBorderColourPicker").val(winButtonProperties.borderColor);
	$("#winButtonBorderColourPicker").parent().css("background-color",winButtonProperties.borderColor);
	$("#sampleWindowButton").css("cssText","border-color: "+winButtonProperties.borderColor+" !important;");


    if (localStorage.getItem('winTextColourProperties') != null) {
	var winTextColourProperties = JSON.parse(localStorage.getItem('winTextColourProperties')); 
    } else {
	var winTextColourProperties = {
			generalTextColor: "rgba(255, 255, 255, 1)",
			headingsTextColor: "rgba(255, 255, 255, 1)",
			sidebarTextColor: "rgba(255, 255, 255, 1)"
	}
    }
	$("#winTextColourPicker").val(winTextColourProperties.generalTextColor);
	$("#winTextColourPicker").parent().css("background-color",winTextColourProperties.generalTextColor);
	$("#sampleCustomWindow").css("color",winTextColourProperties.generalTextColor);

	$("#winHeadingsTextColourPicker").val(winTextColourProperties.headingsTextColor);
	$("#winHeadingsTextColourPicker").parent().css("background-color",winTextColourProperties.headingsTextColor);
	//$("#sampleCustomWindow").css("color",winTextColourProperties.generalTextColor);

	$("#winSidebarTextColourPicker").val(winTextColourProperties.sidebarTextColor);
	$("#winSidebarTextColourPicker").parent().css("background-color",winTextColourProperties.sidebarTextColor);
	//$("#sampleCustomWindow").css("color",winTextColourProperties.generalTextColor);


function winTextColourChanged() {
	winTextColourProperties.generalTextColor = $("#winTextColourPicker").val();
	$("#sampleCustomWindow").css("color",winTextColourProperties.generalTextColor);

    for (i = 1; i < runningApps.length; i++)
    {
	$(runningApps[i].windowObject.window.frames.document).contents().find("head")
      .append($("<style type='text/css'>  div,p,span,h1,h2,h3,h4,h5,a {color: "+winTextColourProperties.generalTextColor+" !important;}  </style>"));

    }

	localStorage.setItem('winTextColourProperties', JSON.stringify(winTextColourProperties));
}

function winTextHeadingColourChanged() {
	winTextColourProperties.headingsTextColor = $("#winHeadingsTextColourPicker").val();
	//$("#sampleCustomWindow").css("color",winTextColourProperties.headingsTextColor);

    for (i = 1; i < runningApps.length; i++)
    {
	$(runningApps[i].windowObject.window.frames.document).contents().find("head")
      .append($("<style type='text/css'>  h1,h2,h3,h4,h5 {color: "+winTextColourProperties.generalTextColor+" !important;}  </style>"));

    }

	localStorage.setItem('winTextColourProperties', JSON.stringify(winTextColourProperties));
}





function winButtonBorderColorChanged() {
	winButtonProperties.borderColor = $("#winButtonBorderColourPicker").val();
	$("#sampleWindowButton").css("cssText","border-color: "+winButtonProperties.borderColor+" !important;");

    for (i = 1; i < runningApps.length; i++)
    {
	$(runningApps[i].windowObject.window.frames.document).contents().find("head")
      .append($("<style type='text/css'>  .btn { border-color: "+winButtonProperties.borderColor+" !important;}  </style>"));

    }

	localStorage.setItem('winButtonProperties', JSON.stringify(winButtonProperties));
}

/*
var resolutionSlider = $('#resolutionSlider').slider()
		.on('slide', updateResolution)
		.data('slider');*/

//.slider("values", "0", 25); //min

//resolutionSlider.slider("values", "1", 35); //max

//console.log("resolutionSlider",resolutionSlider);

//resolutionSlider.max = 30;

//$('#resolutionSlider').slider("option", "max", 30);

//$('#resolutionSlider').attr("data-slider-max",30);

//$('#resolutionSlider').slider( "refresh" );


function updateResolution() {
    /*var resolutionVal = resolutionSlider.getValue();
    console.log("resolutionUpdated",resolutionVal);*




    
    /*var exec = require('child_process').exec,
                   child;
            //child = exec("xrandr --query",function (error, stdout, stderr)
            child = exec('xgamma -gamma '+gammaVal,function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        
     $("#gammaPercentage").text(((gammaVal*100).toFixed(2)).replace(/\.00$/,'')+"%");
        
        
        
        
        
        
        
       
        
    }       
});*/
}

function readjustSystemPanelsSizes() {
	runningApps[0].windowObject.setMinimumSize(screen.width, 69)
	runningApps[0].windowObject.width = screen.width;
	runningApps[0].windowObject.repositionWindow();
	//console.log("Sys Panels readjusted screen:"+screen.width+" pwidth: "+runningApps[0].windowObject.width);
}

function readjustHubSize() {
	if (screen.width < 1156) {
		win.width = screen.width;
		//console.log("Hub width readjusted");
	} else {
		win.width = 1156;
	}

	if (screen.height < 716) {
		win.height = screen.height;
		//console.log("Hub height readjusted");
	} else {
		win.height = 716;
	}
}

function reAdjustSystemAppsResolution() {
	//chrome.runtime.reload(); //FIXME use this for now

/*
	runningApps[0].desktopObject.close(true);//adjustDisplayResolution();

	setTimeout(function() { desktop();}, 50); 

	setTimeout(function() { $("#monitorResolutionDropdown").text(screen.width+" X "+screen.height); readjustSystemPanelsSizes(); window.exploreBarWin.openHubs(); readjustHubSize(); reloadWallpaper(); reloadWallpaper(); }, 2000); 

	//setTimeout(function() {  }, 2300);

	//setTimeout(function() {  }, 5300);

	setTimeout(function() { console.log("lets try again"); readjustSystemPanelsSizes(); window.exploreBarWin.openHubs(); }, 5400); 

*/
	
}


function selectMonitor(monitorId,displayName,displaySelected) {
	currentDisplay = displaySelected;
	$(".selectedMonitor").removeClass("selectedMonitor");
	$(`#draggableMonitor${monitorId}`).addClass("selectedMonitor");
	$("#selectedMonitorTitle").text(displayName);
	if (screens[monitorId] != null) {
		$("#monitorResolutionDropdown").text(screens[monitorId].work_area.width+" X "+screens[monitorId].work_area.height);
		$("#monitorResolutionDropdown").parent().prop('disabled', false);
		$("#refreshRate").parent().prop('disabled', false);
		
	} else {
		$("#monitorResolutionDropdown").parent().prop('disabled', true);
		$("#refreshRate").parent().prop('disabled', true);
	}

	console.log("enabledScreens: ",enabledScreens);

	if (enabledScreens[monitorId]) {
		$('#monitorEnabled').parent().removeClass("switch-off"); 
		$('#monitorEnabled').parent().addClass("switch-on"); 
		$('#monitorEnabled').iCheck('update');
	} else {
		$('#monitorEnabled').parent().removeClass("switch-on"); 
		$('#monitorEnabled').parent().addClass("switch-off"); 
	}
    	loadDisplayResolutionOptions(displaySelected);
}

var gui = require('nw.gui');
//init must be called once during startup, before any function to gui.Screen can be called
gui.Screen.Init();
var screens = gui.Screen.screens;
//screens = screensx;
var enabledScreens = [];
var allScreenInfo = [];


var screenCB = {
	onDisplayBoundsChanged: function(screen) {
	  for (var i = 0; i < screens.length; i++) {
		  if (screens[i].id == screen.id) {
			screens[i] = screen;
			//screens.splice(i, 1);
			  break;
		  }
	  }

	  console.log("screens: ",screens);
	  console.log('displayBoundsChanged', screen);
	},
  
	onDisplayAdded: function(screen) {
		let searchIfExists = screens.filter(el => el.id == screen.id);

		if (searchIfExists.length == 0) {
			screens.push(screen);
		}
  
	  console.log('displayAdded', screen);
	  console.log("screens: ",screens);
	},
  
	onDisplayRemoved: function(screen) {
	  screens = screens.filter(el => el.id !== screen.id);
	  console.log('displayRemoved', screen)
	}
  };
  
  // listen to screen events
  gui.Screen.on('displayBoundsChanged', screenCB.onDisplayBoundsChanged);
  gui.Screen.on('displayAdded', screenCB.onDisplayAdded);
  gui.Screen.on('displayRemoved', screenCB.onDisplayRemoved);

function loadDisplayInformation() {
	$("#monitorResolutionDropdown").text(screen.width+" X "+screen.height);
        
        si.graphics(function(data) {
            if (data.displays.length > 1)
                $("#allDisplays").addClass("multimonitors");
            else
                $("#allDisplays").removeClass("multimonitors");
            
            $("#allDisplays").empty();
            $("#primaryMonitorDropdownOptions").empty();

		let displays = data.displays;
		let maxWidth = 0;
		let maxHeight = 0;
		console.log("AAAA displaysss: ",data.displays);
		allScreenInfo = data.displays;
		enabledScreens = [];

		$("#monitorsDropdown").empty();
            
            for (var i = 0; i < data.displays.length; i++) {
                
                var displayName = getDisplayName(data.displays[i]);

				//screens[i].enabled = data.displays[i].enabled;

				enabledScreens.push(data.displays[i].enabled);

				$("#monitorsDropdown").append(`
				<li>
					<a href="javascript:void(0);" onclick="selectMonitor(${i},&quot;${displayName}&quot;,&quot;${data.displays[i].connection}&quot;)"><span class="icon">&#61729;</span> ${displayName}</a>
				</li>`);
                    
                if (i == 0) {

					if (data.displays[i].enabled) {
						$('#monitorEnabled').parent().removeClass("switch-off"); 
						$('#monitorEnabled').parent().addClass("switch-on"); 
						$('#monitorEnabled').iCheck('update');
						$("#allDisplays").append(`<div id="draggableMonitor${i}" onclick="selectMonitor(${i},&quot;${displayName}&quot;,&quot;${data.displays[i].connection}&quot;)" class="draggable ui-widget-content displays_16-9 selectedMonitor"> <div class="display_16_9_number"><h1>${(i+1)}</h1></div><h4 class="display_16_9_label">${displayName}</h4> </div>`);
					} else {
						$('#monitorEnabled').parent().removeClass("switch-on"); 
						$('#monitorEnabled').parent().addClass("switch-off"); 
					}

					
					
					$("#selectedMonitorTitle").text(displayName);
				} else {
					if (data.displays[i].enabled)
						$("#allDisplays").append(`<div id="draggableMonitor${i}"  onclick="selectMonitor(${i},&quot;${displayName}&quot;,&quot;${data.displays[i].connection}&quot;)" class="draggable ui-widget-content displays_16-9"> <div class="display_16_9_number"><h1>${(i+1)}</h1></div><h4 class="display_16_9_label">${displayName}</h4> </div>`);
				}
                

				//$("#allDisplays").append('<div class="displays_16-9"><div class="display_16_9_number"><h1>'+(i+1)+'</h1></div><h4 class="display_16_9_label">'+displayName+'</h4></div>');
                
                $("#primaryMonitorDropdownOptions").append('<li><a href="#" onclick="setSelectedDisplay(`'+displayName+'`,`'+data.displays[i].connection+'`)"><span class="icon">&#61729;</span> '+displayName+'</a></li>')
                
		
		if (screens[i].work_area.width > maxWidth) {
			maxWidth = screens[i].work_area.width;
			maxHeight = screens[i].work_area.height;
		}
		
		//{...data.displays[i], ...screens[i]}
		//displays.push(data.displays[i]);
		data.displays[i].scaleFactor = screens[i].scaleFactor;
		data.displays[i].work_area = screens[i].work_area;
		
                
            }


			console.log("displaysss: ",data.displays);

		const scaleWidth = 450/maxWidth;
		const scaleHeight = 230/maxHeight;

		for (var i = 0; i < data.displays.length ; i++) {
			
			const adjustedHeight = data.displays[i].work_area.height*scaleHeight;
			console.log("adjustedHeight: ",adjustedHeight);
			$(`#draggableMonitor${i}`).height(adjustedHeight);
			$(`#draggableMonitor${i}`).width(data.displays[i].work_area.width*scaleWidth);
			var offsetX = data.displays[i].work_area.x*scaleWidth;
			if (i != 0) {
				offsetX += 22;
			}
			
			try {
			console.log(`offset ${i}: `,$(`#draggableMonitor${i}`).position());
			const relativePosTop = $(`#draggableMonitor${i}`).position().top;
			const offsetY = (data.displays[i].work_area.y*scaleHeight)-(relativePosTop-79);
			$(`#draggableMonitor${i}`).css({top: `${offsetY}px`, left: `${offsetX}px`});
			} catch (e) {
				console.log("error processing display data");
			}

			
		}

			//$("#allDisplays").height((maxHeight*scaleHeight)*2); //FIXME Add expand option for people that might want to stack monitors

			$( ".draggable" ).draggable({snap: true, containment: '#allDisplays'});

			console.log("displaysss: ",data.displays);

			

			addDisplayOptions(data.displays,false);

			


            //console.log('Graphics:',data);
            //setTimeout(function(){updateDisplay(); }, 5000);
});
}


function openDisplaySettings() {

    if (currentSysSettingsMenu !="sys_displays")
    {
	if (localStorage.getItem('displayBrightness') != null)
    		displayBrightness = JSON.parse(localStorage.getItem('displayBrightness'));

	$('#brightnessSlider').slider( 'setValue', displayBrightness );
	window.autoMonitors = false;
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_displays").fadeIn();
        currentSysSettingsMenu = "sys_displays";
	loadDisplayInformation();
    }
}

function autoUpdateMonitors() {
    si.graphics(function(data) {
            if (data.displays.length > 1)
                $("#allDisplays").addClass("multimonitors");
            else
                $("#allDisplays").removeClass("multimonitors");
            
            $("#allDisplays").empty();
            $("#primaryMonitorDropdownOptions").empty();
            
            for (var i = 0; i < data.displays.length ; i++) {
                
                var displayName = getDisplayName(data.displays[i]);
                    
                
                $("#allDisplays").append('<div class="displays_16-9"><div class="display_16_9_number"><h1>'+(i+1)+'</h1></div><h4 class="display_16_9_label">'+displayName+'</h4></div>');
                
                $("#primaryMonitorDropdownOptions").append('<li><a href="#" onclick="setSelectedDisplay(`'+displayName+'`,`'+data.displays[i].connection+'`)">'+displayName+'</a></li>')
                
                addDisplayOptions(data.displays,true);
            }
            //console.log('Graphics:',data);
            //setTimeout(function(){updateDisplay(); }, 5000);
});
}





$("#saveDisplaySettings").click(function() {
    /*if (currentDisplay != "")
        enableThisDisplayOnly(currentDisplay);*/

	setResolution();

});

var parse = require('xrandr-parse');

function tempSearchResolutionArray(dispArray,resWidth,resHeight) {
	var foundPos = -1;
	for (var j = 0; j < dispArray.length; j++) {
		if ((dispArray[j].width == resWidth) && (dispArray[j].height == resHeight)) {
			foundPos = j;
			break;
		}
	}

	return foundPos;
}

function openResolutionSelection() {
		$("#resSelectionConfirmationModal").addClass("hidden");
		$("#resSelectionModal").removeClass("hidden");
	$("#dispResolutionsSelectionWindow").removeClass("hidden");

	setTimeout(function() { $("#dispResolutionsSelectionWindow").removeClass("hiddenOpacity"); }, 500); 
}

function closeResolutionsSelectionWindow() {
	$("#dispResolutionsSelectionWindow").addClass("hiddenOpacity");
	$("#displaySettingsBody").removeClass("hidden");
	

	setTimeout(function() { $("#dispResolutionsSelectionWindow").addClass("hidden"); }, 500); 
}

function selectResolution(selectedDiv) {
	oldSelectedResolutionDiv = $(".res-btn")[0];
	$(".res-btn").removeClass("res-btn-selected");
	$(selectedDiv).addClass("res-btn-selected");

}

var revertChanges = true; // Checked after the 15 seconds timeout to see if the user has reponded or not
var revertChangesTimeout; //store the timeout here. Used to be able to clear it when the user cancels

function rotateDisplay(direction,output,waitForConfirmation) {
	let childProcess = require('child_process');
                            let spawn = childProcess.spawn;
                            let child = spawn('xrandr', ['--output',output,'--rotate',direction]);
                            
                            child.on('error', function () {
                                console.log("Failed to start child.");
                            });
                            
                            child.on('close', function (code) {
                                console.log('Child process exited with code ' + code);
                            });
                            
                            child.stdout.on('end', function () {
                                console.log('Finished collecting data chunks: ');

			});
}

function updateResolution(output,newResolution,newRefreshRate,waitForConfirmation,positionCOnfigured) {

var oldResolution = screen.width+"x"+ screen.height;//selectedDisplayResolution.width+"x"+selectedDisplayResolution.height;
var oldRefreshRate = selectedDisplayResolution.refreshRate;
let positionString = "";

if (positionCOnfigured != null)
	positionString = " "+positionCOnfigured;

  
  console.log("updateResolution output: ",output);
  
  console.log("updateResolution newResolution: ",newResolution);
  
      var exec = require('child_process').exec,
                   child;
            child = exec('xrandr --output '+output+' --mode '+newResolution+' --rate '+newRefreshRate+positionString,function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
	
	reAdjustSystemAppsResolution();
	selectedDisplayResolution.refreshRate = newRefreshRate;

	//readjustSystemApps();
		if (waitForConfirmation) {
			$("#displaySettingsBody").addClass("hidden");
			$("#resSelectionModal").addClass("hidden");
			$("#resSelectionConfirmationModal").removeClass("hidden");
			$("#dispResolutionsSelectionWindow").removeClass("hidden");
			$("#dispResolutionsSelectionWindow").removeClass("hiddenOpacity");
			

		
			revertChangesTimeout = setTimeout(function() { 
				if (revertChanges) {
					selectedDisplayResolution.refreshRate = oldRefreshRate;
					updateResolution(output,oldResolution,oldRefreshRate,false);
					$(".res-btn").removeClass("res-btn-selected");
					$(oldSelectedResolutionDiv).addClass("res-btn-selected"); 
					$("#displaySettingsBody").removeClass("hidden");
				}

				revertChanges = true; //Reset
			}, 18000); //Supposed to be 15 seconds, just making up for the screen turn off and on times plus the desktop reload times.
		} else {
			closeResolutionsSelectionWindow();
		}
	//var Screen = nw.Screen.Init();
      //console.log("new res set Screen.screens");
      //console.log(screen);
    }  
    
});

}

function keepResolutionChanges() {

	revertChanges = false;
	closeResolutionsSelectionWindow();
	clearTimeout(revertChangesTimeout);
}

function revertResolutionChanges() {
	//FIXME Add an instant revert
	closeResolutionsSelectionWindow();
}



function setResolution() {

	var newResolution = $(".res-btn-selected").text().replace(" X ","x").replace("","");
	var newResolutionRefreshRate = $("#refreshRate").text();
	 $('#saveDisplaySettings').prop('disabled', true);
  
    
    updateResolution(selectedDisplayResolution.connection,newResolution,newResolutionRefreshRate,true);

}

function scrollToBottom() {
	setTimeout(function() { console.log("scrolled to bottom");

	var element = $("#displaySettingsBody")[0];
   element.scrollTop = element.scrollHeight - element.clientHeight;
	 }, 50);
	
}

function setRefreshRate(newRefreshRate) {
	resolutionManuallySetByUser = true;
	localStorage.setItem('resolutionManuallySetByUser', JSON.stringify(resolutionManuallySetByUser));
	$("#refreshRate").text(newRefreshRate);
	$('#saveDisplaySettings').prop('disabled', false);

}

var doneFirstScreen = false;

function loadDisplayResolutionOptions(selectedDisplay) {

	

var updateResToThisHigherRes = "";
var updateRefreshToThis = "";
var updateResToThisWidth = 0; //store the smallest but within minimum spec width (this is for auto resolution on VMs). IN other words if supported optimum would be 1366x768 minimum


    var exec = require('child_process').exec,
                   child;
            child = exec('xrandr',function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
	var allAddedResolutions = [];
        var resolutionOptions = parse(stdout);
		console.log("allScreenInfo.length: ",allScreenInfo.length);
	for (let i = 0; i < allScreenInfo.length; i++) {
		console.log("resolutionOptions[allScreenInfo[i].connection]: ",resolutionOptions[allScreenInfo[i].connection]);
		allScreenInfo[i].modes = resolutionOptions[allScreenInfo[i].connection].modes;
	}
	console.log("resolutionOptions",resolutionOptions);
	//$("#monitorResolutionDropdownOptions").empty();
	$("#dispResolutions").empty();
	var selectedClass = "";
	var lowResFixed = false;
	for (var i = 0; i < resolutionOptions[selectedDisplay].modes.length; i++) {
		//$("#monitorResolutionDropdownOptions").append('<li><a href="#" onclick="setSelectedDisplay(`'+i+'`)">'+resolutionOptions[selectedDisplay].modes[i].width+' X '+resolutionOptions[selectedDisplay].modes[i].height+'</a></li>');

		selectedClass = "";

		if (resolutionOptions[selectedDisplay].modes[i].isSelected) {
			selectedClass = "res-btn-selected";
			$("#refreshRateOptions").empty();
			for (var j = 0; j < resolutionOptions[selectedDisplay].modes[i].refreshRates.length; j++) {
				
				$("#refreshRateOptions").append('<li><a href="javascript:void(0);" onclick="setRefreshRate('+resolutionOptions[selectedDisplay].modes[i].refreshRates[j]+')">'+resolutionOptions[selectedDisplay].modes[i].refreshRates[j]+'</a></li>');
			}
			$("#refreshRate").text(resolutionOptions[selectedDisplay].modes[i].rate);
			
			//doneFirstScreen = true;
			
		}

		$("#dispResolutions").append('<a href="#" refreshRate="'+resolutionOptions[selectedDisplay].modes[i].rate+'" class="btn btn-alt res-btn '+selectedClass+'">'+resolutionOptions[selectedDisplay].modes[i].width+' X '+resolutionOptions[selectedDisplay].modes[i].height+'</a>');
	var foundArrayPos = tempSearchResolutionArray(allAddedResolutions,resolutionOptions[selectedDisplay].modes[i].width, resolutionOptions[selectedDisplay].modes[i].height);
		if (foundArrayPos == -1) {
			allAddedResolutions.push(resolutionOptions[selectedDisplay].modes[i]);
			//allAddedResolutions[allAddedResolutions.length-1].refreshRates = [];
			//allAddedResolutions[allAddedResolutions.length-1].refreshRates.push(resolutionOptions[selectedDisplay].modes[i].rate);
		} else {
			//allAddedResolutions[foundArrayPos].refreshRates.push(resolutionOptions[selectedDisplay].modes[i].rate);
		}

		

		if ((screen.width < 1366) && (!lowResFixed) && (resolutionOptions[selectedDisplay].modes[i].width > 1365) && (resolutionOptions[selectedDisplay].modes[i].height > 767) && (!resolutionManuallySetByUser) && (!lowResFixed)) { //Are we below minimum requirements? Probably in VM
			console.log("selectedDisplayResolution.width",selectedDisplayResolution.width);
			console.log("found....: ",updateResToThisHigherRes);
			if ((updateResToThisWidth > parseInt(resolutionOptions[selectedDisplay].modes[i].width)) ||(updateResToThisWidth == 0)) {
			//lowResFixed = true;
			updateResToThisWidth = parseInt(resolutionOptions[selectedDisplay].modes[i].width);
			updateResToThisHigherRes = resolutionOptions[selectedDisplay].modes[i].width+"x"+resolutionOptions[selectedDisplay].modes[i].height;
			updateRefreshToThis = resolutionOptions[selectedDisplay].modes[i].rate;
			}
		}


	}

	$('.res-btn').click( function(e) {e.preventDefault(); resolutionManuallySetByUser = true; localStorage.setItem('resolutionManuallySetByUser', JSON.stringify(resolutionManuallySetByUser)); selectResolution(this); return false; } );
    console.log("resolutionOptions: ",resolutionOptions);
    console.log("selectedDisplay: ",selectedDisplay);
    console.log("allAddedResolutions",allAddedResolutions);
    }  

	if (updateResToThisHigherRes != "") {
		lowResFixed = true;
		console.log("updating to higher res of: ",updateResToThisHigherRes);
		updateResolution(selectedDisplayResolution.connection,updateResToThisHigherRes,updateRefreshToThis,true);
	}
    
});


}


// FIXME: Supposed to be default/main monitor selector
function setSelectedDisplay(displayName,displaySelected) {
    //currentDisplay = displaySelected;
    $("#mainMonitorDropdown").text(displayName);
    //$('#saveDisplaySettings').prop('disabled', false);
    //loadDisplayResolutionOptions(displaySelected);
    //console.log("Current Display updated: ",currentDisplay);
}

function returnToSettings() {
    if (currentSysSettingsMenu !="sys_main")
    {
        $("#"+currentSysSettingsMenu).fadeOut();
        $("#sys_main").fadeIn();
        currentSysSettingsMenu = "sys_main";
    }
}

function closeSettings() {
    $("#main").fadeOut(300, function() {
    // Animation complete.
	$("#startMenu").fadeIn(200);
  });
    //$("#startMenu").fadeIn();
    //$("#startMenu").removeClass("hidden");
    //$("#startMenu").trigger( "click" );
    currentMenuMode = 'apps';
    //$("#main").fadeOut(500);
    //$("#startMenu").fadeIn();
}

function closeSysPerfomance() {
    $("#sysPerfomance").fadeOut(1);
    $("#startMenu").fadeIn();
    $("#startMenu").removeClass("hidden");
    $("#startMenu").trigger( "click" );
    currentMenuMode = 'apps';
    //$("#main").fadeOut(500);
    //$("#startMenu").fadeIn();
}

function closeSysAbout() {
    //$("#sysAbout").fadeOut(500);
    $("#sysAbout").fadeOut(1);
    $("#startMenu").fadeIn();
    $("#startMenu").removeClass("hidden");
    $("#startMenu").trigger( "click" );
    currentMenuMode = 'apps';
    //$("#main").fadeOut(500);
    //$("#startMenu").fadeIn();
}

loadDisplayInformation();

$( "#aiInput" ).focus(function() { $( "#aiInputGO" ).removeClass("hidden"); $( "#voiceRequestMic" ).addClass("hidden");})
.focusout(function() {$( "#aiInputGO" ).addClass("hidden"); $( "#voiceRequestMic" ).removeClass("hidden");});

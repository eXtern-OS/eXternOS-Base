var si = require('systeminformation');
var njds = require('nodejs-disks');
var win = nw.Window.get();
var focusedDriveName = ""; //Name of the drive currently on focus (i.e context menu/right click)
var focusedDriveMounted; //Is drive on focus mounted? (i.e context menu/right click)
var autoOpenFilesOnMount = true;
var waitRefresh = false;
var currentContextMenuType = "";
var currentlyOpenedStack; //Stores the currently opened stack div
var justMovedStackPosition = false;
var possibleGrids;
var stackFileContents = [];
var deskStacks = [];
var stackDragged = 0; //used to prevent on click from firing on stack being dragged
var doNotCloseStack = false; //Prevent Stack from closing
var drivesWithUsageInfo = [];
var firstCheckOnLoad = true; // Used to check if this is the first time we are getting system info such as mounted drives
var currentlyStackShowingContextMenu; //Store stack div that is currently right clicked
var stackInformation = {};
var stackStyle = win.stackStyle; //Stores the style class to be used on the stack icons

/* disa

minimize ctrl alt 0
close



*/

//win.showDevTools();




function generate_new_piechartB()
{
var oilData = {
    labels: [
        "Saudi Arabia",
        "Russia",
        "Iraq",
        "United Arab Emirates",
        "Canada"
    ],
    datasets: [
        {
            data: [133.3, 86.2, 52.2, 51.2, 50.2],
            backgroundColor: [
                "#FF6384",
                "#63FF84",
                "#84FF63",
                "#8463FF",
                "#6384FF"
            ]
        }]
};
var pieChartCanvas = $("#pieChart").get(0).getContext("2d");

var pieChart = new Chart(pieChartCanvas, {
  type: 'pie',
  data: oilData
});

}

function generate_new_piechart()
{

$('#pieChart').remove(); // this is my <canvas> element
  $('#chart_properties').append('<canvas id="pieChart"><canvas>');
  //canvas = document.querySelector('#results-graph');
      
      
      
      var pieChartCanvas = $("#pieChart").get(0).getContext("2d");
        var pieChart = new Chart(pieChartCanvas);
        pieChart.canvas.width = 100;
        var PieData = [
          {
            value: 700,
            color: "rgba(0,0,0,0.1)",
            highlight: "#f56954",
            label: "Chrome"
          },
          {
            value: 500,
            color: "rgba(0,0,0,0.1)",/*"#00a65a",*/
            highlight: "#00a65a",
            label: "IE"
          },
          {
            value: 400,
            color: "rgba(0,0,0,0.1)",
            highlight: "#f39c12",
            label: "FireFox"
          },
          {
            value: 600,
            color: "rgba(0,154,255,1)",
            highlight: "#00c0ef",
            label: "Safari"
          },
          {
            value: 300,
            color: "rgba(0,0,0,0.1)",
            highlight: "#3c8dbc",
              showTooltip: true,
            label: "Opera"
          },
          {
            value: 100,
            color: "rgba(0,0,0,0.1)",
            highlight: "#d2d6de",
            label: "Navigator"
          }
        ];
        var pieOptions = {
          //Boolean - Whether we should show a stroke on each segment
          segmentShowStroke: true,
          //String - The colour of each segment stroke
          segmentStrokeColor: "rgba(255,255,255,0.3)",
          //Number - The width of each segment stroke
          segmentStrokeWidth: 2,
          //Number - The percentage of the chart that we cut out of the middle
          percentageInnerCutout: 50, // This is 0 for Pie charts
          //Number - Amount of animation steps
          animationSteps: 100,
          //String - Animation easing effect
          animationEasing: "easeInOutCirc",
          //Boolean - Whether we animate the rotation of the Doughnut
          animateRotate: true,
          //Boolean - Whether we animate scaling the Doughnut from the centre
          animateScale: false,
          //Boolean - whether to make the chart responsive to window resizing
          responsive: true,
          // Boolean - whether to maintain the starting aspect ratio or not when responsive, if set to false, will take up entire container
          maintainAspectRatio: true,
          
          tooltipTemplate: "<%= value %>",
        
        onAnimationComplete: function()
        {
            //this.showTooltip(this.segments, true);
        },
          //String - A legend template
          legendTemplate: "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<segments.length; i++){%><li><span style=\"background-color:<%=segments[i].fillColor%>\"></span><%if(segments[i].label){%><%=segments[i].label%><%}%></li><%}%></ul>"
        };
        //Create pie or douhnut chart
        // You can switch between pie and douhnut using the method below.
        pieChart.Doughnut(PieData, pieOptions);
}


function showDispPieChart(usedSpace) {

	var animateTime = 3000;
	if (usedSpace < 20) {
		animateTime = 500;
	} else if (usedSpace < 50) {
		animateTime = 1000;
	} else if (usedSpace < 80) {
		animateTime = 2000;
	}


$("#drivePieChart").prepend('<div class="pie-chart-med" data-percent="'+usedSpace+'"><span class="percent"></span></div>')
    $('.pie-chart-med').easyPieChart({
        easing: 'easeOutSine',
        barColor: 'rgba(255,255,255,0.6)',
        trackColor: 'rgba(0,0,0,0.3)',
        scaleColor: false,
        lineCap: 'round',
        lineWidth: 30,
        size: 200,
        animate: animateTime,
        onStep: function(from, to, percent) {
            $(this.el).find('.percent').text(Math.round(percent));
        }
    });

    var charts = window.chart = $('.pie-chart-med').data('easyPieChart');
    $('.pie-chart-tiny .pie-title > i').on('click', function() {
        $(this).closest('.pie-chart-tiny').data('easyPieChart').update(Math.random()*200-100);
    });
}

function openDrivePropertiesLinkInFiles() {
loadFilesApp(location)
}

var selectedDriveMountLocation;

function showDriveProperties(e) {

console.log("rightclickedE",e);
//console.log("loadedDrives",loadedDrives);


if (focusedDriveName == "") {
var partitionName = $(this).attr("name");
var mounted = $(this).attr("mounted");
var openFiles = true;
} else {
var openFiles = false;
var partitionName = focusedDriveName;
var mounted = focusedDriveMounted;
}

mountPoint = "/dev/"+partitionName;

if (mounted == 'true') {

for (var i = 0; i < loadedDrives.length; i++) {
		if (loadedDrives[i].name == partitionName) {
			$("#driveProperties > .modal-content").removeClass("minModalWindow");
			$(".modal-content").addClass("driveModalWindow");
			$(".modal-content").fadeIn();

			$("#propertiesDriveName").text(loadedDrives[i].label);
			$("#propertiesDriveLocation").text(loadedDrives[i].mount);
			$("#propertiesDriveFs").text(loadedDrives[i].fstype);
			if (loadedDrives[i].protocol == "")
				$("#propertiesDriveProtocol").parent().addClass("hidden");
			else {
				$("#propertiesDriveProtocol").text(loadedDrives[i].protocol);
				$("#propertiesDriveProtocol").parent().removeClass("hidden");
			}

			if (loadedDrives[i].name == "sd_extern")
				$("#propertiesDriveInternalName").parent().addClass("hidden");
			else {
				$("#propertiesDriveInternalName").text(loadedDrives[i].name);
				$("#propertiesDriveInternalName").parent().removeClass("hidden");
			}

			$("#propertiesDriveSize").text(convertBytes(loadedDrives[i].size));

			if (loadedDrives[i].freeSpace == 0) {
				$("#propertiesDriveFreeSpace").parent().addClass("hidden");
			} else {
				$("#propertiesDriveFreeSpace").text(convertBytesExact(loadedDrives[i].freeSpace));
				$("#propertiesDriveFreeSpace").parent().removeClass("hidden");
			}

			selectedDriveMountLocation = loadedDrives[i].mount;

			$('#propertiesDriveLocation')[0].addEventListener('click', function(){
    				loadFilesApp(selectedDriveMountLocation);
			}, false);

			showDispPieChart(100-loadedDrives[i].freePercentage);

			console.log("found drive here ",loadedDrives[i]);
			//win.openApp("extern.files.app",loadedDrives[i].mount);
			//setTimeout(function(){ doNotCloseStack = false; closeMenu(); }, 2000);
			break;
		}
}

//console.log("mounted triggered");
} else {


}


doNotCloseStack = false;
closeMenu();
closeStack();


$("#diagueBoxes").removeClass("hidden");
$("#driveProperties").removeClass("hidden");
//$(".modal-body").removeClass("hidden");

//setTimeout(function(){ $(".modal-body").removeClass("hidden"); }, 2000);
}

function closeModalWindow() {
$("#diagueBoxes").addClass("hidden");
$("#driveProperties").addClass("hidden");
//$(".modal-body").addClass("hidden");
$("#driveProperties > .modal-content").addClass("minModalWindow");
$(".modal-content").removeClass("driveModalWindow");
$(".modal-content").fadeOut();
$(".pie-chart-med").remove();
}



//generate_new_piechart();

window.addEventListener("dragover",function(e){
  e = e || event;
  e.preventDefault();
},false);
window.addEventListener("drop",function(e){
  e = e || event;
  e.preventDefault();
},false);


win.changeStackStyle = function (newStackStyle) {
	if (stackStyle != newStackStyle) {
		$("."+stackStyle).addClass(newStackStyle).removeClass(stackStyle);
		stackStyle = newStackStyle;
	}
	
}

win.adjustDisplayResolution = function () {
	win.width = screen.width;
	win.height = screen.height;
}

 document.addEventListener("contextmenu", function (e) {
        e.preventDefault();
    }, false);

if (localStorage.getItem('allStacks') === null) {
    var allStacks = [];
var driveStack = {
	col: Math.floor(win.width/170),
	id: 0,
	row: 1,
	name: "Drives",
	type: "drives",
	location: "drives"
}

var filesStack = {
	col: Math.floor(win.width/170),
	id: 1,
	row: 2,
	name: "Files",
	type: "files",
	location: "/home/extern/Projects/Files"
}

allStacks.push(driveStack);
allStacks.push(filesStack);

stackInformation.allStacks = allStacks;
stackInformation.nextID = 3;

stackInformation.nextID = 3;

} else {
    var stackInformation = JSON.parse(localStorage.getItem('allStacks'));
    var allStacks = stackInformation.allStacks;
}

//console.log("All filesStack",allStacks);
//console.log("All filesStack",stackInformation.nextID);

//http://interactjs.io/

var columnCount = 100/5;
//console.log(columnCount);
//document.getElementById('drives').style.webkitColumnCount = columnCount;
//document.getElementById('drives').style.column_count = columnCount;
/*$("#drives").append('<a href="javascript:void(0);" class="shortcut iconSizeA"> <img src="icons/drive-removable-media-usb.svg"> <small> Anesu </small></a>');*/

function convertBytes(input) {
if (input != 0) {
    current_filesize = input.toFixed(2);
    var size_reduction_level = 0;
    while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
          /*Check if its a whole number or not*/
          if (current_filesize % 1 !== 0)
      current_filesize = Math.round(current_filesize); /*.toFixed(2);*/

	if (current_filesize < 10)
		current_filesize += ".0";
          
      
      switch(size_reduction_level){
          case 0: current_filesize +=" B"; break;
          case 1: current_filesize +=" KB"; break;
          case 2: current_filesize +=" MB"; break;   
          case 3: current_filesize +=" GB"; break;
          case 4: current_filesize +=" TB"; break;
          case 5: current_filesize +=" PB"; break;
          case 6: current_filesize +=" EB"; break;
          case 7: current_filesize +=" ZB"; break;
      }
    
    return current_filesize;
} else {
	return 0;
}
}

function convertBytesExact(input) {
if (input != 0) {
    current_filesize = input.toFixed(2);
    var size_reduction_level = 0;
    while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
          /*Check if its a whole number or not*/
          //if (current_filesize % 1 !== 0)
      //current_filesize = Math.round(current_filesize); /*.toFixed(2);*/

	//if (current_filesize < 10)
		//current_filesize += ".0";

	current_filesize = current_filesize.toFixed(2);
          
      
      switch(size_reduction_level){
          case 0: current_filesize +=" B"; break;
          case 1: current_filesize +=" KB"; break;
          case 2: current_filesize +=" MB"; break;   
          case 3: current_filesize +=" GB"; break;
          case 4: current_filesize +=" TB"; break;
          case 5: current_filesize +=" PB"; break;
          case 6: current_filesize +=" EB"; break;
          case 7: current_filesize +=" ZB"; break;
      }
    
    return current_filesize;
} else {
	return 0;
}
}

function unhumanizeDriveSize(text) { 
    var powers = {'k': 1, 'm': 2, 'g': 3, 't': 4};
    var regex = /(\d+(?:\.\d+)?)\s?(k|m|g|t)?b?/i;

    var res = regex.exec(text);

    return res[1] * Math.pow(1024, powers[res[2].toLowerCase()]);
}

function addNewStack(location) {

var stackLocation = String(location);

if (fs.existsSync(stackLocation) && fs.lstatSync(stackLocation).isDirectory()) {

console.log("add stacks called", location);



var filesStack = {
	col: Math.floor(win.width/170),
	id: stackInformation.nextID,
	row: 2,
	name: stackLocation.split('/').pop(),
	type: "files",
	location: stackLocation
}

allStacks.push(filesStack);


currentStackBeingLoaded = allStacks.length-1;

//console.log("Added filesStack",allStacks);
//console.log("Added filesStack",stackInformation.nextID);

loadStackFiles(currentStackBeingLoaded);
localStorage.setItem('allStacks', JSON.stringify(stackInformation));

stackInformation.nextID++;
} else {
	console.log("failed to add desktop stack because it's either not a directory or doesn't exist");
}

}



win.addNewStack = addNewStack;

function removeStack() {

//FIXME to be finished

closeMenu();



var stackID = $(currentlyStackShowingContextMenu).attr("stackID");
console.log("allStacks",allStacks);
	for (var i = 0; i < allStacks.length; i++) {
		if (allStacks[i].id == stackID) {
			console.log("found");
			$(currentlyStackShowingContextMenu).remove();
			allStacks.splice (i, 1);
			localStorage.setItem('allStacks', JSON.stringify(stackInformation));
			break;
		}
	}
//stackFileContents[fileslocation]
}

//setTimeout(function(){ addNewStack("/home/extern/Videos"); }, 20000);




function loadUsages(callback, callbackVariableA) {
  
  var njds = require('/usr/eXtern/systemX/Shared/node_modules_fixed/nodejs-disks/lib/disks.js');
    njds.drives(
        function (err, drives) {
            njds.drivesDetail(
                drives,
                function (err, data) {
                  //console.log("alternative drives",data);
                  drivesWithUsageInfo = data;

		if (err)
			console.log("error",err);

		console.log("drivesWithUsageInfo",drivesWithUsageInfo);

		if (callback != null)
                  getDriveUsages(false,callback, callbackVariableA);
		else
                  getDriveUsages(false);                    



                }
            );
        }
    )
  
}


function getDriveUsages(reloadDrives, callback, callbackVariableA) {
console.log("gets here",reloadDrives);
  if (reloadDrives) {
    loadUsages(callback, callbackVariableA);
  } else {
	
    for( var i = 0; i < drivesWithUsageInfo.length; i++) {
                      for (var j = 0; j < mountedDrives.length; j++) {
			console.log("drivesWithUsageInfo[i].mountpoint",drivesWithUsageInfo[i].mountpoint);
                        if (drivesWithUsageInfo[i].mountpoint == mountedDrives[j].mount) {

				//console.log("found drive: ",drivesWithUsageInfo[i]);
                          if (mountedDrives[j].size == 0)
                          		mountedDrives[j].size = unhumanizeDriveSize(drivesWithUsageInfo[i].total);

				//console.log("found",mountedDrives[j]);
				//console.log("foundB",drivesWithUsageInfo[i]);

                          	mountedDrives[j].usedPercentage = drivesWithUsageInfo[i].usedPer;
				mountedDrives[j].freePercentage = drivesWithUsageInfo[i].freePer; // I mean we may as well haha

				if (drivesWithUsageInfo[i].available == 0.00) {
					mountedDrives[j].freeSpace = 0;
				} else {
				mountedDrives[j].freeSpace = unhumanizeDriveSize(drivesWithUsageInfo[i].available);
				}
				break;
				
				
                          
                        }
                      }
                      
                    }

				if (callback != null) {
					console.log("callback is not null");
					callback(callbackVariableA);
				}
  }
  
  
}


/*

				if (mountedDrives[j].size == 0)
                          		mountedDrives[j].size = data[i].total;

                          	mountedDrives[j].usedPercentage = data[i].usedPer;
				mountedDrives[j].freePercentage = data[i].freePer; // I mean we may as well haha

*/

function loadFilesApp(location) {
	win.openApp("extern.files.app",location);
}


function openDrive(e) {
doNotCloseStack = true;
console.log("focusedDriveName: ",focusedDriveName);
console.log("focusedDriveName: event: ",e);
if (focusedDriveName == "") {
var partitionName = $(this).attr("name");
var mounted = $(this).attr("mounted");
var openFiles = true;
} else {
var openFiles = false;
var partitionName = focusedDriveName;
var mounted = focusedDriveMounted;
}

mountPoint = "/dev/"+partitionName;

if (mounted == 'true') {

for (var i = 0; i < loadedDrives.length; i++) {
		if (loadedDrives[i].name == partitionName) {
			//console.log("opening extern.files.app with",loadedDrives[i]);
			win.openApp("extern.files.app",loadedDrives[i].mount);
			setTimeout(function(){ doNotCloseStack = false; closeMenu(); }, 2000);
			break;
		}
}

//console.log("mounted triggered");
} else {

    var exec = require('child_process').exec,
                   child;
            child = exec("udisksctl mount -b "+mountPoint,function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        if (stdout.indexOf("failed") == -1) {
	    var mountPoint = stdout.substring(stdout.indexOf(" at /")+1, stdout.length-2).replace("at ","");
            //console.log("successfully mounted: "+mountPoint);
	    //console.log("win.openApp");

	    currentTotal = 0;

	    for (var i = 0; i < loadedDrives.length; i++) {
		if (loadedDrives[i].name == partitionName) {
			var driveIcon = getDriveIcon(loadedDrives[i].fstype, loadedDrives[i].mount, loadedDrives[i].removable);
			loadedDrives[i].mount = mountPoint;
			//console.log(" IMG",$('#driv_'+loadedDrives[i].name+" > img"));
			//console.log(" driveIcon ",driveIcon);
			$('#driv_'+loadedDrives[i].name+" > img").attr("src",driveIcon+"_mount.svg");
			$('#driv_'+loadedDrives[i].name).attr("mounted",true);
			mountedDrives.push(loadedDrives[i]);
console.log("mountedDrives",mountedDrives);
			getBase64Image(driveIcon+'_mount.svg',mountedDrives[mountedDrives.length-1]);
			win.setMountedDrives(mountedDrives);
			if (autoOpenFilesOnMount && openFiles) {
				doNotCloseStack = true;
				getDriveUsages(true,loadFilesApp,loadedDrives[i].mount);
				//console.log("loadedDrives.length",mountedDrives.length);
	    		//win.openApp("extern.files.app",loadedDrives[i].mount);
				setTimeout(function(){ doNotCloseStack = false; closeMenu(); }, 4000);
			} else {
				getDriveUsages(true);
			}
			//console.log("mountedDrives",mountedDrives);

			
		}
	    }
          
          //getDriveUsages(true);

            //checkConnectedDrives();
        } else
            console.log("failed to mount");
    }  
closeMenu();     
});
}
}


function unMountDrive() {
var partitionName = focusedDriveName;
    var mountPoint = "/dev/"+partitionName;
    //console.log("UNMOUNT",mountPoint);
    
if (focusedDriveMounted == "true") {
    var exec = require('child_process').exec,
                   child;
            child = exec("udisksctl unmount -b "+mountPoint,function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        if (stdout.indexOf("failed") == -1) {
            //console.log("successfully unmounted");

	    for (var i = 0; i < loadedDrives.length; i++) {
		if (loadedDrives[i].name == partitionName) {
			var driveIcon = getDriveIcon(loadedDrives[i].fstype, loadedDrives[i].mount, loadedDrives[i].removable);
			//console.log(" IMG",$('#driv_'+loadedDrives[i].name+" > img"));
			//console.log(" driveIcon ",driveIcon);
			$('#driv_'+loadedDrives[i].name+" > img").attr("src",driveIcon+".svg");
			$('#driv_'+loadedDrives[i].name).attr("mounted",false);
			
		}
	    }

	for (var i = 0; i < mountedDrives.length; i++) {
		if (mountedDrives[i].name == partitionName) {
			mountedDrives.splice(i, 1);
			console.log("removed from mounted");
		}
	}

            //listAvailableDrives();
        } else
            console.log("failed to unmount");
    }
closeMenu();
       
});
    
}
}

function getDriveIcon (fstype, mount, removable) {
var driveIcon = "icons/drive-harddisk";

if (fstype == "ext" || fstype == "ext2" || fstype == "ext3" || fstype == "ext4" || fstype == "ext5")
	driveIcon = "icons/drive-harddisk-system"; //is Linux Partition (ext5 just future proofing if that ever happens haha)

if (mount == "/cdrom")
	driveIcon = "icons/drive-optical"; //is CD/DVD

if (fstype == "vfat" && removable && mount != "/cdrom")
	driveIcon = "icons/drive-removable-media-usb"; //is USB

return driveIcon;

}


var maxNumberOfDrviesPerColumn = Math.floor(win.height/140);
var addedIcons = 0;
var addedIconsCurrentRow = 0;
var currentRowNum = 0;
var iconPositionX = 0;
var iconPositionY = 0;
var loadedDrives = [];
var mountedDrives = [];



var currentTotal = 0;

function checkConnectedDrives() {

si.blockDevices(function(data) {
  
  if (loadedDrives.length != data.length+1) {

//console.log("refreshed",loadedDrives.length);
//console.log("refreshedk",data.length);

//console.log("data drives",data);

	if ((loadedDrives.length < data.length+1) && loadedDrives.length != 0) {
		new Audio("file://"+process.cwd()+"/Shared/CoreAudio/USB-PeripheralDeviceEntered.mp3").play()
	} else if (loadedDrives.length != 0) {
		new Audio("file://"+process.cwd()+"/Shared/CoreAudio/USB-PeripheralDeviceExited.mp3").play()
	}

var systemDrive = {
			fstype:"ext4",
			label: "eXtern OS",
			model: "",
			mount: "/",
			name: "sd_extern",
			physical:"HDD",
			protocol:"usb",
			removable:false,
			serial:"",
			size:0,
			type:"part",
			uuid:"extern_os"
		};

data.unshift(systemDrive);

var drivesData = data;

loadedDrives = data;
mountedDrives = [];

if (data.length != currentTotal) {
closeMenu();
$(".folderContents > ul").empty();
addedIcons = 1;

var addedIcons = 0;
var addedIconsCurrentRow = 0;
var currentRowNum = 0;
var iconPositionX = 0;
var iconPositionY = 0;

for (var i = 0; i < data.length; i++) {
if (data[i].label != "eXtern OS alpha" && data[i].fstype != "" && data[i].uuid != "" && data[i].fstype !="swap" && data[i].type !="disk") {
    var driveName = data[i].label;

var driveIcon = getDriveIcon(data[i].fstype, data[i].mount, data[i].removable);

var classes = ""; // Store apropriate css classes for the desktop icon
var oldDriveIcon = driveIcon;

var mounted = false;
    
    if (data[i].label == "") {
	driveName = convertBytes(data[i].size)+" Volume";
	data[i].label = driveName;
	}
            var showMountButton = "";
            var showUnmountButton = "hidden";
            
            if (data[i].mount != ""){
                showMountButton = "hidden";
                showUnmountButton = "";
		driveIcon = driveIcon+"_mount";
		mounted = true;
            }

if (mounted) {
  mountedDrives.push(data[i]);
console.log("mountedDrives",mountedDrives);
  getDriveUsages(false);
  getBase64Image(driveIcon+'.svg',mountedDrives[mountedDrives.length-1])
}

//onclick="openDrive(&quot;'+data[i].name+'&quot;,'+mounted+')"



//console.log("addedIconsCurrentRow",addedIconsCurrentRow);
//console.log("iconPositionY",iconPositionY);

//if (addedIcons < maxNumberOfDrviesPerColumn) {



	$("#drives").append('<li style="top: 0px; right: 0px;" xpos = "'+iconPositionX+'" ypos = "'+iconPositionY+'" class="tempDriveIcon"><a id="driv_'+data[i].name+'" href="javascript:void(0);" name="'+data[i].name+'" mounted="'+mounted+'" class="shortcut iconSizeA"> <img src="'+driveIcon+'.svg"> <small> '+driveName+' </small></a></li>');





var oldaddedIconsCurrentRow = addedIconsCurrentRow;


addedIconsCurrentRow = Math.floor(addedIcons/5);
iconPositionY = (170*addedIconsCurrentRow);

if (addedIconsCurrentRow > oldaddedIconsCurrentRow) {
	iconPositionX = 0;
} else {
	iconPositionX += 150;
}

//}

/*if (addedIcons >= maxNumberOfDrviesPerColumn && addedIcons < (maxNumberOfDrviesPerColumn*2)) {
	$("#drives1").append('<li><a id="driv_'+data[i].name+'" href="javascript:void(0);" name="'+data[i].name+'" mounted="'+mounted+'" class="shortcut iconSizeA"> <img src="'+driveIcon+'.svg"> <small> '+driveName+' </small></a></li>');
}

if (addedIcons >= (maxNumberOfDrviesPerColumn*2)) {
	$("#drives2").append('<li><a id="driv_'+data[i].name+'" href="javascript:void(0);" name="'+data[i].name+'" mounted="'+mounted+'" class="shortcut iconSizeA"> <img src="'+driveIcon+'.svg"> <small> '+driveName+' </small></a></li>');
}*/

document.getElementById('driv_'+data[i].name).addEventListener('click', openDrive, false);

//$('#driv_'+data[i].name).on("click",console.log("triggered"); //openDrive(data[i].name,mounted)

addedIcons++;


document.getElementById('driv_'+data[i].name).oncontextmenu = function(event) {
		waitRefresh = true; //Avoid system from refreshing desktop to check for checking drives
		$(".iconSizeA").addClass("shortcutUnfocus");
		/*if (event.srcElement.tagName != "A" && event.parentElement != null) {
			console.log("EVENT !A: ",event);
			var contextMenuX = event.parentElement.offsetLeft;//event.clientX;
			var contextMenuY = event.parentElement.offsetTop;//event.clientY;
			$(event.parentElement).addClass("shortcutFocus");
			focusedDriveName = $(event.parentElement).attr("name");
			focusedDriveMounted = $(event.parentElement).attr("mounted");
			//$(event.parentElement).zoomTo({targetsize: 0.2});
		} else {*/
			console.log("EVENT A: ",this);
			$(this).addClass("shortcutFocus");
			focusedDriveName = $(this).attr("name");
			focusedDriveMounted = $(this).attr("mounted");

			//$(event.path[1]).zoomTo({targetsize: 0.2});
			//if (event.srcElement.x == null && event.srcElement.tagName != "A") {
				//var iconPosition = $(event.srcElement).position();
				var contextMenuX = event.clientX;
			var contextMenuY = event.clientY;

				for (var m = 0; m < event.path.length; m++) {
					if (event.path[m].tagName == "A") {
						var contextOffset = $(event.path[m]).offset();
						$(event.path[m]).removeClass("shortcutUnfocus");
						//console.log("POS FOR A",);
						var contextMenuX = contextOffset.left-5;
			    			var contextMenuY = contextOffset.top;
						break;
					}
				}

				//used to work
				//var contextMenuX = event.path[1].offsetLeft;//event.clientX;
				//var contextMenuY = event.path[1].offsetTop;//event.clientY;
			/*} else {
				var contextMenuX = event.srcElement.x;//event.clientX;
				var contextMenuY = event.srcElement.y;//event.clientY;
			}*/
		//}

		if (focusedDriveMounted == "true") {
			$('#properties > a').removeClass("disabled"); //Enable properties option
			$("#openFilesOption").removeClass("hidden"); //Show "Open in Files" option in context menu
			$("#mount").addClass("hidden"); //Hide "Mount" option in context menu
			$("#unmount").removeClass("hidden"); //Show "Safely Remove" option in context menu
			$("#mountedContextMenu > .dropdown-menu").removeClass("unmountedResize-menu"); // Resize menu

		

		/* Avoid user from unmounting the live cd! */
		$('#unmount > a').removeClass("disabled");

		for (var i = 0; i < loadedDrives.length; i++) {
		if (loadedDrives[i].name == focusedDriveName && (loadedDrives[i].mount == "/cdrom" || loadedDrives[i].mount == "/")) {
			$('#unmount > a').addClass("disabled");
			
		}
	    }

		} else {
			$('#properties > a').addClass("disabled"); //Disable properties option
			$("#openFilesOption").addClass("hidden"); //Hide "Open in Files" option in context menu
			$("#mount").removeClass("hidden"); //Show "Mount" option in context menu
			$("#unmount").addClass("hidden"); //Hide "Safely Remove" option in context menu
			$("#mountedContextMenu > .dropdown-menu").addClass("unmountedResize-menu"); // Resize menu


		}

		$(".stackMenuItem").addClass("hidden");
		currentContextMenuType = "stack_item";
		showContextMenu(contextMenuX,contextMenuY);            
                
                return false;
            
            };



} else {


}
}
}
  
  if (firstCheckOnLoad)
    getDriveUsages(true);
  
  firstCheckOnLoad = false;

setTimeout(function(){
win.setMountedDrives(mountedDrives);

}, 2000);
//console.log("mountedDrives",mountedDrives);
//new_win.setDrives();
  }
});
}

function showContextMenu(contextMenuX,contextMenuY) {
$(".folderEditor").addClass("hidden");
$(".folderInfo").removeClass("hidden");
//console.log("contextMenuX: "+contextMenuX+" contextMenuY: "+contextMenuY);
                $("#mountedContextMenu").removeClass("hidden");
		setTimeout(function(){$("#mountedContextMenu > .dropdown-menu").removeClass("zeroHeight");}, 50);
		
		$("#blur").removeClass("hidden");
		if (contextMenuY > ((win.height-46)-225)) {
                $("#mountedContextMenu").css("top",contextMenuY-135);
		} else {
                $("#mountedContextMenu").css("top",contextMenuY+10);
		}

		if (contextMenuX < (160)) {
			$("#mountedContextMenu").css("left",contextMenuX-40);
		} else {
			$("#mountedContextMenu").css("left",(contextMenuX-160)-180);
		}
		setTimeout(function(){
$(".fa-eject").removeClass("randomResize"); //The eject icon doesn't show up until a font size "change". Trying to fix the bug this way
//$(".icon").removeClass("randomResize"); //The icons also doesn't show up anymore until a font size "change". Trying to fix the bug this way
}, 500);  
}

function closeMenu() {
//Reset and close any rename options
	$(".stackRenamer").addClass("hidden");
	$(".label").removeClass("hidden");

focusedDriveName = "";
focusedDriveMounted = "";
$("#mountedContextMenu").addClass("hidden");
$("#mountedContextMenu > .dropdown-menu").addClass("zeroHeight");
$("#mountedContextMenu > .dropdown-menu").removeClass("twoItemsContextHeight");
$("#mountedContextMenu > .dropdown-menu").removeClass("threeItemsContextHeight");
$("#blur").addClass("hidden");
$(".shortcut").removeClass("shortcutFocus");
$(".shortcut").removeClass("shortcutUnfocus");
waitRefresh = false; // Restore the system's ability to refresh when drives are available
//console.log("closeMenu() clicked",$(".stackOpened"));
$(".driveMenuItem").removeClass("hidden");
$(".stackMenuItem").removeClass("hidden");
$(".folderEditor").addClass("hidden");
$(".folderInfo").removeClass("hidden");
//console.log("this is triggered");
if ((currentContextMenuType == "stack" || currentContextMenuType == "") && !doNotCloseStack)
	closeStack();

currentContextMenuType = "";
doNotCloseStack = false;
}


/* Drives Context Menu */
$("#mainBg").append('<div id="mountedContextMenu" class="contextMenu dropdown open hidden" style="margin-left: 180px;">'
                        +'<ul class="dropdown-menu dropdown-menu-alt zeroHeight" role="menu">'
                            +'<li id="openFilesOption" role="presentation" class="driveMenuItem"><a id="filesOption" role="menuitem" tabindex="-1" href="javascript:void(0);"><span><img src="../apps/extern.files.app/icon.svg"></span>Open in Files</a></li>'
                            +'<li role="presentation" class="driveMenuItem"><a role="menuitem" tabindex="-1" href="javascript:void(0);" class="driveMenuItem"><span class="icon randomResize">&#61763;</span> Format</a></li>'
                            +'<li id="properties" role="presentation" class="driveMenuItem"><a role="menuitem" tabindex="-1" href="javascript:void(0);" class="driveMenuItem"><span class="icon randomResize">&#61721;</span> Properties</a></li>'
                            +'<li role="presentation" class="divider driveMenuItem"></li>'
                            +'<li id="unmount" role="presentation" class="driveMenuItem"><a role="menuitem" style="padding-top: 0;" tabindex="-1" href="javascript:void(0);"><span><i class="fa fa-eject randomResize" aria-hidden="true"></i></span> Safely Remove</a></li>'
                            +'<li id="mount" role="presentation" class="driveMenuItem"><a role="menuitem" style="text-align: center;" tabindex="-1" href="javascript:void(0);"> Mount</a></li>'

                            +'<li role="presentation" class="stackMenuItem"><a role="menuitem" style="padding-top: 0;" tabindex="-1" onclick="renameThisStack();" href="javascript:void(0);"><span class="icon randomResize">&#61952;</span> Rename</a></li>'
                            +'<li id="removeStack" role="presentation" class="stackMenuItem"><a onclick="removeStack()" role="menuitem" tabindex="-1" href="javascript:void(0);"><span class="icon randomResize">&#61918;</span> Remove</a></li>'
                        +'</ul>'
                    +'</div>');

checkConnectedDrives();



setInterval(function(){ 
	if (!waitRefresh)
	checkConnectedDrives(); 
}, 5000);

//setTimeout(function(){ checkConnectedDrives(); console.log("Hello"); }, 3000);


$('#unmount > a')[0].addEventListener('click', unMountDrive, false);
$('#mount > a')[0].addEventListener('click', openDrive, false); //Mount only (does not open files)
$('#properties > a')[0].addEventListener('click', showDriveProperties, false);

//setTimeout(function(){ $("#mountedContextMenu").addClass("hidden"); }, 2000);



    (function() {
	if($('.overflow')[0]) {
	    var overflowRegular, overflowInvisible = false;
	    overflowRegular = $('.overflow').niceScroll();
	}
    })();

//https://mobirise.com/bootstrap-carousel/

function getBase64Image(icon,driveToAssignTo) {
var newImg = new Image();

newImg.onload = function() {
        convertImg(newImg,driveToAssignTo);
    }

newImg.src = icon;

}


function  convertImg(img,driveToAssignTo) {
    // Create an empty canvas element
    var canvas = document.createElement("canvas");
    canvas.width = img.width;
    canvas.height = img.height;

    // Copy the image contents to the canvas
    var ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);

    // Get the data-URL formatted image
    var dataURL = canvas.toDataURL("image/png");


    driveToAssignTo.icon = dataURL;

    }



  
  //Call this function from within your .on('dragmove') method.
//It should replace your translations.

function noOverlap(event, overlapElements){

    //just for flagging when the target would overlap another element
    var overlap = false;
    var targetDims = event.target.getBoundingClientRect();

	dx = event.dx;
	dy = event.dy;

	//console.log("dx: "+dx+" dy: "+dy);
	//console.log("x+dx: "+x+dx+" y+dy: "+y+dy);

    for(i = 0; i < overlapElements.length; i++){
        var overlapElementDims =  
        overlapElements[i].getBoundingClientRect();

        //make sure the element doesn't look at itself..
        if(overlapElements[i] != event.target){
            //checks if the target "doesn't" overlap
            if(((targetDims.right + dx) < (overlapElementDims.left + 1)) 
            ||((targetDims.left + 1 + dx) > (overlapElementDims.right)) 
            ||((targetDims.top + 1 + dy) > (overlapElementDims.bottom)) 
            ||((targetDims.bottom + dy) < (overlapElementDims.top + 1))){

            //Basically, the target element doesn't overlap the current 
            //element in the HTMLCollection, do nothing and go to the 
            //next iterate
            }
            else{
                //This is if the target element would overlap the current element

                //set overlap to true and break out of the for loop to conserve time.
		//console.log("overlaps");
                overlap = true;
                break;
            }
        }
    };

/*var rect = event.target.getBoundingClientRect();
console.log(rect.top, rect.right, rect.bottom, rect.left);

console.log("rect.right",rect.right);
console.log('body width',($("body").width()-(50)));

	if (rect.right > ($("body").width()-(50)))
		overlap = true;

	console.log("body width", $("body").width());*/

    if(overlap === false){

	x += event.dx;
    y += event.dy;

    event.target.style.webkitTransform =
    event.target.style.transform =
        'translate(' + x + 'px, ' + y + 'px)';

	

        //if there's no overlap, do your normal stuff, like:
        /*event.target.x += dx;
        event.target.y += dy;

        event.target.style.webkitTransform =
            event.target.style.transform =
                'translate(' + event.target.x + 'px, ' + event.target.y + 'px)';

        //then reset dx and dy
        dy = 0;
        dx = 0;*/
    }
    else{
        if(event.interaction.pointers[event.interaction.pointers.length - 1].type 
        === "pointerup"){

            //check if the target "is" in the restriction zone
            var restriction = 
            interact(event.target).options.drag.restrict.restriction;
            var restrictionDims = restriction.getBoundingClientRect();

            if((targetDims.right > restrictionDims.right) || 
            (targetDims.left < restrictionDims.left) || 
            (targetDims.bottom > restrictionDims.bottom) || 
            (targetDims.top < restrictionDims.top)){
                event.target.style.webkitTransform =
                event.target.style.transform =
                    'translate(0px, 0px)';

                //then reset dx and dy
                dy = 0;
                dx = 0;

                //then reset x and y
                event.target.x = 0;
                event.target.y = 0;
            }
        }       
    } 
}



//https://stackoverflow.com/questions/37545130/how-to-restrict-drag-elements-to-overlap-in-interact-js

//jQuery.data( document.body, "foo", 52 );
//https://api.jquery.com/jquery.data/

var overlapElements = [];

function makeStackDraggable(element) {

overlapElements.push(element);
/*
https://tympanus.net/codrops/2014/03/05/simple-stack-effects/
*/

//var allStackElements = $(".stackIcon");//document.getElementById('grid-snap'),

/*
    x = 0, y = 0;


interact(element)
  .draggable({
    snap: {
      targets: [
        interact.createSnapGrid({ x: 150, y: 65 }) //30
      ],
      range: Infinity,
      relativePoints: [ { x: 0, y: 0 } ]
    },
    inertia: true,
    restrict: {
      restriction: element.parentNode,
      elementRect: { top: 0, left: 0, bottom: 1, right: 1 },
      endOnly: true
    }
  })
  .on('dragend', function (event) {
	justMovedStackPosition = true;
	setTimeout(function(){ justMovedStackPosition = false; }, 100);
	console.log('dragend',event);
   })
  .on('dragmove', function (event) {

	 noOverlap(event, overlapElements);

  });*/


}

//data-row="1" data-col="1" data-sizex="1" data-sizey="1"

var stackIconTemplate = '<li><a id="drivesStack" stackID=0 href="javascript:void(0);" class="shortcut deskIcon stackIcon" title="Drives" folder-control="folderContents">'
				+'<div class="closeFolder hiddenOpacity">'
				+'<img class="closeFolderImg" src="../Shared/CoreIMG/icons/actions/close-icon.png">'
				+'<small> Close</small>'
				+'</div>'
				+'<figure class="stack '+stackStyle+' notActive">'
					+'<img src="../../extern.explorebar/icons/drive-harddisk.svg" alt="img01"/>'
					+'<img src="../../extern.explorebar/icons/drive-harddisk-system.svg" alt="img02"/>'
					+'<img src="../../extern.explorebar/icons/drive-harddisk-system_mount.svg" alt="img03"/>'
				+'</figure>'
+'<small class="label"> Drives </small>'
+'<input onfocus="this.value = this.value;" class="stackRenamer hidden form-control input-sm" type="text" placeholder="Rename Stack" value="Drives">'			
 +'</a></li>';

for (var i = 0; i < allStacks.length; i++) {
	if (allStacks[i].type == "drives") {
		deskStacks.push([stackIconTemplate, 1, 1, allStacks[i].col, allStacks[i].row]);
		break;
	}

}

//http://dsmorse.github.io/gridster.js/#usage




function openfile(fId, stackID, currentFileType) {
var filesToAppend = stackFileContents[stackID].files;
doNotCloseStack = true;

var fileToOpen = filesToAppend[fId];

//console.log("fileToOpen",fileToOpen);

//console.log("win.fileTypesApps",win.fileTypesApps);
var filesToOpen = [];
filesToOpen.push(fileToOpen.location);

if (fileToOpen.isDirectory) {
win.openApp("extern.files.app",fileToOpen.location);
setTimeout(function(){ doNotCloseStack = false; closeMenu(); }, 2000);
} else {
var requiredApps = win.fileTypesApps.prefferedFileTypesApps;//fileTypesApps;//.audio;
        //console.log("FILE OPENED AS MIME",requiredApps[currentFileType]);
        if (requiredApps[currentFileType] != null) {
            //App.openWithApp(requiredApps[currentFileType].id);

	  win.openApp(requiredApps[currentFileType].id,filesToOpen);
	setTimeout(function(){ doNotCloseStack = false; closeMenu(); }, 2000);
            
        }
        else {
            //console.log("ITS  NULL"); 
        }
}

//win.openApp(App,$.filesToOpen);
}




var currentDiv;

function setContetMenusOnStack(el) {
	//[].slice.call( document.querySelectorAll( '.deskIcon' ) ).forEach( function( el ) {
		var togglebtt = el,//.previousElementSibling,
			togglefn = function(e) {
              if (!stackDragged && (!$(this).find(".label").hasClass("hidden"))) { //justMovedStackPosition && if we are in rename mode, don't activate
				doNotCloseStack = true;
				//console.log("togglefn",e);
				
				//console.log("small",$(currentlyOpenedStack).find( "small.label" ));
				//console.log("clicked",$(this).find(".stack").hasClass( 'notActive' ));
				if( $(this).find(".stack").hasClass( 'notActive' ) ) {
					var contextOffset = $(this).offset();
				var stackX = contextOffset.left-5;
			    	var stackY = contextOffset.top;
				var pileFrom = "pileTopRight";
				var animateXFrom = "right";
				var animateYFrom = "top"

				//console.log("stackX: "+stackX);
                  if (stackX < (win.width/2)) {
                    $(".folderContents").css("top",stackY+10);
                	$(".folderContents").css("left",(stackX+90));
			//$("."+$(this).attr("folder-control")).addClass("animated slideInLeft");
			pileFrom = "pileTopLeft";
			animateXFrom = "left";
			//console.log("animateXFrom",animateXFrom);
                  } else {
                    $(".folderContents").css("top",stackY+10);
                	$(".folderContents").css("left",(stackX-770));
			$("."+$(this).attr("folder-control")).addClass("animated slideInRight");
                  }

		  if (stackY > (win.height-526)) {
			var animateYFrom = "bottom";
			$(".folderContents").css("top",stackY-400);

		  } else {
			$(".folderContents").css("top",stackY+10);

		   }

				currentlyOpenedStack = this;
					$("#blurWallpaper").addClass("hiddenOpacity");
					//$("#blurWallpaper").removeClass("hidden");
					setTimeout(function(){$("#blurWallpaper").removeClass("hiddenOpacity");}, 300);

                  if (this.id == "drivesStack") {
					$("#drives").removeClass("hidden");
                    
                    $("#drives").attr("animateyfrom",animateYFrom);
                  	$("#drives").attr("startyfrom",0);
					$("#drives").attr("animatexfrom",animateXFrom);
					$("#drives").attr("startxfrom",-120);
                    
                    $(".tempDriveIcon").each(function(){
                      $(this).css(animateYFrom,$("#drives").attr("startyfrom"));
                      $(this).css(animateXFrom,$("#drives").attr("startxfrom"));
                    });
                    
                    
                  } else {
					$("#files").empty();
					$("#files").removeClass("hidden");
					var filesToAppend = stackFileContents[$(this).attr("filesLocation")].files;

					var maxNumberOfDrviesPerColumn = Math.floor(win.height/140);
					var addedIcons = 1;
					var addedIconsCurrentRow = 0;
					var currentRowNum = 0;
					var iconPositionX = 0;
					var iconPositionY = 0;
					$("#files").attr("animateyfrom",animateYFrom);
                  			$("#files").attr("startyfrom",0);
					$("#files").attr("animatexfrom",animateXFrom);
					$("#files").attr("startxfrom",-120);
					for (var m = 0; m < filesToAppend.length; m++) {
							$("#files").append('<li id="stackFile'+m+'" xpos = "'+iconPositionX+'" ypos = "'+iconPositionY+'" style="'+animateYFrom+': 0px; '+animateXFrom+': 0px;" class="tempStackFile"><a href="javascript:void(0);" onclick="openfile('+m+','+$(this).attr("filesLocation")+',&quot;'+filesToAppend[m].fileType+'&quot;)" class="shortcut iconSizeA"> <img src="'+filesToAppend[m].fileIcon+'"> <small> '+filesToAppend[m].name+' </small></a></li>');
					var oldaddedIconsCurrentRow = addedIconsCurrentRow;


					addedIconsCurrentRow = Math.floor(addedIcons/5);
					iconPositionY = (170*addedIconsCurrentRow);

						if (addedIconsCurrentRow > oldaddedIconsCurrentRow) {
						iconPositionX = 0;
						} else {
						iconPositionX += 150;
						}

						addedIcons++;

					}
				}

					$(".stackOpened").click();
					currentDiv = this;
					$(".folderInfo > a > h3").text($(currentlyOpenedStack).find( "small.label" ).text());
					$("#stackRenamer").val($(currentlyOpenedStack).find( "small.label" ).text());
					$(".stackIcon").not(this).addClass("hiddenOpacity");
					setTimeout(function(){ $(".stackIcon").not(currentDiv).addClass("hidden"); }, 1000);
					
					$(this).addClass("stackOpened");
					$(this).find(".stack").removeClass( 'notActive' );
					//$("."+$(this).attr("folder-control")).addClass("animated slideInRight");
					$("."+$(this).attr("folder-control")).addClass("hiddenOpacity");
					$("."+$(this).attr("folder-control")).removeClass("hidden");
					
					setTimeout(function(){ $("."+$(currentDiv).attr("folder-control")).removeClass("hiddenOpacity");}, 300); 
					//setTimeout(function(){ $("."+$(currentDiv).attr("folder-control")).addClass("addBlur"); /*$(currentDiv).addClass("addBlur");*/}, 400);
					
					
					
					$(this).find("figure").addClass("hiddenOpacity");
					$(this).find(".closeFolder").removeClass("hiddenOpacity");
					$(this).find(".closeFolder").addClass("smallerCloseButton");
					$(this).find(".label").addClass("hiddenOpacity");
                  
                  if (this.id == "drivesStack") {
			if (animateXFrom != "left")
                      		$(".tempDriveIcon").css("left","");
			else
		      		$(".tempDriveIcon").css("right","");
		      if (animateYFrom != "top")
		      		$(".tempDriveIcon").css("top","");
		      else	
		      		$(".tempDriveIcon").css("bottom","");	

                    setTimeout(function(){  
                      
                      $(".tempDriveIcon").each(function(){
                        var ypos = parseInt($(this).attr("ypos"));
						var xpos = parseInt($(this).attr("xpos"));		
                      $(this).css(animateYFrom,ypos);
                      $(this).css(animateXFrom,xpos);
                    });
                      
                      /*
					for (var m = 0; m < filesToAppend.length; m++) {

						console.log('$("#stackFile"+m)',$("#stackFile"+m));
						var ypos = parseInt($("#stackFile"+m).attr("ypos"));
						var xpos = parseInt($("#stackFile"+m).attr("xpos"));
						console.log("set to y: ",ypos);
						$("#stackFile"+m).css(animateYFrom,ypos);
						$("#stackFile"+m).css(animateXFrom,xpos);
					}*/

}, 100);
                    
                  } else {
					setTimeout(function(){ //$(".folderContents > ul > li").removeClass(pileFrom); 

                      			$(".tempStackFile").each(function(){
					//for (var m = 0; m < filesToAppend.length; m++) {

						//console.log('$("#stackFile"+m)',$("#stackFile"+m));
						var ypos = parseInt($(this).attr("ypos"));
						var xpos = parseInt($(this).attr("xpos"));
						//console.log("set to y: ",ypos);
						$(this).css(animateYFrom,ypos);
						$(this).css(animateXFrom,xpos);
					//}
					});

}, 100); 
                  }
					
					
				}
				else {
					closeStack();
					/*$(".folderEditor").addClass("hidden");
					$(".folderInfo").removeClass("hidden");
					$(this).removeClass("stackOpened");
					$("."+$(currentDiv).attr("folder-control")).removeClass("addBlur");
					$(this).find(".stack").addClass( 'notActive' );
					$("."+$(this).attr("folder-control")).addClass("hidden");
					$("."+$(this).attr("folder-control")).removeClass("animated slideInRight");
					//$(this).removeClass("addBlur");
					$(this).find("figure").removeClass("hiddenOpacity");
					$(this).find(".closeFolder").addClass("hiddenOpacity");
					$(this).find(".closeFolder").removeClass("smallerCloseButton");
					$(this).find(".label").removeClass("hiddenOpacity");
					$("#drives").addClass("hidden");
					$("#files").addClass("hidden");*/
				}
            }
              
              stackDragged = 0;
			};
		//console.log("el",togglebtt);

		togglebtt.addEventListener( 'click', togglefn );
	//} );
};


function closeStack() {
					$("#blurWallpaper").addClass("hiddenOpacity");
					//setTimeout(function(){  $("#blurWallpaper").addClass("hidden");}, 800);
					if (currentDiv != null) {
					if (currentDiv.id == "drivesStack") {
  					$(".tempDriveIcon").css($("#drives").attr("animateyfrom"),parseInt($("#drives").attr("startyfrom")));
					$(".tempDriveIcon").css($("#drives").attr("animatexfrom"),parseInt($("#drives").attr("startxfrom")));
					} else {
  					$(".tempStackFile").css($("#files").attr("animateyfrom"),parseInt($("#files").attr("startyfrom")));
					$(".tempStackFile").css($("#files").attr("animatexfrom"),parseInt($("#files").attr("startxfrom")));

					}
					}
					
					//$(".folderContents > ul > li").addClass("pileTopRight");
					
					setTimeout(function(){   
					$(".folderContents").addClass("hiddenOpacity");

					}, 200);
					setTimeout(function(){  
					//$("#files").addClass("hidden"); 
					$("."+$(".stackOpened").attr("folder-control")).removeClass("addBlur");
					$(".stackOpened").find(".stack").addClass( 'notActive' );
					$("."+$(".stackOpened").attr("folder-control")).addClass("hidden");
					$("."+$(".stackOpened").attr("folder-control")).removeClass("animated slideInRight");
					$("."+$(".stackOpened").attr("folder-control")).removeClass("animated slideInLeft");
					//$(this).removeClass("addBlur");
					$(".stackOpened").find("figure").removeClass("hiddenOpacity");
					$(".stackOpened").find(".closeFolder").addClass("hiddenOpacity");
					$(".stackOpened").find(".closeFolder").removeClass("smallerCloseButton");
					$(".stackOpened").find(".label").removeClass("hiddenOpacity");
					$(".stackOpened").removeClass("stackOpened");
					$("#drives").addClass("hidden");
					$("#files").addClass("hidden");
					$(".stackIcon").removeClass("hidden");
					$(".stackIcon").removeClass("hiddenOpacity");
					}, 400);
}

/*
$('.stackIcon').on('contextmenu', function(e){
  	e.stopPropagation();
  	e.preventDefault();
  	// Your code.
  	console.log("slack icon clicked",e);
  	var contextOffset = $(e.currentTarget).offset();
  	$(e.currentTarget).removeClass("shortcutUnfocus");
	$(".driveMenuItem").addClass("hidden");
	console.log("POS FOR A",);
	var contextMenuX = contextOffset.left-25;
	var contextMenuY = contextOffset.top;
	currentContextMenuType = "stack";
	$("#mountedContextMenu > .dropdown-menu").addClass("threeItemsContextHeight");
	closeStack();
  	showContextMenu(contextMenuX,contextMenuY);  
});*/

function showStackEditor() {
	$(".folderInfo").addClass("hidden");
	$(".folderEditor").removeClass("hidden");
	$("#stackRenamer").focus();
}



//const stackLocation = '/home/extern/Projects/Files';
const fs = require('fs');
var currentStackBeingLoaded = 1;

//console.log("gets here",allStacks.length);

function loadStackFiles(stackPosition) {
//for (var m = 1; m < allStacks.length; m++) {
  
  var stackLocation = allStacks[stackPosition].location;

fs.readdir(stackLocation, (err, files) => {
var stackFiles = [];
  files.forEach(file => {
    //console.log("file",file);
	var fileInfo = {
		file: file,
		isDirectory: fs.lstatSync(stackLocation+'/'+file).isDirectory(),
		fullUrl: stackLocation+'/'+file 
	}
	stackFiles.push(fileInfo);	
  });
	//console.log("stackFiles",allStacks[currentStackBeingLoaded]);
	appendStack(stackLocation,stackFiles,allStacks[currentStackBeingLoaded]);
})
//console.log("LOL1");
  
//}
}
  
  if (allStacks.length > 1)
    loadStackFiles(currentStackBeingLoaded);
  else
	loadGridster();

function appendStack(location,stackContents, desktopStackData) {
//var stackID = "stackFiles";

tempStackFiles = [];

for (var i = 0; i < stackContents.length; i++) {
	if (stackContents[i].isDirectory) {
		var fileIcon = "../../apps/extern.files.app/icons/"+win.resolveFileType("*folder*",true);
		var fileType = "folder";
	} else {
		var fileIcon = "../../apps/extern.files.app/icons/"+win.resolveFileType(stackContents[i].file.split('.').pop(),true);
		var fileType = win.resolveFileType(stackContents[i].file.split('.').pop(),false);
}
	var tempFile = {
		name: stackContents[i].file.split('\\').pop().split('/').pop(),
		location: stackContents[i].fullUrl,
		fileIcon: fileIcon,
		fileType: fileType,
		isDirectory: stackContents[i].isDirectory
	}
	//console.log("extension",stackContents[i].file.split('.').pop());
	tempStackFiles.push(tempFile);
}


	var tempStack = {
			name: location.split('\\').pop().split('/').pop(),
			location: location,
			files: tempStackFiles
	}
	stackFileContents.push(tempStack);

	//console.log("stackFileContents",stackFileContents);

	//We want atleast 3 file icons. We want to avoid folders as much as possible. We also want to avoid unknown files
	var finalIcons = []; //store the three icons of interest here
	 if (stackFileContents[stackFileContents.length-1].files.length > 2) {
		for (var k = 0; k < stackFileContents[stackFileContents.length-1].files.length; k++)
			if (!stackFileContents[stackFileContents.length-1].files[k].isDirectory)
				finalIcons.push(stackFileContents[stackFileContents.length-1].files[k].fileIcon);

			for (var k = 0; k < stackFileContents[stackFileContents.length-1].files.length; k++) {
				if (stackFileContents[stackFileContents.length-1].files[k].isDirectory)
				finalIcons.push(stackFileContents[stackFileContents.length-1].files[k].fileIcon);
			}
     } else if (stackFileContents[stackFileContents.length-1].files.length > 1){
       finalIcons.push(stackFileContents[stackFileContents.length-1].files[0].fileIcon);
       finalIcons.push(stackFileContents[stackFileContents.length-1].files[1].fileIcon);
       finalIcons.push(stackFileContents[stackFileContents.length-1].files[1].fileIcon);
                } else {
                  finalIcons.push(stackFileContents[stackFileContents.length-1].files[0].fileIcon);
                  finalIcons.push(stackFileContents[stackFileContents.length-1].files[0].fileIcon);
                  finalIcons.push(stackFileContents[stackFileContents.length-1].files[0].fileIcon);
                }

/*
$('#deskStacksContainter').append('<li data-row="2" data-col="1" data-sizex="1" data-sizey="1"><a id="'+stackID+'" href="javascript:void(0);" class="shortcut deskIcon stackIcon" title="'+stackFileContents[stackFileContents.length-1].name+'" folder-control="folderContents" filesLocation='+(stackFileContents.length-1)+'>'
				+'<div class="closeFolder hiddenOpacity">'
				+'<img class="closeFolderImg" src="../Shared/CoreIMG/icons/actions/close-icon.png">'
				+'<small> Close</small>'
				+'</div>'
				+'<figure class="stack stack-sideslide notActive">'
					+'<img src="'+finalIcons[2]+'" alt="img01"/>'
					+'<img src="'+finalIcons[1]+'" alt="img02"/>'
					+'<img src="'+finalIcons[0]+'" alt="img03"/>'
				+'</figure>'
+'<small class="label">'+stackFileContents[stackFileContents.length-1].name+'</small>'			
 +'</a></li>');*/

// data-row="2" data-col="1" data-sizex="1" data-sizey="1"

//console.log("desktopStackData",desktopStackData);
//console.log("stackFileContents",stackFileContents);

var stackIconTemplate = '<li><a href="javascript:void(0);" class="shortcut deskIcon stackIcon" title="'+stackFileContents[stackFileContents.length-1].name+'" folder-control="folderContents" stackID='+desktopStackData.id+' filesLocation='+(stackFileContents.length-1)+'>'
				+'<div class="closeFolder hiddenOpacity">'
				+'<img class="closeFolderImg" src="../Shared/CoreIMG/icons/actions/close-icon.png">'
				+'<small> Close</small>'
				+'</div>'
				+'<figure class="stack '+stackStyle+' notActive">'
					+'<img src="'+finalIcons[2]+'" alt="img01"/>'
					+'<img src="'+finalIcons[1]+'" alt="img02"/>'
					+'<img src="'+finalIcons[0]+'" alt="img03"/>'
				+'</figure>'
+'<small class="label">'+stackFileContents[stackFileContents.length-1].name+'</small>'
+'<input onfocus="this.value = this.value;" class="stackRenamer hidden form-control input-sm" type="text" placeholder="Rename Stack" value="'+stackFileContents[stackFileContents.length-1].name+'">'				
 +'</a></li>';



deskStacks.push([stackIconTemplate, 1, 1, desktopStackData.col, desktopStackData.row]);
  
  currentStackBeingLoaded += 1;
  
  if(currentStackBeingLoaded >= allStacks.length) {
    loadGridster();
  } else {
    loadStackFiles(currentStackBeingLoaded);
  }


//deskStacks.push([stackIconTemplate,1,1,2,1]);
/*
    $("#deskStacksContainter").gridster({
        widget_margins: [10, 10],
	min_rows: 2,
	min_cols: 5,
	max_cols: Math.floor(win.width/170),
	shift_widgets_up: false,
	shift_larger_widgets_down: false,
            collision: {
                wait_for_mouseup: true
            },
        widget_base_dimensions: [160, 140]
    }).data('gridster');


$.each(widgets, function (i, widget) {
            gridster.add_widget.apply(gridster, widget)
        });*/



//Gridster was here



}

var gridsterAlreadyLoaded = false;
var gridster;
var lastAddedGridsterPosition = 0;

function loadGridster() {

      

    $(function () {

	if (!gridsterAlreadyLoaded) {
        gridster = $("#deskStacksContainter").gridster({
        widget_margins: [10, 10],
	min_rows: 2,
	min_cols: 5,
	max_cols: Math.floor(win.width/170),
	max_rows: Math.floor(win.height/140),
	shift_widgets_up: false,
	shift_larger_widgets_down: false,
              draggable: {
        start: function(event, ui) {
	    closeStack(); //checked
            stackDragged = 1;
            // DO SEOMETHING
        },

	stop: function(event, ui){ 
		//console.log("drag stop event:", event);
		//console.log("drag stop ul:", ui);

		var test = ui.$player[0].dataset;
  //console.log('draggable stop test = ' + JSON.stringify(test));

	var newrow = ui.$player[0].dataset.row;
var newcol = ui.$player[0].dataset.col;

	var stackID = $(ui.$player[0].children[0]).attr("stackID");

	//console.log("allStacks",allStacks);

	for (var i = 0; i < allStacks.length; i++) {
		if (allStacks[i].id == stackID) {
			//console.log("found");
			allStacks[i].row = newrow;
			allStacks[i].col = newcol;
			break;
		}
	}

	//console.log("found allStacks",allStacks);

	//console.log("found allStacks stackInformation",stackInformation);

	localStorage.setItem('allStacks', JSON.stringify(stackInformation));

	//console.log("LOOL", JSON.parse(localStorage.getItem('allStacks')));


	//console.log("stackID:", stackID);
	//console.log("newrow:", newrow);
	//console.log("newcol:", newcol);

//https://stackoverflow.com/questions/27915907/how-to-get-new-col-and-row-on-drag-stop-event-in-gridster
                             // your events here
                }
    },
            collision: {
                wait_for_mouseup: true
            },
        widget_base_dimensions: [160, 140]
        }).data('gridster');




	//makeStackDraggable($("#drivesStack")[0]);

	//console.log("deskIcons",$(".deskIcon"));

    } //else {
      
      $.each(deskStacks, function (i, widget) {
        if (lastAddedGridsterPosition <= i) {
            gridster.add_widget.apply(gridster, widget);
            lastAddedGridsterPosition = (i+1);
	    //console.log("widget",widget);
          }

        });
      
      /*$.each(deskStacks, function (i, widget) {
	console.log("widget add attemt");
            gridster.add_widget.apply(gridster, widget);
	    console.log("widget",widget);
        });*/
      
    //}

$(".stackRenamer").change(function() {
  // Check input( $( this ).val() ) for validity here
  //console.log("stack renamed");
  //$(currentlyOpenedStack).attr("title",$("#stackRenamer").val());
  //$(currentlyOpenedStack).find( "small.label" ).text( $(currentlyOpenedStack).find(".stackRenamer").val());
  $(currentlyStackShowingContextMenu).attr("title",$(currentlyStackShowingContextMenu).find(".stackRenamer").val());
  $(currentlyStackShowingContextMenu).find( "small.label" ).text( $(currentlyStackShowingContextMenu).find(".stackRenamer").val());
  $(".folderInfo > a > h3").text($(currentlyStackShowingContextMenu).find(".stackRenamer").val());

$(currentlyStackShowingContextMenu).find(".label").removeClass("hidden");
$(currentlyStackShowingContextMenu).find(".stackRenamer").addClass("hidden");
});

$(".stackRenamer").click(function(e) {
   // Do something
   e.stopPropagation();
});


	$( ".stackIcon" ).each(function( index ) {
  //console.log( index + ": " + $( this ).text() );
		
      
      if (!$(this).hasClass("addedContextMenuEvent")) {
        setContetMenusOnStack(this);
        $(this).addClass("addedContextMenuEvent");
$(this).on('contextmenu', function(e){
  	e.stopPropagation();
  	e.preventDefault();
  	
	currentlyStackShowingContextMenu = e.currentTarget;
	
	//Reset and close any rename options
	$(".stackRenamer").addClass(".hidden");
	$(".label").removeClass(".hidden");

  	//console.log("slack icon clicked",e);

	if (this.id == "drivesStack")
		$("#removeStack > a").addClass("disabled");
	else
		$("#removeStack > a").removeClass("disabled");
	
  	var contextOffset = $(e.currentTarget).offset();
  	$(e.currentTarget).removeClass("shortcutUnfocus");
	$(".driveMenuItem").addClass("hidden");
	//console.log("POS FOR A",);
	var contextMenuX = contextOffset.left-25;
	var contextMenuY = contextOffset.top;
	currentContextMenuType = "stack";
	$("#mountedContextMenu > .dropdown-menu").addClass("threeItemsContextHeight");
	closeStack();
  	showContextMenu(contextMenuX,contextMenuY);  
});
      }
});

gridsterAlreadyLoaded = true;


    });
  
      /*var gridster;

        gridster = $(".gridster ul").gridster({
            widget_base_dimensions: [100, 100],
            widget_margins: [5, 5],
            shift_widgets_up: false,
            shift_larger_widgets_down: false,
            collision: {
                wait_for_mouseup: true
            }
        }).data('gridster');*/


/*makeStackDraggable($("#"+stackID)[0]);

setContetMenusOnStack($("#"+stackID)[0]);

$("#"+stackID).on('contextmenu', function(e){
  	e.stopPropagation();
  	e.preventDefault();
  	// Your code.
  	console.log("slack icon clicked",e);
  	var contextOffset = $(e.currentTarget).offset();
  	$(e.currentTarget).removeClass("shortcutUnfocus");
	$(".driveMenuItem").addClass("hidden");
	console.log("POS FOR A",contextOffset );
	var contextMenuX = contextOffset.left-25;
	var contextMenuY = contextOffset.top;
	currentContextMenuType = "stack";
	$("#mountedContextMenu > .dropdown-menu").addClass("threeItemsContextHeight");
	closeStack();
  	showContextMenu(contextMenuX,contextMenuY);  
});

*/
  
  
}

function renameThisStack() {
closeMenu();
//console.log("renameThisStack()");
$(currentlyStackShowingContextMenu).find(".label").addClass("hidden");
$(currentlyStackShowingContextMenu).find(".stackRenamer").removeClass("hidden");
$(currentlyStackShowingContextMenu).find(".stackRenamer").focus();
$(currentlyStackShowingContextMenu).find(".stackRenamer").scrollLeft = $(currentlyStackShowingContextMenu).find(".stackRenamer").scrollWidth;
//$(currentlyStackShowingContextMenu).find(".stackRenamer").select();
}

//setContetMenusOnStack();

/*
Simulate drag

interact(element).fire({
  type: 'dragstart',
  target: element,
  pageX: 10,
  ...
});

*/






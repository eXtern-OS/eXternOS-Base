var dlToRemove;
var stopDownloadRequest;
var dlCounts = 0;

	function closeDeleteDownloadWindow(closeDeleteDownloadWindowResponse) {
		if (closeDeleteDownloadWindowResponse.type == "cancel") {
			App.closeCustomModal();
		} else if (closeDeleteDownloadWindowResponse.type == "remove") {
			if (dlToRemove != null) {
				chrome.downloads.erase({
					id: dlToRemove.dlId
				}, 
				erasedIds => {
					console.log("erasedIds: ",erasedIds);
					clearInterval(downloadIntervals[dlToRemove.dlId]);
					downloadIntervals[dlToRemove.dlId] = null;
					$("#dl"+dlToRemove.countId).remove();
					App.closeCustomModal();
					stopDownloadRequest = null;
					dlToRemove = null;
				});
			}
		}
	}

	function  requestToStopDownload() {
  var messageBodyData = '<div class="row" style="text-align: center; margin-bottom: 10px;">'
                                        +'It looks like this item is still downloading. Do you want to cancel the download and remove this entry?'
                                    +'</div>';

  var messageBody = {
    title: "Item is still downloading...",
    data: messageBodyData
  }

  var inputElements = {
    buttons: []
  }

  inputElements.closeModal = {
    callback: closeDeleteDownloadWindow,
    callbackData: {
      type: "cancel"
    }
  }

	inputElements.buttons.push({
    text: "Cancel",
    pullLeft: true,
    callback: closeDeleteDownloadWindow,
    callbackData: {
      type: "cancel"
    }
		});

	  inputElements.buttons.push({
    text: "Remove",
    pullRight: true,
    callback: closeDeleteDownloadWindow,
    callbackData: {
      type: "remove"
    }
		});

  inputElements.buttons.centerise = true;

  stopDownloadRequest = App.openCustomModal(messageBody,inputElements);
}

function customDownload(dlUrl) {
		if (dlCounts == 0){
			$("#downloadsInner").empty();
		}

		
		handleDownload(dlUrl,downloadLocation,dlCounts);
		dlCounts++;
		
		
	}

function convertBytes(currentSpeed){
		var speed_reduction_level = 0;
		
		while (currentSpeed >= 1000){
			currentSpeed /=1000;
			speed_reduction_level++;
		}
		
		/*Check if its a whole number or not*/
		if (currentSpeed % 1 !== 0){
			currentSpeed = currentSpeed.toFixed(2);
		}
			  
		  
		switch(speed_reduction_level){
			case 0: currentSpeed +=" B/s"; break;
			case 1: currentSpeed +=" KB/s"; break;
			case 2: currentSpeed +=" MB/s"; break;   
			case 3: currentSpeed +=" GB/s"; break;
			case 4: currentSpeed +=" TB/s"; break;
			case 5: currentSpeed +=" PB/s"; break;
			case 6: currentSpeed +=" EB/s"; break;
			case 7: currentSpeed +=" ZB/s"; break;
		}
		
		return currentSpeed;
	}


function reDownload(dlId, dlCount) {
		chrome.downloads.search({
			id: dlId
		}, download => {
			var dlUrl = download[0].url;
			cancelDownload(dlId, dlCount);
			
			handleDownload(dlUrl,downloadLocation,dlCounts,dlCount);
			dlCounts++;
		});
	}

function cancelDownload(downloadToCancel, dlCount) {
		console.log("downloadToCancel: ",downloadToCancel);
		chrome.downloads.cancel(downloadToCancel
		, () => {
			
			clearInterval(downloadIntervals[downloadToCancel]);
			$("#dl"+dlCount+" .reDownload").removeClass("hidden");
			$("#dl"+dlCount+" .cancelDownload").addClass("hidden");
			$("#dl"+dlCount+"eta").text("Canceled");
			
			});
	}


	function removeDownload(downloadToCancel, dlCount) {
		chrome.downloads.search({
			id: downloadToCancel
		}, download => {
			if (download[0].state == "in_progress") {
				dlToRemove = {
					dlId: downloadToCancel,
					countId: dlCount
				};
				console.log("still downloading..");
				requestToStopDownload();
			} else {
				chrome.downloads.erase({
					id: downloadToCancel
				}, 
				erasedIds => {
					console.log("erasedIds: ",erasedIds);
					$("#dl"+dlCount).remove();

					if ($('#downloadsInner').contents().length == 0)
						$("#downloadsInner").append("<h3>No new downloads for this session.</h3>");
				});
			}
		});



	}

	function copyDownloadLink(dlId) {
		
		chrome.downloads.search({
			id: dlId
		}, download => {
			clipboard.set(download[0].url, 'text');
			console.loh("copied url");
		});
	}

var max_speed = 0;

	function addDownloadUIItem(dlCount,dlId,complted) {
		$("#downloadsInner").prepend('<div id="dl'+dlCount+'" class="downloadDiv"><div id="divProgress'+dlCount+'" class="dlProgressDiv"></div><div id="dl'+dlCount+'Text" class="dlTextDiv"><p id="dl'+dlCount+'label" class="dlTextName">Downloading...</p><p id="dl'+dlCount+'speed" class="dlText">0 Mb/s</p><p id="dl'+dlCount+'eta"class="dlText" >About <span id="dl'+dlCount+'eta">Estimating...</span> remaining</p><p id="dl'+dlCount+'downloading"class="dlText hidden" >Getting there....</p><div class="dldoneOptions hidden"><a href="#" style="margin-right: 10px;" class="btn btn-alt btn-sm">Open</a><a href="#" class="btn btn-alt btn-sm"><img style="height: 18px;" src="../extern.files.app/icon.svg"> Open in Files</a></div></div>'
		+'<div class="tile-config dropdown">'
                                    +'<a data-toggle="dropdown" href="#" class="tooltips tile-menu" title="" data-original-title="Options"></a>'
                                    +'<ul class="dropdown-menu pull-right text-right" style="height: auto;">'
																				+'<li class="reDownload hidden"><a href="#" onclick="reDownload('+dlId+','+dlCount+')">Download Again</a></li>'
																				+'<li class="copyDownloadUrl hidden"><a href="#" onclick="copyDownloadLink('+dlId+')">Copy Download Link</a></li>'
                                        +'<li class="cancelDownload"><a href="#" onclick="cancelDownload('+dlId+','+dlCount+')">Cancel</a></li>'
                                        +'<li><a href="#" onclick="removeDownload('+dlId+','+dlCount+')"><span class="icon">&#61918;</span> Remove</a></li>'
                                    +'</ul>'
                                +'</div>'
		
		+'</div>');
		$("#divProgress"+dlCount).circularloader({
			backgroundColor: "transparent",//background colour of inner circle
			fontColor: "rgba(255, 255, 255, 0.6)",//font color of progress text
			fontSize: "15px",//font size of progress text
			radius: 20,//radius of circle
			progressBarBackground: "rgba(0,0,0,0.2)",//background colour of circular progress Bar
			progressBarColor: "rgba(0,0,0,0.5)",//colour of circular progress bar
			progressBarWidth: 5,//progress bar width
			progressPercent: 0,//progress percentage out of 100
			progressValue:0,//diplay this value instead of percentage
			showText: true,//show progress text or not
		});
	}

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

function toHHMMSS(secs) {
				var sec_num = parseInt(secs, 10); // don't forget the second param
				var hours   = Math.floor(sec_num / 3600);
				var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
				var seconds = sec_num - (hours * 3600) - (minutes * 60);
					var time = "";
					if (hours != 0)
						time += hours+" hours ";
					if (minutes != 0)
						time += minutes+" minutes ";
					
					if (seconds != 0)
						time += seconds+" seconds";
					else
						if (time == "")
							time = "Getting there.....";

				if (isNaN(hours) || isNaN(minutes) || isNaN(seconds))
					time = "-";
					
				return time;
			}

var progress = require('request-progress');

	var downloadIntervals = {}; //store intervals to cancel if user requests to cancel a download
	
	function handleDownload(url,destination,dlCount,removeThisDl){


		console.log("dl added");

		var doownloadReady = false;



var downloadId;
var monitoredDOwnloads;
var filename = "";
var completedTime = false;

chrome.downloads.setShelfEnabled(false);

// listen for events

handleStateChange = delta => {
	console.log("delat event: ",delta);

		
};


chrome.downloads.download({
    url: url,
		filename: url.split('/').pop(),
		conflictAction: "uniquify",
		saveAs: false,
}, newDownloadId => {
	console.log("new Id: ",newDownloadId);
    downloadId = newDownloadId;
});
var firstResProcessed = false;
// monitor progress. Wish there was like an event being triggered but here we are. Probably would too much?
monitoredDOwnloads = setInterval(function(){ 
chrome.downloads.search({
    id: downloadId
}, download => {
	if (!firstResProcessed) {
		console.log("current downloads: ",download);
		console.log("downloadId: ",downloadId);
		console.log("download.id: ",download[0].id);
	}
		


	firstResProcessed = true;

    downloadObject = download[0];


		if (filename == "" && downloadObject.filename != "") {
			addDownloadUIItem(dlCount,download[0].id);
			filename = downloadObject.filename.split("/").pop();
			$("#dl"+dlCount+"label").text(filename);
			console.log("new file added now");
			downloadIntervals[download[0].id] = monitoredDOwnloads; //Seems dodgey, but it's faster to look for later instead of looping etc
			if ($("#downloadsContainer").hasClass("hidden")) { //Auto show
				openDownloads();
			}
			if (removeThisDl != null)
				$("#dl"+removeThisDl).remove();
			
		} else {

			var percentage = (downloadObject.bytesReceived/downloadObject.totalBytes)*100;

			$("#divProgress"+dlCount).remove();
			$("#dl"+dlCount).prepend('<div id="divProgress'+dlCount+'" class="dlProgressDiv"></div>');
			
			$("#divProgress"+dlCount).circularloader({
				backgroundColor: "transparent",//background colour of inner circle
				fontColor: "rgba(255, 255, 255, 0.6)",//font color of progress text
				fontSize: "15px",//font size of progress text
				radius: 20,//radius of circle
				progressBarBackground: "rgba(0,0,0,0.1)",//background colour of circular progress Bar
				progressBarColor: "rgba(255,255,255,0.2)",//colour of circular progress bar
				progressBarWidth: 5,//progress bar width
				progressPercent: percentage,//progress percentage out of 100
				progressValue:0,//diplay this value instead of percentage
				showText: true,//show progress text or not
			});
		
		$("#dl"+dlCount+"speed").text(convertBytes(downloadObject.bytesReceived)+" of "+convertBytes(downloadObject.totalBytes));


		const diffTime = Math.abs(new Date((downloadObject.estimatedEndTime)) - (new Date()));

	

		if (!isNaN(diffTime) && !completedTime) {
			var timeRemaining = toHHMMSS(diffTime/1000);
			if (timeRemaining == "Getting there.....")
				completedTime = true;
			
			$("#dl"+dlCount+"eta").text(timeRemaining);
		}

		

		if (downloadObject.state == "complete") {
			console.log("download completed");
			$("#dl"+dlCount).addClass("completedDl");
			$("#dl"+dlCount+" .dldoneOptions").removeClass("hidden");
			$("#dl"+dlCount+"eta").text("Done");
			$("#dl"+dlCount+" .cancelDownload").addClass("hidden");
			if (stopDownloadRequest != null) {
				App.closeCustomModal();
				stopDownloadRequest = null;
			}
			clearInterval(monitoredDOwnloads);
		}
		}
		

});
}, 1000);



	}
    


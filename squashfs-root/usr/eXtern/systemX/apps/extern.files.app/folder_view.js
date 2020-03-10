console.log("RIGHT CLICK ICON",this);
var events = require('events');
var fs = require('fs-extra');
var path = require('path');
var jade = require('jade');
var util = require('util');
var mime = require('/usr/eXtern/systemX/apps/extern.files.app/mime.js');
var currentlyInMultiSelectFilesMode = false;
var localVars = {};
var path = require('path');

//localVars.locationHistory = []; //FIXME replaces the old way of storing history in an html element (I know I was still learning JS at the time, probably did it to resolce some problem I was experiencing haha).
//localVars.locationHistoryCurrentPos = 0;

//var location_history = [process.env['HOME']];



// Template engine
var gen_files_view = jade.compile([
    '- each file in files',
    '  .file(data-path="#{file.path}", id="#{file.id}",filesize="#{file.size}",filename="#{file.name}",fileid="#{file.id}",filetype="#{file.type}",filebirth="#{file.birthtime}",filemod="#{file.modtime}",fileaccessed="#{file.actime}",filepos="#{file.position}")',
    '    .icon',
    '      img(src="#{file.icon}")',
    '      span(class="playIcon fa fa-play #{file.showPlay}")',
    '    .name #{file.name}',
    '    .filetype #{file.type}',
].join('\n'));

//img(src="icons/#{file.type}.png")
//#{file.type}


var thumbGenerated = false;

function getFontIcon(fileName, fileType) {
        var iccon = "#61769;";
        if (fileType == "folder")
            if (fileName.indexOf("Game") != -1 || fileName.indexOf("game") != -1)
            iccon = "#61902;";
        else
            iccon = "#61882;";
        
        if (fileType == "audio")
            iccon = "#61859;";
        
        if (fileType == "presentation")
            iccon = "#61753;";
          
          if (fileType == "image")
            iccon = "#61862;";
        
        if (fileType == "video")
            iccon = "#61931;";
          
        if (fileType == "web page")
            iccon = "#61838;";
        
        if (fileType == "document" || fileType.indexOf("code") != -1 || fileType.indexOf("script") != -1 || fileType == "css" || fileType == "text")
            iccon = "#61955;";
        
        if (fileType == "pdf")
            iccon = "#61854;";
        
        if (fileType.indexOf("compressed") != -1)
            iccon = "#61804;";
        
        if (fileType == "binary")
            iccon = "#61886;";

        if (fileType == "eXtern OS Installer")
            iccon = "#61750;";

        if (fileType == "xapp")
            iccon = "#61750;";

return iccon;
}


// Our type
function Folder(jquery_element) {
  events.EventEmitter.call(this);
  this.element = jquery_element;

  var self = this;
  localVars.self = this;
    localVars.self.element = jquery_element;
    

    
    
  // Click on blank
  this.element.parent().on('click', function() {

      if (!localVars.doNotTriggerOncickedOnBlank) {
          localVars.self = this;
      localVars.self.element = jquery_element;
      localVars.hiderenameWindow();

      if (!localVars.draggingOnFiles) {
          	localVars.ctrlCurrentlyPressed = false; //FIXME trying to fix a bug where ctrl is pressed and not released virtually

	localVars.diselectMultiFile();

	if (!localVars.ctrlCurrentlyPressed && !localVars.shiftCurrentlyPressed) {



	if (localVars.currentlyInMultiSelectFilesMode) {
	
		localVars.currentlyInMultiSelectFilesMode = false;
		//localVars.localVars.$(".flip-item").removeClass("hidden");
      
      localVars.getFilePreviewDiv().empty();;


	var current_folder_name = localVars.currentDirectory.name;
      var backward_path_check = localVars.currentDirectory.fullLocation.split("/");
      var iccon = "#61882;";
      var directory_type = "folder";
      

      

      
      if (backward_path_check[1] == "media" && backward_path_check.length == 4)
      {
          iccon = "#61831;";
          directory_type = "Storage Drive";
      }
      
      if (localVars.currentDirectory.fullLocation == "/")
      {
          iccon = "#61729;";
          current_folder_name = "System Files";
      }

      console.log("we are getting here");

	      $OuterDiv = localVars.getFilePreviewDiv()
        .append(localVars.$('<li><a href="#" class="Button Block"><div class = "curent_preview"><span class="icon nav_buttons">&'+iccon+'</span></div><h4 class="file_name_info">'+current_folder_name+'</h4></a></li>'));
        
        for (var i = 0; i < localVars.filesCurrentlyBeingViewed.length; i++) {
          
          localVars.getFilePreviewDiv()
        .append(localVars.$('<li><a href="#" class="Button Block"><div class = "curent_preview"><span id="flipsterItem'+localVars.filesCurrentlyBeingViewed[i].id+'" class="icon nav_buttons">&'+getFontIcon(localVars.filesCurrentlyBeingViewed[i].name, localVars.filesCurrentlyBeingViewed[i].type)+'</span></div><h4 class="file_name_info">'+localVars.filesCurrentlyBeingViewed[i].name+'</h4></a></li>')
    );
          
        }

	

localVars.resetFlipsters();

	}

      localVars.resetSelection();





      localVars.setGenericRightClickPreview();
	localVars.currentlySelectedFiles = [];

	localVars.currentlySelectedFilename = "";

	}

	localVars.$("#modified_title").removeClass('hide_element');
	localVars.$("#filesize_info").removeClass('hide_element');

	localVars.$("#filesize_info_tag").removeClass('hide_element');
	localVars.$("#filemodified_info").removeClass('hide_element');

	localVars.$("#accessed_title").removeClass('hide_element');
	localVars.$("#fileaccessed_info").removeClass('hide_element');


      
      //hide the rename option
      localVars.$("#renameButtonMain").fadeOut();
      
      //localVars.filesInClipboard = [];
      localVars.filesToDelete = [];
      localVars.filesToExtract = [];
      }

      }

      


  });
  // Click on file
  this.element.delegate('.file', 'click', function(e) {

	localVars.fileSection(this);

    e.stopPropagation();
      
      
  });
    
    // Right-Click on an empty space of the folder
  /*this.element.delegate('#files_container', 'contextmenu', function(e) {
      console.log("YASYAYA");
  });*/
    
    
     // Right-Click on file
  this.element.delegate('.file', 'contextmenu', function(e) {
      localVars.hiderenameWindow();
      localVars.filesToOpen = [];

	console.log("localVars",localVars);

	

	if (localVars.currentlySelectedFiles.length < 2)
          self.element.children('.focus').removeClass('focus');

	localVars.$(this).addClass("focus");

	localVars.$(".file").addClass('reduce_opacity'); 
      

	localVars.$('.focus').each(function() {
		localVars.$(this).removeClass('reduce_opacity');
    		localVars.filesToOpen.push(localVars.$(this).attr('data-path'));//localVars.$(this).attr('data-path')
	});
      
      
     console.log("THUMB CACHE: ");
      /*Close Context Menu if Open*/
      
      localVars.$('#file_context_menu').removeClass('animated fadeInDown');
      localVars.$('#file_context_menu').addClass('hidden');
      localVars.$('#fileContextMenuBlurBg').addClass('hidden');
	localVars.$("#right_click_preview").addClass("hidden");
      //localVars.$("#right_click_preview").attr("src", 'images/thumbnail.jpg');
        //localVars.$("#rightclick_bg").attr("src", 'images/blur.jpg');
        localVars.$('#rightclick_icon_bg').attr('src',localVars.$(this)[0].children[0].children[0].attributes[0].value);
      //localVars.$("#right_click_preview").removeClass('animated fadeIn');
      //localVars.$("#rightclick_bg").removeClass('animated fadeIn');
    localVars.$('#rightclick_icon_bg').removeClass('animated fadeIn');
	localVars.$('#rightclick_icon_bg').removeClass("hidden");
      //var gui = require('nw.gui');
            var win = localVars.guis.Window.get();
      
      var win_width = win.width;//window.innerWidth;
      var win_height = win.height;//window.innerHeight;
      var set_y = e.pageY;
      var file_position = localVars.$(this).position();
      var file_x = file_position.left+400;
      var file_y = file_position.top+50;
      localVars.$("#console_w").text("height: "+win_height+" y: "+e.pageY);
      console.info("height: "+win_height+" y: "+e.pageY);
      console.log("RETRYING");
      
      if (file_y > (win_height/2)-30)
      {
          file_y -= 190;
      }

	console.log("winn",win);
      
      
    localVars.$("#onDirectory").addClass("hidden");
      localVars.$("#onFile").removeClass("hidden");
      localVars.$('#fileContextMenuBlurBg').css("top",file_y);
      localVars.$('#fileContextMenuBlurBg').css("left",file_x);
      localVars.$('#file_context_menu').css("top",file_y);
      localVars.$('#file_context_menu').css("left",file_x);
      localVars.$('#file_context_menu').css("background-position","-"+file_x+"px -"+file_y+"px");
      localVars.$('#file_context_menu').css("background-image",localVars.$(win.outerBodyBackground).css("background-image"));
      localVars.$('#file_context_menu').css("background-size",localVars.$(win.outerBodyBackground).css("background-size"));
      //localVars.$('#generated_thumbnail').css("top",file_y);
      //localVars.$('#generated_thumbnail').css("left",file_x);
      
      localVars.$('#file_context_menu').addClass('animated fadeInDown');
      localVars.$('#file_context_menu').removeClass('hidden');
      localVars.$('#fileContextMenuBlurBg').removeClass('hidden');      
      
      
      /*Copy and pasted from the click code, above! I know I am tired :P*/
	

      console.log("RIGHT CLICK ICON",this);
      var current_filepos = localVars.$(this).attr('filepos');
      var current_filename = localVars.filesCurrentlyBeingViewed[current_filepos].name;//localVars.$(this).attr('filename');
      var current_filesize = localVars.$(this).attr('filesize');
      var curent_birth_time = localVars.$(this).attr('filebirth');
      var current_filetype = localVars.$(this).attr('filetype');
      var current_filemod = localVars.$(this).attr('filemod');
      var current_fileac = localVars.$(this).attr('fileaccessed');
      var file_path = localVars.filesCurrentlyBeingViewed[current_filepos].path;//localVars.$(this).attr('data-path');

	localVars.loadRelatedApps(current_filetype);


      current_filepos = parseInt(current_filepos);
	localVars.$("#accessed_title > b").text("Accessed: ");
      localVars.$("#fileaccessed_info").removeClass('hide_element');
      localVars.$("#filemodified_info").removeClass('hide_element');
	localVars.$("#modified_title").text("Modified: ");
      localVars.$("#modified_title").removeClass('hide_element');
      localVars.$("#accessed_title").removeClass('hide_element');
      localVars.$("#thumbnail_exists").text("false");



localVars.currentlySelectedFilename = current_filename;

var fileSelected = {
	name: current_filename,
	type: current_filetype
}

var alreadyeXists = false;




/*for (var j = 0; j < localVars.currentlySelectedFiles.length; j++ {
	if (this.name == fileSelected.name) {
    		return true;
	}
}*/

//localVars.currentlySelectedFiles.push(fileSelected);

			/*var checkFile = localVars.currentlySelectedFiles
  .filter(function( index ) {

	if (this.name == current_filename) {
    		return false;
		alreadyeXists = true;
	} else {
		
		return true;
	}
	
  });

	console.log("checkFile",checkFile);*/

	if (localVars.ctrlCurrentlyPressed || localVars.shiftCurrentlyPressed) {
//id="file_preview_'+files[i].name+'_'+files[i].type+'"
	for (var i = 0; i < localVars.currentlySelectedFiles.length; i++) {
		
		if (localVars.currentlySelectedFiles[i].name == current_filename) {
			alreadyeXists = true;
			break;
		}
	}

	} 



	if (localVars.currentlySelectedFiles.length < 2) {

		localVars.currentlySelectedFiles = [];

		localVars.currentlySelectedFiles.push(fileSelected);

	}





	if (localVars.currentlySelectedFiles.length < 2) {
      		localVars.$("#fileToDelete").text(current_filename);
		localVars.tempFilesInClipboard = [];
		localVars.filesToDelete = [];
		localVars.filesToExtract = [];
		localVars.tempFilesInClipboard.push(file_path);
		localVars.filesToDelet = localVars.currentlySelectedFiles;
		localVars.filesToExtract.push(file_path);
	} else {
		localVars.$("#fileToDelete").text(localVars.currentlySelectedFiles.length+" items");
		localVars.filesToDelete = localVars.currentlySelectedFiles;
		localVars.filesToExtract = localVars.currentlySelectedFiles;

	}
//localVars.filesInClipboard = [];
localVars.currentlySelectedFilename = current_filename;


localVars.$('#extractButton').attr('onclick', 'App.extractFile(folder_view.localVars.filesToExtract)');

console.log("file info",localVars.filesCurrentlyBeingViewed[current_filepos]);


localVars.tempFilesInClipboard.copyDir = localVars.$("#current_location_full").text();
localVars.copyDir = localVars.$("#current_location_full").text();
      localVars.$('#copyButton').attr('onclick', 'App.filesToClipboard(folder_view.localVars.tempFilesInClipboard,false)'); //"'+file_path+'"
      localVars.$('#cutButton').attr('onclick', 'App.filesToClipboard(folder_view.localVars.tempFilesInClipboard,true)');
      localVars.$('#deleteButton').attr('onclick', 'App.delete_files(folder_view.localVars.filesToDelete)'); //"'+file_path+'"
      localVars.$('#rightclick_icon_bg').removeClass("hidden");
      localVars.$('#rightclickBgIcon').removeClass("hidden");
      localVars.$('#generated_thumbnail').addClass("hidden");

localVars.$("#noActions").addClass("hidden");
localVars.$("#renameDiv").addClass("hidden");
localVars.$("#renameButton").removeClass("hidden");

localVars.$("#renameDiv > input").val(current_filename);
localVars.$("#renameDiv > input").attr('filepos',current_filepos);


      if (current_filetype == "image") {
		localVars.$("#setAsDesktopWallpaper").removeClass("hidden");
	} else {
		localVars.$("#setAsDesktopWallpaper").addClass("hidden");
	}


      if (current_filetype == "compressed zip" || current_filetype == "compressed rar" || current_filetype == "compressed gz" || current_filetype == "compressed 7z" || current_filetype == "compressed tar" || current_filetype == "compressed bz2" || current_filetype == "compressed xz") {
//localVars.$("#noActions").addClass("hidden");
localVars.$("#extractButton").removeClass("hidden");
} else {
//localVars.$("#noActions").removeClass("hidden");
localVars.$("#extractButton").addClass("hidden");
}

      if (current_filetype == "folder") {
localVars.$("#addToDeskButton2").removeClass("hidden");
} else {
localVars.$("#addToDeskButton2").addClass("hidden");
}


      if (current_filetype == "video")
      {
          //localVars.$("#rightclick_icon_bg").removeClass("hidden");
          localVars.$("#rightclick_icon").empty();
          localVars.$("#rightclick_icon").append("&#61931;");

		//localVars.$("#right_click_preview").removeClass("hidden");
		//localVars.$('#rightclick_icon_bg').addClass('hidden');
          
          var thumb_cache = localVars.$("#thumbnail_url").text();
          
          
          if (thumb_cache !="")
          {
              var file_path = localVars.$(this).attr('data-path');
              console.log("etetets");
              file_path2 = "file://"+(file_path.replace(/\\/g,"/"));
              //console.log('hibjbbbjbjbj');
localVars.$("#generated_thumbnail").html(
    '<video id = "vid_thumb" width="640" height="264">' +
        '<source src="'+file_path2+'" type="video/mp4"></source>' +
    '</video>');
              
              function setThumb()
              {
                  
                  localVars.$("#thumbnail_name").text(current_filename);
                  var thumb_cache = localVars.$("#thumbnail_url").text();
                  
                  var thumb_url = thumb_cache+current_filename+'.jpg';
                  var thumb_url = "file://"+(thumb_url.replace(/\\/g,"/"));
                  var thumbExists = false;
                  if (fs.existsSync(thumb_cache+current_filename+'.jpg')) {
                    
                    
                    var stats = fs.statSync(thumb_cache+current_filename+'.jpg');
                    
                    var fileSizeInBytes = stats["size"];
                    
                    if (fileSizeInBytes != 0) {
                    
                  //if (thumbExists) {
                      localVars.$("#thumbnail_exists").text("true");
                          
                          localVars.$("#right_click_preview").addClass("hidden");
                      localVars.$('#rightclick_icon_bg').addClass("hidden");
                localVars.$("#rightclick_bg").addClass("hidden");
                //localVars.$('#rightclick_icon_bg').addClass("hidden");
                localVars.$("#right_click_preview").addClass('animated fadeIn');
                        //localVars.$("#rightclick_bg").addClass('animated fadeIn');
                        //localVars.$('#rightclick_icon_bg').addClass('animated fadeIn');
                localVars.$("#right_click_preview").attr("src", thumb_url);
              //localVars.$("#rightclick_bg").attr("src", thumb_url);
              //localVars.$('#rightclick_icon_bg').css('background-image', 'url("'+thumb_url+'")');
                localVars.$("#thumbnail_name").text("");
                localVars.$("#thumbnail_type").text("");
                          //localVars.$('#rightclick_icon_bg').removeClass("hidden");
                setTimeout(function(){
                    localVars.$("#generated_thumbnail").addClass("hidden");
                    localVars.$("#right_click_preview").removeClass("hidden");
                    localVars.$("#rightclick_bg").removeClass("hidden");
                    
                }, 5);
                      //}
                    }
                  };
                
                
                
                
                  var setPos = localVars.$("#vid_thumb")[0].duration/3;
                  var thumb_exists = localVars.$("#thumbnail_exists").text();
                  if (thumb_exists != "true")
                  {
                  if (isNaN(setPos) == false)
                  {
                      console.log("should not get here");
                      //localVars.$("#vid_thumb")[0].play();
                      localVars.$("#vid_thumb")[0].currentTime = setPos;
                      setTimeout(function(){
                          
                      
                      localVars.$("#thumbnail_type").text("video");
                      localVars.$("#generated_thumbnail").removeClass("hidden");
                          localVars.load_thumb();
                          }, 1000);
                  }
                  else
                  {
                      setTimeout(function(){ setThumb();}, 20);
                  }
                  }
                  localVars.$("#thumbnail_exists").text("false");
              }


		function setThumbsB() {
			win.thumbnailGenerator(current_filename);
		}
              //setThumbsB();
              setThumb();

          }
      }
      

      
      var size_reduction_level = 0;
      if (current_filetype != "folder")
      {
      while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
          /*Check if its a whole number or not*/
          if (current_filesize % 1 !== 0)
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
	  localVars.$("#filesize_info_tag > b").text("Size: ");
          localVars.$("#filesize_info").text(current_filesize);
          localVars.$("#filesize_info").removeClass('hide_element');
          localVars.$("#filesize_info_tag").removeClass('hide_element');
      }
      else
      {
          localVars.$("#filesize_info").addClass('hide_element');
          localVars.$("#filesize_info_tag").addClass('hide_element');
          //App.set_current_folder(current_filename);
      }
      localVars.$("#footer_text").text("");
      if (current_filetype == "folder")
          localVars.$("#footer_text").append("<b>Selected Folder: </b>"+current_filename);
      else
          localVars.$("#footer_text").append("<b>Selected File: </b>"+current_filename);

        if (current_filetype == "video") {
          localVars.getVideoInfo(file_path);
        }
        
        if (current_filetype == "image") {
            localVars.getImageInformation(file_path);
        }
      
    localVars.$("#fileaccessed_info").text(current_fileac);
    localVars.$("#filemodified_info").text(current_filemod);      
    localVars.$("#filename_info").text(current_filename);
    localVars.$("#filetype_info").text(current_filetype);
    localVars.$(".flipster").flipster('jump',current_filepos+1);
    localVars.selectFilePieChart(this);
    localVars.$(this).addClass('focus');
    e.stopPropagation();
      return false;
  });
  // Double click on file
  this.element.delegate('.file', 'dblclick', function() {
      
      localVars.hiderenameWindow();
      
      /*Close Context Menu if Open*/
      localVars.$('#file_context_menu').removeClass('animated fadeInDown');
      localVars.$('#file_context_menu').addClass('hidden');
      localVars.$('#fileContextMenuBlurBg').addClass('hidden');
      localVars.$("#right_click_preview").removeClass('animated fadeIn');
      
      var file_path = localVars.$(this).attr('data-path');
      if (localVars.$(this).attr('filetype') == "folder")
      {
          //location_history_text = localVars.$("#location_history").text();
      //var location_history = location_history_text.splt("[{^\&}]");
      //location_history.push(file_path);
          //location_history_text += "[{^\&}]"+file_path;
          //localVars.$("#location_history").text(location_history_text);
          ////console.log(localVars.$("#location_history").text());
          //var text_to_add = "";
          /*for (var i = 0; i < location_history.length; i++)
          {
              if (i != 0)
              text_to_add += "[{^\&}]"+location_history[i];
              else
                  text_to_add += location_history[i];
                  
          }*/
      }
      

	localVars.currentlySelectedFiles = [];
    
    self.emit('navigate', file_path, mime.stat(file_path),localVars.$(this).attr('filetype'));
  });
}

util.inherits(Folder, events.EventEmitter);

Folder.prototype.deepSearch = function (searchString) {
    var self = this;
        var exec = require('child_process').exec,
                child;
    child = exec('find "'+localVars.currentDirectory.fullLocation+'" -name "*'+searchString+'*"',function (error, stdout, stderr) {
                                    
                        var foundFiles = stdout.split("\n");

                        var files = [];
                        localVars.justFiles = [];
                        localVars.processingFileTypeForPos = 0;

			localVars.currentlySearching = true;

                        
                       localVars.getFilePreviewDiv().empty();
                       
                       $OuterDiv = localVars.getFilePreviewDiv()
                       .append(localVars.$('<li><a href="#" class="Button Block"><div class = "curent_preview"><span class="icon nav_buttons">&#61788;</span></div><h4 class="file_name_info">Search</h4></a></li>'));
        

                        if (foundFiles.length == 0) {
                            //Do not found actions here
                        } else {
                            //console.log("foundFiles",foundFiles);
                            for (var i = 0; i < foundFiles.length; i++) {
                                if (foundFiles[i] != "") {
                                    var file = {
                                    id: "fsf"+i,
                                    name: foundFiles[i].replace(/^.*[\\\/]/, ''),
                                    path: foundFiles[i],
                                    type: "Blank",
                                    birthtime: "Unknown",
                                    size: "Unknown",
                                    modtime: "Unknown",
                                    actime: "Unknown",
                                    showPlay: "hidden",
                                    position: i,
                                    icon: "icons/blank.png"

                                }
                                //console.log("file a1: ", file);
                                  try {
                                      var stat = fs.statSync(foundFiles[i]);
                                      file.size = stat["size"];
                                      file.birthtime = stat.birthtime;
                                      file.modtime = stat.mtime;
                                      file.actime = stat.atime;
                                      //console.log("file stat: ",stat);
                                    if (stat.isDirectory()) {
                                        file.type = 'folder';
                                        file.icon = 'icons/folder.png'
                                    } else {
                                        localVars.justFiles.push(file);
                                    }
                                  }catch (e) {
                                      console.log("mime",e);
                                      }
                                      console.log("file processed A2");

                                files.push(file);

                                localVars.getFilePreviewDiv()
                                .append(localVars.$('<li><a href="#" class="Button Block"><div class = "curent_preview"><span id="flipsterItem'+file.id+'" class="icon nav_buttons">&'+getFontIcon(file.name, file.type)+'</span></div><h4 class="file_name_info">'+file.name+'</h4></a></li>'));
                                }

                                
                            }

                            localVars.filesCurrentlyBeingViewed = files;

                            console.log("files",files);

                            localVars.resetFlipsters();

                            localVars.create_PieChart(files);

                            localVars.processingFileTypeForPos = 0;

                            localVars.getFileFormart();

                            console.log("self.element",self.self.element);
                            self.self.element.html(gen_files_view({ files: files }));
                        }


                        
    if (error !== null) {
      console.log('exec error: ' + error);
       }
});
}

localVars.deepSearch = Folder.prototype.deepSearch;

Folder.prototype.open = function(dir) {

  var self = this;
  fs.readdir(dir, function(error, files) {
    if (error) {
      //console.log(error);
      console.log(error);
      return;
    }
      
      location_history_text = localVars.$("#location_history").text();
      var refreshing = localVars.$("#refreshing").text();
      location_history_array = localVars.locationHistory;//location_history_text.split("[{^\&}]");
      if ((location_history_array .length != 0) && localVars.$("#going_back").text() == "false" && refreshing == "false")
      {
          //var cur_url_pos_str = localVars.$("#location_history_pos").text();
          var cur_url_pos = localVars.locationHistoryCurrentPos; //parseInt(cur_url_pos_str); //
          cur_url_pos += 1;
          //console.log("Total length: "+location_history_array.length);
          //console.log("Current Position: "+cur_url_pos);
          if (location_history_array.length <= cur_url_pos)
          {
		localVars.locationHistory.push(dir);
              //location_history_text += "[{^\&}]"+dir;
              //console.log("YAY");
          }
          else
          {
              //console.log("well, no idea whats happening?");
              location_history_text = "";
              //localVars.locationHistory = [];
              for (var i = 0; i < location_history_array.length; i++)
              {
                  //console.log("Adding...");
                  if ( i < cur_url_pos && i!=0)
                     //localVars.locationHistory.push(location_history_array[i]); // location_history_text += "[{^\&}]"+location_history_array[i]; 
                  
                  if (i==0)
                  {
                      //console.log("Started here with url: "+location_history_array[i]);
			            //localVars.locationHistory.push(location_history_array[i]);
                     // location_history_text += location_history_array[i];
                  }
                          
                  
                  if (i == cur_url_pos)
                  {
                      //console.log("Added at pos: "+cur_url_pos);
			            localVars.locationHistory.push(dir);
                      //location_history_text += "[{^\&}]"+dir;
                  }
              }
          }
          
              
              //localVars.$("#location_history_pos").text(cur_url_pos);
		localVars.locationHistoryCurrentPos = cur_url_pos;
      }
      else
      {
          localVars.$("#refreshing").text("false");
          console.log("EXECUTED PATH B and here is the data:");
          console.log("going_back = "+localVars.$("#going_back").text());
          console.log("history_text: "+location_history_text);
          console.log("refreshing: "+refreshing);
          if (localVars.$("#going_back").text() == "true")
              localVars.$("#going_back").text("false");
          else
              localVars.locationHistory.push(dir); //location_history_text += dir; 
      }
      
          //localVars.$("#location_history").text(location_history_text);
          //console.log(localVars.$("#location_history").text());
      //localVars.$('#go_back_button')
      
     // var exists = location_history.indexOf(dir)
      
      
      /*
      location_history_text = localVars.$("#location_history").text();
      var location_history = location_history_text.splt("[{^\&}]");
      location_history.push(dir);*/
      
      /*if (dir == location_history[location_history.length-2])
      {
          localVars.$('#go_back_button').attr("nw-path",location_history[location_history.length-3]);
      }
      else
      {
          if (dir == location_history[location_history.length-1])
              localVars.$('#go_back_button').attr("nw-path",location_history[location_history.length-2]);
      }*/
      //document.getElementById("#go_back_button").setAttribute("nw-path",location_history[location_history.length-1]);
      
      
          for (var i = 0; i < files.length; ++i) {
      files[i] = mime.stat(path.join(dir, files[i]));
		files[i].id = "fsf"+i;
    }
	//console.log("filess",files);
      
            /*localVars.$( "#files_container" ).empty();
      
                      $OuterFiles = localVars.$('#files_container')
        .append(localVars.$('<ul class = "animated fadeIn" style="margin: 5px;" id="files"></ul>')
    );*/
      

      
      /*Setting up the totals*/
/*
      localVars.$("#total_files").text(files_extract.length-1);
      localVars.$("#total_folders").text(folders_extract.length-1);*/
      
      /*Setting up our status text*/
/*
      localVars.$("#footer_text").text("");
      localVars.$("#footer_text").append("You are currently viewing <b>"+files_extract.length+" files</b> and <b>"+folders_extract.length+" folders</b>.");*/
      
      
          

      /*Hide hidden files when true*/
      //var show_hidden = localVars.show_hidden_files;
      var items_to_hide = new Array();
      if (!localVars.show_hidden_files)
      {
       for (var i = 0; i < files.length; i++)
      {   
          if (files[i].name.charAt(0) == ".")
              items_to_hide.push(files[i].name);
      }
          
          for (var i = 0; i < items_to_hide.length; i++)
          {
              ////console.log("hidden: "+files[items_to_hide[i]].name);
              
              for (j = 0;j<files.length;j++)
                  if (files[j].name == items_to_hide[i])
                      files.splice(j, 1);
              
              
          }
      }

      var order_type = localVars.$("#order_by_type").text();
      
      if (order_type == "true")
      {
      var folders_extract = new Array();
      var files_extract = new Array();
      var files_reset = new Array();
      
      for (var i = 0; i < files.length; i++)
      {
          if (files[i].type == "folder")
              folders_extract.push(files[i]);
          else
              files_extract.push(files[i]);
      }
      
      /*Replace the order of files*/
      var j = 0;
      for (var i = 0; i < files.length; i++)
      {
          if (i<folders_extract.length)
              files[i]=folders_extract[i];
          else
          {
              files[i]=files_extract[j];
              j++;
          }
          
      }
      }

	localVars.filesCurrentlyBeingViewed = files;
      
            /*Setting up the totals*/
      localVars.$("#total_files").text(files_extract.length-1);
      localVars.$("#total_folders").text(folders_extract.length-1);
      
      /*Setting up our status text*/
      localVars.$("#footer_text").text("");
	if (files_extract.length > 1)
		var filesText = "files";
	else
		var filesText = "file";

	if (folders_extract.length > 1)
		var foldersText = "folders";
	else
		var foldersText = "folder";

	if (files_extract.length == 0) {
		localVars.$("#footer_text").append("You are currently viewing <b>"+folders_extract.length+" "+foldersText+"</b>.");
	} else if (folders_extract.length == 0) {
		      localVars.$("#footer_text").append("You are currently viewing <b>"+files_extract.length+" "+filesText+"</b>.");
	} else if ((folders_extract.length == 0) && (files_extract.length == 0)) {
		//display nothing
	} else {
      localVars.$("#footer_text").append("You are currently viewing <b>"+files_extract.length+" "+filesText+"</b> and <b>"+folders_extract.length+" "+foldersText+"</b>.");
	}
      
      
      
      /*Recreate pie chart*/
      localVars.create_PieChart(files_extract);
      
      localVars.$( "#file_preview" ).empty();
      
      //#61831;
      var current_folder_name = dir.match(/([^\/]*)\/*$/)[1];
      var backward_path_check = dir.split("/");
      var iccon = "#61882;";
      var directory_type = "folder";
      

      

      
      if (backward_path_check[1] == "media" && backward_path_check.length == 4)
      {
          iccon = "#61831;";
          directory_type = "Storage Drive";
      }
      
      if (dir == "/")
      {
          iccon = "#61729;";
          current_folder_name = "System Files";
      }

	localVars.currentDirectory = {
			name: current_folder_name,
			type: directory_type,
			fullLocation: dir
	}

      
      /*Setting up the info pane*/
	localVars.$("#filesize_info_tag > b").text("Capacity: ");
	localVars.$("#filesize_info").text(localVars.$("#"+localVars.$("#temp_current_drive").text()+"_progressbarX").attr("volume_size"));

      localVars.$("#modified_title").text("Free Space: ");
      localVars.$("#filemodified_info").text(localVars.$("#"+localVars.$("#temp_current_drive").text()+"_progressbarX").attr("free_space"));

      localVars.$("#accessed_title > b").text("Filesystem Type: ");
      localVars.$("#fileaccessed_info").text(localVars.$("#"+localVars.$("#temp_current_drive").text()+"_progressbarX").attr("fstype"));

	localVars.$("#modified_title").removeClass('hide_element');
	localVars.$("#filesize_info").removeClass('hide_element');

	localVars.$("#filesize_info_tag").removeClass('hide_element');
	localVars.$("#filemodified_info").removeClass('hide_element');

	localVars.$("#accessed_title").removeClass('hide_element');
	localVars.$("#fileaccessed_info").removeClass('hide_element');

      localVars.$("#filename_info").text(current_folder_name);
      localVars.$("#filetype_info").text(directory_type);
      
            /*Making it easy for other scripts to know the name of the folder*/
      localVars.$("#current_location").text(current_folder_name);
      localVars.$("#current_location_type").text(directory_type);
       localVars.$("#current_location_full").text(dir);


      
      /*Setting Window title*/
      localVars.$('title').text(current_folder_name+' - iX Files');
      //localVars.$('#title-text').text('iX Files - '+current_folder_name);    
      localVars.$("#sub_title").text(current_folder_name);
      
      localVars.setTitle(current_folder_name);
          
      $OuterDiv = localVars.$('#file_preview')
        .append(localVars.$('<li><a href="#" class="Button Block"><div class = "curent_preview"><span class="icon nav_buttons">&'+iccon+'</span></div><h4 class="file_name_info">'+current_folder_name+'</h4></a></li>'));

//Clear array for videos thumbnails
localVars.videoThumbs = [];      
      for (var i = 0; i < files.length; ++i) {
        files[i].position = i;
//Set defult icon
files[i].icon = "icons/"+files[i].type+".png";

//Don't show play icon on non video types
files[i].showPlay = "hidden";

//Show Images and video thumbnails when supported
if (files[i].type == "image")
files[i].icon = "file://"+files[i].path;

if (files[i].type == "video") {
var thumb_cache = localVars.$("#thumbnail_url").text();
if (fs.existsSync(thumb_cache+files[i].name+'.jpg')) {
var stats = fs.statSync(thumb_cache+files[i].name+'.jpg');
var fileSizeInBytes = stats["size"];
if (fileSizeInBytes != 0) {
	files[i].icon = "file://"+thumb_cache+files[i].name+'.jpg';
	files[i].showPlay = ""; //Show play icon
}
} else {
	fileProps = { 
		name: files[i].name,
		url: files[i].path,
		processed: false
	}

	localVars.videoThumbs.push(fileProps);
}
}

/*Set side bar icons*/
          
        var iccon = "#61769;";
        if (files[i].type == "folder")
            if (files[i].name.indexOf("Game") != -1 || files[i].name.indexOf("game") != -1)
            iccon = "#61902;";
        else
            iccon = "#61882;";
        
        if (files[i].type == "audio")
            iccon = "#61859;";
        
        if (files[i].type == "presentation")
            iccon = "#61753;";
          
          if (files[i].type == "image")
            iccon = "#61862;";
        
        if (files[i].type == "video")
            iccon = "#61931;";
          
        if (files[i].type == "web page")
            iccon = "#61838;";
        
        if (files[i].type == "document" || files[i].type.indexOf("code") != -1 || files[i].type.indexOf("script") != -1 || files[i].type == "css" || files[i].type == "text")
            iccon = "#61955;";
        
        if (files[i].type == "pdf")
            iccon = "#61854;";
        
        if (files[i].type.indexOf("compressed") != -1)
            iccon = "#61804;";
        
        if (files[i].type == "binary")
            iccon = "#61886;";

        if (files[i].type == "eXtern OS Installer")
            iccon = "#61750;";
        
                $OuterDiv = localVars.$('#file_preview')
        .append(localVars.$('<li id="file_preview_'+files[i].name+'_'+files[i].type+'"><a href="#" class="Button Block"><div class = "curent_preview"><span id="flipsterItem'+files[i].id+'" class="icon nav_buttons">&'+iccon+'</span></div><h4 class="file_name_info">'+files[i].name+'</h4></a></li>')
    );
        
    }
      //setIconThumb();
	localVars.$('.flipster-flat').removeClass('flipster-flat');
      localVars.$('.flipster-active').removeClass('flipster-active');
      localVars.$(".flipster").flipster({ style: 'carousel', start: 0, spacing: 1 });
      
      var display_state = localVars.$('#previous_state').text();
      
      if (files.length == 0)
      {
          if (display_state == "showing")
          {
              localVars.$('#previous_state').text('hidden');
              localVars.$('#files').addClass('hidden');
              localVars.$('#no_files').addClass('animated fadeIn');
              localVars.$('#no_files').removeClass('hidden');
          }
      }
      else
      {
      localVars.$('#files').removeClass('animated fadeInUp');
          if (display_state == "hidden")
          {
              localVars.$('#previous_state').text('showing');
              localVars.$('#no_files').addClass('hidden');
              localVars.$('#no_files').removeClass('animated fadeIn');
          }
          else
              localVars.$('#files').addClass('hidden');
          
      setTimeout(function(){ localVars.$('#files').addClass('animated fadeInUp'); localVars.$('#files').removeClass('hidden');}, 70);
    self.element.html(gen_files_view({ files: files }));

	localVars.justFiles = [];
	localVars.processingFileTypeForPos = 0;

for (var i = 0; i < files.length; i++) {
	if (files[i].type != "folder")
		localVars.justFiles.push(files[i]);
		//localVars.getFileFormart(files[i]);
}

	if (localVars.justFiles.length > 0)
		localVars.getFileFormart();

    //localVars.appendSelectorCover();

	localVars.vidThumbsProcessID++;

	//localVars.thumbnailGeneratorCallback(

	//setTimeout(function(){
		//for (var k = 0; k < localVars.videoThumbs.length; k++) {
			localVars.thumbnailGenerator(localVars.videoThumbs[0].name,localVars.videoThumbs[0].id,localVars.videoThumbs[0].path,"video",localVars.thumbnailGeneratorCallback,0,localVars.vidThumbsProcessID);
		//}
	//}, 5000);

//localVars.$( "input[value='Hot Fuzz']" ).next().text( "Hot Fuzz" );
      }
  });
}

exports.Folder = Folder; 
exports.localVars = localVars;

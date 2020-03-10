var fs = require('fs');
var path = require('path');
var _ = require('underscore');
const execSync = require('child_process').execSync;
var execs = require('sync-exec');

var map = {
  'compressed zip': ['zip'],
    'compressed rar': ['rar'],
    'compressed gz': ['gz'],
    'compressed 7z': ['7z'],
    'compressed tar': ['tar'],
    'compressed bz2': ['bz2'],
    'binary': ['dat','bin','x-executable'],
    'flash package': ['swf','flash'],
    'compile instructions': ['make','cmake','pak','json'],
    'shared library': ['so','dll','x-dosexec','exe','x-sharedlib'],
    'vector graphics': ['svg'],
    'vector image': ['svg','eps','bmp','gif','tif','x-ms-bmp'],
    'illustrator': ['ai'],
    'font': ['vtt','ttf','eot','woff','ttc','pfb','pfm','otf','dfont','pfa','afm'],
    'executable script': ['sh','bat','cmd','csh','com','ksh','rgs','vb','vbs','vbe','vbscript','ws','wsf','x-shellscript'],
  'text': ['txt', 'md','info','nfo', '', 'text', 'plain', 'text/plain'],
    'initialization file': ['ini'],
    'logged data': ['log'],
    'c code': ['c','x-c'],
    'bit torrent': ['.torrent'],
    'CD-DVD Image': ['iso','img'],
    'debian': ['deb'],
    'c++ code': ['cc', 'cpp', 'c++','cp','cxx'],
    'python code': ['py','pyc','pyo','pyd','x-python'],
  'image': ['jpg', 'jpge', 'png','PNG','image'],
  'pdf': ['pdf'],
  'css': ['css'],
  'java script': ['js'],
  'eXtern OS Installer': ['xapp'],
  'web page': ['html'],
    'xml': ['xml'],
    'java': ['java','jar'],
  'document': ['doc', 'docx','odt'],
  'presentation': ['ppt', 'pptx'],
  'video': ['mkv', 'avi', 'rmvb','flv','wmv','mp4','mpeg','video'],
    'audio': ['audio','mp3', 'wma', 'wav','aiff','m4a','ape','wv','act','aac','au','dss','flac','iklax','ivs','m4p','mmf','mpc','ogg','oga','opus','raw','sln','tta','vox'],
};
var total_size = 0;
var cached = {};

exports.stat = function(filepath) {
    
  var result = {
    name: path.basename(filepath),
    path: filepath,
      
  };

  try {
    var stat = fs.statSync(filepath);
      result.size = stat["size"];
      result.birthtime = stat.birthtime;
      //result.id = result.name.replace(/["']/g, "/"); //Use ? because it's not allowed in a file name incase we get a clash with another file
      result.modtime = stat.mtime;
      result.actime = stat.atime;
      total_size+=result.size;
    if (stat.isDirectory()) {
      result.type = 'folder';
    } else {
      var ext = path.extname(filepath).substr(1);
	//result.name = result.name+" lll ";

	//var fileTypeMimeRaw = execSync('file --mime-type -b "'+filepath+'"').toString();
	//var fileMimeTypes = fileTypeMimeRaw.replace(/\s+/g,'').split("/");
	
	

	//result.name = result.name+" ||"+fileTypeMimeRaw.split(":")[1]; //fileMimeTypes[0]+"||";
      //result.type = cached[ext];

/*
      if (!result.type) {

	for (var k = 0; k < fileMimeTypes.length; k++) {
		if (result.type != "audio" && result.type != "video") { //avoid overlap in types (first result will differentiate the two
        		for (var key in map) {
          			if (_.include(map[key], fileMimeTypes[k])) {
            				cached[ext] = result.type = key;
            				break;
          			}
        		}

		}
	}*/
	

	//If we think it's a plain text file there is a chance we don't know what type it is
	//So instead we can use the file extension to figure it out instead
	//Also C++ and C sometimes gets confused




/*
	if ((result.type == "plain" || result.type == "text" || result.type == "c code" || !result.type) && (ext != "")) {
        	for (var key in map) {
          		if (_.include(map[key], ext)) {
            			cached[ext] = result.type = key;
            			break;
          		}
        	}
	}*/

	

	
	//var fileTypeMimeRaw = execSync('file "'+filepath+'" --mime-type').toString();
	
	

	//result.name = result.name+" || "+fileTypeMimeRaw.split(":")[1];
	//result.type = fileTypeMimeRaw.split(":")[1].split("/")[0];

	

	//result.name = result.name+" || "+execs('file "'+filepath+'" --mime-type');//.stdout.split(":")[1];

	result.type = 'blank';

        if (!result.type)
          result.type = 'blank';
      //}
    }
  } catch (e) {
    console.log("mime",e);
  }

  return result;
}


function convert_bytes(fsize)
{
         var current_filesize = fsize;
      var size_reduction_level = 0;
      while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
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
}

var os = require('os'),
    fs = require('fs'),
    sys = require('util'),
    exec = require('child_process').exec;

function linux(brightness,callback){
	// Enumerate the backlight devices...
	fs.readdir('/sys/class/backlight', function(err, brightnessDevices){
		if(err) {
			console.error('Error while listing brightness devices. Maybe you need superuser privileges to run this script?');
			throw err;
		}

		var devicePath = '/sys/class/backlight/' + brightnessDevices[0];
		//Read the maximum for the first device
		fs.readFile(devicePath + '/max_brightness', function(err, maxBrightness){
			maxBrightness = parseInt(maxBrightness, 10)
			if(err) {
				console.error('Error while reading maximum brightness. Maybe you need superuser privileges to run this script?');
				throw err;
			}

			// Turn percent into the actual value we need
			var brightnessValue = Math.floor(brightness / 100 * maxBrightness);

			// Write out new value
			fs.createWriteStream(devicePath + '/brightness')
				.on('end', callback)
				.write(new Buffer(brightnessValue.toString()));
		});
	})
}

function windows(brightness,callback){

//These are the identifiers for the current power scheme

	var GUID;
	var subgroup;
	var powerSetting;

	// powercfg -q gives information about power settings, but can only give accurate brightness info for laptops or other portable windows devices

	exec('powercfg -q', function(error,stdout,stderr){
		if(!error){
			var regExp =  /([a-z\-0-9]+)\s\D+$/
			var splitOutput = stdout.split('\r\n');
			GUID = regExp.exec(splitOutput[0])[1];

			for(var i = 0;i<splitOutput.length;i++){
				if(splitOutput[i].match(/\(Display\)$/)){

					//The subgroup is derived from the output named display

					subgroup = regExp.exec(splitOutput[i])[1];
				}
				else if(splitOutput[i].match(/\(Display\sbrightness\)$/)){

					//The powerSetting is derived from the output named Display

					powerSetting = regExp.exec(splitOutput[i])[1];
				}
			}

			//console.log(GUID,subgroup,powerSetting);

			//Set the the brightness for AC power plan settings

			exec('powercfg -SetAcValueIndex' + ' ' + GUID + ' ' + subgroup + ' ' + powerSetting + ' ' + brightness,function(err,out,stderror){
				if(err) throw err;

				//Set the brightness when on DC power plan settings

				exec('powercfg -SetDcValueIndex' + ' ' + GUID + ' ' + subgroup + ' ' + powerSetting + ' ' + brightness,function(err,out,stderror){
					if(err) throw err;

					//Set the modified power plan as the current system plan

					exec('powercfg -S' + ' ' + GUID,function(err,out,stderror){
						if(err) throw err;
						if(callback) callback();
						return true;
					});
				});
			});

		}
		else{
			throw error;
		}
	});
}

function changeBrightness(brightness,callback){

//Brightness is in percent
	switch(os.platform()){

	case 'win32':
	windows(brightness,callback);
	break;

	case 'linux':
	linux(brightness, callback);
	break;

	default:
	throw new Error('OS is not recognized or is unsupported');
	break;
	}

}

module.exports = changeBrightness;

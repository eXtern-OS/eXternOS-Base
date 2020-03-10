exec = require('child_process').exec

module.exports =
	extract: (path, destPath, time = '00:00:01', size = '200x125', callback) ->
		exec 'ffmpeg -ss ' + time + ' -vframes 1 -i ' + path + ' -y -s ' + size.replace('x', '*') + ' -f image2 ' + destPath, ->
			callback() if callback
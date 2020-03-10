var exec;
exec = require('child_process').exec;
module.exports = {
  extract: function(path, destPath, time, size, callback) {
    if (time == null) {
      time = '00:00:01';
    }
    if (size == null) {
      size = '200x125';
    }
    return exec('ffmpeg -ss ' + time + ' -vframes 1 -i ' + path + ' -y -s ' + size.replace('x', '*') + ' -f image2 ' + destPath, function() {
      if (callback) {
        return callback();
      }
    });
  }
};
var parse = require('../');
var exec = require('child_process').exec;

exec('xrandr', function (err, stdout) {
    var query = parse(stdout);
    console.log(JSON.stringify(query, null, 2));
});

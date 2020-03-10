'use strict';

/**
 * @module HTTP_API
 */

var http    = require('http'),
    url     = require('url'),
    path    = require('path'),
    fs      = require('fs'),
    util    = require('util'),
    speak   = require('./lib/simple-tts');



var port = process.argv.pop();
port = parseInt(port, 10);
if (isNaN(port)) { port = 8888; }



var getMimeType = function(ext) {
    switch (ext) {
        case 'html': return 'text/html';
        case 'css':  return 'text/css';
        case 'js':   return 'text/javascript';
        case 'mp3':  return 'audio/mpeg';
        case 'ogg':  return 'audio/ogg';
        default:
            return 'text/plain';
    }
};


http.createServer(function(request, response) {
    
    var u = url.parse(request.url, true);
    var uri = u.pathname;
    var filename = path.join(process.cwd(), 'static', uri);
    
    //console.log('uri:', uri);

    if (uri === '/') {
        response.writeHead(302, {
            Location: 'html/index.html'
        });
        response.end();
        return;
    }
    
    /**
     * GET /speak
     *
     * supported query arguments:
     * * text
     * * format
     * * lang
     * * amplitude
     * * pitch
     * * speed
     * * wordgap
     * 
     * returns the audio stream
     */
    if (uri === '/speak') {
        var o = u.query;

        var text = o.text;
        delete o.text;

        for (var k in o) {
            if (!o.hasOwnProperty(k)) { continue; }
            if (['lang', 'format'].indexOf(k) !== -1) { continue; }
            o[k] = parseInt(o[k], 10);
        }

        //console.log('text:       "' + text + '"');
        //console.log('parameters: ' + util.inspect(o));

        response.writeHead(200, {'Content-Type': getMimeType(o.format)});
        o.stream = response;
        
        speak(text, o);
        
        return;
    }

    fs.exists(filename, function(exists) {
        
        if (!exists) {
            response.writeHead(404, {'Content-Type': 'text/plain'});
            response.write('404 Not Found\n');
            response.end();
            return;
        }

        if (fs.statSync(filename).isDirectory()) {
            filename += 'index.html';
        }

        fs.readFile(filename, 'binary', function(err, file) {
            if (err) {
                response.writeHead(500, {'Content-Type': 'text/plain'});
                response.write(err + '\n');
                response.end();
                return;
            }

            var ext = filename.split('.').pop();
            var mimeType = getMimeType(ext);
            //console.log('serving filename ' + filename + ' with mime type ' + mimeType);
            response.writeHead(200, {'Content-Type': mimeType});
            response.write(file, 'binary');
            response.end();
        });
        
    });
    
}).listen(port);

console.log('Serving simple-tts-server on port ' + port + '...');

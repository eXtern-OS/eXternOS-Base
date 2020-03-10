(function(window) {
    
    'use strict';

    /*jshint browser:true, eqeqeq:true, undef:true, curly:true, laxbreak:true, forin:false, smarttabs:true */
 


    var objectToQueryString = function(o) {
        var parts = [];
        for (var k in o) {
            if (!o.hasOwnProperty(k)) { continue;   }
            parts.push( [k, '=', encodeURIComponent(o[k])].join('') );
        }
        return parts.join('&');
    };



    var supportsMp3 = (function() {
        var aEl = document.createElement('audio');
        return !!(aEl.canPlayType && aEl.canPlayType('audio/mpeg').replace(/no/, ''));
    })();


    /**
     * @module client_API
     */

    /**
     * @function speak
     *
     * @param {String}    text              text to speak
     *
     * @param {Object}    o
     *
     * @param {Number}   [o.amplitude=200]  espeak parameter. amplitude ~ volume.
     * @param {Number}   [o.pitch=40]       espeak parameter. voice pitch.
     * @param {Number}   [o.speed=150]      espeak parameter. narration speed.
     * @param {Number}   [o.wordgap=3]      espeak parameter. time between words.
     *
     * @param {Boolean}  [o.autoplay=true]  if trueish, sample is played as soon as it's available
     * @param {Function} [o.onReady]        called when playback can start
     * @param {Function} [o.onDone]         called when playback ended
     *
     * @returns {Object} The returned object has the following interface:  
     *   {Object}   options (the hash of primitive parameters passed in)
     *   {Function} play
     *   {Function} pause
     */
    window.speak = function(text, o) {
        if (!o) { o = {}; }

        o.text = text;

        var audioEl = document.createElement('audio');

        if ('onReady' in o) {
            audioEl.addEventListener('canplay', o.onReady);
            delete o.onReady;
        }

        if ('onDone' in o) {
            audioEl.addEventListener('ended', o.onDone);
            delete o.onDone;
        }

        var server = '';
        if ('server' in o) {
            server = o.server;
            delete o.server;
        }

        var autoplay = true;
        if ('autoplay' in o) {
            autoplay = !!o.autoplay;
            delete o.autoplay;
        }

        o.format = supportsMp3 ? 'mp3' : 'ogg';

        var sourceEl = document.createElement('source');
        sourceEl.setAttribute('src', server + '/speak?' + objectToQueryString(o));
        sourceEl.setAttribute('type', supportsMp3 ? 'audio/mpeg' : 'audio/ogg');
        audioEl.appendChild(sourceEl);

        if (autoplay) {
            audioEl.play();
        }

        return {
            options: o,
            play:    function() { audioEl.play();  },
            pause:   function() { audioEl.pause(); }
        };
    };
    
})(window, undefined);

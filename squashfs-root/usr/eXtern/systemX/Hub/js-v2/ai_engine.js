//AIMLInterpreter = require('./AIMLInterpreter');
var tts_enabled = false;
var tts_online_enabled = false;
var useOnlineInterpreter = true;
//https://askubuntu.com/questions/195503/how-to-disable-right-click-in-nautilus
//https://www.experts-exchange.com/questions/26662052/Disable-Right-Click-Context-Menu-on-Desktop.html

//https://askubuntu.com/questions/84847/how-to-disable-nautilus-from-handling-the-desktop

if (!useOnlineInterpreter) {

    var aimlInterpreter = new AIMLInterpreter({ name: 'I.T.A.I', age: '1' });
    aimlInterpreter.loadAIMLFilesIntoArray(['AI Brain/ai.aiml',
        'AI Brain/alice.aiml',
        'AI Brain/astrology.aiml',
        'AI Brain/atomic.aiml',
        'AI Brain/badanswer.aiml',
        'AI Brain/biography.aiml',
        'AI Brain/bot.aiml',
        'AI Brain/bot_profile.aiml',
        'AI Brain/client.aiml',
        'AI Brain/client_profile.aiml',
        'AI Brain/computers.aiml',
        'AI Brain/continuation.aiml',
        'AI Brain/date.aiml',
        'AI Brain/default.aiml',
        'AI Brain/drugs.aiml',
        'AI Brain/emotion.aiml',
        'AI Brain/food.aiml',
        'AI Brain/geography.aiml',
        'AI Brain/gossip.aiml',
        'AI Brain/history.aiml',
        'AI Brain/humor.aiml',
        'AI Brain/imponderables.aiml',
        'AI Brain/inquiry.aiml',
        'AI Brain/interjection.aiml',
        'AI Brain/iu.aiml',
        'AI Brain/knowledge.aiml',
        'AI Brain/literature.aiml',
        'AI Brain/loebner10.aiml',
        'AI Brain/money.aiml',
        'AI Brain/movies.aiml',
        'AI Brain/mp0.aiml',
        'AI Brain/mp1.aiml',
        'AI Brain/mp2.aiml',
        'AI Brain/mp3.aiml',




        'AI Brain/mp6.aiml',

        'AI Brain/music.aiml',
        'AI Brain/numbers.aiml',
        'AI Brain/personality.aiml',

        'AI Brain/phone.aiml',



        'AI Brain/politics.aiml',
        'AI Brain/primeminister.aiml',
        'AI Brain/primitive-math.aiml',
        'AI Brain/psychology.aiml',
        'AI Brain/pyschology.aiml',
        'AI Brain/reduction.names.aiml',
        'AI Brain/reductions-update.aiml',
        'AI Brain/religion.aiml',
        'AI Brain/salutations.aiml',
        'AI Brain/science.aiml',
        'AI Brain/sex.aiml',
        'AI Brain/sports.aiml',
        'AI Brain/stack.aiml',
        'AI Brain/stories.aiml',
        'AI Brain/that.aiml',
        'AI Brain/update1.aiml',
        'AI Brain/update_mccormick.aiml',
        'AI Brain/wallace.aiml',
        'AI Brain/xfind.aiml',
        './AI Custom.aiml',


    ]);

}

function speak(response) {
    if (!tts_online_enabled) {
        meSpeak.speak(response, {
            amplitude: amplitude,
            wordgap: wordgap,
            pitch: pitch,
            speed: speed,
            variant: variant
        });
    }
    else {
        getSpeechData(response);
    }
}

var http = require("http");
var amplitude = 100;
var wordgap = 0;
var pitch = 50;
var speed = 175;
var variant = "m1";

//Personal Assistant TTS
//meSpeak.loadConfig("json/mespeak_config.json");

function getSpeechData(text) {
    console.log("GOOTOT here");
    var xmlhttp = new XMLHttpRequest();
    var url = "http://www.yakitome.com/api/rest/tts?api_key=JnXJKgMFMn7SGyu56cLB2KlQ&voice=Crystal&speed=5&text=" + text.replace(/\s+/g, '+');

    xmlhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var myArr = JSON.parse(this.responseText);
            //myFunction(myArr);
            console.log("JSON: ", myArr);
            console.log("SENT URL: ", myArr.iframe.replace("https", "http").replace("index", "text_to_speech"));
            console.log("executttted");
            document.getElementById('audioiframe').src = myArr.iframe.replace("https", "http").replace("index", "text_to_speech");
            
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function playSpeech(test_str) {
    var start_pos = test_str.indexOf('<source src') + 1;
    var end_pos = test_str.indexOf('.mp3', start_pos);
    var text_to_get = test_str.substring(start_pos, end_pos)
    text_to_get = "https://www.yakitome.com" + text_to_get.replace(/\\/g, "").replace('source src="', "").replace("download_mp3", "download_mp3.load") + ".mp3";
    console.log("DL'D DATA: ", text_to_get);
    //console.log("ALLL'D DATA: ",test_str);

    var audio = document.getElementById('speechPlayer');
    var source = document.getElementById('sourceMp3');
    source.src = text_to_get;

    audio.load(); //call this to just preload the audio without playing
    audio.play(); //call this to play the song right away
}

// Utility function that downloads a URL and invokes
// callback with the data.
function download(url, callback) {
    http.get(url, function (res) {
        var data = "";
        res.on('data', function (chunk) {
            data += chunk;
        });
        res.on("end", function () {
            if (data.search("<source src") == -1)
                setTimeout(function () { download(url, callback); }, 3000);
            else
                callback(data);
        });
    }).on("error", function () {
        callback(null);
    });
}


function loadVoice(id) {
    var fname = "json/voices/" + id + ".json";
    meSpeak.loadVoice(fname, voiceLoaded);
}

function voiceLoaded(success, message) {
    if (success) {
        console.log("Voice loaded: " + message + ".");
        //meSpeak.speak("hello world");
    }
    else {
        console.log("Failed to load a voice: " + message);
    }
}
//meSpeak.loadVoice("json/voices/en/en.json", voiceLoaded);

var callback = function (answer, wildCardArray, input) {
    console.log(answer + ' | ' + wildCardArray + ' | ' + input);
};

var caseCallback = function (answer, wildCardArray, input) {
    if (answer == this) {
        console.log(answer + ' | ' + wildCardArray + ' | ' + input);
    } else {
        console.log('ERROR:', answer);
        console.log('   Expected:', this.toString());
    }
};



function aiRequest(requestInput, callback) {
    //$("#aiResponse").empty();
    //$("#aiResponse").append('<div class="blob blob-1"></div><div class="blob blob-2"></div><div class="blob blob-3"></div><div class="blob blob-4"></div><div class="blob blob-5"></div><div class="blob blob-6"></div>'); 
    if (useOnlineInterpreter) {
        requestOnlineInterpreter(requestInput, callback);
    } else {
        //aimlInterpreter.findAnswerInLoadedAIMLFiles($("#aiInput").val(), aiCallback);
        var reply = bot.reply("local-user", requestInput);
        callback(reply);
    }

}




function loadLocalAi() {
    var bot = new RiveScript();
    bot.loadFile([
        "aiBrain/about-aiden.rive",
        "aiBrain/begin.rive",
        "aiBrain/data-names.rive",
        "aiBrain/emoji-categories.rive",
        "aiBrain/emoji-sub.rive",
        "aiBrain/emoji.rive",
        "aiBrain/sarcasm.rive",
        "aiBrain/std-arrays.rive",
        "aiBrain/std-chat.rive",
        "aiBrain/std-learn.rive",
        "aiBrain/std-reductions.rive",
        "aiBrain/std-salutations.rive",
        "aiBrain/std-star.rive",
        "aiBrain/std-substitutions.rive"
    ], loading_done, loading_error);
}

function loading_done(batch_num) {
    console.log("Batch #" + batch_num + " has finished loading!");

    // Now the replies must be sorted!
    bot.sortReplies();

    // And now we're free to get a reply from the brain!
    var reply = bot.reply("local-user", "Hello, bot!");
    console.log("The bot says: " + reply);
}

// It's good to catch errors too!
function loading_error(error) {
    console.log("Error when loading files: " + error);
}

//loadLocalAi();

window.aiRequest = aiRequest;

var aiCallback = function (answer, wildCardArray, input) {
    //$("#aiResponse").text(answer);

    if (tts_enabled)
        if (answer != undefined)
            speak(answer);
    console.log(answer + ' | ' + wildCardArray + ' | ' + input);
};

function setResponse(response) {
    /*if ($("#hideAiChat")[0].children[0].innerHTML == "Show Replies" && response !="")
             toggleAiChat();
    $("#aiResponse").text(response);*/
}

$("#aiInput").keyup(function (e) {
    if (e.keyCode == 13) {
        window.aiCallback(aiRequest($("#aiInput").val(), setResponse));
        $("#aiInput").val("");
        document.getElementById("aiInput").focus();
    }
});





/*Use online version*/
var firstTime = false;

window.aiCallback = setResponse;

var conversation_id = -1;

function requestOnlineInterpreter(request, callback) {
    window.aiCallback = callback;

    var aiResponseData = new XMLHttpRequest();

    var url = "https://externos.io/externapps/AI/chatbot/conversation_start.php";//use secure https for AI

    aiResponseData.onreadystatechange = function () {
        if (aiResponseData.readyState == 4 && aiResponseData.status == 200) {

            /*Getting Artist data from Deezer response*/
            var aiResponse = JSON.parse(aiResponseData.responseText);
            console.log("aiResponse", aiResponse);
            var answer = aiResponse.botsay;
	    conversation_id = aiResponse.convo_id;
            if (!firstTime) {

                window.aiCallback(answer);

                if (tts_enabled)
                    if (answer != undefined)
                        speak(answer);
            }

            firstTime = false;
        }
    };
    aiResponseData.open("POST", url, true);
    //Send the proper header information along with the request
    aiResponseData.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    if (conversation_id != -1)
    	aiResponseData.send("say=" + request+"&convo_id="+conversation_id);
    else
	aiResponseData.send("say=" + request);

}

function toggleITAI () {

if (win.runningApps[1].windowObject.minimized) {
win.loadWinBG(win.runningApps[1].windowObject);
if (win.runningApps[1].windowObject.sysWinId != null) {
    var exec = require('child_process').exec,
                   child;
            child = exec("wmctrl -i -R "+win.runningApps[1].windowObject.sysWinId,function (error, stdout, stderr)
    {
                
    if (error !== null) {
      console.log('exec error: ' + error);
    } else {
        

    }

	win.show();
	restoreWin(win.runningApps[1].windowObject);
	console.log("Restore itai");
	//win.runningApps[1].windowObject.restore();
	win.runningApps[1].windowObject.minimized = false;       
});
}

} else {
win.runningApps[1].windowObject.minimize();
win.runningApps[1].windowObject.minimized = true;
//win.loadWinBG(win.runningApps[1].windowObject);
console.log("Minimized itai");
}
}

function setEmoji(response) {
    var emojiSet = false;
    
    if (response.indexOf("amusing") != -1 || response.indexOf("glad") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-innocent"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("Me either") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-joy"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("I like you a lot too") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-blush"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("God") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-smile"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("clever") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-smirk"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("comedy") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-laughing"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("sad") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-no_mouth"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("wrong") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-no_mouth"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("A normal seventy degrees inside the computer.") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-stuck_out_tongue"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("How well do you know this person?") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-no_mouth"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("to know") != -1 || response.indexOf("good") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-grinning"></i>');
        emojiSet = true;
    }
    
    if (response.indexOf("Mountain Goats") != -1) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<i class="em em-goat"></i>');
        emojiSet = true;
    }
    
    if (!emojiSet) {
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).empty();
        //$("#aiIconDiv").append('<i class="em em-grinning"></i>');
        $( win.runningApps[0].extrabarObject.window.document.getElementById("aiIconDiv")).append('<span class="AiIcon icon">&#61704;</span>');
        emojiSet = true;
    }
}

function aiResponse(response) {
    //console.log("AI RESPONSE",response);
    setEmoji(response);
    
    $( win.runningApps[0].extrabarObject.window.document.getElementById("aiResponse")).text(response);
}

//win.runningApps[0].windowObject.sysWin.window.aiCallback = aiResponse;

setTimeout(function(){ 
       
        }, 5000);


$( "input" ).focus(function() {
  //$("#extraAiBar").removeClass("hideOpacity");
    
    if (!win.runningApps[0].extrabarObject.currentlyVisible) {
        win.runningApps[0].extrabarObject.currentlyVisible = true;
        win.runningApps[0].extrabarObject.show();
        
        setTimeout(function(){  win.focus();/*$( "input" ).focus();*/}, 500); //foce refocus since we lost focus
    }
    
    $( win.runningApps[0].extrabarObject.window.document.getElementById("extraAiBar")).removeClass("animated fadeOutDown");
    $(win.runningApps[0].extrabarObject.window.document.getElementById("extraAiBar")).addClass("animated fadeInUp");
    //$("#extraAiBar").removeClass("hidden");
    
    //win.height = 335;
    //win.y = screen.height-(335);
});

$( "input" ).focusout(function() {
  //$("#extraAiBar").addClass("hideOpacity");
    setTimeout(function(){ 
    if (!$("input").is(":focus")) {
        win.runningApps[0].extrabarObject.currentlyVisible = false;
    $(win.runningApps[0].extrabarObject.window.document.getElementById("extraAiBar")).removeClass("animated fadeInUp");
    $(win.runningApps[0].extrabarObject.window.document.getElementById("extraAiBar")).addClass("animated fadeOutDown");
    win.runningApps[0].extrabarObject.hide();
    }
    //setTimeout(function(){ $("#extraAiBar").addClass("hidden"); }, 1000);
    
       // win.height = 66;
        //win.y = screen.height-(66);
        }, 500);
    
});

$("#aiInput").keyup(function (e) {
    if (e.keyCode == 13) {
var inputVal = $("#aiInput").val();
if (inputVal == "gnome_terminal_exec") {
    var exec = require('child_process').exec,
                   child;
            child = exec('gnome-terminal',function (error, stdout, stderr)
    {//process.cwd()+"/blur_app.sh"
    //console.log('stdout: ' + stdout);
    //console.log('stderr: ' + stderr);
                
   
      
});
} else {
        win.runningApps[0].windowObject.sysWin.window.aiRequest($("#aiInput").val(),aiResponse);
        $("#aiInput").val("");
    document.getElementById("aiInput").focus();
}
    }
});

function aiRequest() {
    win.runningApps[0].windowObject.sysWin.window.aiRequest($("#aiInput").val(),aiResponse);
        $("#aiInput").val("");
    document.getElementById("aiInput").focus();
}

/*
var bot = new RiveScript();

function tempAI() {
    bot.loadFile([
	"aiBrain/begin.rive",
	"aiBrain/admin.rive",
	"aiBrain/coffee.rive",
	"aiBrain/eliza.rive",
	"aiBrain/myself.rive",
	"aiBrain/clients.rive"
], loading_done, loading_error);
}


function loading_done (batch_num) {
	console.log("Batch #" + batch_num + " has finished loading!");

	// Now the replies must be sorted!
	bot.sortReplies();

	// And now we're free to get a reply from the brain!
	var reply = bot.reply("local-user", "Hello, bot!");
	console.log("The bot says: " + reply);
}

// It's good to catch errors too!
function loading_error (error) {
	console.log("Error when loading files: " + error);
}

*/
//tempAI();


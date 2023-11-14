//console.log("hi"); 

var totalBlurs = 0; //Used to limit the amount of blured elements to avoid rediced perfomance
var totalBlursLimit = 10;

var lastRightCLickTime = 0;

new MutationObserver(function(mutations) {
    console.log("itle detected: ", mutations[0].target.nodeValue);
    alert("extern-new-title-xp: ",mutations[0].target.nodeValue);
}).observe(
    document.querySelector('title'),
    { subtree: true, characterData: true }
);

function scrollInit() {
//$("html").niceScroll({mousescrollstep: 80, smoothscroll: true, zindex:2999999999, bouncescroll: true, enabletranslate3d:true});

//$("html").niceScroll({zindex:2999999999});
//$("embed").niceScroll({mousescrollstep: 80, smoothscroll: true, zindex:2999999999, bouncescroll: true, enabletranslate3d:true});

//$("embed").niceScroll({zindex:2999999999});
//$("div").niceScroll({mousescrollstep: 80, smoothscroll: true, zindex:2999999999, bouncescroll: true, enabletranslate3d:true});
}

if ($("#main-frame-error").length != 0) {
    //console.log("ERROR");
}

/*Fix overflow issue*/
 /*var fixOverflow = $('*').filter(function () { 
        return (($(this).height() == $("body").height()) && ($(this).width() == $("body").width()) && ($(this).prop("tagName") != "HTML") && ($(this).prop("tagName") != "BODY")) ;
    });

$($(fixOverflow)[0]).css("overflow-y","scroll");*/
function fixTopLevelDomElements() {

 var find = $('*').filter(function () { 
        return $(this).offset().top < 60;
    });

var findFixed = $(find).filter(function () { 
        return $(this).css('position') == 'fixed';
    });

//console.log("fixed elements",findFixed);

/* var find = $('*').filter(function () { 
        return $(this).css('position') == 'fixed';
    });

*/

/*finderr = $(find).filter(function () { 
        return $(this).outerWidth() > 2;
    });*/

$.fn.widthPerc = function(){
    var parent = this.parent();
    return ~~((this.width()/parent.width())*100)+"%";
}

/*finderr = $(find).filter(function () { 
        return $(this).widthPerc() == "100%";
    });*/

/*
finderr = $(finderr).filter(function () { 
        return $(this).outerWidth() > 100;
    });*/

/*
var findFixed = $(finderr).filter(function () { 
        return $(this).css('position') == 'fixed';
    });

console.log("fixed elements",findFixed);*/

for (var i = 0; i < findFixed.length; i++) {
	if (!$(findFixed[i]).hasClass("alreadyFixedeXternOS")) {
	var topPos = parseInt($(findFixed[i]).css('top'), 10);
	$(findFixed[i]).css({top: topPos+60});
	$(findFixed[i]).addClass("alreadyFixedeXternOS");
	//console.log("fixed this now: ",findFixed[i]);
	}
}

/*
finderr = $(finderr).filter(function () { 
        return $(this).prop("tagName") != "HTML" && $(this).prop("tagName") != "BODY"  && $(this).prop("tagName") != "STYLE" && $(this).prop("tagName") != "SCRIPT";
    });

console.log("fixed elements",finderr);
*/
}


fixTopLevelDomElements();

// A $( document ).ready() block.
$( document ).ready(function() {
    

    //Sometimes didn't work on all elements as they were still loading
  setTimeout(function(){ fixTopLevelDomElements() }, 2000);
});




//detect right click
var clickedEl = null;


function setRightClick() {
elm = document.getElementsByTagName("a");
    for (var i = 0; i < elm.length; i++) {
elm[i].addEventListener("mousedown", function(event){
    //right click
    if(event.button == 2) { 
        clickedEl = event.target;
window.rightClickedElement = clickedEl;
window.rightClickedElementThumb = $(clickedEl).closest('div').find("img").attr("src");
    }
}, true);
}
}




$( "a" ).contextmenu(function(eventData) {
var currentTimeSeconds = new Date().getTime() / 1000;
if ((currentTimeSeconds - lastRightCLickTime) > 2) { //To prevent overriding the first detected element
lastRightCLickTime = currentTimeSeconds;
  //console.log("CONTEXT",eventData);
  alert("extern-command: cs-move: x:"+eventData.clientX+" y:"+eventData.clientY);
window.rightClickedElement = eventData.currentTarget;
}
});

$( "IMG" ).contextmenu(function(eventData) {
var currentTimeSeconds = new Date().getTime() / 1000;
if ((currentTimeSeconds - lastRightCLickTime) > 2) { //To prevent overriding the first detected element
lastRightCLickTime = currentTimeSeconds;
  //console.log("CONTEXT IMG",eventData);
window.rightClickedElement = eventData.currentTarget;
}
});


elm = document.getElementsByTagName("html");

    for (var i = 0; i < elm.length; i++) {
//console.log("added body",elm[i]);
elm[i].addEventListener("mousedown", function(event){
    //right click
    if(event.button == 2) {
		alert("extern-command: cs-move: x:"+event.clientX+" y:"+event.clientY);
        clickedEl = event.target;
window.rightClickedElement = this;
      //console.log("rightclicked body",this);
//window.rightClickedElementThumb = $(clickedEl).closest('div').find("img").attr("src");
    }
}, true);
}


$(document).bind('DOMNodeInserted', function(e) {
    //setRightClick();
    //scrollInit();
//console.log("domInserted",e);



        /*var color = $(e.target).css("background-color");
        if (color == "rgb(255, 255, 255)" || color == "white" || color == "#fff") {
            $(e.target).css("background-color", "rgba(255,255,255,0.3)");
	   if (($(e.target).zIndex() > 800) && ($(e.target).height() > 40) && (totalBlurs < totalBlursLimit) && (window.getComputedStyle(e.target).getPropertyValue("opacity") != 0)) {
		$(e.target).css("backdrop-filter", "blur(10px)");
		//$(e.target).css("background-color", "rgba(255,255,255,0.6)");
		$(e.target).css('box-shadow', 'none');
		totalBlurs++;
		console.log("totalBlurs",totalBlurs);
		console.log("totalBlurs element",e.target);
		//console.log("calculated opacity",window.getComputedStyle(e.target).getPropertyValue("opacity"));
	    }
        }*/

        //var color = $(e.target).css("background");
        //if (color == "rgb(255, 255, 255)" || color == "white" || color == "#fff") {
			
			//console.log("type of",e.target.tagName);
			if (e.target.tagName != undefined) {
				var color = window.getComputedStyle(e.target).backgroundColor;
        if (color.indexOf("255, 255, 255") > -1) {
            $(e.target).css("background", "rgba(255,255,255,0.3)");
	    $(e.target).css("background-color", "rgba(255,255,255,0.3)");
	   if (($(e.target).zIndex() > 800) && ($(e.target).height() > 40) && (totalBlurs < totalBlursLimit) && (window.getComputedStyle(e.target).getPropertyValue("opacity") != 0)) {
		$(e.target).css("backdrop-filter", "blur(10px)");
		$(e.target).css("background-color", "rgba(255,255,255,0.6)");
		$(e.target).css('box-shadow', 'none');
		totalBlurs++;
		//console.log("totalBlurs AA",totalBlurs);
		//console.log("totalBlursAA element",e.target);
	    }
        }
			}
	

//https://twitter.com/github


if (e.target.tagName == "A") {
  $(e.target).mouseenter(function() {
    alert("extern-command: a: mouseenter:"+$(this).prop('href'));
  })
  .mouseleave(function() {
    alert("extern-command: a: mouseleave:"+$(this).prop('href'));
  });
//console.log("DOM INSERT",e.target.tagName);
$(e.target).contextmenu(function(eventData) {
  //console.log("CONTEXT",eventData);
var currentTimeSeconds = new Date().getTime() / 1000;
if ((currentTimeSeconds - lastRightCLickTime) > 2) { //To prevent overriding the first detected element
lastRightCLickTime = currentTimeSeconds;
  console.log("rightclicked element2");
window.rightClickedElement = eventData.currentTarget;
}
});
}


if (e.target.tagName == "A") {
//console.log("DOM INSERT",e.target.tagName);
$(e.target).contextmenu(function(eventData) {
  //console.log("CONTEXT",eventData);
window.rightClickedElement = eventData.currentTarget;
});
}

if (e.target.tagName == "IMG") {
$(e.target).contextmenu(function(eventData) {
  //console.log("CONTEXT",eventData);
var currentTimeSeconds = new Date().getTime() / 1000;
if ((currentTimeSeconds - lastRightCLickTime) > 2) { //To prevent overriding the first detected element
lastRightCLickTime = currentTimeSeconds;
  console.log("rightclicked image 2",eventData.currentTarget);
window.rightClickedElement = eventData.currentTarget;
}
});
}
/*
    $( "img" ).contextmenu(function(eventData) {
  //console.log("CONTEXT",eventData);
window.rightClickedElement = eventData.currentTarget;
});*/
});

//For transparency

jQuery.fn.getCssNumber = function(prop){
    var v = parseInt(this.css(prop),10);
    return isNaN(v) ? 0 : v;
};

$("*").each(function () {



	if (this.tagName == "UL" && $(this).attr("role") == "listbox") { //Google search results blur fix
		var color = window.getComputedStyle($(this).parent()[0]).backgroundColor;
		
		if (color.indexOf("255, 255, 255") > -1) {
		$($(this).parent()[0]).css("backdrop-filter", "blur(10px)");
		}
		

	}

	if ($(this).height() == $(document).height() && this.nodeName != "HTML") {
		//console.log("element full",this);
		this.style.setProperty("background-color","rgba(0, 0, 0, 0)","important");
		this.style.setProperty("margin-top","60px","important");
		this.style.setProperty("position","relative");
	}

	var alphaSet = false;
        //var color = $(this).css("background-color");
	var color = window.getComputedStyle(this).backgroundColor;
        if (color.indexOf("255, 255, 255") > -1) {
            $(this).css("background-color", "rgba(255,255,255,0.3)");
	    alphaSet = true;

	    if (($(this).zIndex() > 800) && ($(this).height() > 40) && (totalBlurs < totalBlursLimit)) { //&& (window.getComputedStyle(this).getPropertyValue("opacity") != 0)

		var continueToApplyBlur = true;



		if ((window.getComputedStyle(this).getPropertyValue("opacity") == 0) && (window.getComputedStyle(this).getPropertyValue("top") != "60px"))
			continueToApplyBlur = false;

		if (continueToApplyBlur) {
		$(this).css("backdrop-filter", "blur(10px)");
		$(this).css("background-color", "rgba(255,255,255,0.6)");
		$(this).css('box-shadow', 'none');
		totalBlurs++;
		
		}
	    }
        }

	if (this.tagName == "HEADER") {

		var continueToApplyBlur = true;

		if ((window.getComputedStyle(this).getPropertyValue("opacity") == 0) && (window.getComputedStyle(this).getPropertyValue("top") != "60px"))
			continueToApplyBlur = false;

		if (continueToApplyBlur) {
			$(this).css("backdrop-filter", "blur(10px)");
			$(this).css('box-shadow', 'none');
		}
	}

	/*var color = $(this).css("background");
        if (color.indexOf("255, 255, 255") > -1) {
            $(this).css("background", "rgba(255,255,255,0.3)");
	    alphaSet = true;
	    if (($(this).zIndex() > 800) && ($(this).height() > 40) && (totalBlurs < totalBlursLimit) && (window.getComputedStyle(this).getPropertyValue("opacity") != 0)) {
		$(this).css("backdrop-filter", "blur(10px)");
		$(this).css("background-color", "rgba(255,255,255,0.6)");
		$(this).css('box-shadow', 'none');
		totalBlurs++;
		console.log("totalBlurs",totalBlurs);
	    }
        }*/

	var color = $(this).css("background");
        if (color == "#fafbfc") {
            $(this).css("background", "rgba(255,255,255,0.3)");
	    alphaSet = true;
	    if (($(this).zIndex() > 800) && ($(this).height() > 40) && (totalBlurs < totalBlursLimit) && (window.getComputedStyle(this).getPropertyValue("opacity") != 0)) {
		$(this).css("backdrop-filter", "blur(10px)");
		$(this).css("background-color", "rgba(255,255,255,0.6)");
		$(this).css('box-shadow', 'none');
		totalBlurs++;
		//console.log("totalBlurs",totalBlurs);
		//console.log("totalBlursB div",this);
	    }
        }

		    if (!alphaSet) {
		//console.log("element",this);
	    //console.log("z-index",$(this).zIndex());
		var elementColor = window.getComputedStyle(this, null).getPropertyValue("background-color");

		if (elementColor != "rgb(0,0,0)") { //I was going to add alpha in the else later on
			//console.log("bg colour",elementColor);
			if (elementColor.indexOf("rgb") != -1) {
				if (elementColor.indexOf("rgba") == -1) {
					var newColor = elementColor.replace("rgb","rgba").replace(")",",0.6");
					//console.log("css",this.style.cssText+" background-color: "+ newColor+" !important;");
					this.style.setProperty("background-color",newColor,"important");
					//$(this).css("cssText",this.style.cssText+" background-color: "+ newColor+" !important;");
				}
			}
			
		}
		//$(this).css("backdrop-filter", "blur(10px)");
		//$(this).css("background-color", "rgba(255,255,255,0.6)");
	    }
    });
	
setTimeout(function(){ 
  $("a").addClass("weGotHERE");
  $("a").mouseenter(function() {
    alert("extern-command: a: mouseenter:"+$(this).prop('href'));
  })
  .mouseleave(function() {
    alert("extern-command: a: mouseleave:"+$(this).prop('href'));
  });

  $( "a" ).contextmenu(function(eventData) {
var currentTimeSeconds = new Date().getTime() / 1000;
if ((currentTimeSeconds - lastRightCLickTime) > 2) { //To prevent overriding the first detected element
lastRightCLickTime = currentTimeSeconds;
  //console.log("CONTEXT",eventData);
  alert("extern-command: cs-move: x:"+eventData.clientX+" y:"+eventData.clientY);
window.rightClickedElement = eventData.currentTarget;
}
});
			}, 2000);

scrollInit();
if ($("html").attr("itemtype") != "http://schema.org/SearchResultsPage") {
	var htmlEl = $("html")[0];
	htmlEl.style.setProperty("padding-top","60px","important");
  //htmlEl.style.setProperty("position","relative");
} else {
	if ($("#viewport").length != 0)
		$("#viewport")[0].style.setProperty("padding-top","60px","important");
  var htmlEl = $("html")[0];
  //htmlEl.style.setProperty("position","relative");
}

var elementColor = window.getComputedStyle($("html")[0], null).getPropertyValue("background-color");

//console.log("computed html colour",elementColor);

var htmlEl = $("html")[0];
if (elementColor == "rgba(255, 255, 255)")
htmlEl.style.setProperty("background-color","rgba(0, 0, 0, 0)","important");

var htmlEl = $("body")[0];
htmlEl.style.setProperty("background-color","rgba(0, 0, 0, 0)","important");

alert("extern-command: status:ready");

//console.log("hi"); 

var lastRightCLickTime = 0;

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
	}
}

/*
finderr = $(finderr).filter(function () { 
        return $(this).prop("tagName") != "HTML" && $(this).prop("tagName") != "BODY"  && $(this).prop("tagName") != "STYLE" && $(this).prop("tagName") != "SCRIPT";
    });

console.log("fixed elements",finderr);
*/
}




// A $( document ).ready() block.
$( document ).ready(function() {
    fixTopLevelDomElements();

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
      //console.log("rightclicked element");
        clickedEl = event.target;
window.rightClickedElement = clickedEl;
window.rightClickedElementThumb = $(clickedEl).closest('div').find("img").attr("src");
    }
}, true);
}
  
  elm = document.getElementsByTagName("img");
  
    for (var i = 0; i < elm.length; i++) {
elm[i].addEventListener("mousedown", function(event){
    //right click
    if(event.button == 2) {
      //console.log("rightclicked image");
        clickedEl = event.target;
window.rightClickedElement = clickedEl;
//window.rightClickedElementThumb = $(clickedEl).closest('div').find("img").attr("src");
    }
}, true);
}




  
}

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
  //console.log("rightclicked element2");
window.rightClickedElement = eventData.currentTarget;
}
});
}

if (e.target.tagName == "IMG") {
$(e.target).contextmenu(function(eventData) {
  //console.log("CONTEXT",eventData);
var currentTimeSeconds = new Date().getTime() / 1000;
if ((currentTimeSeconds - lastRightCLickTime) > 2) { //To prevent overriding the first detected element
lastRightCLickTime = currentTimeSeconds;
  //console.log("rightclicked image 2",eventData.currentTarget);
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

$("*").each(function () {


	if ($(this).height() == $(document).height()) {
		this.style.setProperty("margin-top","60px","important");
    this.style.setProperty("position","relative");
	}

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

$( "IMG" ).contextmenu(function(eventData) {
var currentTimeSeconds = new Date().getTime() / 1000;
if ((currentTimeSeconds - lastRightCLickTime) > 2) { //To prevent overriding the first detected element
lastRightCLickTime = currentTimeSeconds;
  //console.log("CONTEXT IMG",eventData);
window.rightClickedElement = eventData.currentTarget;
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
	htmlEl.style.setProperty("margin-top","60px","important");
  htmlEl.style.setProperty("position","relative");
} else {
  if ($("#viewport").length != 0)
	  $("#viewport")[0].style.setProperty("margin-top","60px","important");
  var htmlEl = $("html")[0];
  htmlEl.style.setProperty("position","relative");
}

alert("extern-command: status:ready");


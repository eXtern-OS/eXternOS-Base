$(document).ready(function() {
    
$('#allTabss').carousel({
    interval: 5000
});

//win.showDevTools();
    

	window.areWeAutoCorrectingTheView = 0; //this is 1 when change track is called to adjust things we then set it to 2 to change back to the previous slide and then 0 to default
    
    
    $('.single-item').slick({
        dots: false,
        infinite: true,
        speed: 300,
        slidesToShow: 1,
        slidesToScroll: 1
    })
        .on('beforeChange', function(event, slick, currentSlide, nextSlide){
        //$.videoChanged(nextSlide);
        //testTest();
        //$.videoChanged(nextSlide);
        console.log("beforechange event window.areWeAutoCorrectingTheView: ",window.areWeAutoCorrectingTheView);
        var gui = require('nw.gui');
            var win = gui.Window.get();



	 if (window.areWeAutoCorrectingTheView == 1) {
		setTimeout(function(){
		window.areWeAutoCorrectingTheView++;
		$('.single-item').slick('slickPrev');
		}, 500);
	} else if (window.areWeAutoCorrectingTheView == 2) {
		//$('.single-item').slick('slickPrev');
		setTimeout(function(){
		$("#playingInfoControls").removeClass("hiddenOpacity");
		}, 500);
		window.areWeAutoCorrectingTheView = 0;
	} else if (window.areWeAutoCorrectingTheView == 0)
		window.changeTrack(nextSlide);
        //console.log("Here is a bug onChangeSlide: ");

        //$(".selected_song")[0].parentNode.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"});
        var target = $(".selected_song")[0];
        //target.parentNode.parentNode.scrollTop = target.offsetTop;

        $(target.parentNode.parentNode).animate({
                    scrollTop: target.offsetTop
                }, 500);
        
        });
});
console.log("WE ARE SO COOL");


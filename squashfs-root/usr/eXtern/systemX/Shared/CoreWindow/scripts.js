$(document).ready(function() {
    
$('#allTabss').carousel({
    interval: 5000
});
    
    
    
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
        
        var gui = require('nw.gui');
            var win = gui.Window.get();
        
        window.changeTrack(nextSlide);
        //console.log("Here is a bug onChangeSlide: ");
        
        });
});
console.log("WE ARE SO COOL");


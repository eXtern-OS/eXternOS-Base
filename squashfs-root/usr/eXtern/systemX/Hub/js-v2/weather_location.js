

function initLocation() {
$.getJSON("http://freegeoip.net/json/", function(data) {
    var country_code = data.country_code;
    var country = data.country_name;
    var ip = data.ip;
    var time_zone = data.time_zone;
    var latitude = data.latitude;
    var longitude = data.longitude;
    var city = data.city;

    /*console.log("Country Code: " + country_code);
    console.log("Country Name: " + country);
    console.log("IP: " + ip); 
    console.log("Time Zone: " + time_zone);
    console.log("Latitude: " + latitude);
    console.log("Longitude: " + longitude); 
    console.log("City: " + city); */

    
});
}




var needle = require('needle'),
    qs      = require('querystring'),
    xml2JS  = require('xml2js');

  var xmlParser     = new xml2JS.Parser({charkey: 'C$', attrkey: 'A$', explicitArray: true}),
      defLang       = 'en-US',
      defDegreeType = 'F',
      defTimeout    = 10000,
      findUrl       = 'http://weather.service.msn.com/find.aspx';

  var find = function find(options, callback) {

	//console.log("gets here 1");

    if(typeof callback !== 'function')
      callback = function callback(err, result) { return err || result; };

    if(!options || typeof options !== 'object')
      return callback('invalid options');

    if(!options.search)
      return callback('missing search input');

    var result     = [],
        lang       = options.lang || defLang,
        degreeType = options.degreeType || defDegreeType,
        timeout    = options.timeout || defTimeout,
        search     = qs.escape(''+options.search),
        reqUrl     = findUrl + '?src=outlook&weadegreetype=' + (''+degreeType) + '&culture=' + (''+lang) + '&weasearchstr=' + search;

	console.log("reqUrl",reqUrl);

    needle.get(reqUrl, function(err, response) {

	console.log("gets here 2", response);

	var currentTemperature;

	          // Init weather item
          weatherItem = {
            location: {
              name: response.body.children[0].attributes.weatherlocationname,
              lat: response.body.children[0].attributes.lat,
              long: response.body.children[0].attributes.long,
              timezone: response.body.children[0].attributes.timezone,
              alert: response.body.children[0].attributes.alert,
              degreetype: response.body.children[0].attributes.degreetype
              //url: resultJSON.weatherdata.weather[i]['A$']['url'],
              //code: resultJSON.weatherdata.weather[i]['A$']['weatherlocationcode'],
              //entityid: resultJSON.weatherdata.weather[i]['A$']['entityid'],
              //encodedlocationname: resultJSON.weatherdata.weather[i]['A$']['encodedlocationname']
            },
            current: null,
            forecast: []
          };

	console.log("gets here 1.1");

	for (var i = 0; i < response.body.children[0].children.length; i++) {
		if (response.body.children[0].children[i].name == "current") {
			weatherItem.current = response.body.children[0].children[i].attributes;
			currentTemperature = response.body.children[0].children[i].attributes.temperature;

		} else {

			weatherItem.forecast.push(response.body.children[0].children[i].attributes);

		}
	}

		console.log("gets here 1.2");

		var weatherIconsLocation = "/usr/eXtern/systemX/Shared/CoreIMG/icons/weather/";

		var weatherIconName = weatherItem.current.skycode+".png";

		if (weatherItem.current.skycode == "18" || weatherItem.current.skycode == "40")
			weatherIconName = "18, 40.png";

		if (weatherItem.current.skycode == "10" || weatherItem.current.skycode == "11")
			weatherIconName = "10, 11.png";

		if (weatherItem.current.skycode == "12" || weatherItem.current.skycode == "39")
			weatherIconName = "12, 39.png";

		if (weatherItem.current.skycode == "23" || weatherItem.current.skycode == "24")
			weatherIconName = "23, 24.png";

		if (weatherItem.current.skycode == "37" || weatherItem.current.skycode == "38")
			weatherIconName = "37, 38.png";

		if (weatherItem.current.skycode == "45" || weatherItem.current.skycode == "47")
			weatherIconName = "45, 47.png";

		if (weatherItem.current.skycode == "27" || weatherItem.current.skycode == "29" || weatherItem.current.skycode == "33")
			weatherIconName = "27,29,33.png";

		if (weatherItem.current.skycode == "20" || weatherItem.current.skycode == "21" || weatherItem.current.skycode == "22")
			weatherIconName = "20, 21, 22.png";

		if (weatherItem.current.skycode == "8" || weatherItem.current.skycode == "9" || weatherItem.current.skycode == "13")
			weatherIconName = "8, 9, 13.png";

		if (weatherItem.current.skycode == "28" || weatherItem.current.skycode == "30" || weatherItem.current.skycode == "34")
			weatherIconName = "28,30,34.png";

		if (weatherItem.current.skycode == "0" || weatherItem.current.skycode == "1" || weatherItem.current.skycode == "2" || weatherItem.current.skycode == "3" || weatherItem.current.skycode == "4" || weatherItem.current.skycode == "17" || weatherItem.current.skycode == "35")
			weatherIconName = "0, 1 ,2, 3 ,4, 17, 35.png";

		if (weatherItem.current.skycode == "0" || weatherItem.current.skycode == "5" || weatherItem.current.skycode == "6" || weatherItem.current.skycode == "7" || weatherItem.current.skycode == "41" || weatherItem.current.skycode == "46")
			weatherIconName = "5, 6, 7, 41, 46.png";

		if (weatherItem.current.skycode == "14" || weatherItem.current.skycode == "15" || weatherItem.current.skycode == "16" || weatherItem.current.skycode == "42" || weatherItem.current.skycode == "43")
			weatherIconName = "14, 15, 16, 42, 43.png";

		console.log("weatherItem",weatherItem);


		setLocationLatLongTimezone(weatherItem.location);

		console.log("currentTemperature",currentTemperature);

	      html = '<img style="max-height: 130px; margin-bottom: 50px;" src="file://'+weatherIconsLocation+weatherIconName+'"> <h2>'+weatherItem.current.temperature+'&deg;'+systemTemperatureUnit+'</h2>';
      html += '<h4 style="font-weight: bold;">'+weatherItem.location.name+'</h4>';
      html += '<ul><li class="currently">'+weatherItem.current.skytext+'</li>';
      html += '<li>'+weatherItem.current.winddisplay+'</li></ul>';

	console.log("weather loaded");  

	$("#weather").empty();

      $("#weather").html(html);

      if(err) {
		console.log("error",err);
                    return callback(err);
	}
      //if(res.statusCode !== 200) return callback(new Error('request failed (' + res.statusCode + ')'));
      if(!response.body) {
		console.log("failed to get body content");
                  return callback(new Error('failed to get body content'));
	}





    });
  };

//find({search: 'Mount Gambier, SA', degreeType: 'C'});





//initLocation();


/*
//REENABLE
(function () {
  var blockContextMenu, myElement;

  blockContextMenu = function (evt) {
    evt.preventDefault();
  };

  myElement = document.querySelector('body');
  myElement.addEventListener('contextmenu', blockContextMenu);
})();*/



//console.log('LOCATION GETS HERE');

if (localStorage.getItem('systemTemperatureUnit') === null)
    systemTemperatureUnit = 'c';
else
    systemTemperatureUnit = JSON.parse(localStorage.getItem('systemTemperatureUnit'));

$("#temperatureUnitsOptionsDropdown").empty();

	if (systemTemperatureUnit == 'c')
		$("#temperatureUnitsOptionsDropdown").append('Celsius <span class="caret"></span>');
	else
		$("#temperatureUnitsOptionsDropdown").append('Fahrenheit <span class="caret"></span>');


function setLocationLatLongTimezone(locationDetails) {
      //user_location.timezone = locationDetails.timezone;
      user_location.lat = locationDetails.lat;
      user_location.long = locationDetails.long;

	localStorage.setItem('user_location', JSON.stringify(user_location));

}


function loadWeatherStats() {
    $("#weather").empty();

if (navigator.onLine) { 



//var weather = require('weather-js');
 
// Options:
// search:     location name or zipcode
// degreeType: F or C
 
/*weather.find({search: 'San Francisco, CA', degreeType: 'F'}, function(err, result) {
  if(err) console.log(err);
 
  console.log("weather",JSON.stringify(result, null, 2));
});*/








  if (user_location.city == "") {
    
    
    $.getJSON("http://ip-api.com/json", function(data) {
//console.log("weather ip data",data);

//console.log("loc data",data);
      
      
      user_location.city = data.city;
      user_location.region = data.region;
      user_location.country = data.country;
      user_location.zipcode = data.zip;
      user_location.timezone = data.timezone;
      user_location.lat = data.lat;
      user_location.long = data.lon;
      
      find({search: user_location.city+', '+user_location.region+', '+user_location.country, degreeType: systemTemperatureUnit});
      
      
      
      /*$.simpleWeather({
    location: data.lat+', '+data.lon,//'Melbourne, VIC, Australia',
    woeid: '',
    unit: systemTemperatureUnit,
    success: function(weather) {

	//console.log("weather code",weather);
//<i class="wi '+weatherCode+'"></i>
        var weatherCode = "wi-night-sleet";
        if (weather.code == 6)
            weatherCode = "wi-day-sleet";
      html = '<img style="margin-left: 40px;" src="'+weather.image+'"> <h2>'+weather.temp+'&deg;'+weather.units.temp+'</h2>';
      html += '<h4 style="font-weight: bold;">'+weather.city+', '+weather.region+'</h4>';
      html += '<ul><li class="currently">'+weather.currently+'</li>';
      html += '<li>'+weather.wind.direction+' '+weather.wind.speed+' '+weather.units.speed+'</li></ul>';

	console.log("weather loaded");  

      $("#weather").html(html);
    },
    error: function(error) {
      $("#weather").html('<p>'+error+'</p>');
    }
  });*/

});
    
    
    
  } else {
    
    find({search:user_location.city+', '+user_location.country, degreeType: systemTemperatureUnit});
  }

  



}
}


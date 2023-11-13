//Find in array Function

var contains = function(needle) {
    // Per spec, the way to identify NaN is that it is not equal to itself
    var findNaN = needle !== needle;
    var indexOf;

    if(!findNaN && typeof Array.prototype.indexOf === 'function') {
        indexOf = Array.prototype.indexOf;
    } else {
        indexOf = function(needle) {
            var i = -1, index = -1;

            for(i = 0; i < this.length; i++) {
                var item = this[i];

                if((findNaN && item !== item) || item === needle) {
                    index = i;
                    break;
                }
            }

            return index;
        };
    }

    return indexOf.call(this, needle) > -1;
};



//setTimeout(function(){ meSpeak.speak("hello world"); console.log("executed",meSpeak.isVoiceLoaded());}, 5000);

//Side Widgets

var sideWidgets = [];
//News
var newsCount = 0;
var newsSources = [];
var enabledSources = [];

//console.log("Accessed Apps",accessedApps);

//localStorage.setItem('enabledSources', JSON.stringify(newsSources));

if (localStorage.getItem('enabledSources') === null)
    var enabledSources = [];
else
    var enabledSources = JSON.parse(localStorage.getItem('enabledSources'));

/*if (enabledSources.length != 0)
    setTimeout(function(){ runningApps[0].windowObject.canOpenHub = true; }, 3000);*/

function enableNewsSources(newsSourcesx) {
    //console.log("newsSources",newsSources);
    /*
    Code below to use to refresh carousel
    
    $("#main-navigation-carousel").carousel("pause").removeData();
    $("#main-navigation-carousel").carousel(0);
    
    */
sideWidgets = [];
//News
newsCount = 0;
newsSources = [];
enabledSources = [];
localStorage.setItem('enabledSources', JSON.stringify(newsSourcesx));
    
    enabledSources = newsSourcesx;

console.log("enabledSources",enabledSources);

	if (enabledSources.length == 0) {
		newsSources = [];
		allActiveNews = [];
		appsUpdateData();
	} else {


	//insertNews(newsSources);

	loadNewsSources(true);

	}
    
    //loadNewsSources(true);
    //loadWeatherStats();
    //webInformationLoaded = true;
}

/*
enabledSources.push("ABC News AU : Top Stories");
enabledSources.push("CNN : Top Stories");
enabledSources.push("TechCrunch");
enabledSources.push("TechCrunch : Social");


//enabledSources.push("TechCrunch");
enabledSources.push("The Verge");
*/

function loadNewsFeed(sourceName,url,div) {
  //const url = 'http://www.theverge.com/rss/index.xml'
  //const textarea = document.getElementById('rickys-blog-textarea')
  feednami.load(url)
    .then(feed => {
      //textarea.value = ''
      //console.log(feed);
      //feedImage = feed.entries[m].image.url;
      for (var m = 0; m < 3; m++) {
          
          if (feed.entries[m].image.url != null & feed.entries[m].author != "ABC News") {
              feedImage = feed.entries[m].image.url;
              //console.log("NOT ABC NEWS");
          } else {
              if (feed.entries[m]["media:group"] != null) {
              feedImage = feed.entries[m]["media:group"]["media:content"][0]["@"].url;
              } else {
                  feedImage = $(feed.entries[m].description).closest('img').attr("src");
              }
          }
          
          //console.log("IMAGE: ",feedImage);
          
          //feedImage = feed.entries[m];//.image.url;
          feedLink = feed.entries[m].link;
          feedTitle = feed.entries[m].title;
          
          //console.log("feedIMG:",feedImage);
          //console.log("feedLnk:",feedLink);
         // console.log("feedTitle:",feedTitle);
	var newsObject = {
			title: feedTitle,
			image: feedImage,
			link: feedLink,
			Source: sourceName

}
          allActiveNews.push(newsObject);
          s = "";
      s += '<li class="m-b-10" style="position: relative;"><a class="newsArticle" href="#" onclick="openNewsInBrowser(`'+feedLink+'`)"> <img  src="'+feedImage+'" alt="" style="width: 100%; /*height: 100px;*/ border-radius: 10px; display: inline-block; margin: 0 5px 0 0;"><span class="itemTitle" style="display: inline-block; /*width: 75%;*/"><p style="    color: rgba(255, 255, 255, 0.8);    text-shadow: 0 0 20px rgb(0, 0, 0); font-size: 13px; /*height: 44px;*/ /*display: table-cell;*/ /*vertical-align: middle;*/" >' + feedTitle + "</p></span>";
      

	if (div != null)
		$(div).append('<ul class="feedEkList list-unstyled">' + s + "</ul>");
          
      }

	processedNews++;

	if (processedNews == totalNewsToProcess) {
		console.log("allActiveNews.length: ",allActiveNews.length);
		appsUpdateData();
	}
      
      /*for(let entry of feed.entries){
        textarea.value += `${entry.title}\n${entry.link}\n\n`
      }*/
    })

}

var processedNews = 0;
var totalNewsToProcess = 0;

function insertNews(newsSources) {

	processedNews = 0;
	totalNewsToProcess = newsSources.length;

//allActiveNews = [];
for (var i = 0; i < newsSources.length; i++)
{
    /*if (i==0)
        var active = ' active';
    else
        var active = '';
    //console.log("executed news");
$("#sideWidgets").append('<div class="item'+active+'" style="height: 100%;"><h2 class="tile-title" style="background: rgba(255, 255, 255, 0.18); text-shadow: 0 0 10px rgba(2, 2, 2, 0.7); font-weight: bold; font-size: 12px; color: rgba(255, 255, 255, 0.9);"><span class="icon" style="font-size: 15px; text-shadow: 0 0 10px rgba(0, 0, 0, 0.7); color: rgba(255, 255, 255, 0.61);">&#61940;</span> NEWS <span style="float: right; font-size: 10px;">'+newsSources[i].name+'</span></h2><div id="news-feed'+i+'" class="newsSourceContent" style="text-shadow: 0 0 10px rgba(2, 2, 2, 0.7); font-weight: bold; padding: 10px; height: 90%;"></div></div>'); */

	console.log("feed load",newsSources[i]);

    loadNewsFeed(newsSources[i].name,newsSources[i].url,$('#news-feed'+i));
/*(function(){
	if($('#news-feed'+i)[0]){
	    $('#news-feed'+i).FeedEk({
		FeedUrl: newsSources[i].url,
		MaxCount: 5,
		ShowDesc: false,
		ShowPubDate: false,
		DescCharacterLimit: 0
	    });
	}
    })();*/
    
    
}
	
    $(".item").removeClass("active");
    
    $('.item').last().addClass('active');
    $(".newsSourceContent").niceScroll();
    
    refreshCourasel();
}



function addNews (source,insertSource) {
    for (var i = 1; i <= source.sourcesTotal; i++)
        if (contains.call(enabledSources, source[i].name))
        {
            newsSources.push(source[i]);
            //console.log("Added Source: "+source[i].name);
        }
    if (insertSource)
        insertNews(newsSources);
}



   /* var json = (function () {
    var json = null;
        console.log("NEWS EXE");
    $.ajax({
        'async': false,
        'global': false,
        'url': "news.json",
        'dataType': "json",
        'success': function (data) {
            addNews(data);
        }
    });
    
})(); */

//win.on('loading', function() {
    var gui = require('nw.gui');
    //console.log("LOCATIONS",gui.App);

$(document).ready(function() {
    
    //https://github.com/sindresorhus/is-online
    

    
    
        
    setTimeout(function(){ loadInfoOnConnection() }, 2000); //Delay to allow the Hub to load first

    
    

    
    

    
    

    
    
    
});





function loadNewsSources (online) {

//Disabled because we don't use this anymore


    var json = (function () {
    var json = null;
    $.ajax({
        'async': false,
        'global': false,
        'url': "json/newsSource.json",
        'dataType': "json",
        'success': function (data) {
            //console.log("EHEHEHE: ",data);
            addNews(data,online);
        }
    });
    
})(); 
}

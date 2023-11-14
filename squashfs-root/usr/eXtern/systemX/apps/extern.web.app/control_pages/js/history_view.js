console.log("page ready");

var itemsPerPage = 50;
var browserHistory = [];
var allSearchResult = []; 
const months = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December'
]

function formatAMPM(date) {
  var hours = date.getHours();
  var minutes = date.getMinutes();
  var ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // the hour '0' should be '12'
  minutes = minutes < 10 ? '0'+minutes : minutes;
  var strTime = hours + ':' + minutes + ' ' + ampm;
  return strTime;
}

var lastDate;
var lastPageNo = 0;
function loadHistory(pageNo) {

    if (pageNo == 0) {
        lastDate == null;
        $("#historyList")[0].scrollTop = 0;
        $("#historyList").empty();
    }
        

    if ($("#searchInput").val() == "")
        var selectedBrowserHistory = browserHistory;
    else
        var selectedBrowserHistory = allSearchResult;
    
    lastPageNo = pageNo;
    var displayItemsFrom = (selectedBrowserHistory.length-1) - (pageNo*itemsPerPage);
    var displayItemsTo = displayItemsFrom - itemsPerPage;

    if (displayItemsTo < -1)
        displayItemsTo = -1;
    
    console.log("selectedBrowserHistory: ",selectedBrowserHistory[0]);
    for(var i = displayItemsFrom; i > displayItemsTo; i--) {
        var d2 = new Date(selectedBrowserHistory[i].time);
        if (lastDate == null) {
            lastDate = new Date(selectedBrowserHistory[i].time);
            lastDate.setHours(0,0,0,0);
            console.log("lastDate: ",lastDate)
            if (lastDate.getFullYear() == new Date().getFullYear()) {
                    var showYear = "";
                } else {
                    var showYear = new Date().getFullYear();
                }
            $("#historyList").append('<h3 class="block-title" style="margin-top: 20px;">'+lastDate.getDate()+' '+months[lastDate.getMonth()]+' '+showYear+'</h3>');
        } else {
            var d2x = new Date(selectedBrowserHistory[i].time);
            d2x.setHours(0,0,0,0);
            if(lastDate >= d2x && lastDate <= d2x) { //same day
                //
            } else {
                if (lastDate.getFullYear() == d2.getFullYear()) {
                    var showYear = "";
                } else {
                    var showYear = d2.getFullYear();
                }
                console.log("showYear: ",showYear);
                lastDate = d2x;
                $("#historyList").append('<h3 class="block-title" style="margin-top: 20px;">'+lastDate.getDate()+' '+months[lastDate.getMonth()]+' '+showYear+'</h3>');
                
            }
        }
        $("#historyList").append('<a href="'+selectedBrowserHistory[i].url+'" class="media p-l-5 d-block"><div class="pull-left"><img width="40" src="'+selectedBrowserHistory[i].favIcon+'" alt=""></div><div class="media-body"><small class="text-muted t-overflow"><b>'+formatAMPM(d2)+'</b> • '+selectedBrowserHistory[i].url+'</small><br/><p class="t-overflow" href="#" onclick="openHistoryItem(&quot;'+selectedBrowserHistory[i].url+'&quot;)">'+selectedBrowserHistory[i].title+'</p></div></a>');
	}
}

var messageSource, messageOrigin;
addEventListener('message', function(e) {
    if (!messageSource) {

        /*
         * Once we have a messageSource, we should not allow anybody to change
         * messageSource again
         */

        //console.log("got message: ",e.data);
        browserHistory = e.data;
        loadHistory(0);



        /* console.log("recieved message: ",e);

            messageSource = e.source;
            messageOrigin = e.origin;
            messageSource.postMessage("hello, host!", messageOrigin); */

        
    }
});

/*
jQuery(function($) {
    

    
});*/

setTimeout(function(){ $("#searchInput").focus(); }, 100);

$(window).focus(function() {
   console.log('welcome (back)');
   setTimeout(function(){ $("#searchInput").focus(); }, 1000);
});

console.log("init scroll: ",$("#searchInput")[0]);
    $('#historyList').on('scroll', function() {
        //$("#searchInput").focus();
        if($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight) {
            console.log('end reached');
            loadHistory(lastPageNo+1);
        }
    })


/*
$(window).on('scroll', function() { 
            if ($(window).scrollTop() >= $( 
              '#historyList').offset().top + $('#historyList'). 
                outerHeight() - window.innerHeight) { 
                
                alert('You reached the end of the DIV'); 
            } 
        }); 
*/


$("#searchInput").on('change keydown paste input', function(){
    console.log("input");
    if ($("#searchInput").val() == "") {
        loadHistory(0);
    } else {
        var searchResult = browserHistory.filter(function (el) {
            var searchRequest = $("#searchInput").val().toLowerCase(); //save processing power from .lowerCase every time lol. Yes not that much work but still
            if (el.url.indexOf(searchRequest) != -1)
                return true;
            else if (el.title.indexOf(searchRequest) != -1)
                return true;
            else return false;
        });

        allSearchResult = searchResult;
        loadHistory(0);
    }
    
		});
setTimeout(function(){
//console.log("main",$(".insertion-point-main")[0].innerHTML);

//console.log("main",$(".insertion-point-main")[0].shadowRoot);

$($(".insertion-point-main")[0].shadowRoot).append('<style type="text/css"> .tabbed-pane-header{ background-color: rgba(255,255,255,0.0) !important; } .tabbed-pane-header-tab.selected { background-color: #ffffff61; } .crumb.selected {     background-color: #ffffff61; } .soft-context-menu {     background-color: rgba(240, 240, 240, 0.28) !important; box-shadow: none !important; backdrop-filter: blur(10px) !important; } .tabbed-pane-tab-slider {     background-color: #000000ad; }  </style>');

$($(".insertion-point-sidebar")[0].shadowRoot).append('<style type="text/css"> .styles-sidebar-pane-toolbar-container {    background-color: rgba(255,255,255,0.0) !important;  } .tabbed-pane-header{ background-color: rgba(255,255,255,0.0) !important; } .tabbed-pane-header-tab.selected { background-color: #ffffff61; } .crumb.selected {     background-color: #ffffff61; } .soft-context-menu {     background-color: rgba(240, 240, 240, 0.28) !important; box-shadow: none !important; backdrop-filter: blur(10px) !important; } .tabbed-pane-tab-slider {     background-color: #000000ad; } .styles-sidebar-pane-toolbar-container {    background-color: rgba(255, 255, 255, 0.43) !important; } .styles-sidebar-pane-filter-box > input { background: #ffffffcc; border-radius: 10px; text-align: center; padding-left: 4px;  }  </style>');

//<script> tab-elements 

//console.log("main2",$(".insertion-point-sidebar")[0].shadowRoot);



}, 500);
//$("iframe").contents().find('*').css("background-color", "rgba(255,255,255,0.0)");

/*setInterval(function(){ 
	$('*').css("background-color", "rgba(255,255,255,0.0)"); 
	$("iframe").contents().find('*').css("background-color", "rgba(255,255,255,0.0)");
}, 3000);*/


//nmcli nm wifi off
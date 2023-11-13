var sudo = require('sudo-js');

if (localStorage.getItem('userDetails') === null)
    var userDetails = {username: require("os").userInfo().username, name: "eXten", avatar: "user-5"};
else
    var userDetails = JSON.parse(localStorage.getItem('userDetails'));

function loadUserDetails() {
	console.log("userDetails.avatar: ",userDetails.avatar);
	if (userDetails.avatar.indexOf("file://") == -1) {
    		$("#userAvatar").attr("src","../Shared/CoreIMG/profile-pics/"+userDetails.avatar+".png");
	} else {
   		$("#userAvatar").attr("src",userDetails.avatar);
	}
	
	executeNativeCommand(`awk -v user="$USER" -F":" 'user==$1{print $5}' /etc/passwd`,function (userFullName, error) {
		if (!error) {
			console.log("returned fullname: ",userFullName);
			userDetails.name = userFullName.replace(",,,","");
			$("#userNameLab").text(userDetails.name);
		}
	});

    
}

loadUserDetails();

if (enabledSources.length == 0)
    window.autoMonitors = true; //Enable during setup/welcome mode
else
    window.autoMonitors = false;

if (window.autoMonitors) {
     autoUpdateMonitors();
    /* autoMonitors = window.setInterval(function(){ 
    if (window.autoMonitors)
        autoUpdateMonitors();
    else
        window.clearInterval(autoMonitors);
}, 10000);*/
}

function changeUserPassword(oldPassword,newPassword,details,callback) {
	var userData = {
    		username: require("os").userInfo().username,
    		oldPassword: oldPassword,
    		newPassword: newPassword
	}

	$.post("http://127.0.0.1:8081/system/change_password",userData, function (data, status) {
		if (status == "success") {
	sudo.setPassword(newPassword);
 
	var command = ['chfn', '-f', details.name, details.username];
		sudo.exec(command, function(err, pid, result) {
    		console.log("change name result", result);
			//if (details.password != null) { //new password
				callback(data);
				localStorage.setItem('userDetails', JSON.stringify(details));
    				userDetails = JSON.parse(localStorage.getItem('userDetails'));
    				loadUserDetails();
			//}
	});
			
		} else {
			callback("An error occurred");
		}
    		//console.log("got back data: ",data);
    		//console.log("got back status: ",status);
	});
	//executeNativeCommand('/usr/eXtern/systemX/Shared/CoreMsc/pwd.sh '+oldPassword+' '+newPassword,callback);
}

function setUserDetails(details,password,callback) {
	console.log("setUserDetails",details);

	if (details.avatar.indexOf("/") == -1) {
		console.log("we are old set avatar");
		var avatar = "/usr/eXtern/systemX/Shared/CoreIMG/profile-pics/"+details.avatar+".png";
	ncp(avatar, "/usr/eXtern/CoreUsers/"+details.username+".png", function (err) {
		console.log("gets here");
  		if (err) {
    			console.error(err);
  		} else {
			console.log("successfully copied avatar");
	var avatarData = {
    		username: require("os").userInfo().username,
    		avatarLocation: "/usr/eXtern/CoreUsers/"+details.username+".png",
	}

	$.post("http://127.0.0.1:8081/system/change_avatar",avatarData, function (data, status) {
		if (status == "success") {
			console.log("success avatar change");
		} else {
			console.log("An error occurred changing avatar");
		}
    		//console.log("got back data: ",data);
    		//console.log("got back status: ",status);
	});
		}

	});
	} else {
		console.log("we are using this custom to set avatar");
		var avatar = details.avatar;
		details.avatar = "file://"+details.avatar;
	var avatarData = {
    		username: require("os").userInfo().username,
    		avatarLocation: avatar,
	}

	$.post("http://127.0.0.1:8081/system/change_avatar",avatarData, function (data, status) {
		if (status == "success") {
			console.log("success avatar change");
		} else {
			console.log("An error occurred changing avatar");
		}
    		//console.log("got back data: ",data);
    		//console.log("got back status: ",status);
	});
	}



	if (password != null) {
		changeUserPassword(password,details.password,details,callback);

	} else {
		callback(true);
		localStorage.setItem('userDetails', JSON.stringify(details));
    		userDetails = JSON.parse(localStorage.getItem('userDetails'));
    		loadUserDetails();
	}

	//sudo chfn -f "Anesu Chiodze" extern



	/*fs.copy("/usr/eXtern/iXAdjust/Shared/CoreIMG/profile-pics/"+details.avatar+".png", "/usr/eXtern/CoreUsers/"+details.username+".png", function (err) {
		console.log("gets here");
		if (err)
			console.log("error occured",err);
		else
			console.log("successfully copied avatar");
	});*/

    
}



function  locationPermissionRequest(event) {
  var messageBodyData = '<div class="row" style="text-align: center; margin-bottom: 10px;">'
													+'<div class="text-center" style="font-size: 50px; margin-bottom: 10px;"><i class="fas fa-map-marker-alt"></i></div>'
                                        +'<p><b>'+event.url+'</b></p> <p>would like to know your location</p>'
                                    +'</div>';

  var messageBody = {
    title: "Geolocation Request",
    data: messageBodyData
  }

  var inputElements = {
    buttons: []
  }

  inputElements.closeModal = {
    callback: processPermissionWindow,
    callbackData: {
      type: "cancel",
			event: event
    }
  }

	inputElements.buttons.push({
    text: "Deny",
    pullLeft: true,
    callback: processPermissionWindow,
    callbackData: {
      type: "deny",
			event: event
    }
		});

	  inputElements.buttons.push({
    text: "Alow",
    pullRight: true,
    callback: processPermissionWindow,
    callbackData: {
      type: "allow",
			event: event
    }
		});

  inputElements.buttons.centerise = true;

  App.openCustomModal(messageBody,inputElements);
	event.preventDefault();
}

function processPermissionWindow(instanceResponse) {
	if (instanceResponse.type == "allow") {
		instanceResponse.event.request.allow();
		allowedLocationPermissions.push(instanceResponse.event.url);
		localStorage.setItem('allowedLocationPermissions', JSON.stringify(allowedLocationPermissions));
	} else if (instanceResponse.type == "deny") {
		instanceResponse.event.request.deny();
		deniedLocationPermissions.push(instanceResponse.event.url);
		localStorage.setItem('deniedLocationPermissions', JSON.stringify(deniedLocationPermissions));
	}
	App.closeCustomModal();
}
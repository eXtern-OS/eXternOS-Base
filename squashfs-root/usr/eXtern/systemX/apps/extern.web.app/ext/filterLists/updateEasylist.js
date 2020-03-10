/* downloads the latest version of easyList and easyPrivacy, removes element hiding rules, and saves them to ext/filterLists/easylist+easyprivacy-noelementhiding.txt */

const https = require('https')
var fs = require('fs')

const filePath = '/usr/eXtern/systemX/apps/extern.web.app/ext/filterLists/easylist+easyprivacy-noelementhiding.txt'

const easylistOptions = {
  hostname: 'easylist.to',
  port: 443,
  path: '/easylist/easylist.txt',
  method: 'GET'
}

const easyprivacyOptions = {
  hostname: 'easylist.to',
  port: 443,
  path: '/easylist/easyprivacy.txt',
  method: 'GET'
}

function makeRequest (options, callback) {
  var request = https.request(options, function (response) {
    response.setEncoding('utf8')

    var data = ''
    response.on('data', function (chunk) {
      data += chunk
    })

    response.on('end', function () {
      callback(data)
    })
  })
  request.end()
}

console.log("got here makeRequest OUT");

/* get the filter lists */

function updateEasyPrivacyList() {

makeRequest(easylistOptions, function (easylist) {
  makeRequest(easyprivacyOptions, function (easyprivacy) {
    var data = easylist + easyprivacy

	console.log("got here makeRequest IN");

    //data = data.replace(/.*##.+\n/g, '')

    fs.writeFile(filePath, data, function(err) {
    if(err) {
        return console.log(err);
    }

    console.log("The file was saved!");
}); 





  });
});
}




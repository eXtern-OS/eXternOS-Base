

//Create function to get CPU information
function cpuAverage() {

  //Initialise sum of idle and time of cores and fetch CPU info
  var totalIdle = 0, totalTick = 0;
  var cpus = os.cpus();

  //Loop through CPU cores
  for(var i = 0, len = cpus.length; i < len; i++) {

    //Select CPU core
    var cpu = cpus[i];

    //Total up the time in the cores tick
    for(type in cpu.times) {
      totalTick += cpu.times[type];
   }     

    //Total up the idle time of the core
    totalIdle += cpu.times.idle;
  }

  //Return the average Idle and Tick times
  return {idle: totalIdle / cpus.length,  total: totalTick / cpus.length};
}


var si = require('systeminformation');
var cpuBrand = "";
// callback style
si.cpu(function(data) {
    console.log('CPU-Information:');
    console.log(data);
    var coreCount = "";
    if (data.cores == 4)
        coreCount = "Quad-Core";
    
    if (data.cores == 2)
        coreCount = "Dual-Core";
    
    cpuBrand = data.brand;
    $("#processorModel").text(coreCount+" "+data.manufacturer+" "+data.brand);
});



si.graphics(function(data) {
    console.log('SI graphics:');
    console.log(data);
    for (var i = 0; i < data.controllers.length; i++)
        $("#graphicsBody").append('<p style="margin:0;"><small class="muted">'+data.controllers[i].vendor+' '+data.controllers[i].model+'</small></p>');
});

si.cpuTemperature(function(data) {
    console.log('SI cpuTemperature:');
    console.log(data);
});




function convertBytes(input) {
    current_filesize = input.toFixed(2);
    var size_reduction_level = 0;
    while (current_filesize >= 1000)
      {
          current_filesize /=1000;
          size_reduction_level++;
      }
      
          /*Check if its a whole number or not*/
          if (current_filesize % 1 !== 0)
      current_filesize = current_filesize.toFixed(2);
          
      
      switch(size_reduction_level){
          case 0: current_filesize +=" B"; break;
          case 1: current_filesize +=" KB"; break;
          case 2: current_filesize +=" MB"; break;   
          case 3: current_filesize +=" GB"; break;
          case 4: current_filesize +=" TB"; break;
          case 5: current_filesize +=" PB"; break;
          case 6: current_filesize +=" EB"; break;
          case 7: current_filesize +=" ZB"; break;
      }
    
    return current_filesize;
}


    
    


setTimeout(function() {
 

console.log("Process jsHeapSizeLimit",convertBytes(window.performance.memory.jsHeapSizeLimit));
console.log("Process totalJSHeapSize",convertBytes(window.performance.memory.totalJSHeapSize));
console.log("usedJSHeapSize",convertBytes(window.performance.memory.usedJSHeapSize));
    
    }, 10000);


console.log("GUI",process);

si.mem(function(data) {
    console.log('SI mem:');
    console.log(data);
    var totSwap = convertBytes(data.swaptotal);
    var totMemory = convertBytes(data.total);
    
        $("#memoryBody").append('<p style="margin:0;"><small class="muted">'+totSwap+' total swap memory available.</small></p>');
        $("#memoryBody").append('<p style="margin:0;"><small class="muted">'+totMemory+' total memory available.</small></p>');
});

/*si.blockDevices(function(data) {
    console.log('SI diskLayout:');
    console.log(data);
});*/


si.cpu(function(data) {
    console.log('CURRENT SPEED:');
    console.log(data);
});

si.memLayout(function(data) {
    console.log('memLayout:');
    console.log(data);
});



    


//https://www.npmjs.com/package/systeminformation

si.currentLoad(function(data) {
    console.log('CURRENT Load:');
    console.log(data);
    si.cpu(function(data2) {
    
    var cpuBrand = data2.brand;
        
        $("#corexA").remove();

    for (var i = 0; i < data.cpus.length; i++) {
        $("#processorCoresList").append('<div class="progress progress-vertical bottom" style="height: 150px; width: 100px;"><div id="core'+i+'A" class="progress-bar progress-bar-cores" role="progressbar" aria-valuenow="'+data.cpus[i].load+'" aria-valuemin="0" aria-valuemax="100" style="height: '+data.cpus[i].load+'%">'+cpuBrand+': Core '+(i+1)+'</div></div>');
    }
        if (data.cpus.length == 1)
            $("#processorCoresList").addClass("oneCoreBoxResize");
        
        if (data.cpus.length == 2)
            $("#processorCoresList").addClass("twoCoreBoxResize");
        
        if (data.cpus.length == 3)
            $("#processorCoresList").addClass("threeCoreBoxResize");
        
        if (data.cpus.length == 4)
            $("#processorCoresList").addClass("fourCoreBoxResize");
        });
});

//$('.progress-bar').css('width', valeur+'%').attr('aria-valuenow', valeur);

setTimeout(function() {
si.cpuCurrentspeed(function(data) {
    console.log('CURRENT SPEED2:');
    console.log(data);
});    
    
}, 1000);

//https://www.npmjs.com/package/os-utils

//Using a seperate function because it seems to be using a bit of processing power
//Which is not good since this is used in the system perfomance tab
function updateDiskSpace() {
    njds.drives(
        
        function (err, drives) {
            njds.drivesDetail(
                drives,
                function (err, data) {
                    for(var i = 0; i<data.length; i++)
                    {
                        var set_active = false;
                        if (data[i].mountpoint == "/") { 
                            $('#hddUsage').data('easyPieChart').update(data[i].usedPer);
                        }
                    }

                }
            );
        }
    )
    
    setTimeout(function() {
        if (currentMenuMode == 'sysMonitor')
            updateDiskSpace(); //Only check if we are still in perfomance analysis menu
}, 20000); //Check after every 20 seconds
}


function updateSysMonitor() {

    //CPU
    
    si.currentLoad(function(data){
        $('#cpuUsage').data('easyPieChart').update(data.currentload);
        $('#cpuAvg').text(data.avgload);
        
        for (var i = 0; i < data.cpus.length; i++) {
            $('#core'+i+'A').css('height', data.cpus[i].load+'%').attr('aria-valuenow', data.cpus[i].load);

        }
});
    
    //Cpu Temperature
    
    si.cpuTemperature(function(data) {
        //console.log('SI cpuTemperature:');
        //console.log(data);
        $("#cpuTemp").text(data.main);
    });
    
    //Network
    
    si.networkInterfaceDefault(function(data) {
    //console.log('SI networkInterfaceDefault');
    //console.log(data);
    
    si.networkStats(data,function(datax) {
    //console.log('SI networkStats:',datax);
        $('#dlsCounter').text(convertBytes(datax.rx));
        $('#UpsCounter').text(convertBytes(datax.tx));
    //console.log('SI networkStats Recieved:',convertBytes(datax.rx));
    //console.log('SI networkStats Transfered:',convertBytes(datax.tx));
        
});
        });
    
    //HDD Space
    
    /*njds.drives(
        
        function (err, drives) {
            njds.drivesDetail(
                drives,
                function (err, data) {
                    for(var i = 0; i<data.length; i++)
                    {
                        var set_active = false;
                        if (data[i].mountpoint == "/") { 
                            $('#hddUsage').data('easyPieChart').update(data[i].usedPer);
                        }
                    }

                }
            );
        }
    )*/
    
    //Memory using an older method here
    var usedRam = os.totalmem() - os.freemem();
    var memPercentage = (usedRam/os.totalmem())*100;
    $('#ramUsage').data('easyPieChart').update(memPercentage);
   
    //Swap memory
    si.mem(function(data) {
        var swapPercentage = (data.swapused/data.swaptotal)*100;
        $('#swapUsage').data('easyPieChart').update(swapPercentage);
});

    
    
    setTimeout(function() {
        if (currentMenuMode == 'sysMonitor')
            updateSysMonitor(); //Only check if we are still in perfomance analysis menu
}, 1000);
}



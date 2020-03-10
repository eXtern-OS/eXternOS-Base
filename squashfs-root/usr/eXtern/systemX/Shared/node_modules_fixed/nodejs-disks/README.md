nodejs-disks
============

[![NPM](https://nodei.co/npm/nodejs-disks.png?downloads=true&stars=true)](https://nodei.co/npm/nodejs-disks/)

Gets current disk information from Server hosting nodejs application.

I have added the drive mount point name as well as calculating the percentage of used space and percentage of free space. Tested on OSX and ubuntu.
Windows support coming soon.

Usage

    var njds = require('nodejs-disks');
        njds.drives(
            function (err, drives) {
                njds.drivesDetail(
                    drives,
                    function (err, data) {
                        for(var i = 0; i<data.length; i++)
                        {
                            /* Get drive mount point */
                            console.log(data[i].mountpoint);

                            /* Get drive total space */
                            console.log(data[i].total);

                            /* Get drive used space */
                            console.log(data[i].used);

                            /* Get drive available space */
                            console.log(data[i].available);

                            /* Get drive name */
                            console.log(data[i].drive);

                            /* Get drive used percentage */
                            console.log(data[i].usedPer);

                            /* Get drive free percentage */
                            console.log(data[i].freePer);
                        }



                    }
                );
            }
        )


LICENSE

nodejs-disks - see License.md file


This was derived from the original creator project, node-diskfree. Source for node-diskfree is available at https://bitbucket.org/pinchprojectbackend/node-diskfree/ license for this project is shown in OriginalLicense.md


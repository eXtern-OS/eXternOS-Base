'''apport package hook for libmtp

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.

(c) 2009 Sense Hofstede <sense@qense.nl>
'''

import apport.hookutils

def add_info(report, ui):

    ui.information('Please make sure the affected device is connected and on before continuing.')

    apport.hookutils.attach_related_packages(report, [
        "udev",
        ])

    # Try using the mtp-detect command to obtain more information
    if apport.hookutils.command_available("mtp-detect"):
        report['MTPDetect'] = apport.hookutils.command_output("mtp-detect")
    else:
        ui.information("Please install the package 'mtp-tools' so we can gather "\
                        "more detailed debugging information. Afterwards, rerun " \
                        "the command 'ubuntu-bug libmtp8' or add more information "\
                        "to an existing bug report by running the command "\
                        "'apport-collect -p libmtp9 '<bugnumber>', replacing "\
                        "<bugnumber> with the number of your bug report.")

    # Obtain information about changes to udev configuration files
    apport.hookutils.attach_conffiles(report, "udev")
    apport.hookutils.attach_hardware(report)

    # Get all connected USB devices
    report['USBDevices'] = apport.hookutils.usb_devices()

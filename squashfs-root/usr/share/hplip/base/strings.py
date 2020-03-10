# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Author: Don Welch, Naga Samrat Chowdary Narla, Yashwant Kumar Sahu, Sanjay Kumar
#

# string_table := { 'string_id' : 'short', 'long' ), ... }

# string_id's for error codes are the string form of the error code
# Strings that need localization use (self.__tr'string' ) form.
# Strings that refer to other strings, use '%reference%' form.
# Blank strings use '' form.

class StringTable:
    def __init__(self):

        self.string_table = {
            '0' : (self.__tr('Unknown'), ''),
            'unknown' : (self.__tr('Unknown'), ''),
            'try_again' : ('', self.__tr('Please correct the problem and try again')),
            'press_continue' : ('',self.__tr('Please correct the problem and press continue on the printer')),
            'unable_validate' : (self.__tr('Unable to validate'), ''),
            '101' : (self.__tr('<STR1> file not found'), ''),
            '102' : (self.__tr('<STR1> directory not found'), ''),
            '103' : (self.__tr('Unable to connect to network. Please check your network connection and try again'), ''),
            '104' : (self.__tr('<STR1> file does not match its checksum. File may have been corrupted or altered'), ''),
            '105' : (self.__tr('GPG command not found'), ''),
            '106' : (self.__tr('Unable to recieve key from keyserver'), ''),
            '107' : (self.__tr('Failed to download <STR1>'), ''),
            '108' : (self.__tr('Digital signature verification failed for the file <STR1>. File may have been corrupted or altered'), ''),
            '109' : (self.__tr('Incorrect password'), ''),
            '110' : (self.__tr('Unknown error'), ''),
            '111' : (self.__tr('No device found having smart install enabled'), ''),
            '112' : (self.__tr('Failed to disable smart install'), ''),

            '500' : (self.__tr('Started a print job'), ''),
            '501' : (self.__tr('Print job has completed'), ''),
            '502' : (self.__tr("Print job failed - required plug-in not found"), self.__tr("Please run hp-plugin to install the required plug-in")),
            '503' : (self.__tr('should not be run as root/superuser'), ''),
            '600' : (self.__tr('Started a fax job'), ''),
            '601' : (self.__tr('Fax job is ready for send'), ''),
            '700' : (self.__tr('Printer queue stopped'), ''),
            '701' : (self.__tr('Printer queue started'), ''),
            '702' : (self.__tr('Printer is rejecting jobs'), ''),
            '703' : (self.__tr('Printer is accepting jobs'), ''),
            '704' : (self.__tr('Printer set as default'), ''),
            '800' : (self.__tr('Fax queue stopped'), ''),
            '801' : (self.__tr('Fax queue started'), ''),
            '802' : (self.__tr('Fax is rejecting jobs'), ''),
            '803' : (self.__tr('Fax is accepting jobs'), ''),
            '804' : (self.__tr('Fax set as default'), ''),
            '805' : (self.__tr("Fax job failed - required plug-in not found"), '%502%'),
            '1000' : (self.__tr('Idle'), ''),
            '1001' : (self.__tr('Busy'), ''),
            '1002' : (self.__tr('Print job is continuing'), ''),
            '1003' : (self.__tr('Turning off'), ''),
            '1004' : (self.__tr('Report printing'), ''),
            '1005' : (self.__tr('Canceling'), ''),
            '1006' : ('%5002%', '%try_again%'),
            '1007' : (self.__tr('Waiting for ink to dry'), ''),
            '1008' : (self.__tr('Pen change'), ''),
            '1009' : (self.__tr('The printer is out of paper'), self.__tr('Please load more paper and follow the instructions on the front panel (if any) to continue printing')),
            '1010' : (self.__tr('Banner eject needed'), ''),
            '1011' : (self.__tr('Banner mismatch'), '%try_again%'),
            '1012' : (self.__tr('Photo mismatch'), '%try_again%'),
            '1013' : (self.__tr('Duplex mismatch'), '%try_again'),
            '1014' : (self.__tr('Paper or cartridge carriage jammed'), self.__tr('Please clear the jam and press continue on the printer')),
            '1015' : ('%1014%', '%1014%'),
            '1016' : ('%1014%', '%1014%'),
            '1017' : (self.__tr('There is a problem with a print cartridge'), '%press_continue%'),
            '1018' : ('%unknown_error%', '%try_again%'),
            '1019' : (self.__tr('Powering down'), ''),
            '1020' : (self.__tr('Front panel test'), ''),
            '1021' : (self.__tr('Clean out tray missing'), '%try_again%'),
            '1022' : (self.__tr('Output bin full'), '%try_again%'),
            '1023' : (self.__tr('Media size mismatch'), '%try_again%'),
            '1024' : (self.__tr('Duplexer is jammed'), '%1014%'),
            '1025' : ('%1014%', '%1014%'),
            '1026' : (self.__tr('An ink cartridge is out of ink'), '%try_again%'),
            '1027' : (self.__tr('Internal device error'), '%try_again%'),
            '1028' : ('%1014%', '%1014%'),
            '1029' : (self.__tr('Second tray missing'), '%try_again%'),
            '1030' : (self.__tr('Duplexer missing'), '%try_again%'),
            '1031' : (self.__tr('Rear tray missing'), '%try_again%'),
            '1032' : (self.__tr('Cartridge not latched'), '%try_again%'),
            '1033' : (self.__tr('Battery very low'), '%try_again%'),
            '1034' : ('%1017%', '%try_again%'),
            '1035' : (self.__tr('Output tray closed'), '%try_again%'),
            '1036' : (self.__tr('Manual feed blocked'), '%1014%'),
            '1037' : (self.__tr('Rear feed blocked'), '%1014%'),
            '1038' : (self.__tr('Second tray out of paper'), '%1009%'),
            '1039' : (self.__tr('Input tray locked'), '%try_again%'),
            '1040' : (self.__tr('Non-HP ink'), '%try_again%'),
            '1041' : (self.__tr('Pen calibration needs resume'), '%press_continue%'),
            '1042' : (self.__tr('Media type mismatch'), '%try_again%'),
            '1043' : (self.__tr('Custom media mismatch'), '%try_again%'),
            '1044' : (self.__tr('Pen cleaning in progress'), ''),
            '1045' : (self.__tr('Pen checking in progress'), ''),
            '1046' : (self.__tr('In power save mode'), ''),
            '1047' : (self.__tr('Incorrect cartridge'), ''),
            '1048' : (self.__tr('Missing cartridge'), ''),
            '1049' : (self.__tr('Missing Printhead(s)'), ''),

            #Alert messages for Pentane products RQ 8888
            '1050' : (self.__tr('ADF can not load original, please try reloading'), ''),
            '1051' : (self.__tr('Paper too short to auto duplex'), ''),
            '1052' : (self.__tr('Tray 2/3 missing or door open'), ''),
            '1053' : (self.__tr('Ink too low to complete startup process'), ''),
            '1054' : (self.__tr('Very low on ink'), ''),
            '1055' : (self.__tr('Service ink container in duplex module in filled almost to its capacity'), self.__tr('Consider replacing duplex module from HP')),
            '1056' : (self.__tr('Service ink container in duplex module in filled very close to its capacity'), self.__tr('Consider replacing duplex module from HP')),
            '1057' : (self.__tr('Service ink container in duplex module is full'), self.__tr('Consider replacing duplex module from HP')),
            '1058' : (self.__tr('Duplex module missing'), ''),
            '1059' : (self.__tr('Printhead jam'), ''),
            '1060' : (self.__tr('Remove paper and other material from output flap area'), ''),
            '1061' : (self.__tr('To Maintain print quality, remove and re-install duplex module'), ''),
            '1062' : (self.__tr('Manually feed correct paper in MP tray'), ''),
            '1063' : (self.__tr('Printhead(s) Failed'), ''),
            '1064' : (self.__tr('Incompatible Printhead(s)'), ''),
            '1065' : (self.__tr('Unknown status'), ''),
            '1066' : (self.__tr('Unable to process jobs. Please resolve printer error and then try again'), ''),
            '1067' : (self.__tr('Printer paused'), ''),
            '1068' : (self.__tr('Input tray is missing'), ''),


            '1501' : (self.__tr('Black cartridge is low on ink'), ''),
            '1502' : (self.__tr('Tri-color cartridge is low on ink'), ''),
            '1503' : (self.__tr('Photo cartridge is low on ink'), ''),
            '1504' : (self.__tr('Cyan cartridge is low on ink'), ''),
            '1505' : (self.__tr('Magenta cartridge is low on ink'), ''),
            '1506' : (self.__tr('Yellow cartridge is low on ink'), ''),
            '1507' : (self.__tr('Photo cyan cartridge is low on ink'), ''),
            '1508' : (self.__tr('Photo magenta cartridge is low on ink'), ''),
            '1509' : (self.__tr('Photo yellow cartridge is low on ink'), ''),
            '1510' : (self.__tr('Photo gray cartridge is low on ink'), ''),
            '1511' : (self.__tr('Photo blue cartridge is low on ink'), ''),
            '1601' : (self.__tr('Black cartridge is low on toner'), ''),
            '1604' : (self.__tr('Cyan cartridge is low on toner'), ''),
            '1605' : (self.__tr('Magenta cartridge is low on toner'), ''),
            '1606' : (self.__tr('Yellow cartridge is low on toner'), ''),
            '1800' : (self.__tr('Warming up'), ''),
            '1801' : (self.__tr('Low paper'), ''),
            '1802' : (self.__tr('Door open'), '%try_again%'),
            '1803' : (self.__tr('Offline'), ''),
            '1804' : (self.__tr('Low toner'), ''),
            '1805' : (self.__tr('No toner'), '%try_again%'),
            '1806' : (self.__tr('Service request'), '%try_again%'),
            '1807' : (self.__tr('Fuser error'), '%try_again%'),
            '1808' : (self.__tr('Empty toner'), ''),
            '1809' : (self.__tr('Missing/Empty or incompatible toner'), ''),
            '1900' : (self.__tr('Unsupported printer model'), ''),
            '2000' : (self.__tr('Scan job started'), ''),
            '2001' : (self.__tr('Scan job completed'), ''),
            '2002' : (self.__tr('Scan job failed'), '%try_again%'),
            '2003' : (self.__tr("Scan job failed - Required plug-in not found"), '%502%'),
            '2004' : (self.__tr('Scanner automatic document feeder is loaded'), ''),
            '2005' : (self.__tr('Scan to a destination is not specified'), ''),
            '2006' : (self.__tr('Scanner is waiting for PC'), ''),
            '2007' : (self.__tr('Scanner automatic document feeder jam'), ''),
            '2008' : (self.__tr('Scanner automatic document feeder door opened'), ''),
            '2009' : (self.__tr('Scan job cancelled'), ''),
            '2010' : (self.__tr('Check scan image size requirements'), ''),
            '2011' : (self.__tr('Scanner ADF empty'), ''),
            '2012' : (self.__tr('Scanner ADF mispick'), ''),
            '2013' : (self.__tr('Scanner busy'), ''),
            '3000' : (self.__tr('Fax job started'), ''),
            '3001' : (self.__tr('Fax job complete'), ''),
            '3002' : (self.__tr('Fax job failed'), '%try_again%'),
            '3003' : (self.__tr('Fax job canceled'), ''),
            '3004' : (self.__tr('Fax send job continuing'), ''),
            '3005' : (self.__tr('Fax receive job continuing'), ''),
            '3006' : (self.__tr('Fax dialing'), ''),
            '3007' : (self.__tr('Fax connecting'), ''),
            '3008' : (self.__tr('Fax send error'), ''),
            '3009' : (self.__tr('Fax error storage full'), ''),
            '3010' : (self.__tr('Fax receive error'), ''),
            '3011' : (self.__tr('Fax blocking'), ''),
            '4000' : (self.__tr('Copy job started'), ''),
            '4001' : (self.__tr('Copy job complete'), ''),
            '4002' : (self.__tr('Copy job failed'), '%try_again%'),
            '4003' : (self.__tr('Copy job canceled'), ''),
            '5002' : (self.__tr('Device is busy, powered down, or unplugged'), '%5012%'),
            '5004' : (self.__tr('Invalid device URI'), '%5012%'),
            '5012' : (self.__tr('Device communication error'), '%try_again%'),
            '5021' : (self.__tr('Device is busy'), ''),
            '5026' : (self.__tr("Device status not available"), ''),
            '5031' : ('%5021%', ''),
            '5034' : (self.__tr('Device does not support requested operation'), '%try_again%'),
            '6000' : (self.__tr('Photocard unload started'), ''),
            '6001' : (self.__tr('Photocard unload ended'), ''),
            '6002' : (self.__tr('Photocard unload failed'), self.__tr('Make sure photocard is inserted properly and try again')),
            '6003' : (self.__tr('Unable to mount photocard on device'), '%6002%'),
            '6004' : (self.__tr('Photocard unloaded successfully'), ''),
            '9000' : (self.__tr('Device Added'), ''),
            '9041' : (self.__tr('Device Removed'), ''),
            'unknown_error' : (self.__tr('Unknown error'), ''),
            'print' : (self.__tr('Print'), ''),
            'scan' : (self.__tr('Scan'), ''),
            'send_fax' : (self.__tr('Send fax'), ''),
            'make_copies' : (self.__tr('Make copies'), ''),
            'access_photo_cards' : (self.__tr('Access photo cards'), ''),
            'agent_invalid_invalid' : (self.__tr('Invalid/missing'), ''),
            'agent_invalid_supply' : (self.__tr('Invalid/missing ink cartridge'), ''),
            'agent_invalid_cartridge':(self.__tr('Invalid/missing cartridge'), ''),
            'agent_invalid_head' : (self.__tr('Invalid/missing print head'), ''),
            'agent_unknown_unknown' : ('%unknown%', ''),
            'agent_unspecified_battery' : ('Battery', ''),
            'agent_black_head' : (self.__tr('Black print head'), ''),
            'agent_black_supply' : (self.__tr('Black ink cartridge'), ''),
            'agent_black_cartridge' : (self.__tr('Black cartridge'), ''),
            'agent_cmy_head' : (self.__tr('Tri-color print head'), ''),
            'agent_cmy_supply' : (self.__tr('Tri-color ink cartridge'), ''),
            'agent_cmy_cartridge' : (self.__tr('Tri-color cartridge'), ''),
            'agent_kcm_head' : (self.__tr('Photo print head'), ''),
            'agent_kcm_supply' : (self.__tr('Photo ink cartridge'), ''),
            'agent_kcm_cartridge' : (self.__tr('Photo cartridge'), ''),
            'agent_cyan_head' : (self.__tr('Cyan print head'), ''),
            'agent_cyan_supply' : (self.__tr('Cyan ink cartridge'), ''),
            'agent_cyan_cartridge' : (self.__tr('Cyan cartridge'), ''),
            'agent_light_cyan_head' : (self.__tr('Light Cyan print head'), ''),
            'agent_light_cyan_supply' : (self.__tr('Light Cyan ink cartridge'), ''),
            'agent_light_cyan_cartridge' : (self.__tr('Light Cyan cartridge'), ''),
            'agent_magenta_head' : (self.__tr('Magenta print head'), ''),
            'agent_magenta_supply' : (self.__tr('Magenta ink cartridge'), ''),
            'agent_magenta_cartridge':(self.__tr('Magenta cartridge'), ''),
            'agent_yellow_head' : (self.__tr('Yellow print head'), ''),
            'agent_yellow_supply' : (self.__tr('Yellow ink cartridge'), ''),
            'agent_yellow_cartridge': (self.__tr('Yellow cartridge'), ''),
            'agent_red_head' : (self.__tr('Red print head'), ''),
            'agent_red_supply' : (self.__tr('Red ink cartridge'), ''),
            'agent_red_cartridge': (self.__tr('Red cartridge'), ''),
            'agent_photo_black_head' : (self.__tr('Photo Black print head'), ''),
            'agent_photo_black_supply' : (self.__tr('Photo Black ink cartridge'), ''),
            'agent_photo_black_cartridge': (self.__tr('Photo Black cartridge'), ''),
            'agent_matte_black_head' : (self.__tr('Matte Black print head'), ''),
            'agent_matte_black_supply' : (self.__tr('Matte Black ink cartridge'), ''),
            'agent_matte_black_cartridge': (self.__tr('Matte Black cartridge'), ''),
            'agent_gray_head' : (self.__tr('Gray print head'), ''),
            'agent_gray_supply' : (self.__tr('Gray ink cartridge'), ''),
            'agent_gray_cartridge': (self.__tr('Gray cartridge'), ''),
            'agent_light_gray_head' : (self.__tr('Light Gray print head'), ''),
            'agent_light_gray_supply' : (self.__tr('Light Gray ink cartridge'), ''),
            'agent_light_gray_cartridge': (self.__tr('Light Gray cartridge'), ''),
            'agent_dark_gray_head' : (self.__tr('Dark Gray print head'), ''),
            'agent_dark_gray_supply' : (self.__tr('Dark Gray ink cartridge'), ''),
            'agent_dark_gray_cartridge': (self.__tr('Dark Gray cartridge'), ''),
            'agent_photo_cyan_head' : (self.__tr('Photo cyan print head'), ''),
            'agent_photo_cyan_supply' : (self.__tr('Photo cyan ink cartridge'), ''),
            'agent_photo_cyan_cartridge' : (self.__tr('Photo cyan cartridge'), ''),
            'agent_photo_magenta_head' : (self.__tr('Photo magenta print head'), ''),
            'agent_photo_magenta_supply' : (self.__tr('Photo magenta ink cartridge'), ''),
            'agent_photo_magenta_cartridge':(self.__tr('Photo magenta cartridge'), ''),
            'agent_photo_yellow_head' : (self.__tr('Photo yellow print head'), ''),
            'agent_photo_yellow_supply' : (self.__tr('Photo yellow ink cartridge'), ''),
            'agent_photo_yellow_cartridge': (self.__tr('Photo yellow cartridge'), ''),
            'agent_photo_gray_head' : (self.__tr('Photo gray print head'), ''),
            'agent_photo_gray_supply' : (self.__tr('Photo gray ink cartridge'), ''),
            'agent_photo_gray_cartridge' : (self.__tr('Photo gray cartridge'), ''),
            'agent_photo_blue_head' : (self.__tr('Photo blue print head'), ''),
            'agent_photo_blue_supply' : (self.__tr('Photo blue ink cartridge'), ''),
            'agent_photo_blue_cartridge' : (self.__tr('Photo blue cartridge'), ''),
            'agent_kcmy_cm_head' : (self.__tr('Print head'), ''),
            'agent_photo_cyan_and_photo_magenta_head' : (self.__tr('Photo magenta and photo cyan print head'), ''),
            'agent_yellow_and_magenta_head' : (self.__tr('Magenta and yellow print head'), '' ),
            'agent_cyan_and_black_head' : (self.__tr('Black and cyan print head'), '' ),
            'agent_light_gray_and_photo_black_head' : (self.__tr('Light gray and photo black print head'), '' ),
            'agent_light_gray_supply' : (self.__tr('Light gray ink cartridge'), '' ),
            'agent_medium_gray_supply' : (self.__tr('Medium gray ink cartridge'), '' ),
            'agent_photo_gray_supply' : (self.__tr('Photo black ink cartridge'), '' ),
            'agent_cyan_and_magenta_head' : (self.__tr('Cyan and magenta print head'), ''),
            'agent_black_and_yellow_head' : (self.__tr('Black and yellow print head'), ''),
            'agent_black_toner' : (self.__tr('Black toner cartridge'), ''),
            'agent_cyan_toner' : (self.__tr('Cyan toner cartridge'), ''),
            'agent_magenta_toner' : (self.__tr('Magenta toner cartridge'), ''),
            'agent_yellow_toner' : (self.__tr('Yellow toner cartridge'), ''),
            'agent_unspecified_maint_kit' : (self.__tr('Maintenance kit (fuser)'), ''),
            'agent_unspecified_adf_kit' : (self.__tr('Document feeder (ADF) kit'), ''),
            'agent_unspecified_drum_kit' : (self.__tr('Drum maintenance kit'), ''),
            'agent_unspecified_transfer_kit' : (self.__tr('Image transfer kit'), ''),
            'agent_health_unknown' : ('Unknown', ''),
            'agent_health_ok' : (self.__tr('Good/OK'), ''),
            'agent_health_fair_moderate' : (self.__tr('Fair/Moderate'), ''),
            'agent_health_misinstalled': (self.__tr('Not installed'), ''),
            'agent_health_incorrect' : (self.__tr('Incorrect'), ''),
            'agent_health_failed' : (self.__tr('Failed'),''),
            'agent_health_overtemp' : (self.__tr('Overheated'),''),
            'agent_health_discharging' : (self.__tr('Discharging'), ''),
            'agent_health_charging' : (self.__tr('Charging'), ''),
            'agent_level_unknown' : ('%unknown%', ''),
            'agent_level_low' : (self.__tr('Low'), ''),
            'agent_level_out' : (self.__tr('Very low'),''),
            'vsa_000' : (self.__tr("The Ethernet cable is plugged in which will prevent you from connecting to a wireless network. To connect wirelessly, remove the cable and try again. (VSA000)"), ''),
            'vsa_001' : (self.__tr("A wireless network was found that matches what you have configured. However, the Ethernet cable is plugged in which will prevent you from connecting to it. To connect wirelessly, remove the cable and try again. (VSA001)"), ''),
            'vsa_002' : (self.__tr("The wireless adaptor on your printer is not enabled. You cannot connect to a wireless network until this is turned on. (VSA002)"), ''),
            'vsa_003' : (self.__tr("Your Access Point (AP) is not broadcasting its SSID. This feature is probably disabled. (VSA003)"), ''),
            'vsa_004' : (self.__tr("The wireless adaptor on your printer is not functioning properly. There may be a problem with the hardware. (VSA004)"), ''),
            'vsa_100' : (self.__tr("Check if MAC address filtering or IP address filtering is being used by your Access Point. If it is, then refer to your troubleshooting documentation that came with your HP device and make any necessary corrections. (VSA100)"), ''),
            'vsa_101' : (self.__tr("The access point you are trying to connect to has settings that are NOT consistent with the ones in the printer. (VSA101)"), ''),
            'vsa_102' : (self.__tr("Unknown (VSA102)"), ''),
            'vsa_200' : (self.__tr("Your printer is configured to connect to an Access Point (AP) with the manufacturer's default (SSID) name. You should consider changing the AP name to avoid connecting to the wrong access point. (VSA200)"), ''),
            'vsa_201' : (self.__tr("The network that you are trying to connect to cannot be found. Please make sure your access point is powered on. (VSA201)"), ''),
            'vsa_202' : (self.__tr("You are trying to connect to an ad hoc network, and no other devices with that SSID can be found. (VSA202)"), ''),
            'vsa_203' : (self.__tr("Check that your HP device (SSID) name matches your Access Point (SSID) name exactly (SSID names are case sensitive). (VSA203)"), ''),
            'vsa_204' : (self.__tr("The SSID that you have configured is empty. In order to connect wirelessly you must enter a valid, non-blank SSID. (VSA204)"), ''),
            'vsa_300' : (self.__tr("The printer is configured to connect to an ad hoc wireless network in 802.11g mode. This can cause compatibility issues with older 802.11b devices. (VSA300)"), ''),
            'vsa_301' : (self.__tr("The printer is configured so that it shows that it is connected to an ad hoc network even if no other devices are present. This setting should only be used to connect to non-compliant 802.11 devices. WiFi certified devices won't have this issue. (VSA301)"), ''),
            'vsa_302' : (self.__tr("The printer is configured to show that it isn't connected to an ad hoc network when no other devices are present. This setting should only be used to connect to compliant/WiFi certified 802.11 devices. (VSA302)"), ''),
            'vsa_303' : (self.__tr("The printer is configured to connect to the wireless network in 802.11b mode. This setting should only be used to connect to a non-compliant 802.11 device. WiFi certified devices don't have this issue. (VSA303)"), ''),
            'vsa_400' : (self.__tr("The signal strength for your wireless network too low (below -85dBm) which may result in your network becoming unstable. (VSA400)"), ''),
            'vsa_401' : (self.__tr("You are not currently associated with a wireless network. However, a network that is consistent with your settings has been detected, but its signal strength is below -85dBm which could be preventing association. (VSA401)"), ''),
            'vsa_500' : (self.__tr("There were multiple access points (or wireless repeaters) with your configured found in the area. The printer will connect to the one with the strongest signal. If you have setup a network with multiple APs, this is normal and this message is for information purposes only. (VSA500)"), ''),
            'vsa_501' : (self.__tr("There were multiple access points (or wireless repeaters) with your configured found in the area. Some of these networks have settings that are inconsistent with your printer's wireless settings. (VSA501)"), '' ),
            'vsa_600' : (self.__tr("Your wireless network requires a WEP key. The key you have provided does not match what is expected. Click <i>&lt; Back</i> to re-enter the key. (VSA600)"), ''),
            'vsa_601' : (self.__tr("Your wireless network requires a WEP key. However, no data has been received to decrypt. Please try again in a few seconds. (VSA601)"), ''),
            'vsa_602' : (self.__tr("The WEP key index on your HP device does not match that of your Access Point. Refer to the documentation that came with your HP device regarding changing the WEP key index. (VSA602)"), ''),
            'vsa_603' : (self.__tr("Your Access Point (AP) requires a WPA pass phrase. The pass phrase you entered for your HP device does not match exactly your AP pass phrase. Click <i>&lt; Back</i> to re-enter the pass phase. (VSA603)"), ''),
            'vsa_604' : (self.__tr("The HP printer is configured to connect to a WEP wireless network and the authentication method has been changed from the default setting. (VSA604)"), ''),
            'vsa_605' : (self.__tr("The HP printer is configured to connect using WPA-PSK authentication. However, the encryption method you have chosen is not the default. (VSA605)"), ''),
            'vsa_606' : (self.__tr("The HP printer is configured to connect using WPA-PSK authentication. However, the authentication method you have chosen is not the default. (VSA606)"), ''),
        }

    def __tr(self,s,c = None):
        return s

import re
from . import logger
log = logger.Logger('', logger.Logger.LOG_LEVEL_INFO, logger.Logger.LOG_TO_CONSOLE)

inter_pat = re.compile(r"""%(.*)%""", re.IGNORECASE)
st = StringTable()
strings_init = False


def initStrings():
    global strings_init, st
    strings_init = True
    cycles = 0

    while True:
        found = False

        for s in st.string_table:
            short_string, long_string = st.string_table[s]
            short_replace, long_replace = short_string, long_string

            try:
                short_match = inter_pat.match(short_string).group(1)
            except (AttributeError, TypeError):
                short_match = None

            if short_match is not None:
                found = True

                try:
                    short_replace, dummy = st.string_table[short_match]
                except KeyError:
                    log.error("String interpolation error: %s" % short_match)

            try:
                long_match = inter_pat.match(long_string).group(1)
            except (AttributeError, TypeError):
                long_match = None

            if long_match is not None:
                found = True

                try:
                    dummy, long_replace = st.string_table[long_match]
                except KeyError:
                    log.error("String interpolation error: %s" % long_match)

            if found:
                st.string_table[s] = (short_replace, long_replace)

        if not found:
            break
        else:
            cycles +=1
            if cycles > 1000:
                break


def queryString(string_id, typ=0, str1=None, str2=None):
    if not strings_init:
        initStrings()

    s = st.string_table.get(str(string_id), ('', ''))[typ]
   
    if str1 is not None:
         s = s.replace("<STR1>", str1)
    elif "<STR" in s:
         raise Exception("Substitution string needed for this string. <STRING: %s>" %s) 

    if str2 is not None:
         s = s.replace("<STR2>", str2)

    if type(s) == type(''):
        return s

    return s()


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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Shunmugaraj.K
#

# StdLib
import time
import io
import binascii
import xml.parsers.expat
from string import *

# Local
from .g import *
from . import device, utils
from .sixext import to_bytes_utf8

http_result_pat = re.compile("""HTTP/\d.\d\s(\d+)""", re.I)
HTTP_OK = 200
HTTP_ACCEPTED = 202
HTTP_NOCONTENT = 204
HTTP_ERROR = 500

MAX_RETRIES = 2

LEDM_WIFI_BASE_URI = "/IoMgmt/Adapters/"

# This payload is working for LaserJet Devices
adapterPowerXml_payload2 ="""<?xml version="1.0" encoding="UTF-8" ?><io:Adapter xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:io="http://www.hp.com/schemas/imaging/con/ledm/iomgmt/2008/11/30" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:wifi="http://www.hp.com/schemas/imaging/con/wifi/2009/06/26">  <io:HardwareConfig> <dd:Power>%s</dd:Power> </io:HardwareConfig> </io:Adapter>"""

# This payload is working for OfficeJet and Photosmart Devices
adapterPowerXml_payload1 = """<?xml version="1.0" encoding="UTF-8"?><io:Adapters xmlns:io="http://www.hp.com/schemas/imaging/con/ledm/iomgmt/2008/11/30" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/"><io:Adapter><io:HardwareConfig><dd:Power>%s</dd:Power></io:HardwareConfig></io:Adapter></io:Adapters>"""

passPhraseXml="""<io:Profile xmlns:io="http://www.hp.com/schemas/imaging/con/ledm/iomgmt/2008/11/30" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:wifi="http://www.hp.com/schemas/imaging/con/wifi/2009/06/26" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.hp.com/schemas/imaging/con/ledm/iomgmt/2008/11/30 ../../schemas/IoMgmt.xsd http://www.hp.com/schemas/imaging/con/dictionaries/1.0/ ../../schemas/dd/DataDictionaryMasterLEDM.xsd"><io:AdapterProfile><io:WifiProfile><wifi:SSID>%s</wifi:SSID><wifi:CommunicationMode>%s</wifi:CommunicationMode><wifi:EncryptionType>%s</wifi:EncryptionType><wifi:AuthenticationMode>%s</wifi:AuthenticationMode></io:WifiProfile></io:AdapterProfile></io:Profile>"""

keyInfoXml = """<io:KeyInfo><io:WpaPassPhraseInfo><wifi:RsnEncryption>AESOrTKIP</wifi:RsnEncryption><wifi:RsnAuthorization>autoWPA</wifi:RsnAuthorization><wifi:PassPhrase>%s</wifi:PassPhrase></io:WpaPassPhraseInfo></io:KeyInfo>"""

def getAdaptorList(dev):
    ret,params,elementCount,code ={},{},0,HTTP_ERROR         
    max_tries = 0
    while max_tries < MAX_RETRIES:
        max_tries +=1
        URI = LEDM_WIFI_BASE_URI[0:len(LEDM_WIFI_BASE_URI)-1]# to remove "\" from the string
        paramsList,code = readXmlTagDataFromURI(dev,URI,'<io:Adapters', '<io:Adapter>')
        if code == HTTP_OK:
            break

    if code != HTTP_OK:
        log.error("Request Failed With Response Code %d"%code)
        return ret

    ret['adaptorlistlength'] = len(paramsList)
    if len(paramsList) != 0:        
            a = 0
            for params in paramsList:
                ret['adaptorpresence-%d' % a] = ''
                ret['adaptorstate-%d' % a] = ''
                try:
                    ret['adaptorid-%d' % a] = params['io:adapter-map:resourcenode-map:resourcelink-dd:resourceuri']
                except KeyError as e:
                    log.debug("Missing response key: %s" % e)    #changed from error to debug
                    ret['adaptorid-%d' % a]=""
                try:
                    ret['adaptorname-%d' % a] = params['io:adapter-io:hardwareconfig-dd:name']
                except KeyError as e:
                    log.debug("Missing response key: %s" % e)    #changed from error to debug
                    ret['adaptorname-%d' % a] = ""
                try:
                    ret['adaptortype-%d' % a] = params['io:adapter-io:hardwareconfig-dd:deviceconnectivityporttype']
                except KeyError as e:
                    log.debug("Missing response key: %s" % e)    #changed from error to debug
                    ret['adaptortype-%d' % a] = ""
                    
                a = a+1
    return ret   


def getWifiAdaptorID(dev):
    rVal = []

    ret = getAdaptorList(dev)
    try:
        num_adaptors = ret['adaptorlistlength']
    except KeyError:
        num_adaptors = 0

    for n in range(num_adaptors):
        try:
            name = ret['adaptortype-%d' % n]
        except KeyError:
            name = ''

        if name.lower() in ('wifiembedded', 'wifiaccessory'):            
            params = ['adaptorid', 'adaptorname', 'adaptorstate', 'adaptorpresence']            
            r = []
            for p in params:
                try:
                    x = ret[''.join([p, '-', str(n)])]
                except KeyError:
                    if p == 'adaptorid':
                        x = -1
                    else:
                        x = 'Unknown'

                r.append(x)

            rVal.append(r)

    return rVal
                         
def setAdaptorPower(dev, adapterList, power_state='on'):
    adaptor_id=-1
    adaptorName =""
    for a in adapterList:
       adaptor_id = a[0]
       adaptorName = a[1]
       ret,powerXml,URI,code = {},'','',HTTP_ERROR
       URI = LEDM_WIFI_BASE_URI + adaptorName
       powerXml = adapterPowerXml_payload1 %(power_state)  
  
       ret['errorreturn'] = writeXmlDataToURI(dev,URI,powerXml,10)    
       if not(ret['errorreturn'] == HTTP_OK or ret['errorreturn'] == HTTP_NOCONTENT):
          log.debug("Wifi Adapter turn ON request Failed. ResponseCode=%s AdaptorId=%s AdaptorName=%s. Trying another interface" %(ret['errorreturn'],adaptor_id,adaptorName))
          powerXml = adapterPowerXml_payload2 %(power_state)
          ret['errorreturn'] = writeXmlDataToURI(dev,URI,powerXml,10)

       if not(ret['errorreturn'] == HTTP_OK or ret['errorreturn'] == HTTP_NOCONTENT):
          log.error("Wifi Adapter turn ON request Failed. ResponseCode=%s AdaptorId=%s AdaptorName=%s" %(ret['errorreturn'],adaptor_id,adaptorName))
       else:
          log.debug("Wifi Adapter turn ON request is Success. AdaptorId=%s AdaptorName=%s" %(adaptor_id,adaptorName))
#          adapaterState = a[2], adapterPresence= a[3] 
          return adaptor_id, adaptorName, a[2], a[3] 

    return -1 ,"","",""

def performScan(dev, adapterName, ssid=None):
    ret ={}

    if ssid is None:
        URI = LEDM_WIFI_BASE_URI + adapterName + "/WifiNetworks"
    else:
        URI = LEDM_WIFI_BASE_URI + adapterName + "/WifiNetworks/SSID="+ssid 

    while True:            
        params,code,elementCount = readXmlDataFromURI(dev,URI,'<io:WifiNetworks', '<io:WifiNetwork>',10)        
        if code == HTTP_ACCEPTED:
            continue
        else:
            break  

    ret['numberofscanentries'] = elementCount 
    if code != HTTP_OK:
        log.error("Request Failed With Response Code %d"%code)
        return ret
       
    if params is not None:              
        if elementCount == 1:
            try:
                ssid = binascii.unhexlify(str(params['io:wifinetworks-io:wifinetwork-wifi:ssid']).encode('utf-8')).decode("utf-8")
                if not ssid:
                    ret['ssid-0'] = to_unicode('(unknown)')
                else:
                    ret['ssid-0'] = ssid
                try:
                    ret['bssid-0'] = binascii.unhexlify(str(params['io:wifinetworks-io:wifinetwork-wifi:bssid']).encode('utf-8')).decode("utf-8")
                except:
                    ret['bssid-0'] = params['io:wifinetworks-io:wifinetwork-wifi:bssid']
                                   
                ret['channel-0'] = params['io:wifinetworks-io:wifinetwork-wifi:channel']
                ret['communicationmode-0'] = params['io:wifinetworks-io:wifinetwork-wifi:communicationmode']
                ret['dbm-0'] = params['io:wifinetworks-io:wifinetwork-io:signalinfo-wifi:dbm']
                ret['encryptiontype-0'] = params['io:wifinetworks-io:wifinetwork-wifi:encryptiontype']
                ret['signalstrength-0'] = params['io:wifinetworks-io:wifinetwork-io:signalinfo-wifi:signalstrength']                
            except KeyError as e:
                log.debug("Missing response key: %s" % e)  
        else:
            for a in range(elementCount):
                try:
                    try:
                        ssid = binascii.unhexlify(str(params['io:wifinetworks-io:wifinetwork-wifi:ssid-%d' % a]).encode('utf-8')).decode('utf-8')
                    except TypeError: 
                        # Some devices returns one invalid SSID (i.e. 0) along with valid SSIDs. e.g. Epic.
                        ssid = params['io:wifinetworks-io:wifinetwork-wifi:ssid-%d' % a]

                    if not ssid:
                        ret['ssid-%d' % a] = to_unicode('(unknown)')
                    else:
                        ret['ssid-%d' % a] = ssid
                    try:
                        ret['bssid-%d' % a] = binascii.unhexlify(str(params['io:wifinetworks-io:wifinetwork-wifi:bssid-%d' % a]).encode('utf-8')).decode("utf-8")
                    except:
                        ret['bssid-%d' % a] = params['io:wifinetworks-io:wifinetwork-wifi:bssid-%d' % a]
                    ret['channel-%d' % a] = params['io:wifinetworks-io:wifinetwork-wifi:channel-%d' % a]
                    ret['communicationmode-%d' % a] = params['io:wifinetworks-io:wifinetwork-wifi:communicationmode-%d' % a]
                    ret['dbm-%d' % a] = params['io:wifinetworks-io:wifinetwork-io:signalinfo-wifi:dbm-%d' % a]
                    ret['encryptiontype-%d' % a] = params['io:wifinetworks-io:wifinetwork-wifi:encryptiontype-%d' % a]
                    ret['signalstrength-%d' % a] = params['io:wifinetworks-io:wifinetwork-io:signalinfo-wifi:signalstrength-%d' % a]                        
                
                except KeyError as e:
                    log.debug("Missing response key: %s" % e)  
                try:                    
                    ret['signalstrengthmax'] = 5
                    ret['signalstrengthmin'] = 0
                except KeyError as e:
                    log.debug("Missing response key: %s" % e)       
    return ret    

def getIPConfiguration(dev, adapterName):
    ip, hostname, addressmode, subnetmask, gateway, pridns, sec_dns = \
        '0.0.0.0', 'Unknown', 'Unknown', '0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0'
    protocol = 'old'
    URI = LEDM_WIFI_BASE_URI + adapterName + "/Protocols"
    #URI = "/DevMgmt/IOConfigDyn.xml"
    params,code,elementCount = {},HTTP_ERROR,0  
    max_tries = 0

    while max_tries < MAX_RETRIES:
        max_tries +=1
        params,code,elementCount = readXmlDataFromURI(dev,URI,'<io:Protocol', '<io:Protocol')
        if code == HTTP_OK:
            break 
     
    if code != HTTP_OK:
        max_tries = 0
        URI = "/DevMgmt/IOConfigDyn.xml"
        while max_tries < MAX_RETRIES:
            max_tries +=1
            params,code,elementCount = readXmlDataFromURI(dev,URI,'<iocfgdyn2:IOConfigDyn', '<dd3:IOAdaptorConfig')
            if code == HTTP_OK:
                protocol = 'new'
                break 
    if code != HTTP_OK:
        log.error("Request Failed With Response Code %d" %code)
        return ip, hostname, addressmode, subnetmask, gateway, pridns, sec_dns

    if protocol == 'old':
        if params is not None and code == HTTP_OK:
            try:
                ip = params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:ipv4address']            
                subnetmask = params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:subnetmask']
                gateway = params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:defaultgateway']
            
                if 'DHCP' in params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:configmethod']:
                    addressmode = 'dhcp'
                else:
                    addressmode = 'autoip'    
                    if elementCount ==1:
                        pridns = params['io:protocols-io:protocol-dd:dnsserveripaddress']
                        sec_dns = params['io:protocols-io:protocol-dd:secondarydnsserveripaddress']          
                        for a in range(elementCount):
                            if params['io:protocols-io:protocol-dd:dnsserveripaddress-%d' %a] !="::":
                                pridns = params['io:protocols-io:protocol-dd:dnsserveripaddress-%d' %a]
                                sec_dns = params['io:protocols-io:protocol-dd:secondarydnsserveripaddress-%d' %a]
                                break
            except KeyError as e:
                log.error("Missing response key: %s" % str(e))
    else:
        if params is not None and code == HTTP_OK:
            try:
            #ip = params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:ipv4address']
                try:
                    ip = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:ipaddress']
                except:
                    ip = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:ipaddress-0']

                #subnetmask = params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:subnetmask']
                try:
                    subnetmask = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:subnetmask']
                except:
                    subnetmask = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:subnetmask-0']

                #gateway = params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:defaultgateway']
                try:
                    gateway = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:defaultgateway']
                except:
                    gateway = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:defaultgateway-0']

                #if 'DHCP' in params['io:protocols-io:protocol-io:addresses-io:ipv4addresses-io:ipv4address-dd:configmethod']:
                try:
                    addressmode = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:ipconfigmethod'] 
                except:
                    addressmode = params['iocfgdyn2:ioconfigdyn-dd3:ioadaptorconfig-dd3:networkadaptorconfig-dd3:ipversionconfig-dd3:ipconfig-dd:ipconfigmethod-0'] 

                if 'dhcp' in addressmode.lower():
                    addressmode = 'dhcp'
                else:
                    addressmode = 'autoip'

            #if elementCount ==1:
            #    pridns = params['io:protocols-io:protocol-dd:dnsserveripaddress']
            #    sec_dns = params['io:protocols-io:protocol-dd:secondarydnsserveripaddress']          
            #for a in xrange(elementCount):
            #    if params['io:protocols-io:protocol-dd:dnsserveripaddress-%d' %a] !="::":
            #        pridns = params['io:protocols-io:protocol-dd:dnsserveripaddress-%d' %a]
            #        sec_dns = params['io:protocols-io:protocol-dd:secondarydnsserveripaddress-%d' %a]
            #        break
            except KeyError as e:
                log.error("Missing response key: %s" % str(e))        

    log.debug("ip=%s, hostname=%s, addressmode=%s, subnetmask=%s, gateway=%s, pridns=%s, sec_dns=%s"%(ip, hostname, addressmode, subnetmask, gateway, pridns, sec_dns))
    return ip, hostname, addressmode, subnetmask, gateway, pridns, sec_dns  




# TODO: Temporary Function. To be removed after refactoring.
def getwifiotherdetails(dev,adapterName):
    ip, subnet, gateway, pri_dns, sec_dns, mode = '', '', '', '', '', ''
    params1, params2, code1, code2, elementCount ={}, {}, HTTP_ERROR, HTTP_ERROR,0
    URI1 = LEDM_WIFI_BASE_URI + adapterName + "/Profiles/Active"
    URI2 = "/IoMgmt/IoConfig.xml" 
    max_tries = 0

    while max_tries < MAX_RETRIES:
        max_tries +=1
        params1, code1, elementCount = readXmlDataFromURI(dev,URI1,'<io:Profile', '<io:Profile')
        params2, code2, elementCount = readXmlDataFromURI(dev,URI2,'<io:IoConfig', '<io:IoConfig')
        if code1 == HTTP_OK and code2 == HTTP_OK:
            break 

    if code1 !=HTTP_OK and code2 != HTTP_OK:
        log.error("Request Failed With Response Code %d" %code)
        return ip, subnet, gateway, pri_dns, sec_dns 
	
    if params1 is not None and params2 is not None:
        try:
            ip = params1['io:profile-io:networkprofile-io:ipv4network-dd:ipaddress']
            subnet = params1['io:profile-io:networkprofile-io:ipv4network-dd:subnetmask']
            gateway = params1['io:profile-io:networkprofile-io:ipv4network-dd:defaultgateway']
            pri_dns  = params1['io:profile-io:networkprofile-io:ipv4network-dd:dnsserveripaddress']
            sec_dns = params1['io:profile-io:networkprofile-io:ipv4network-dd:secondarydnsserveripaddress']
            mode = params2['io:ioconfig-io:iodeviceprotocolconfig-io:ipv4domainname-dd:domainnameconfig-dd:configmethod']

        except KeyError as e:
            log.debug("Missing response key: %s" % str(e))
    return ip, subnet, gateway, pri_dns, sec_dns, mode
	
def getCryptoSuite(dev, adapterName):
    alg, mode, secretid = '', '', ''
    parms,code,elementCount ={},HTTP_ERROR,0
    URI = LEDM_WIFI_BASE_URI + adapterName + "/Profiles/Active"
    max_tries = 0
    
    while max_tries < MAX_RETRIES:
        max_tries +=1
        parms,code,elementCount = readXmlDataFromURI(dev,URI,'<io:Profile', '<io:Profile')
        if code == HTTP_OK:
            break 
    
    if code !=HTTP_OK:
        log.error("Request Failed With Response Code %d" %code)
        return  alg, mode, secretid

    if parms is not None:        
        try:
            mode = parms['io:profile-io:adapterprofile-io:wifiprofile-wifi:communicationmode']
            alg = parms['io:profile-io:adapterprofile-io:wifiprofile-wifi:encryptiontype']
            secretid = parms['io:profile-io:adapterprofile-io:wifiprofile-wifi:bssid']    
        except KeyError as e:
            log.debug("Missing response key: %s" % str(e))
    
    return  alg, mode, secretid


def associate(dev, adapterName, ssid, communication_mode, encryption_type, key):
    ret,code = {},HTTP_ERROR    
    URI = LEDM_WIFI_BASE_URI + adapterName + "/Profiles/Active"

    if encryption_type == 'none':
        authMode = 'open'
        ppXml = passPhraseXml%(binascii.hexlify(to_bytes_utf8(ssid)).decode('utf-8'), communication_mode,encryption_type,authMode)
    else:
        authMode = encryption_type
        pos = passPhraseXml.find("</io:WifiProfile>",0,len(passPhraseXml))
        ppXml = (passPhraseXml[:pos] + keyInfoXml + passPhraseXml[pos:])%(binascii.hexlify(to_bytes_utf8(ssid)).decode('utf-8'),communication_mode,encryption_type,\
        authMode,binascii.hexlify(to_bytes_utf8(key)).decode('utf-8'))        

    code = writeXmlDataToURI(dev,URI,ppXml,10)    
    ret['errorreturn'] = code
    if not(code == HTTP_OK or HTTP_NOCONTENT):
        log.error("Request Failed With Response Code %d" % ret['errorreturn'])
    
    return ret


def getVSACodes(dev, adapterName):
    ret,params,code,elementCount = [],{},HTTP_ERROR,0
    severity,rule ='',''
    URI = LEDM_WIFI_BASE_URI + adapterName + "/VsaCodes.xml"
    max_tries = 0
    
    while max_tries < MAX_RETRIES:
        max_tries +=1
        params,code,elementCount = readXmlDataFromURI(dev,URI,"<io:VsaCodes","<io:VsaCodes",10)
        if code == HTTP_OK:
            break
    
    if code != HTTP_OK:
        log.warn("Request Failed With Response Code %d"%code)
        return ret
 
    if params is not None:
        try:
            severity= params['io:vsacodes-wifi:vsacode-dd:severity']
        except:
            severity = ""
        try:
            rule = params['io:vsacodes-wifi:vsacode-wifi:rulenumber']            
       # except KeyError, e:
           # log.error("Missing response key: %s" % str(e))
        except:
            rule = ""
        ret.append((rule, severity))       
    return ret  


def getHostname(dev):
    hostName = ''
    URI = "/IoMgmt/IoConfig.xml"    
    max_tries = 0
    
    while max_tries < MAX_RETRIES:
        max_tries +=1
        params,code,elementCount = readXmlDataFromURI(dev,URI,'<io:IoConfig', '<io:IoConfig')        
        if code == HTTP_OK:
            break    
    
    if code != HTTP_OK:
        log.warn("Request failed with Response code %d. HostName not found."%code)
        return  hostName
       
    if params is not None:        
        try:               
            hostName = params['io:ioconfig-io:iodeviceconfig-dd3:hostname']            
        except KeyError as e:
            log.debug("Missing response key: %s" % e)

    return  hostName

def getSignalStrength(dev, adapterName, ssid, adaptor_id=0):
    ss_max, ss_min, ss_val, ss_dbm = 5, 0, 0, -200
    params,code,elementCount = {},HTTP_ERROR,0

    if ssid is not None:      
        URI = LEDM_WIFI_BASE_URI + adapterName + "/WifiNetworks/SSID="+ssid 
    else:
        return ss_max, ss_min, ss_val, ss_dbm

    while True:            
        params,code,elementCount = readXmlDataFromURI(dev,URI,'<io:WifiNetworks', '<io:WifiNetwork>',10)        
        if code == HTTP_ACCEPTED:
            log.info("Got Response as HTTP_ACCEPTED, so retrying to get the actual result")
            continue
        else:
            break  

    if code != HTTP_OK:
        log.error("Request Failed With Response Code %d"%code)
        return ss_max, ss_min, ss_val, ss_dbm
       
    if params is not None:        
        if elementCount == 1:
            try:                
                ss_dbm = params['io:wifinetworks-io:wifinetwork-io:signalinfo-wifi:dbm']                
                ss_val = params['io:wifinetworks-io:wifinetwork-io:signalinfo-wifi:signalstrength']                
            except KeyError as e:
                log.error("Missing response key: %s" % e)

    return  ss_max, ss_min, ss_val, ss_dbm


def readXmlTagDataFromURI(dev,URI,xmlRootNode,xmlReqDataNode,timeout=5):
    paramsList,code =[],HTTP_ERROR
    
    data = format_http_get(URI,0,"")
    log.info(data)
    response = io.BytesIO()
    if dev.openLEDM() == -1:
        dev.closeLEDM()
        if dev.openEWS_LEDM() == -1:
            
            dev.openMarvell_EWS()
            dev.writeMarvell_EWS(data)
            try:
                while dev.readMarvell_EWS(1024, response, timeout):
                    pass
            except Error:
                dev.closeMarvell_EWS()
                log.error("Unable to read Marvell_EWS Channel")
        else:
            dev.writeEWS_LEDM(data)
            try:
                dev.readLEDMData(dev.readEWS_LEDM, response, timeout)
            except Error:
                dev.closeEWS_LEDM()
                log.error("Unable to read EWS_LEDM Channel")
    else:
        dev.writeLEDM(data)
        try:
            dev.readLEDMData(dev.readLEDM, response, timeout)
        except Error:
            dev.closeLEDM()
            log.error("Unable to read LEDM Channel")
        
    strResp = response.getvalue().decode('utf-8')
    if strResp is not None:                             
        code = get_error_code(strResp)
        if code == HTTP_OK:
            strResp = utils.unchunck_xml_data(strResp)
            pos = strResp.find(xmlRootNode,0,len(strResp))    
            repstr = strResp[pos:].strip()
            repstr = repstr.replace('\r',' ').replace('\t',' ').replace('\n',' ') # To remove formating characters from the received xml
            repstr = repstr.rstrip('0')   # To remove trailing zero from the received xml
            try:
                parser_object = utils.extendedExpat()
                root_element = parser_object.Parse(repstr)
                xmlReqDataNode = ''.join(l for l in filter(lambda x: x not in '<>', xmlReqDataNode)) # [c for c in xmlReqDataNode if c not in "<>"] # To remove '<' and '>' characters
                reqDataElementList = root_element.getElementsByTagName(xmlReqDataNode)
                for node in reqDataElementList:
                    repstr = node.toString()
                    repstr = repstr.replace('\r',' ').replace('\t',' ').replace('\n',' ') # To remove formating characters from the received xml
                    params = utils.XMLToDictParser().parseXML(to_bytes_utf8(repstr))
                    paramsList.append(params)
            except xml.parsers.expat.ExpatError as e:
                log.debug("XML parser failed: %s" % e)  #changed from error to debug 
        else:
            log.debug("HTTP Responce failed with %s code"%code)
    return paramsList,code



def readXmlDataFromURI(dev,URI,xmlRootNode,xmlChildNode,timeout=5):
    params,code,elementCount ={},HTTP_ERROR,0 
    
    data = format_http_get(URI,0,"")
    log.info(data)
    response = io.BytesIO()
    if dev.openLEDM() == -1:
        dev.closeLEDM()
        if dev.openEWS_LEDM() == -1:
            
            dev.openMarvell_EWS()
            dev.writeMarvell_EWS(data)
            try:
                while dev.readMarvell_EWS(1024, response, timeout):
                    pass
            except Error:
                dev.closeMarvell_EWS()
                log.error("Unable to read Marvell_EWS Channel")
        else:
            dev.writeEWS_LEDM(data)
            try:
                dev.readLEDMData(dev.readEWS_LEDM, response,timeout)
            except Error:
                dev.closeEWS_LEDM()
                log.error("Unable to read EWS_LEDM Channel")
    else:
        dev.writeLEDM(data)
        try:
            dev.readLEDMData(dev.readLEDM, response,timeout)
        except Error:
            dev.closeLEDM()
            log.error("Unable to read LEDM Channel") 
    #dev.closeEWS_LEDM()    
    strResp = response.getvalue().decode('utf-8')
    if strResp is not None:                             
        code = get_error_code(strResp)
        if code == HTTP_OK:
            #strResp = utils.unchunck_xml_data(strResp)
            strResp = utils.extract_xml_chunk(strResp)
            pos = strResp.find(xmlRootNode,0,len(strResp))    
            repstr = strResp[pos:].strip()
            repstr = repstr.replace('\r',' ').replace('\t',' ').replace('\n',' ') # To remove formating characters from the received xml
            repstr = repstr.rstrip('0')   # To remove trailing zero from the received xml
            elementCount = repstr.count(xmlChildNode)
            try:
                params = utils.XMLToDictParser().parseXML(repstr)            
            except xml.parsers.expat.ExpatError as e:
                log.debug("XML parser failed: %s" % e)  #changed from error to debug 
        else:
            log.debug(" HTTP Responce failed with %s code"%code)

    return params,code,elementCount


def writeXmlDataToURI(dev,URI,xml,timeout=5):
    code = HTTP_ERROR

    data = format_http_put(URI,len(xml),xml)
    response = io.BytesIO()

    if dev.openLEDM() == -1:
        if dev.openEWS_LEDM() == -1:
            dev.openMarvell_EWS()
            dev.writeMarvell_EWS(data)
            try:
               while dev.readMarvell_EWS(1000, response, timeout):
                   pass
            except Error:
                dev.closeMarvell_EWS()
                log.error("Unable to read Marvell_EWS Channel")
        else:
            dev.writeEWS_LEDM(data)
            try:
                dev.readLEDMData(dev.readEWS_LEDM, response, timeout)
            except Error:
                dev.closeEWS_LEDM()
                log.error("Unable to read EWS_LEDM Channel")
            
    else:
        dev.writeLEDM(data)
        try:
            dev.readLEDMData(dev.readLEDM, response,timeout )
        except Error:
            dev.closeLEDM()
            log.error("Unable to read LEDM Channel") 
        

    strResp = response.getvalue().decode('utf-8')
    if strResp is not None:
        code = get_error_code(strResp)           
    return code


def get_error_code(ret):
    if not ret: return HTTP_ERROR
    match = http_result_pat.match(ret)
    if match is None: return HTTP_ERROR
    try:
        code = int(match.group(1))
    except (ValueError, TypeError):
        code = HTTP_ERROR
    return code


def format_http_get(requst, ledmlen, xmldata, content_type="text/xml; charset=utf-8"):
    host = 'localhost'
    return  utils.cat(
"""GET $requst HTTP/1.1\r
Host: $host\r
User-Agent: hplip/3.0\r
Content-Type: $content_type\r
Content-Length: $ledmlen\r
\r
$xmldata""")


def format_http_put(requst, ledmlen, xmldata, content_type="text/xml; charset=utf-8"):
    host = 'localhost'
    return  utils.cat(
"""PUT $requst HTTP/1.1\r
Host: $host\r
User-Agent: hplip/3.0\r
Content-Type: $content_type\r
Content-Length: $ledmlen\r
\r
$xmldata""")    

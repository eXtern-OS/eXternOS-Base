#       xutils.py -- Enhanced class of X-Kit's parser
#       
#       Copyright 2008 Alberto Milone <albertomilone@alice.it>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from __future__ import print_function
from __future__ import unicode_literals
from .xorgparser import *
import sys

class XUtils(Parser):
    '''Subclass with higher-level methods
    
    See xorgparser.Parser for the low-level methods'''
    def __init__(self, source=None):
        super(XUtils, self).__init__(source)
    
    def fix_broken_references(self):
        '''Fix broken references to non-existent sections'''
        broken_references = self.get_broken_references()
        for section in broken_references:
            for reference in broken_references[section]:
                self.make_section(section, identifier=reference)
     
    def get_driver(self, section, position):
        '''Get the driver in use in a section

        If no driver is found it will return False.

        For further information see get_value()'''
        option = 'Driver'
        return self.get_value(section, option, position)
        
    def set_driver(self, section, driver, position):
        '''Set the driver in use in a section'''
        option = 'Driver'
        self.add_option(section, option, driver, position=position)

    def section_has_driver(self, driver, sections_list=None):
        '''Look for a driver in the Device sections

        Return True if the driver is found in each of the specified
        sections, otherwise return False.

        if sections_list == None check all the Device sections'''
        if sections_list == None:
            sections_list = list(self.globaldict['Device'].keys())

        for section in sections_list:
            try:
                if self.get_driver('Device', section) != driver:
                    return False
            except OptionException:
                #no references to the Device section
                return False
        return True

    def get_devices_in_serverlayout(self, position):
        '''Return a list of references to the Device sections in ServerLayout
        
        This method looks for references to Device sections in the Screen
        sections referred to in the ServerLayout[position] section.'''
        devices_to_check = []
        references = self.get_references('ServerLayout', position, ['Screen'])
        if len(references['Screen']) > 0:
            # Check all the device sections related to these Screen sections
            #
            # references will look like {'Screen': ['Screen1', '0']}
            for reference in references['Screen']:
                try:
                    screen_position = self.get_position('Screen', reference)
                except IdentifierException:
                    continue
                # Get references to the Device sections in the Screen sections
                try:
                    device_references = self.get_references('Screen',
                                             screen_position, ['Device'])
                    for device in device_references['Device']:
                        device_position = self.get_position('Device', device)
                        devices_to_check.append(device_position)
                except OptionException:
                    #no references to the Device section
                    pass
        return devices_to_check
    
    def get_devices_in_use(self):
        '''Return the Device sections in use

        If no Device sections are referenced in ServerLayout then all of
        the available Device sections are returned.

        This method supports old Xinerama setups and therefore looks for
        references to Device sections in the ServerLayout section(s) and
        checks only the default ServerLayout section provided than one is
        set in the ServerFlags section.'''
        devices_to_check = []
        driver_enabled = False
        
        serverlayout = self.globaldict['ServerLayout']
        serverflags = self.globaldict['ServerFlags']
        serverlayout_length = len(serverlayout)
        serverflags_length = len(serverflags)
        
        if serverlayout_length > 0:
            if serverlayout_length > 1:#More than 1 ServerLayout?
                if serverflags_length > 0:#has ServerFlags
                    # If the ServerFlags section exists there is a chance that
                    # a default ServerLayout is set.
                    #
                    # If no ServerLayout is set, this might be intentional
                    # since the user might start X with the -layout command
                    # line option.

                    # See if it has a default ServerLayout
                    default = self.get_default_serverlayout()

                    if len(default) == 1:
                        devices_to_check = \
                        self.get_devices_in_serverlayout(default[0])
                    else:
                        for layout in serverlayout:
                            devices_to_check += \
                            self.get_devices_in_serverlayout(layout)
                else:
                    for layout in serverlayout:
                        devices_to_check += \
                        self.get_devices_in_serverlayout(layout)
            else:
                devices_to_check = self.get_devices_in_serverlayout(0)

        if len(devices_to_check) == 0:
            # Check all the Device sections
            devices_to_check = list(self.globaldict['Device'].keys())

        return devices_to_check
    
    def is_driver_enabled(self, driver):
        '''See if a driver is enabled in the Device sections

        When possible, this method checks only the Device sections in use,
        otherwise it checks any available Device section.

        This method supports old Xinerama setups and therefore looks for
        references to Device sections in the ServerLayout section(s) and
        checks only the default ServerLayout section provided than one is
        set in the ServerFlags section.'''
        devices_to_check = self.get_devices_in_use()
        driver_enabled = self.section_has_driver(driver,
                                               sections_list=devices_to_check)

        return driver_enabled

    def get_screen_device_relationships(self):
        '''See which Screen sections are related to which Device sections'''
        relationships = {}
        it = 0
        for screen in self.globaldict['Screen']:
            references = self.get_references('Screen', it, reflist=['Device'])
            device = references['Device'][0]
            device = self.get_position('Device', device)
            relationships.setdefault(device)
            relationships[device] = {}
            relationships[device]['Screen'] = it
            it += 1

        return relationships


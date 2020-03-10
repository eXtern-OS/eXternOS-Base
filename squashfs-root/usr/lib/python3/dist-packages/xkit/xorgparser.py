#       xorgparser.py -- Core class of X-Kit's parser
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
import sys
from sys import stdout, stderr
import copy

class IdentifierException(Exception):
    '''Raise if no identifier can be found'''
    pass

class OptionException(Exception):
    '''Raise when an option is not available.'''
    pass
   
class SectionException(Exception):
    '''Raise when a section is not available.'''
    pass

class ParseException(Exception):
    '''Raise when a postion is not available.'''
    pass

class Parser(object):
    '''Only low-level methods here.
    
    See the xutils.XUtils subclass for higher-level methods.'''
    def __init__(self, source=None):
        '''source = can be an object or a file. If set to None (default)
                 Parser will start from scratch with an empty
                 configuration.
        
        Public:
        
        comments = name of the section which stores the commented lines
                   located outside of the sections in the xorg.conf.

        globaldict = a global dictionary containing all the sections and
                     options. For further information on globaldict, have a
                     look at __check_sanity() and at get_value().

        globaldict['Comments'] = stores the commented lines located inside of
                                 the sections in the xorg.conf.

        require_id = a list of the sections which require to have an
                    "Identifier" set in the xorg.conf (e.g. Device sections).

        identifiers = a dictionary of the sections which require identifiers.

        sections = a tuple containing the names of all the sections in
                   globaldict. Their names are not guaranteed to be all legal
                   in xorg.conf (see "valid_sections").

        valid_sections = a tuple containing the names of all the sections
                         which __check_sanity() will look for in the
                         xorg.conf. Sections with other names will be ignored
                         by self._check_sanity().

        references = a list containing the names of all the possible
                     references.'''
        
        self.subsection = 'SubSection'
        self.commentsection = 'Comments'
        self.source = source
        self.sections = ('InputDevice',
                         'Device',
                         'Module',
                         'Monitor',
                         'Screen',
                         'ServerLayout',
                         'ServerFlags',
                         'Extensions',
                         'Files',
                         'InputClass',
                         'DRI',
                         'VideoAdaptor',
                         'Vendor',
                         'Modes',
                         self.subsection,
                         self.commentsection)
        # "Comments" is not a valid section
        self.valid_sections = self.sections[:-1]

        self.require_id = [
                          'InputClass',
                          'InputDevice',
                          'Device',
                          'Monitor',
                          'Screen',
                          'ServerLayout'
                         ]
        self.references = [
                           'Device',
                           'InputDevice',
                           'Monitor',
                           'Screen'
                          ]
        
        self.identifiers = {}.fromkeys(self.require_id)
        
        self.comments = []
        self._gdict = {}.fromkeys(self.sections, 0)
        for elem in self._gdict:
            self._gdict[elem] = {}
        
        self._check_sanity()
        
    def _get_global(self):
        return self._gdict

    def _set_global(self, global_dict):
        self._gdict = global_dict

    # Property to expose _gdict as globaldict
    globaldict = property(_get_global, _set_global)
            
    def _check_sanity(self):
        '''Perform a sanity check of the file and fill self.globaldict with
        all the sections and subsections in the xorg.conf
        
        
        empty = is the file empty? If yes, then don't check if:
            * the last section is not complete
            * there are duplicates
        
        has_section:
            * == True: a section is already open
            * == False: a section is closed and/or a new section can be opened
            
        has_subsection:
            * == True: a subsection is already open
            * == False: a section is closed and/or a new section can be opened
            
        section_flag:
            * == '':a section is closed and/or a new section can be opened
            * == the name the current section
        
        section_tags = counter of the number of Section and EndSection strings
        
        subsection_tags = counter of the number of SubSection and EndSubSection
                         strings
        
        lines_list = the list of the lines in the source object.
        
        global_iters = counts how many times each kind of section
                             (section_flag) is found in the xorg.conf'''
        
        #See if the source is a file or a file object
        #and act accordingly
        file = self.source
        if file == None:
            lines_list = []
        else:
            if not hasattr(file, 'write'):#it is a file
                myfile = open(file, 'r')
                lines_list = myfile.readlines()
                myfile.close()
            else:#it is a file object
                lines_list = file.readlines()
        
        
        # Create a dictionary such as the following:
        # {'Device': {}, 'InputDevice': {}}
        
        global_iters = {}.fromkeys(self.sections, 0)
        
        empty = True
        
        has_section = False
        has_subsection = False
        section_flag = ''
        
        section_tags = 0
        subsection_tags = 0
        
        it = 0
        for line in lines_list:
            if line.strip().startswith('#'):
                if has_section == False:
                    self.comments.append(line)
                else:#has_section == True
                    section_pos = global_iters[section_flag]
                    if has_subsection == False:
                        self._gdict[self.commentsection].setdefault(section_flag, {})
                        temp_dict = self._gdict[self.commentsection][section_flag]
                        temp_dict.setdefault(section_pos, {})
                        temp_dict[section_pos].setdefault('identifier', None)
                        temp_dict[section_pos].setdefault('position', section_pos)
                        temp_dict[section_pos].setdefault('section', None)
                        temp_dict[section_pos].setdefault('options', [])
                        temp_dict[section_pos]['options'].append(line.strip())
                    else:#has_subsection == True
                        curlength = global_iters[self.subsection]
                        self._gdict[self.commentsection].setdefault(self.subsection, {})
                        temp_dict = self._gdict[self.commentsection][self.subsection]
                        temp_dict.setdefault(curlength, {})
                        temp_dict[curlength].setdefault('identifier', subsection_id)
                        temp_dict[curlength].setdefault('position', section_pos)
                        temp_dict[curlength].setdefault('section', section_flag)
                        temp_dict[curlength].setdefault('options', [])
                        temp_dict[curlength]['options'].append(line.strip())
                    del temp_dict
                
                
            # See if the name of the section is acceptable
            # i.e. included in self.valid_sections
            elif line.lower().strip().startswith('section'):#Begin Section
                test_line_found = False
                for sect in self.valid_sections:
                    if line.lower().find('"' + sect.lower() + '"') != -1:
                        test_line_found = True
                        section = sect
                        break
                if not test_line_found:
                    # e.g. in case the name of the section is not
                    # recognised:
                    # Section "whatever"
                    error = ('The name in the following line is invalid for a '
                             'section:\n%s' % (line))
                    raise ParseException(error)
                else:
                    if has_section == False:
                        section_tags += 1

                        section_flag = section
                        empty = False
                        has_section = True
                    else:
                        error = 'Sections cannot be nested in other sections.'
                        raise ParseException(error)
            elif line.lower().strip().startswith('endsection') == True:
                #End Section
                section_tags += 1
                if has_section == True and has_subsection == False:
                    global_iters[section_flag] += 1
                    
                    section_flag = ''
                    has_section = False
                else:
                    error = 'An EndSection is in the wrong place.'
                    raise ParseException(error)
            elif line.lower().strip().startswith('subsection') == True:
                #Begin SubSection
                subsection_tags += 1
                
                if has_section == True and has_subsection == False:
                    has_subsection = True
                    subsection_id = line[line.find('"') + 1:
                                         line.rfind('"')].strip()
                    
                    self._gdict.setdefault(self.subsection, {})
                    curlength = global_iters[self.subsection]
                    self._gdict[self.subsection][curlength] = {}
                    # self._gdict - keys:
                    #
                    # section =  the section in which the subsection is
                    #            located (e.g. "Screen")
                    # position = e.g. in key 0 of the
                    #            self._gdict['Screen']
                    # identifier = e.g. 'Display' (in SubSection "Display")
                    # options = a list of lines with the options 
                    
                    temp_dict = self._gdict[self.subsection][curlength]
                    temp_dict['section'] = section_flag
                    try:
                        temp_dict['position'] = global_iters[section_flag]
                    except KeyError:
                        del temp_dict
                        error = ('SubSections can be nested only in well '
                                 'formed sections.')
                        raise ParseException(error)
                    temp_dict['identifier'] = subsection_id
                    temp_dict['options'] = []
                    del temp_dict
                else:
                    error = ('SubSections can be nested only in well formed '
                             'sections.')
                    raise ParseException(error)
                
            elif line.lower().strip().startswith('endsubsection') == True:
                #End SubSection
                subsection_tags += 1
                
                if has_subsection == True:
                    has_subsection = False
                    global_iters[self.subsection] += 1
                else:
                    error = ('SubSections can be closed only after being '
                             'previously opened.')
                    raise ParseException(error)
            else:
                if section_flag != '':
                    #any other line
                    if line.strip() != '':
                        #options
                        if has_subsection == True:
                            # section =  the section in which the subsection
                            #            is located (e.g. "Screen")
                            # position = e.g. in key 0 of the
                            #            self._gdict['Screen']
                            # identifier = e.g. 'Display' (in SubSection
                            #                             "Display")
                            # options = a list of lines with the options
                            self._gdict[self.subsection][curlength][
                                 'options'].append('\t' + line.strip() + '\n')
                        else:
                            self._gdict.setdefault(section_flag, {})
                            curlength = global_iters[section_flag]
                            self._gdict[section_flag].setdefault(curlength,
                                        []).append('\t' + line.strip() + '\n')
            it += 1
        
        if not empty:
            # If the last section is not complete
            if section_tags % 2 != 0 or subsection_tags % 2 != 0:
                error = 'The last section is incomplete.'
                raise ParseException(error)
            
            # Fill self.identifiers
            self._fill_identifiers()
            

            # Make sure that the configuration file is compliant with
            # the rules of xorg

            self._check_syntax()
            
        else:
            self._fill_identifiers()
    
    def _check_syntax(self):
        '''This method contains the several checks which can guarantee
        compliance with the syntax rules of the xorg.conf'''
        
#        '''
#        Raise an exception if there are duplicate options i.e.
#        options (not references) of the same kind with the same
#        or with a different value.
#        
#        e.g. Driver "nvidia" and Driver "intel" cannot coexist in the
#        same Device section.
#        '''
#        if len(self.check_duplicate_options()) > 0:
#            error = ('There cannot be Duplicate Options:\n%s' %
#                     (str(self.check_duplicate_options())))
#            raise ParseException(error)
            
        
        # Raise an exception if there are duplicate sections i.e. 
        # sections of the same kind (e.g. "Device") with the same 
        # identifier.
        # 
        # e.g. The following configuration is not allowed:
        # 
        # Section "Device"
        #     Identifier "My Device"
        # EndSection
        # 
        # Section "Device"
        #     Identifier "My Device"
        # EndSection
        if len(self.get_duplicate_sections()) > 0:
            error = ('There cannot be Duplicate Sections:\n%s'
                     % (str(self.get_duplicate_sections())))
            raise ParseException(error)
        
        
        # One word entries are not acceptable as either options or references.
        # If one is found, ParseException will be raised.
        self._validate_options()
        
        
        # Raise an exception if there are broken references i.e. references
        # to sections which don't exist.
        # 
        # For example, if the xorg.conf were the following:
        # 
        # Section "Device"
        #     Identifier "Another Device"
        # EndSection
        # 
        # Section "Screen"
        #     Identifier "My Screen"
        #     Device "My Device"
        # EndSection
        # 
        # There would be no Device section which has "My Device" as an
        # identifier
        broken = self.get_broken_references()
        
        it = 0
        for section in broken:
            it += len(broken[section])
        if it > 0:
            error = 'There cannot be Broken References:\n%s' % (str(broken))
            raise ParseException(error)
        
        
        # If there are sections which don't have an identifier
        # but they should (i.e. they are in self.require_id)
        # 
        # NOTE: if there are empty sections without an identifier
        # e.g. Section "Device"
        #      EndSection
        #         
        #      they won't trigger the ParseException but won't
        #      cause any problem since they will be completely
        #      ignored and won't appear in the target file.
        for section in self.require_id:
            if len(self._gdict[section]) != len(self.identifiers[section]):
                error = ('Not all the sections which require an identifier '
                         'have an identifier.')
                raise ParseException(error)
        
        # The ServerLayout section must have at least 1 reference to a
        # "Screen" section
        if len(self._gdict['ServerLayout']) > 0:
            for section in self._gdict['ServerLayout']:
                screen_references = self.get_references('ServerLayout',
                                                        section,
                                                        reflist=['Screen'])
                if len(screen_references['Screen']) == 0:
                    error = ('The ServerLayout section must have at '
                             'least 1 reference to a "Screen" section.')
                    raise ParseException(error)
            
        
        # No more than one default ServerLayout can be specified in the
        # ServerFlags section
        default_layout = self.get_default_serverlayout()
        if len(default_layout) > 0:
            if len(default_layout) > 1:
                error = ('No more than one default ServerLayout can be '
                         'specified in the ServerFlags section.')
                raise ParseException(error)
            
            if not self.is_section('ServerLayout', position=default_layout[0]):
                error = 'The default ServerLayout does not exist.'
                raise ParseException(error)
        
    def _fill_identifiers(self):
        '''Fill self.identifiers
        
        self.identifiers has the section types as keys and a list of tuples
        as values. The tuples contain the identifier and the position of
        each section.
        
        Here's a basic scheme:
        
        self.identifiers = {section_type1: [
                                        (identifier1, position1),
                                        (identifier2, position2)
                                      ], etc.
                           }
        
        Concrete example:
        
        self.identifiers = {'Device': [
                                        ('Configured Video Device', 0),
                                        ('Another Video Device', 1)
                                      ],
                            'Screen': [
                                        ('Configured Screen Device', 0),
                                        ('Another Screen Device', 1)
                                      ],
                           } '''
        
        for sect in self.require_id:#identifiers.keys():
            self.identifiers[sect] = []
            it = 0
            for elem in self._gdict[sect]:
                try:
                    identifier = self.get_value(sect, 'Identifier', it)
                except (OptionException, SectionException):
                    #if no identifier can be found
                    error = ('No Identifier for section %s, position %d, '
                             'can be found.' % (sect, elem))
                    raise ParseException(error)
                try:
                    identifier.append('')
                    identifier = identifier[0]
                except AttributeError:
                    pass
                
                self.identifiers[sect].append((identifier, it))
                it += 1
    
    def _validate_options(self):
        '''One word entries are not acceptable as either options or references

        If a one word entry is found, ParseException will be raised.'''

        # Sections in sections_whitelist won't be validated
        sections_whitelist = ['Files', 'Comments']
        options_whitelist = ['endmode']
        for section in self.sections:
            if section not in sections_whitelist:
                for position in self._gdict[section]:
                    if section == self.subsection:#'SubSection':
                        options = self._gdict[section][position]['options']
                    else:
                        options = self._gdict[section][position]
                    
                    
                    for option in options:
                        option = option.strip()
                        if option.find('#') != -1:#remove comments
                            option = option[0: option.find('#')]
                        
                        error = ('The following option is invalid: %s'
                                 % (option.strip()))
                        
                        optbits = self._clean_duplicates(option,
                                                         include_null=True)

                        if (len(optbits) == 1
                        and optbits[0].strip().lower() not
                        in options_whitelist):
                            raise ParseException(error)
                        
                        if not optbits[0][0].isalpha():
                            raise ParseException(error)
    
    def get_duplicate_options(self, section, position):
        '''See if there are duplicate options in a section

        It is ok to have duplicated references e.g. several Load options, or
        Screen, etc. though'''

        blacklist = ['driver', 'busid', 'identifier']
        total = []
        duplicates = []

        if section == 'SubSection':
            options = self._gdict[section][position]['options']
        else:
            options = self._gdict[section][position]

        for option in options:
            option = option.strip()
            if option.find('#') != -1:#remove comments
                option = option[0: option.find('#')]
            
            optbits = self._clean_duplicates(option)
            # optbits may look like this:
            # 
            # ['Option', 'TestOption1', '0']
            # 
            # or
            # ['Screen', 'My screen 1']
            try:
                if optbits[0].lower() in blacklist:
                    total.append(optbits[0])
                elif optbits[0].lower() == 'option':
                    if len(optbits) > 1 and optbits[1] != None:
                        '''
                        make sure it's not a broken option e.g.
                          Option
                        '''
                        total.append(optbits[1])
            except (AttributeError, IndexError):
                pass
        final = {}
        for option in total:
            if final.get(option) != None:
                duplicates.append(option)
            else:
                final[option] = option
        return duplicates
        
    def check_duplicate_options(self):
        '''Look for and return duplicate options in all sections'''
        
        duplicates = {}
        for section in self._gdict:
            for elem in self._gdict[section]:
                duplopt = self.get_duplicate_options(section, elem)
                if len(duplopt) > 0:
                    duplicates.setdefault(section, {}).setdefault(elem,
                                                                  duplopt)

        return duplicates

    def _clean_duplicates(self, option, include_null=None):
        '''Clean the option and return all its components in a list
        
        include_null - is used only by _validate_options() and makes
        sure that options with a null value assigned in quotation
        marks are not considered as one-word options'''
        
        #print '\nCLEAN', repr(option)
        optbits = []
        optbit = ''
        it = 0
        quotation = 0
        optcount = option.count('"')
        if optcount > 0:#dealing with a section option
            for i in option:
                #print 'i', repr(i), 'optbit', optbit
                if not i.isspace():
                    if i == '"':
                        quotation += 1
                    else:
                        optbit += i
                else:    
                
                    if quotation % 2 != 0:
                        optbit += i
                        
                    else:
                        if len(optbit) > 0:
                            optbits.append(optbit)
                            #print 'i=', i, 'optbit=', optbit
                            optbit = ''
                        
                if it == len(option) - 1:
                    if optbit != '':
                        optbits.append(optbit)
                        #print 'i=END', 'optbit=', optbit
                it += 1            
        else:#dealing with a subsection option
            for i in option:
                #print 'i', repr(i), 'optbit', optbit
                if not i.isspace():
                    optbit += i
                else:    
                    if len(optbit) > 0:
                        optbits.append(optbit)
                        #print 'i=', i, 'optbit=', optbit
                        optbit = ''
                        
                if it == len(option) - 1:
                    if optbit != '':
                        optbits.append(optbit)
                        #print 'i=END', 'optbit=', optbit
                    else:
                        if include_null:
                            optbit = ''
                            optbits.append(optbit)
                it += 1

        if include_null and len(optbits) != optcount/2 +1:
            # e.g. if the option looks like the following:
            # 
            # Modelname ""
            # 
            # add a '' which wouldn't be caught by this method otherwise.
            optbit = ''
            optbits.append(optbit)

        return optbits

    def get_duplicate_sections(self):
        '''Return a dictionary with the duplicate sections i.e. sections
        of the same kind, with the same identifier'''
        
        duplicates = {}
        for section in self.identifiers:
            temp = []
            for sect in self.identifiers[section]:
                temp.append(sect[0])
            for elem in temp:
                if temp.count(elem) > 1:
                    duplicates.setdefault(section, {}).setdefault(elem,
                                                       temp.count(elem))

        return duplicates


    def add_option(self, section, option, value, option_type=None,
                   position=None, reference=None, prefix='"'):
        '''Add an option to a section
        
        section= the section which will have the option added
        option= the option to add
        value= the value which will be assigned to the option
        position= e.g. 0 (i.e. the first element in the list of Screen
                      sections)
        option_type= if set to "Option" it will cause the option to look like
                    the following:
                    Option "NameOfTheOption" "Value"
                    
                    Otherwise it will look like the following:
                    NameOfTheOption "Value"
        position= e.g. 0 (i.e. the first element in the list of Screen
                      sections)
        reference= used only in a particular case of reference (see
                   add_reference)
        
        prefix= usually quotation marks are used for the values (e.g. "True")
                however sometimes they don't have to be used
                (e.g. DefaultDepth 24) and prefix should be set to '' instead
                of '"'  '''
        refSections = ['device']
        #prefix = '"'#values are always in quotation marks
        if position != None:
            if self._gdict[section].get(position) == None:
                raise SectionException
            if reference:
                # Remove an option if it has a certain assigned value. We want
                # to do this when removing a reference.
                self.remove_option(section, option, value=value,
                                  position=position)
                #print 'Remove', option, 'from', section, 'position', position
            else:
                # value has to be set to None, however there is no way to do
                # so other than this since add_option() cannot be called with
                # value=None. Hence the need for this ugly nested if-block.
                self.remove_option(section, option, position=position)
        else:
            #print 'Remove', option, 'from all', section
            self.remove_option(section, option)
        if option_type == None:
            if reference == None:
                toadd = ('\t' + option + '\t' + prefix + str(value) + prefix
                         + '\n')
            else:
                if section.strip().lower() not in refSections:
                    # e.g. Screen "New Screen"
                    toadd = ('\t' + option + '\t' + prefix + str(value)
                             + prefix + '\n')
                else:
                    # e.g. Screen 0
                    # which is used for Xinerama setups in the Device section
                    toadd = '\t' + option + '\t' + str(value) + '\n'
        else:
            toadd = ('\t' + option_type + '\t' + '"' + option + '"' + '\t'
                     + prefix + str(value) + prefix + '\n')
                    
        if len(self._gdict[section]) == 0:
            self._gdict[section] = {}
            self._gdict[section][0] = []
            if section in self.require_id:
                identifier = '\tIdentifier\t"Default ' + section + '"\n'
                self._gdict[section][0].append(identifier)
        if position == None:
            for elem in self._gdict[section]:
                self._gdict[section][elem].append(toadd)
        else:
            self._gdict[section][position].append(toadd)
        
    def _get_options_to_blacklist(self, section, option, value=None,
                                  position=None, reference=None):
        '''Private method shared by remove_option and comment_out_option'''
        to_remove = {}
        if len(self._gdict[section]) != 0:#if the section exists

            if position == None:
                #print 'Removing', option, 'from all', section, 'sections'
                for elem in self._gdict[section]:
                    it = 0
                    for line in self._gdict[section][elem]:
                        if value != None:
                            #print 'line =', line, 'option=', option, 'value',
                            # value
                            if (line.lower().find(option.lower()) != -1
                            and line.lower().find(value.lower()) != -1):
                                to_remove.setdefault(elem, []).append(it)
                        else:
                            if line.lower().find(option.lower()) != -1:
                                to_remove.setdefault(elem, []).append(it)
                        it += 1
            else:
                if self._gdict[section].get(position) == None:
                    return
                else:
                    #print 'Removing', option, 'from', section, 'position',
                    # position
                    it = 0
                    for line in self._gdict[section][position]:
                        if value != None:
                            # Remove the option only if it has a certain value
                            # assigned. This is useful in case we want to
                            # remove a reference to a certain Section from
                            # another section:
                            # e.g. Screen "Generic Screen".
                            if (line.lower().find(option.lower()) != -1
                            and line.lower().find(value.lower()) != -1):
                                to_remove.setdefault(position, []).append(it)
                        else:
                            # Remove the option without caring about the
                            # assigned value
                            if line.lower().find(option.lower()) != -1:
                                to_remove.setdefault(position, []).append(it)
                        it += 1
        return to_remove
        
    def remove_option(self, section, option, value=None, position=None,
                     reference=None):
        '''Remove an option from a section.
        
        section= the section which will have the option removed
        option= the option to remove
        value= if you want to remove an option only if it has a certain value
        position= e.g. 0 (i.e. the first element in the list of Screen
                      sections)'''
        
        to_remove = self._get_options_to_blacklist(section, option, value,
                                                  position, reference)
        for part in to_remove:
            modded = 0
            for line in to_remove[part]:
                realpos = line - modded
                del self._gdict[section][part][realpos]
                modded += 1

    def make_section(self, section, identifier=None):
        '''Create a new section and return the position of the section

        The position is relative to the list of sections of the same type
        (e.g. "Screen") so as to make it available in case the user wants
        to add some options to it.
        
        The identifier and the position of the new section is added to 
        self.identifiers[section]
        
        section= the section to create
        identifier= the identifier of a section (if the section requires
                    an identifier)'''

        position  = len(self._gdict[section])

        if section in self.require_id:
            if identifier != None:
                option = 'Identifier'
                # Don't create a new section if one of the same kind and
                # with the same 'Identifier' is found
                create = True
                for sub in self._gdict[section]:
                    if self.get_value(section, option, sub):
                        try:
                            if (self.get_value(section,
                                              option,
                                              sub).strip().lower()
                                              == identifier.strip().lower()):
                                create = False
                                break
                        except AttributeError:
                            for elem in self.get_value(section, option, sub):
                                #print 'elem=', elem, 'id=', identifier
                                if (elem.strip().lower()
                                    == identifier.strip().lower()):
                                    create = False
                                    break
                
                if create:
                    self._gdict[section][position] = []
                    self.add_option(section, option, value=identifier,
                                    position=position)
                    # Add to identifiers
                    self.identifiers[section].append((identifier, position))
                    #print 'Created section', section, 'id =', identifier,
                    #      'position =', position
                #else:
                    #print section, 'Section labelled as', identifier,
                    #'already exists. None will be created.'
            else:
                raise IdentifierException(('%s Section requires an identifier'
                                           %(section)))
        else:
            self._gdict[section][position] = []
        return position
    
    def remove_section(self, section, identifier=None, position=None):
        '''Remove Sections by identifier, position or type'''
        # Remove any section of "section" type with the same identifier
        # currently sections of the same type cannot have the same id
        # for obvious reasons
        to_remove = {}
        if identifier:
            try:
                pos = self.get_position(section, identifier)
                to_remove.setdefault(pos, None)
            except IdentifierException:
                pass
                    
        # Comment the section of "section" type at position "position"
        elif position != None:
            if self.is_section(section, position=position):
                to_remove.setdefault(position, None)

        # Comment any section of "section" type
        else:
            allkeys = list(self._gdict[section].keys())
            to_remove = {}.fromkeys(allkeys)

        # If the section has an identifier i.e. if the section
        # is in self.require_id
        if section in self.require_id:
            # Get the references to remove from self.identifiers 
            it = 0
            for reference in self.identifiers[section]:
                try:
                    ref = list(to_remove.keys()).index(reference[1])
                    to_remove[list(to_remove.keys())[ref]] = it
                except ValueError:
                    pass
                it += 1

        sorted_remove = list(to_remove.keys())
        sorted_remove.sort()

        modded = 0
        for sect in sorted_remove:
            subsections = self.get_subsections(section, sect)

            # Remove all its SubSections from SubSection
            for sub in subsections:
                try:#remove subsection
                    del self._gdict[self.subsection][sub]
                except KeyError:
                    pass

            # Remember to remove any related entry from the "Comments"
            # section
            self._remove_comment_entries(section, sect)
        
            # Remove the section from _gdict
            del self._gdict[section][sect]
            
            # Remove the reference from identifiers
            # if such reference exists
            identref = to_remove[sect]
            if identref != None:
                realpos = identref - modded

                del self.identifiers[section][realpos]
                modded += 1


    def add_reference(self, section, reference, identifier, position=None):
        '''Add a reference to a section from another section.

        For example:
        to put a reference to the Screen section named "Default Screen"
        in the ServerLayout section you should do:

        section='ServerLayout'
        reference='Screen'
        identifier='Default Screen'
        position=0 #the first ServerLayout section

        NOTE: if position is set to None it will add such reference to any
        instance of the section (e.g. to any ServerLayout section)'''

        self.add_option(section, reference, value=identifier,
                        position=position, reference=True)

    def remove_reference(self, section, reference, identifier, position=None):
        '''Remove a reference to a section from another section.

        For example:
        to remove a reference to Screen "Default Screen" from the
        ServerLayout section you should do:

        section='ServerLayout'
        reference='Screen'
        identifier='Default Screen'
        position=0 #the first ServerLayout section

        NOTE: if position is set to None it will remove such reference from
        any instance of the section (e.g. from any ServerLayout section)'''

        self.remove_option(section, reference, value=identifier,
                           position=position, reference=True)

    def get_references(self, section, position, reflist=None):
        '''Get references to other sections which are located in a section.

        section= the section (e.g. "Screen")
        position= e.g. 0 stands for the 1st Screen section
        reflist= a list of references which this function should look for.
                 The default list of references is self.require_id but this
                 list can be overridden by the reflist argument so that, for
                 example, if reflist is set to ['Device'], this function will
                 look for references to other devices only (references to,
                 say, screens, will be ignored).'''

        if reflist == None:
            options = self.require_id
        else:
            # if the following operation fails
            # an AttributeError will be raised
            # since reflist must be a list
            reflist.append('')
            del reflist[-1]
            options = reflist
        references = {}.fromkeys(options)
        for option in options:
            references[option] = []
            reference_dict = {}
            try:
                ref = self.get_value(section, option, position, reference=True)
            except OptionException:
                ref = []
            if ref:
                try:#if ref is already a list
                    ref.append('')
                    del ref[-1]
                    
                    for elem in ref:
                        try:
                            elem.append('')
                            del elem[-1]
                            for extref in elem:
                                if elem:
                                    reference_dict.setdefault(extref)
                        except AttributeError:# if ref is a string
                            if elem:
                                reference_dict.setdefault(elem)
                except AttributeError:# if ref is a string
                    if ref:
                        reference_dict.setdefault(ref)
                for reference in list(reference_dict.keys()):
                    references[option].append(reference)
        return references

    def make_subsection(self, section, identifier, position=None):
        '''Create a new subsection inside of a section.

        section= the section to which the subsection will belong
        identifier= the name of the subsection
        position= the position of the section in the dictionary with the
                  sections (e.g. the 1st "Screen" section would be 0).
                  If set to None, it will create a new subsection in all
                  the instances of the said section (e.g. in all the
                  "Screen" sections)'''

        curlength = len(self._gdict[self.subsection])

        if position == None:
            for elem in self._gdict[section]:
                # don't create a new subsection if one with the same
                # 'section', 'identifier' and 'position' is found
                create = True
                for sub in self._gdict[self.subsection]:
                    if (self._gdict[self.subsection][sub].get('section')  ==
                        section and 
                        self._gdict[self.subsection][sub].get('identifier') ==
                        identifier and
                        self._gdict[self.subsection][sub].get('position') ==
                        elem):
                        create = False

                if create:
                    temp_dict = self._gdict[self.subsection][curlength] = {}
                    temp_dict['section'] = section
                    temp_dict['identifier'] = identifier
                    temp_dict['options'] = []
                    temp_dict['position'] = elem
                    del temp_dict
                    curlength += 1
        else:
            # don't create a new subsection if one with the same
            # 'section', 'identifier' and 'position' is found
            create = True
            for sub in self._gdict[self.subsection]:
                if (self._gdict[self.subsection][sub].get('section') ==
                    section and
                    self._gdict[self.subsection][sub].get('identifier') ==
                    identifier and
                    self._gdict[self.subsection][sub].get('position') ==
                    position):
                    create = False

            if create:
                temp_dict = self._gdict[self.subsection][curlength] = {}
                temp_dict['section'] = section
                temp_dict['identifier'] = identifier
                temp_dict['options'] = []
                temp_dict['position'] = position
                del temp_dict

    def remove_subsection(self, section, identifier, position=None):
        '''Remove a subsection from one or more sections.
        
        section= the section to which the subsection belongs
        identifier= the name of the subsection
        position= the position of the section in the dictionary with the
                  sections (e.g. the 1st "Screen" section would be 0).
                  If set to None it will remove a subsection from all the
                  instances of the said section (e.g. in all the "Screen"
                  sections)'''
        
        curlength = len(self._gdict[self.subsection])
        to_remove = []
        if position == None:
            for elem in self._gdict[self.subsection]:
                if (self._gdict[self.subsection][elem].get('section') ==
                    section and
                    self._gdict[self.subsection][elem].get('identifier') ==
                    identifier):
                    to_remove.append(elem)
        else:
            for elem in self._gdict[self.subsection]:
                if (self._gdict[self.subsection][elem].get('section') ==
                    section and
                    self._gdict[self.subsection][elem].get('identifier') ==
                    identifier and
                    self._gdict[self.subsection][elem].get('position') ==
                    position):
                    to_remove.append(elem)
        for item in to_remove:
            del self._gdict[self.subsection][item]

    def add_suboption(self, section, identifier, option, value,
                      option_type=None, position=None):
        '''Add an option to one or more subsections.
        
        section= the section which contains the subsection
        identifier= the identifier of the SubSection (e.g. Display)
        option= the option to add
        value= the value which will be assigned to the option
        option_type= if set to "Option" it will cause the option to look like
                     the following:
                     Option "NameOfTheOption" "Value"
                    
                     Otherwise it will look like the following:
                     NameOfTheOption "Value"
        position= e.g. 0 (i.e. the option will be added to a subsection which
                  is located in the first element in the list of Screen
                  sections)'''

        prefix = '"'
        not_to_create = []
        to_modify = []
        if position == None:
            self.remove_suboption(section, identifier, option)
        else:
            self.remove_suboption(section, identifier, option,
                                 position=position)
        if option_type == None:
            toadd = '\t' + option + '\t' + str(value) + '\n'
        else:
            toadd = ('\t' + option_type + '\t' + prefix + option + prefix +
                     '\t' + prefix + str(value) + prefix + '\n')

        curlength = len(self._gdict[self.subsection])
        if curlength == 0:
            self._gdict[self.subsection][0] = {'section': section,
            'identifier': identifier, 'options': []}

        if position == None:
            # if there is not a subsection for each selected section then
            # create it
            cursect_length = len(self._gdict[section])
            it = 0
            while it < cursect_length:
                for elem in self._gdict[self.subsection]:
                    if (self._gdict[self.subsection][elem].get("position") ==
                        it and
                        self._gdict[self.subsection][elem].get("section") ==
                        section and
                        self._gdict[self.subsection][elem].get("identifier") ==
                        identifier):
                        not_to_create.append(it)
                it += 1
            for i in range(cursect_length + 1):
                if i not in not_to_create:
                    self.make_subsection(section, identifier, position=i)

            for elem in self._gdict[self.subsection]:
                if (self._gdict[self.subsection][elem].get("identifier") ==
                    identifier and
                    self._gdict[self.subsection][elem].get("section") ==
                    section):
                    to_modify.append(elem)
        else:
            for elem in self._gdict[self.subsection]:
                if (self._gdict[self.subsection][elem].get("position") ==
                    position and
                    self._gdict[self.subsection][elem].get("identifier") ==
                    identifier):
                    to_modify.append(elem)
            if len(to_modify) == 0:
                curlength = len(self._gdict[self.subsection])
                self._gdict[self.subsection][
                len(self._gdict[self.subsection])] = \
                {'section': section, 'identifier': identifier,
                 'options': [], 'position': position}
                to_modify.append(curlength)

        for elem in to_modify:
            self._gdict[self.subsection][elem]['options'].append(toadd)


    def _get_suboptions_to_blacklist(self, section, identifier, option,
                                     position=None):
        '''Get a dictionay of the suboptions to blacklist.

        See add_suboption() for an explanation on the arguments.

        Used in both remove_option() and remove_suboption()'''
        to_remove = {}
        if len(self._gdict[section]) != 0:#if the section exists
            if len(self._gdict[self.subsection]) != 0:
                for elem in self._gdict[self.subsection]:
                    temp_elem = self._gdict[self.subsection][elem]
                    if position == None:
                        if (temp_elem.get('section') == section and
                            temp_elem.get('identifier') == identifier):
                            it = 0
                            for opt in temp_elem['options']:
                                if (opt.strip().lower()
                                    .find(option.strip().lower()) != -1):
                                    to_remove.setdefault(elem, []).append(it)
                                it += 1
                    else:
                        if (temp_elem.get('section') == section and
                            temp_elem.get('identifier') == identifier and
                            temp_elem.get('position') == position):
                            it = 0
                            for opt in temp_elem['options']:
                                if (opt.strip().lower()
                                    .find(option.strip().lower()) != -1):
                                    to_remove.setdefault(elem, []).append(it)
                                it += 1
                    del temp_elem
        return to_remove


    def remove_suboption(self, section, identifier, option, position=None):
        '''Remove an option from a subsection.'''

        to_remove = self._get_suboptions_to_blacklist(section, identifier,
                                                      option, position)
        for elem in to_remove:
            modded = 0
            for part in to_remove[elem]:
                real_pos = part - modded
                del self._gdict[self.subsection][elem]['options'][real_pos]
                modded += 1

    def get_identifier(self, section, position):
        '''Get the identifier of a specific section from its position.'''

        error_msg = ('No identifier can be found for section "%s" No %d'
                    % (section, position))
        try:
            for sect in self.identifiers[section]:
                if sect[1] == position:
                    return sect[0]
        except KeyError:
            raise SectionException
        raise IdentifierException(error_msg)


    def _clean_option(self, option, optname, reference=None, section=None):
        '''Clean the option and return the value

        This returns the last item of the list which this method generates.

        If no value can be found, return False.'''

        if reference:
            # If it's a reference to another section then options such as
            # Option  "Device"  "/dev/psaux" should not be taken into
            # account.
            if 'option' in option.strip().lower():
                return False

            # Do not confuse Device "Configure device" with InputDevice
            # "device"
            if not option.strip().lower().startswith(optname.strip().lower()):
                return False

        optbits = []
        optbit = ''
        it = 0
        quotation = 0
        optcount = option.count('"')
        if optcount > 0:#dealing with a section option
            for i in option:
                if optcount in [2, 4] and section == 'ServerLayout':
                    if not i.isspace():
                        if i == '"':
                            if quotation != 0 and quotation % 2 != 0:
                                if len(optbit) > 0:
                                    optbits.append(optbit)
                                    optbit = ''
                            quotation += 1
                        else:
                            if quotation % 2 != 0:
                                optbit += i
                    else:    
                    
                        if quotation % 2 != 0:
                            optbit += i
                else:
                    #print 'i', repr(i), 'optbit', optbit
                    if not i.isspace():
                        if i == '"':
                            quotation += 1
                        else:
                            optbit += i
                    else:    
                    
                        if quotation % 2 != 0:
                            optbit += i
                            
                        else:
                            if len(optbit) > 0:
                                optbits.append(optbit)
                                #print 'i=', i, 'optbit=', optbit
                                optbit = ''

                if it == len(option) - 1:
                    if optbit != '':
                        optbits.append(optbit)
                        #print 'i=END', 'optbit=', optbit
                it += 1            
        else:#dealing with a subsection option
            for i in option:
                #print 'i', repr(i), 'optbit', optbit
                if not i.isspace():
                    optbit += i
                else:    
                    if len(optbit) > 0:
                        optbits.append(optbit)
                        #print 'i=', i, 'optbit=', optbit
                        optbit = ''
                        
                if it == len(option) - 1:
                    if optbit != '':
                        optbits.append(optbit)
                        #print 'i=END', 'optbit=', optbit
                it += 1

        optlen = len(optbits)

        if optlen > 1:
            # Let's make sure that the option is the one we're looking for
            # e.g. if we're looking for a reference to Device we are not
            # interested in getting references to InputDevice

            references_list = [x.lower().strip() for x in self.references]

            if (section != 'ServerLayout' and
                quotation == 0 and optlen == 2 and
                optbits[0].lower().strip() in references_list):
                # e.g. Screen 1 -> 1 stands for the position, therefore the 
                # identifier of the section at position 1 should be returned
                # instead of the number (if possible).
                # 
                # return [Screen, identifier]
                try:
                    sect = ''
                    value = int(optbits[1].strip())
                    for item in self.require_id:
                        if optbits[0].lower().strip() == item.lower().strip():
                            sect = item
                            break
                    try:                     
                        identifier = self.get_identifier(sect, value)
                        return [identifier]
                    except (IdentifierException):
                        return False
                except ValueError:
                    pass

            if optcount != 4 and section != 'ServerLayout':
                status = False
                for elem in optbits:
                    if elem.lower() == optname.lower():
                        status = True
                if status == False:
                    return False

            if optlen == 2 and optbits[0].lower().strip() == 'option':
                # e.g. Option "AddARGBGLXVisuals"
                # (The value was omitted but it will be interpreted as True by
                # Xorg)
                return 'True'

            sections = [sect.strip().lower() for sect in self.sections]

#            if optlen == 2 and optbits[0].lower().strip() in sections:
#                # Do not confuse Device "Configure device" with InputDevice
#                # "device"
#                if optbits[0].lower().strip() != optname.strip().lower():
#                    return False

            if optcount == 4 and section == 'ServerLayout':
                #If it's something like InputDevice "stylus" "SendCoreEvents"
                if (optname.lower().strip() == 'inputdevice' and
                    len(optbits) == 2):
                    del optbits[1]
                server_dict = {}
                for elem in optbits:
                    server_dict.setdefault(elem)
                return list(server_dict.keys())
            elif optcount > 0 and optcount <= 4:
                #dealing with a section option
                return optbits[optlen -1]
            elif optcount > 4:
                del optbits[0]
                return optbits
            elif optcount == 0:
                del optbits[0]
                return ' '.join(optbits)
        else:
            if optcount in [2, 4] and section == 'ServerLayout':
                return optbits
            return False

    def get_value(self, section, option, position, identifier=None,
                  sect=None, reference=None):
        '''Get the value which is assigned to an option.

        Return types:
          * string (if only one value is available)
            - usually in options
          * list (if more than one option is found)
            - having multiple references of the same type is allowed.
              for example it is not unusual to have 2 references to
              Screen sections in the ServerLayout section (in case of
              Xinerama)
            - if the options are actually options and not references
              then there are duplicate options, which should be detected
              in advance with get_duplicate_options()   
          * None (if no value can be found) - Not always true -> See below.

        Use-case for returning None
          * When dealing with incomplete references. For example:
                Screen "Configured Screen"
              is different from:
                Screen
                (which is an incomplete reference)
          * When dealing with incomplete options. For example:
                Depth 24
              is different from:
                Depth
                (which is an incomplete option)
          * Exception:
              Some options (with the "Option" prefix) (not references)
              can be used with no value (explicitly) assigned and are
              considered as True by the Xserver. In such case get_value()
              will return "True". For example:
                Option "AddARGBGLXVisuals" 
              is the same as:
                Option "AddARGBGLXVisuals" "True"

        Meaning of keys in Sections and SubSections:
          * When dealing with a Section:
              section= e.g. 'Screen', 'Device', etc.
              option= the option
              position= e.g. 0 (i.e. the first element in the list of Screen
                        sections)
              reference= used only by get_references()

          * When dealing with a SubSection:
              section= 'SubSection' (this is mandatory)
              option= the option
              position= e.g. 0 would mean that the subsection belongs to 
                        the 1st item of the list of, say, "Screen" sections.
                        (i.e. the first element in the list of Screen 
                        sections)
                        ["position" is a key of an item of the list of 
                        subsections see below]
              identifier= the name of the subsection e.g. 'Display'
              sect = the 'section' key of an item of the list of 
                     subsections e.g. the "Display" subsection can be 
                     found in the "Screen" section ('sect' is the latter)

        Anatomy of Sections and SubSections:
          * Anatomy of subsections:
              self.globaldict['SubSection'] =
                  {0: {'section': 'Screen', 'identifier': 'Display', 
                   'position': 0, 'options': [option1, option2, etc.], 
                   etc.}
                  In this case we refer to the 'Display' subsection 
                  which is located in the first 'Screen' section.

          * Anatomy of a section:
              self.globaldict['Screen'] =
                  {0: [option1, option2, etc.], 1: [...], ...}
              0, 1, etc. is the position '''

        values = []

        if self._gdict[section].get(position) == None:
            raise SectionException

            #if len(values) == 0:
                #raise OptionException

            #return values

        else:
            try:
                # see if it's a dictionary (e.g. in case of a subsection)
                # or a list (in case of a normal section) and act
                # accordingly
                self._gdict[section][position].index('foo')
            except AttributeError:#dict
                if identifier == None:
                    raise Exception('An identifier is required for '
                                    'subsections')
                else:
                    for elem in self._gdict[section]:
                        if (self._gdict[section][elem].get('identifier') ==
                            identifier and
                            self._gdict[section][elem].get('position') ==
                            position and
                            self._gdict[section][elem].get('section') == sect):
                            for opt in self._gdict[section][elem]['options']:
                                if (option.strip().lower() in
                                    opt.strip().lower()):
                                    if opt.strip().find('#') != -1:
                                        stropt = opt.strip()[0: opt
                                                            .strip().find('#')]
                                    else:
                                        stropt = opt.strip()
                                    # clean the option and return the value
                                    values.append(self._clean_option(stropt,
                                                  option, reference=reference))

                    if len(values) == 0:
                        raise OptionException

                    if len(values) > 1:
                        return values
                    else:
                        try:
                            return values[0]
                        except IndexError:
                            return None

            except ValueError:#list
                for elem in self._gdict[section][position]:
                    if option.strip().lower() in elem.strip().lower():
                        # clean the option and return the value
                        if elem.strip().find('#') != -1:
                            stropt = elem.strip()[0: elem.strip().find('#')]
                        else:
                            stropt = elem.strip()
                        values.append(self._clean_option(stropt, option,
                                      reference=reference, section=section))

                if len(values) == 0:
                    raise OptionException

                if len(values) > 1:
                    return values
                else:
                    try:
                        return values[0]
                    except IndexError:
                        return None
            except KeyError:#not found
                raise OptionException

    def is_section(self, section, identifier=None, position=None):
        '''See if a section with a certain identifier exists.

        NOTE: either identifier or position must be provided.'''

        if identifier != None:
            try:
                self.get_position(section, identifier)
                return True
            except IdentifierException:
                return False
        elif position != None:
            return self._gdict[section].get(position) != None
        else:
            error_msg = 'Either identifier or position must be provided'
            raise Exception(error_msg)
    
    def get_position(self, section, identifier):
        '''Get the position of a specific section from its identifier.'''

        error_msg = ('No %s section named "%s" can be found' %
                     (section, identifier))
        for sect in self.identifiers[section]:
            try:
                if sect[0].strip().lower() == identifier.strip().lower():
                    return sect[1]
            except AttributeError:
                pass
        raise IdentifierException(error_msg)

    def get_broken_references(self):
        '''Look for references to sections which don't exist

        This returns a dictionary having the items of self.require_id as keys
        and a dictionary with the identifiers of the sections which are
        being referred to by the broken references.

        For example:

        broken_references = {
                            'InputDevice': {'InputDevice 1': None,
                                            'Another input device': None},
                            'Device': {...},
                            'Monitor' {...},
                            'Screen' {...},
                            'ServerLayout' {...}
                            }'''

        broken_references = {}.fromkeys(self.require_id)
        references_tree = {}
        for section in self.require_id:#['Screen', 'ServerLayout']
            references_tree[section] = {}
            broken_references[section] = {}
            for sect in self._gdict[section]:
                references_tree[section][sect] = self.get_references(section,
                                                                     sect)
        #print >> stderr, 'REFERENCES = %s' % (str(references_tree))
        for section in references_tree:
            for elem in references_tree[section]:
                for refsect in references_tree[section][elem]:
                    if len(references_tree[section][elem][refsect]) > 0:
                        #references_tree[section][elem][refsect]
                        for ref in references_tree[section][elem][refsect]:
                            for sect in self.sections:
                                if sect.lower() == refsect.strip().lower():
                                    refsect = sect
                            if not self.is_section(refsect, ref):
                                #print '*****WARNING:', refsect, 'Section',
                                # ref, 'does not exist!*****'
                                broken_references[refsect].setdefault(ref)
                                #print 'FIX: Creating', refsect, 'Section',
                                # ref self.make_section(refsect,
                                # identifier=ref)
        return broken_references


    def get_default_serverlayout(self):
        '''Return a list with the position of default ServerLayout sections

        NOTE: If the section set as the default ServerLayout doesn't exist
              it will raise a ParseException.'''

        default = []
        serverflags = self._gdict['ServerFlags']
        it = 0
        for flag in serverflags:
            try:
                default_layout = self.get_value('ServerFlags',
                                               'DefaultServerLayout', it)
                if default_layout:
                    def_it = 0
                    for identifier in self.identifiers['ServerLayout']:
                        if (identifier[0].lower().strip() ==
                            default_layout.lower().strip()):
                            default.append(identifier[1])#LayoutPosition
                            def_it += 1
                    if def_it == 0:
                        # If the section set as the default ServerLayout
                        # doesn't exist raise a ParseException
                        error = 'The default ServerLayout does not exist.'
                        raise ParseException(error)
            except OptionException:#no default_layout
                pass
            it += 1
        return default


    def _merge_subsections(self, temp_dict):
        '''Put SubSections back into the sections to which they belong.'''

        for sect in temp_dict['SubSection']:
            section = temp_dict['SubSection'][sect]['section']
            identifier = temp_dict['SubSection'][sect]['identifier']
            position = temp_dict['SubSection'][sect].get('position')
            options = temp_dict['SubSection'][sect]['options']
            temp_dict[section].setdefault(position, []).append(
                                                            '\tSubSection ' +
                                                            '"' + identifier +
                                                            '"' + '\n')
            if len(options) > 0:
                temp_dict[section][position].append('\t' +
                                                    '\t'.join(options) +
                                                    '\tEndSubSection\n')
            else:
                temp_dict[section][position].append('\t'.join(options) +
                                                    '\tEndSubSection\n')
        try:
            #remove subsection since it was merged
            del temp_dict['SubSection']
        except KeyError:
            pass

        return temp_dict


    def write(self, destination, test=None):
        '''Write the changes to the destination

        The destination can be either a file (e.g. /etc/X11/xorg.conf)
        or a file object (e.g. sys.stdout).

        destination = the destination file or file object (mandatory)
        test = if set to True write will append the result to the
               destination file instead of overwriting it. It has no
               effect on file objects. Useful for testing.'''

        temp_dict = copy.deepcopy(self._gdict)

        # Commented options must be dealt with first
        temp_dict = self._merge_commented_options(temp_dict)

        # Merge all the non-commented subsections
        temp_dict = self._merge_subsections(temp_dict)
        lines = []
        comments = ''.join(self.comments) + '\n'
        lines.append(comments)
        for section in temp_dict:
            if section != self.commentsection:
                if len(temp_dict[section]) > 0:
                    for elem in temp_dict[section]:
                        lines.append('Section ' + '"' + section + '"' + '\n')
                        lines.append(''.join(temp_dict[section][elem]) +
                                     'EndSection\n\n')

        del temp_dict

        if not hasattr(destination, 'write'):#it is a file
            if test:
                destination = open(destination, 'a')
            else:
                destination = open(destination, 'w')
            destination.write(''.join(lines))
            destination.close()
        else:#it is a file object
            try:
                destination.write(str(bytes(''.join(lines), 'UTF-8')))
            except TypeError:
                destination.write(b''.join(lines))

    def get_subsections(self, section, position):
        '''Get all the subsections contained in a section'''
        # loop through subsections and see what subsections match
        # the section
        subsections = []
        for sub in self._gdict[self.subsection]:
            if (self._gdict[self.subsection][sub]['section'] == section
                and self._gdict[self.subsection][sub]['position'] == position):
                subsections.append(sub)

        return subsections

    def _permanent_merge_subsections(self, subsections):
        '''Put SubSections back into their sections and comment them out

        This alters globaldict and should be used only in
        comment_out_section() i.e. when the whole section is being
        commented out.

        subsections = the list of the indices subsections to merge and
        remove'''

        for sect in subsections:
            section = self._gdict[self.subsection][sect]['section']
            identifier = self._gdict[self.subsection][sect]['identifier']
            position = self._gdict[self.subsection][sect].get('position')
            options = self._gdict[self.subsection][sect]['options']
            self.comments.append('#\tSubSection ' + '"' + identifier + '"' +
                                 '\n')

            for option in options:
                opt = '#\t\t%s\n' % (option.strip())
                self.comments.append(opt)
                self.comments.append('#\tEndSubSection\n')

            try:#remove subsection since it was merged
                del self._gdict[self.subsection][sect]
            except KeyError:
                pass

    def _get_comments(self, section, position):
        '''Return the index of the entry in the Comments section of a section'''

        comments = []
        if self._gdict[self.commentsection].get(section):
            for sect in self._gdict[self.commentsection][section]:
                if (self._gdict[self.commentsection][section][sect]
                    .get('position') == position):
                    comments.append(sect)

        return comments

    def _merge_subsections_with_comments(self, subsections):
        '''Put SubSections back into their sections and comment them out

        This alters globaldict and should be used only to comment out
        subsections (i.e. in comment_out_subsection()) when the whole section
        is not being commented out.

        subsections = the list of the indices subsections to merge and
                      remove'''

        end_subsection = '#\tEndSubSection\n'

        for sect in subsections:
            section = self._gdict[self.subsection][sect]['section']
            identifier = self._gdict[self.subsection][sect]['identifier']
            position = self._gdict[self.subsection][sect].get('position')
            options = self._gdict[self.subsection][sect]['options']

            start_subsection = '#\tSubSection "%s"\n' % (identifier)

            comments = self._get_comments(section, position)
            if not comments:
                self._gdict[self.commentsection][section] = {}
                self._gdict[self.commentsection][section][position] = {}
                temp_dict = self._gdict[self.commentsection][section][position]
                temp_dict['identifier'] = None
                temp_dict['position'] = position
                temp_dict['section'] = None
                temp_dict['options'] = []
                del temp_dict

            comments_options = self._gdict[self.commentsection][section
                                           ][position]['options']

            comments_options.append(start_subsection)
            for option in options:
                opt = '#\t\t%s\n' % (option.strip())
                comments_options.append(opt)

            comments_options.append(end_subsection)

            #remove subsection since it was merged
            del self._gdict[self.subsection][sect]

    def _comment_out_subsections(self, section, position):
        '''Comment out all the subsections of a section.'''

        subsections = self.get_subsections(section, position)
        self._permanent_merge_subsections(subsections)

    def _remove_comment_entries(self, section, position):
        '''Remove comment sections of a "section" from the "Comments" section'''

        comments = self._get_comments(section, position)
        for comment_section in comments:
            del self._gdict[self.commentsection][section][comment_section]

    def comment_out_section(self, section, identifier=None, position=None):
        '''Comment out a section and all its subsections.'''

        start_section = '\n#Section "%s"\n' % (section)
        end_section = '#EndSection\n'

        # Comment any section of "section" type with the same identifier
        #   currently sections of the same type cannot have the same id
        #   for obvious reasons
        to_remove = {}
        if identifier:
            try:
                pos = self.get_position(section, identifier)
                to_remove.setdefault(pos, None)
            except IdentifierException:
                pass

        # Comment the section of "section" type at position "position"
        elif position != None:
            if self.is_section(section, position=position):
                to_remove.setdefault(position, None)

        # Comment any section of "section" type
        else:
            all_keys = list(self._gdict[section].keys())
            to_remove = {}.fromkeys(all_keys)

        # If the section has an identifier i.e. if the section
        # is in self.require_id
        if section in self.require_id:
            # Get the references to remove from self.identifiers 
            it = 0
            for reference in self.identifiers[section]:
                try:
                    ref = list(to_remove.keys()).index(reference[1])
                    to_remove[list(to_remove.keys())[ref]] = it
                except ValueError:
                    pass
                it += 1

        sorted_remove = list(to_remove.keys())
        sorted_remove.sort()

        modded = 0
        for sect in sorted_remove:
            self.comments.append(start_section)
            for option in self._gdict[section][sect]:
                commented_option = '#\t%s\n' % (option.strip())
                self.comments.append(commented_option)

            # Append all its SubSections (automatically commented
            #  out) and remove them from SubSection
            self._comment_out_subsections(section, sect)
            self.comments.append(end_section)

            # Remember to remove any related entry from the "Comments"
            # section
            self._remove_comment_entries(section, sect)

            # Remove the section from _gdict
            del self._gdict[section][sect]

            # Remove the reference from identifiers
            # if such reference exists
            ident_ref = to_remove[sect]
            if ident_ref != None:
                realpos = ident_ref - modded

                del self.identifiers[section][realpos]
                modded += 1


    def comment_out_subsection(self, section, identifier, position):
        '''Comment out a subsection.

        section= the type of the section which contains the subsection
        identifier= the identifier of the subsection
        position= the position of the section'''

        subsections = []
        for subsection in self._gdict[self.subsection]:
            temp_dict = self._gdict[self.subsection][subsection]
            if (temp_dict['section'] == section
            and temp_dict['identifier'] == identifier
            and temp_dict['position'] == position):
                subsections.append(subsection)
                break
            del temp_dict
        # Add the subsection to the Comments section
        self._merge_subsections_with_comments(subsections)


    def comment_out_option(self, section, option, value=None, position=None,
                           reference=None):
        '''Comment out an option in a section.

        section= the section which will have the option commented out
        option= the option to comment out
        value= if you want to comment out an option only if it has a
               certain value
        position= e.g. 0 (i.e. the first element in the list of Screen
                      sections)'''

        to_remove = self._get_options_to_blacklist(section, option, value,
                                                   position, reference)
        for part in to_remove:
            modded = 0
            for line in to_remove[part]:
                realpos = line - modded
                self._gdict[section][part][realpos] = ('#%s'
                     % (self._gdict[section][part][realpos].strip()))
                
                self._gdict[self.commentsection].setdefault(section, {})
                curlength = len(self._gdict[self.commentsection][section])
                temp_dict = self._gdict[self.commentsection][section]
                temp_dict.setdefault(part, {})
                temp_dict[part].setdefault('identifier', None)
                temp_dict[part].setdefault('position', part)
                temp_dict[part].setdefault('section', None)
                temp_dict[part].setdefault('options', [])
                # Copy the option to the Comments section
                temp_dict[part]['options'].append(
                                          self._gdict[section][part][realpos])
                del temp_dict

                #Remove it from its section in _gdict
                del self._gdict[section][part][realpos]

                modded += 1


    def comment_out_suboption(self, section, identifier, option, position=None):
        '''Comment out an option in a subsection.

        section= the section which contains the subsection
        identifier= the identifier of the subsection
        option= the option to comment out
        position= the position of the section which contains the subsection
                  e.g. 0 (i.e. the first element in the list of Screen
                  sections)'''

        to_remove = self._get_suboptions_to_blacklist(section, identifier,
                                                      option, position)
        for elem in to_remove:
            modded = 0
            for part in to_remove[elem]:
                realpos = part - modded
                
                self._gdict[self.subsection][part]['options'][realpos] = ('#%s'
                    % (self._gdict[self.subsection][part]['options'][realpos]
                    .strip()))

                self._gdict[self.commentsection].setdefault(self.subsection,
                                                            {})
                temp_dict = self._gdict[self.commentsection][self.subsection]

                temp_dict.setdefault(part, {})
                temp_dict[part].setdefault('identifier', identifier)
                temp_dict[part].setdefault('position', part)
                temp_dict[part].setdefault('section', section)
                temp_dict[part].setdefault('options', [])
                # Copy the option to the Comments section
                comments_options = temp_dict[part]['options']
                commented_option = self._gdict[self.subsection][part][
                                              'options'][realpos]
                comments_options.append(commented_option)

                del temp_dict

                #Remove the option from its section in _gdict
                del self._gdict[self.subsection][elem]['options'][realpos]
                modded += 1


    def _merge_commented_options(self, temp_dict):
        '''Put commented out options back into their sections or subsections'''
        
        for sect in temp_dict[self.commentsection]:
            section_options = None
            for section_instance in temp_dict[self.commentsection][sect]:
                section = temp_dict[self.commentsection][sect][
                                    section_instance].get('section')
                identifier = temp_dict[self.commentsection][sect][
                                       section_instance].get('identifier')
                position = temp_dict[self.commentsection][sect][
                                     section_instance].get('position')
                options = temp_dict[self.commentsection][sect][
                                    section_instance]['options']
                if section == self.subsection:
                    for sub in temp_dict[sect]:
                        subsection = temp_dict[sect][sub]
                        if (subsection['identifier'] == identifier
                        and subsection['position'] == position
                        and subsection['section'] == section):
                            section_options = temp_dict[sect][sub]['options']
                            break
                else:
                    section_options = temp_dict[sect].get(position)
            
            if section_options:
                for option in options:
                    option = '\t%s\n' % (option.strip())
                    if sect == self.subsection:
                        section_options.setdefault('options',
                                                   []).append(option)
                    else:
                        section_options.append(option)

        return temp_dict


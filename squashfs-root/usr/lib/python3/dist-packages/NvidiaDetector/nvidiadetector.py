#
#       nvidiadetector.py
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

import os
import re
import subprocess
from subprocess import Popen, PIPE
import sys, logging
import apt

obsoletePackagesPath = '/usr/share/ubuntu-drivers-common/obsolete'

class NoDatadirError(Exception):
    "Exception thrown when no modaliases dir can be found"

class NvidiaDetection(object):
    '''
    A simple class to:
      * Detect the available graphics cards
      * See what drivers support them (If they are
        NVIDIA cards). If more than one card is
        available, try to find the highest common
        driver version which supports them all.
        (READ the comments in the code for further
        details)
      * Return the recommended driver version
    '''

    def __init__(self, printonly=None, verbose=None, obsolete=obsoletePackagesPath):
        '''
        printonly = if set to None will make an instance
                    of this class return the selected
                    driver.
                    If set to True it won't return
                    anything. It will simply and print
                    the choice.

        verbose   = if set to True will make the methods
                    print what is happening.
        '''

        # A simple look-up table for drivers whose name is not a digit
        # "current" is set to 1000 so as to make sure that it always has
        # the highest priority.
        self.__driver_aliases = {'current': 1000}

        self.printonly = printonly
        self.verbose = verbose
        self.oldPackages = self.getObsoletePackages(obsolete)
        self.detection()
        self.getData()
        self.getCards()
        self.removeUnsupported()
        if printonly == True:
            self.printSelection()
        else:
            self.selectDriver()

    def __get_name_from_value(self, value):
        '''Get the name of a driver from its corresponding integer'''
        for k, v in self.__driver_aliases.items():
            if v == value:
                return k
        return None

    def __get_value_from_name(self, name):
        '''Get the integer associated to the name of a driver'''
        v = self.__driver_aliases.get(name)
        if v is None:
            v = int(name)
        return v

    def getObsoletePackages(self, obsolete):
        '''Read the list of obsolete packages from a file'''
        tempList = []
        try:
            tempList = [x.strip() for x in open(obsolete).readlines()]
            tempList = [x for x in tempList if x != '']
        except IOError:
            pass
        return tempList

    def detection(self):
        '''
        Detect the models of the graphics cards
        and store them in self.cards
        '''
        self.cards = []
        p1 = Popen(['lspci', '-n'], stdout=PIPE, universal_newlines=True)
        p = p1.communicate()[0].split('\n')
        # if you don't have an nvidia card, fake one for debugging
        #p = ['00:02.0 0300: 10DE:03DE (rev 02)']
        indentifier1 = re.compile('.*0300: *(.+):(.+) \(.+\)')
        indentifier2 = re.compile('.*0300: *(.+):(.+)')
        for line in p:
            m1 = indentifier1.match(line)
            m2 = indentifier2.match(line)
            if m1:
                id1 = m1.group(1).strip().lower()
                id2 = m1.group(2).strip().lower()
                id = id1 + ':' + id2
                self.cards.append(id)
            elif m2:
                id1 = m2.group(1).strip().lower()
                id2 = m2.group(2).strip().lower()
                id = id1 + ':' + id2
                self.cards.append(id)

    def getData(self):
        '''
        Get the data from the modaliases for each driver
        and store them in self.drivers
        '''
        self.drivers = {}
        vendor_product_re = re.compile('pci:v0000(.+)d0000(.+)sv')

        for package in apt.Cache():
            if (not package.name.startswith('nvidia-')
                or 'updates' in package.name
                or 'experimental' in package.name
                or 'current' in package.name):
                continue
            try:
                m = package.candidate.record['Modaliases']
            except (KeyError, AttributeError):
                # that's entirely expected for -vdpau and friends; just for
                # debugging
                #logging.warning('Package %s has no modalias header' % package.name)
                continue

            # package names can be like "nvidia-173:i386" and we need to
            # extract the driver flavour from the name e.g. "173"
            stripped_package_name = package.name.split('-')[-1].split(':', 1)[0]
            driver_version = self.__get_value_from_name(stripped_package_name)

            try:
                if m:
                    m = m[(m.find('(')+1):].replace(')', '')
                    for alias in m.split(','):
                        vp = vendor_product_re.match(alias.lstrip())
                        if not vp:
                            logging.error('Package %s has unexpected modalias: %s' % (
                                package.name, alias))
                            continue
                        vendor = vp.group(1).lower()
                        product = vp.group(2).lower()

                        self.drivers.setdefault(driver_version, []).append(
                                vendor + ':' + product)
            except ValueError:
                logging.error('Package %s has invalid modalias header: %s' % (
                    package.name, m))

        # If we didn't find anything useful just print none and exit so as not
        # to trigger debconf.
        if len(self.drivers.keys()) == 0:
            sys.stdout.flush()
            print('none')
            #raise ValueError, "modaliases have no useful information"

    def getCards(self):
        '''
        See if the detected graphics cards are NVIDIA cards.
        If they are NVIDIA cards, append them to self.nvidiaCards
        '''
        self.driversForCards = {}
        self.nvidiaCards = []
        '''
        It is possible to override hardware detection (only for testing
        purposes) by setting self.cards to one of the following lists:

        self.cards = ['10de:02e2', '10de:002d', '10de:0296', '10de:087f']
        self.cards = ['10de:02e2', '10de:087f']
        self.cards = ['10de:02e2', '10de:087f', '10de:fake']
        self.cards = ['10de:0288'] # -96 driver only
        self.cards = ['10de:fake']
        '''

        for card in self.cards:
            if card[0: card.find(':')] == '10de':
                if self.verbose:
                    print('NVIDIA card found (' + card + ')')
                self.nvidiaCards.append(card)

        self.orderedList = sorted(self.drivers, reverse=True)

        '''
        See what drivers support each card and fill self.driversForCards
        so as to have something like the following:

        self.driversForCards = {
                                 'id_of_card1': [driver1, driver2],
                                 'id_of_card2': [driver2, driver3],
                               }
        '''
        for card in self.nvidiaCards:
            supported = False
            for driver in self.orderedList:
                if card in self.drivers[driver]:
                    supported = True
                    if self.verbose:
                        print('Card %s supported by driver %s' % (card, driver))
                    self.driversForCards.setdefault(card, []).append(driver)
            if supported == False:
                self.driversForCards.setdefault(card, []).append(None)

    def removeUnsupported(self):
        '''
        Remove unsupported cards from self.nvidiaCards and from
        self.driversForCards
        '''
        unsupportedCards = []
        for card in self.driversForCards:
            if None in self.driversForCards[card]:
                unsupportedCards.append(card)

        for unsupported in unsupportedCards:
            if self.verbose:
                print('Removing unsupported card ' + unsupported)
            self.nvidiaCards.remove(unsupported)
            del self.driversForCards[unsupported]

    def selectDriver(self):
        '''
        If more than one card is available, try to get the highest common driver
        '''
        cardsNumber = len(self.nvidiaCards)
        if cardsNumber > 0:#if a NVIDIA card is available
            if cardsNumber > 1:#if more than 1 card
                '''
                occurrence stores the number of occurrences (the values of the
                dictionary) of each driver version (the keys of the dictionary)

                Example:
                    occurrence = {177: 1, 173: 3}
                    This means that driver 177 supports only 1 card while 173
                    supports 3 cards.
                '''
                occurrence = {}
                for card in self.driversForCards:
                    for drv in self.driversForCards[card]:
                        occurrence.setdefault(drv, 0)
                        occurrence[drv] += 1

                occurrences = sorted(occurrence, reverse=True)
                '''
                candidates is the list of the likely candidates for the
                installation
                '''
                candidates = []
                for driver in occurrences:
                    if occurrence[driver] == cardsNumber:
                        candidates.append(driver)
                if len(candidates) > 0:
                    '''
                    If more than one driver version works for all the available
                    cards then the newest one is selected.

                    USE-CASE:
                        If a user has the following cards:
                        * GeForce 9300 (supported by driver 177 and 173)
                        * GeForce 7300 (supported by driver 177 and 173)
                        * GeForce 6200 (supported by driver 177 and 173)

                        Driver 177 is selected.
                    '''
                    candidates.sort(reverse=True)
                    choice = candidates[0]
                    if self.verbose and not self.printonly:
                        print('Recommended NVIDIA driver: ' + choice)
                else:
                    '''
                    Otherwise, if there is no single driver version which works
                    for all the available cards, the newest one is selected.

                    USE-CASE:
                        If a user has the following cards:
                        * GeForce 9300 (supported by driver 177 and 173)
                        * GeForce 1 (supported by driver 71)
                        * GeForce 2 (supported by driver 71)

                        The most modern card has the highest priority since
                        no common driver can be found. The other 2 cards
                        should use the open source driver
                    '''
                    choice = occurrences[0]
                    if self.verbose and not self.printonly:
                        print('Recommended NVIDIA driver: ' + choice)
            else:#just one card
                '''
                The choice is easy if only one card is available and/or supported.

                The newest driver which supports the card is chosen.
                '''
                choice = self.driversForCards[list(self.driversForCards.keys())[0]][0]
                if self.verbose and not self.printonly:
                    print('Recommended NVIDIA driver: %d' % choice)
            '''
            FIXME: we should use a metapackage for this
            '''

            driver_name = self.__get_name_from_value(choice)
            if driver_name != None:
                choice = (choice >= 390 and 'nvidia-driver-' or 'nvidia-') + str(driver_name)
            else:
                choice = (choice >= 390 and 'nvidia-driver-' or 'nvidia-') + str(choice)
        else:
            '''
            If no card is supported
            '''
            if self.verbose:
                print('No NVIDIA package to install')
            choice = None

        return choice

    def checkpkg(self, pkglist):
        '''
        USAGE:
            * pkglist is the list of packages  you want to check
            * use lists for one or more packages
            * use a string if it is only one package
            * lists will work well in both cases
        '''
        '''
        Checks whether all the packages in the list are installed
        and returns a list of the packages which are not installed
        '''
        lines = []
        notinstalled = []
        p1 = Popen(['dpkg', '--get-selections'], stdout=PIPE, universal_newlines=True)
        p = p1.communicate()[0]
        c = p.split('\n')
        for line in c:
            if line.find('\tinstall') != -1:#the relevant lines
                lines.append(line.split('\t')[0])
        if self.isstr(pkglist) == True:#if it is a string
            try:
                if lines.index(pkglist):
                    pass
            except ValueError:
                notinstalled.append(pkglist)
        else:#if it is a list
            for pkg in pkglist:
                try:
                    if lines.index(pkg):
                        pass
                except ValueError:
                    notinstalled.append(pkg)

        return notinstalled

    def isstr(self, elem):
        if bytes is str:
            #Python 2
            string_types = basestring
        else:
            #Python 3
            string_types = str
        return isinstance(elem, string_types)

    def islst(self, elem):
        return isinstance(elem, (tuple, list))

    def getDrivers(self):
        '''
        oldPackages = a list of the names of the obsolete drivers
        notInstalled = a list of the obsolete drivers which are not
                       installed
        '''
        installedPackage = None
        notInstalled = self.checkpkg(self.oldPackages)
        for package in self.oldPackages:
            if package not in notInstalled:
                installedPackage = package
        return (len(notInstalled) != len(self.oldPackages))

    def printSelection(self):
        '''
        Part for the kernel postinst.d/ hook
        '''
        driver = self.selectDriver()
        if self.getDrivers():#if an old driver is installed
            if driver:#if an appropriate driver is found
                sys.stdout.flush()
                print(driver)
            else:
                sys.stdout.flush()
                print('none')
        else:
            #print driver
            sys.stdout.flush()
            print('none')

#def usage():
#    instructionsList = ['The only accepted parameters are:'
#    '\n  --printonly', '\tprint the suggested driver'
#
#    '\n  --verbose', '\t\teach step will be verbose'
#    ]
#    print(''.join(instructionsList))

#def main():
#    err = 'Error: parameters not recognised'
#    try:
#        opts, args = getopt.getopt(sys.argv[1:], 'hp:v', ['help', 'printonly', 'verbose'])
#    except getopt.GetoptError as err:
#        # print help information and exit:
#        print str(err) # will print something like 'option -a not recognized'
#        usage()
#        sys.exit(2)
#    printonly = None
#    verbose = None
#    for o, a in opts:
#        if o in ('-v', '--verbose'):
#            verbose = True
#        elif o in ('-p', '--printonly'):
#            printonly = True
#        elif o in ('-h', '--help'):
#            usage()
#            sys.exit()
#        else:
#            assert False, 'unhandled option'
#    a = NvidiaDetection(printonly=printonly, verbose=verbose)


#if __name__ == '__main__':
#    main()


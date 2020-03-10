#Copyright (C) 2008 Codethink Ltd
#copyright: Copyright (c) 2005, 2007 IBM Corporation

#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License version 2 as published by the Free Software Foundation.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU Lesser General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

#Portions of this code originally licensed and copyright (c) 2005, 2007
#IBM Corporation under the BSD license, available at
#U{http://www.opensource.org/licenses/bsd-license.php}

#authors: Peter Parente, Mark Doffman

import pyatspi.Accessibility
from pyatspi.deviceevent import allModifiers
import pyatspi.state as state
import pyatspi.registry as registry

#from deviceevent import *

__all__ = [
                "setCacheLevel",
                "getCacheLevel",
                "clearCache",
                "printCache",
                "getInterfaceIID",
                "getInterfaceName",
                "listInterfaces",
                "stringToConst",
                "stateToString",
                "relationToString",
                "allModifiers",
                "findDescendant",
                "findAllDescendants",
                "findAncestor",
                "getPath",
                "pointToList",
                "rectToList",
                "attributeListToHash",
                "hashToAttributeList",
                "getBoundingBox"
         ]

def setCacheLevel(level):
        pass

def getCacheLevel():
        return None

def clearCache():
        pass

def printCache():
        print("Print cache function is deprecated")

def getInterfaceIID(obj):
        """
        Gets the ID of an interface class or object in string format for use in
        queryInterface.

        @param obj: Class representing an AT-SPI interface or instance
        @type obj: object
        @return: IID for the interface
        @rtype: string
        @raise AttributeError: When the parameter does not provide typecode info

        WARNING!! DEPRECATED!!

        In current D-Bus version of pyatspi this simply returns a null string.
        """
        return ""

def getInterfaceName(obj):
        """
        Gets the human readable name of an interface class or object in string
        format.

        @param obj: Class representing an AT-SPI interface or instance
        @type obj: class
        @return: Name of the interface
        @rtype: string
        @raise AttributeError: When the parameter does not provide typecode info
        """
        return obj._dbus_interface.lstrip("org.a11y.atspi.")

def listInterfaces(obj):
        """
        Gets a list of the names of all interfaces supported by this object. The
        names are the short-hand interface names like "Accessible" and "Component",
        not the full interface identifiers.

        @param obj: Arbitrary object to query for all accessibility related
        interfaces. Must provide a queryInterface method.
        @type obj: object
        @return: Set of supported interface names
        @rtype: set
        @raise AttributeError: If the object provide does not implement
        queryInterface
        """
        return obj.get_interfaces()

def stringToConst(prefix, suffix):
        """
        Maps a string name to an AT-SPI constant. The rules for the mapping are as 
        follows:
                - The prefix is captalized and has an _ appended to it.
                - All spaces in the suffix are mapped to the _ character. 
                - All alpha characters in the suffix are mapped to their uppercase.

        The resulting name is used with getattr to look up a constant with that name
        in the L{constants} module. If such a constant does not exist, the string
        suffix is returned instead.

        This method allows strings to be used to refer to roles, relations, etc.
        without direct access to the constants. It also supports the future expansion
        of roles, relations, etc. by allowing arbitrary strings which may or may not
        map to the current standard set of roles, relations, etc., but may still
        match some non-standard role, relation, etc. being reported by an
        application.

        @param prefix: Prefix of the constant name such as role, relation, state, 
                text, modifier, key
        @type prefix: string
        @param suffix: Name of the role, relation, etc. to use to lookup the constant
        @type suffix: string
        @return: The matching constant value
        @rtype: object
        """
        name = prefix.upper()+'_'+suffix.upper().replace(' ', '_')
        return getattr(constants, name, suffix)

def stateToString(value):
        """
        Converts a state value to a string based on the name of the state constant in
        the L{constants} module that has the given value.

        @param value: An AT-SPI state
        @type value: Accessibility.StateType
        @return: Human readable, untranslated name of the state
        @rtype: string
        """
        return state.STATE_VALUE_TO_NAME.get(value)

def relationToString(value):
        """
        Converts a relation value to a string based on the name of the state constant
        in the L{constants} module that has the given value.

        @param value: An AT-SPI relation
        @type value: Accessibility.RelationType
        @return: Human readable, untranslated name of the relation
        @rtype: string
        """
        return pyatspi.Accessibility.RELATION_VALUE_TO_NAME.get(value)


def findDescendant(acc, pred, breadth_first=False):
        """
        Searches for a descendant node satisfying the given predicate starting at 
        this node. The search is performed in depth-first order by default or
        in breadth first order if breadth_first is True. For example,

        my_win = findDescendant(lambda x: x.name == 'My Window')

        will search all descendants of x until one is located with the name 'My
        Window' or all nodes are exausted. Calls L{_findDescendantDepth} or
        L{_findDescendantBreadth} to start the recursive search.

        @param acc: Root accessible of the search
        @type acc: Accessibility.Accessible
        @param pred: Search predicate returning True if accessible matches the 
                        search criteria or False otherwise
        @type pred: callable
        @param breadth_first: Search breadth first (True) or depth first (False)?
        @type breadth_first: boolean
        @return: Accessible matching the criteria or None if not found
        @rtype: Accessibility.Accessible or None
        """
        if breadth_first:
                return _findDescendantBreadth(acc, pred)

        for child in acc:
                try:
                        ret = _findDescendantDepth(acc, pred)
                except Exception:
                        ret = None
                if ret is not None: return ret

def _findDescendantBreadth(acc, pred):
        """
        Internal function for locating one descendant. Called by L{findDescendant} to
        start the search.

        @param acc: Root accessible of the search
        @type acc: Accessibility.Accessible
        @param pred: Search predicate returning True if accessible matches the 
                        search criteria or False otherwise
        @type pred: callable
        @return: Matching node or None to keep searching
        @rtype: Accessibility.Accessible or None
        """
        for child in acc:
                try:
                        if pred(child): return child
                except Exception:
                        pass
        for child in acc:
                try:
                        ret = _findDescendantBreadth(child, pred)
                except Exception:
                        ret = None
                if ret is not None: return ret

def _findDescendantDepth(acc, pred):
        """
        Internal function for locating one descendant. Called by L{findDescendant} to
        start the search.

        @param acc: Root accessible of the search
        @type acc: Accessibility.Accessible
        @param pred: Search predicate returning True if accessible matches the 
                search criteria or False otherwise
        @type pred: callable
        @return: Matching node or None to keep searching
        @rtype: Accessibility.Accessible or None
        """
        try:
                if pred(acc): return acc
        except Exception:
                pass
        for child in acc:
                try:
                        ret = _findDescendantDepth(child, pred)
                except Exception:
                        ret = None
                if ret is not None: return ret

def findAllDescendants(acc, pred):
        """
        Searches for all descendant nodes satisfying the given predicate starting at 
        this node. Does an in-order traversal. For example,

        pred = lambda x: x.getRole() == pyatspi.ROLE_PUSH_BUTTON
        buttons = pyatspi.findAllDescendants(node, pred)

        will locate all push button descendants of node.

        @param acc: Root accessible of the search
        @type acc: Accessibility.Accessible
        @param pred: Search predicate returning True if accessible matches the 
                        search criteria or False otherwise
        @type pred: callable
        @return: All nodes matching the search criteria
        @rtype: list
        """
        matches = []
        _findAllDescendants(acc, pred, matches)
        return matches

def _findAllDescendants(acc, pred, matches):
        """
        Internal method for collecting all descendants. Reuses the same matches
        list so a new one does not need to be built on each recursive step.
        """
        for child in acc:
                try:
                        if pred(child): matches.append(child)
                except Exception:
                        pass
                _findAllDescendants(child, pred, matches)
        
def findAncestor(acc, pred):
        """
        Searches for an ancestor satisfying the given predicate. Note that the
        AT-SPI hierarchy is not always doubly linked. Node A may consider node B its
        child, but B is not guaranteed to have node A as its parent (i.e. its parent
        may be set to None). This means some searches may never make it all the way
        up the hierarchy to the desktop level.

        @param acc: Starting accessible object
        @type acc: Accessibility.Accessible
        @param pred: Search predicate returning True if accessible matches the 
                search criteria or False otherwise
        @type pred: callable
        @return: Node matching the criteria or None if not found
        @rtype: Accessibility.Accessible
        """
        if acc is None:
                # guard against bad start condition
                return None
        while 1:
                if acc.parent is None:
                        # stop if there is no parent and we haven't returned yet
                        return None
                try:
                        if pred(acc.parent): return acc.parent
                except Exception:
                        pass
                # move to the parent
                acc = acc.parent

def getPath(acc):
        """
        Gets the path from the application ancestor to the given accessible in
        terms of its child index at each level.

        @param acc: Target accessible
        @type acc: Accessibility.Accessible
        @return: Path to the target
        @rtype: list of integer
        @raise LookupError: When the application accessible cannot be reached
        """
        path = []
        while 1:
                if acc.parent is None:
                        path.reverse()
                        return path
                try:
                        path.append(acc.getIndexInParent())
                except Exception:
                        raise LookupError
                acc = acc.parent

def pointToList(point):
	return (point.x, point.y)

def rectToList(rect):
	return (rect.x, rect.y, rect.width, rect.height)

def attributeListToHash(list):
        ret = dict()
        for item in list:
                [key, val] = item.split(":")
                val = val.replace(":", r"\:")
                if ret.__contains__(key):
                    ret[key] = ret[key] + ":" + val
                else:
                    ret[key] = val
        return ret

def hashToAttributeList(h):
        return [x + ":" + h[x] for x in h.keys()]

class BoundingBox(list):
        def __new__(cls, x, y, width, height):
                return list.__new__(cls, (x, y, width, height))
        def __init__(self, x, y, width, height):
                list.__init__(self, (x, y, width, height))

        def __str__(self):
                return ("(%d, %d, %d, %d)" % (self.x, self.y, self.width, self.height))

        def _get_x(self):
                return self[0]
        def _set_x(self, val):
                self[0] = val
        x = property(fget=_get_x, fset=_set_x)
        def _get_y(self):
                return self[1]
        def _set_y(self, val):
                self[1] = val
        y = property(fget=_get_y, fset=_set_y)
        def _get_width(self):
                return self[2]
        def _set_width(self, val):
                self[2] = val
        width = property(fget=_get_width, fset=_set_width)
        def _get_height(self):
                return self[3]
        def _set_height(self, val):
                self[3] = val
        height = property(fget=_get_height, fset=_set_height)

def getBoundingBox(rect):
        return BoundingBox (rect.x, rect.y, rect.width, rect.height)

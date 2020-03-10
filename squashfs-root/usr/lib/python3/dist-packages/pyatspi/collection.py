#Copyright (C) 2008 Codethink Ltd
#Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.

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

from gi.repository import Atspi
from pyatspi.atspienum import *
from pyatspi.utils import *

__all__ = [
           "Collection",
           "SortOrder",
           "MatchType",
           "TreeTraversalType",
          ]

#------------------------------------------------------------------------------

class MatchType(AtspiEnum):
        _enum_lookup = {
                0:'MATCH_INVALID',
                1:'MATCH_ALL',
                2:'MATCH_ANY',
                3:'MATCH_NONE',
                4:'MATCH_EMPTY',
                5:'MATCH_LAST_DEFINED',
        }

class SortOrder(AtspiEnum):
        _enum_lookup = {
                0:'SORT_ORDER_INVALID',
                1:'SORT_ORDER_CANONICAL',
                2:'SORT_ORDER_FLOW',
                3:'SORT_ORDER_TAB',
                4:'SORT_ORDER_REVERSE_CANONICAL',
                5:'SORT_ORDER_REVERSE_FLOW',
                6:'SORT_ORDER_REVERSE_TAB',
                7:'SORT_ORDER_LAST_DEFINED',
        }

class TreeTraversalType(AtspiEnum):
        _enum_lookup = {
                0:'TREE_RESTRICT_CHILDREN',
                1:'TREE_RESTRICT_SIBLING',
                2:'TREE_INORDER',
                3:'TREE_LAST_DEFINED',
        }

class Collection:

        MATCH_ALL = MatchType(1)
        MATCH_ANY = MatchType(2)
        MATCH_EMPTY = MatchType(4)
        MATCH_INVALID = MatchType(0)
        MATCH_LAST_DEFINED = MatchType(5)
        MATCH_NONE = MatchType(3)

        SORT_ORDER_CANONICAL = SortOrder(1)
        SORT_ORDER_FLOW = SortOrder(2)
        SORT_ORDER_INVALID = SortOrder(0)
        SORT_ORDER_LAST_DEFINED = SortOrder(7)
        SORT_ORDER_REVERSE_CANONICAL = SortOrder(4)
        SORT_ORDER_REVERSE_FLOW = SortOrder(5)
        SORT_ORDER_REVERSE_TAB = SortOrder(6)
        SORT_ORDER_TAB = SortOrder(3)

        TREE_INORDER = TreeTraversalType(2)
        TREE_LAST_DEFINED = TreeTraversalType(3)
        TREE_RESTRICT_CHILDREN = TreeTraversalType(0)
        TREE_RESTRICT_SIBLING = TreeTraversalType(1)

        def __init__(self, obj):
                self.obj = obj

        def isAncestorOf(self, object):
                return Atspi.Collection.is_ancestor_of(self.obj)

        def createMatchRule(self, states, stateMatchType, attributes, attributeMatchType, roles, roleMatchType, interfaces, interfaceMatchType, invert):
                attributes_hash = attributeListToHash(attributes)
                return Atspi.MatchRule.new(states, stateMatchType, attributes_hash, attributeMatchType, roles, roleMatchType, interfaces, interfaceMatchType, invert)

        def freeMatchRule(self, rule):
                pass

        def getMatches(self, rule, sortby, count, traverse):
                return Atspi.Collection.get_matches(self.obj, rule, sortby, count, traverse)

        def getMatchesTo(self, current_object, rule, sortby, tree, recurse, count, traverse):
                return Atspi.Collection.get_matches_to(self.obj, current_object, rule, sortby, tree, recurse, count, traverse)

        def getMatchesFrom(self, current_object, rule, sortby, tree, count, traverse):
                return Atspi.Collection.get_matches_from(self.obj, current_object, rule, sortby, tree, count, traverse)

        def getActiveDescendant(self):
                return Atspi.Collection.get_active_descendant(self.obj)

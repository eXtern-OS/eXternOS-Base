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
from pyatspi.utils import *
from pyatspi.interface import *

__all__ = [
           "Action",
          ]

#------------------------------------------------------------------------------

class Action(interface):
        """
        An interface through which a user-actionable user interface component
        can be manipulated. Components which react to mouse or keyboard
        input from the user, (with the exception of pure text entry fields
        with no other function), should implement this interface. Typical
        actions include "click", "press", "release" (for instance for
        buttons), "menu" (for objects which have context menus invokable
        from mouse or keyboard), "open" for icons representing files
        folders, and others.
        """

        def getActions(self):
                """
                getActions:
                Retrieves all the actions at once.  
                @return : an array of an array of strings in the form
                [[name, description, keybinding], ...]
                """
                return Atspi.Action.get_actions(self.obj)

        def doAction(self, index):
                """
                doAction: 
                @param : index
                the 0-based index of the action to perform.
                Causes the object to perform the specified action.
                @return : a boolean indicating success or failure.
                """
                return Atspi.Action.do_action(self.obj, index)

        def getDescription(self, index):
                """
                getDescription: 
                @param : index
                the index of the action for which a description is desired.
                Get the description of the specified action. The description
                of an action may provide information about the result of action
                invocation, unlike the action name. 
                @return : a string containing the description of the specified
                action.
                """
                return Atspi.Action.get_action_description(self.obj, index)

        def getKeyBinding(self, index):
                """
                getKeyBinding: 
                @param : index
                the 0-based index of the action for which a key binding is requested.
                Get the key binding associated with a specific action.
                @return : a string containing the key binding for the specified
                action, or an empty string ("") if none exists.
                """
                return Atspi.Action.get_key_binding(self.obj, index)

        def getName(self, index):
                """
                getName: 
                @param : index
                the index of the action whose name is requested.
                Get the unlocalized name of the specified action. Action names
                generally describe the user action, i.e. "click" or "press",
                rather than the result of invoking the action.
                @return : a string containing the name of the specified action.
                """
                return Atspi.Action.get_action_name(self.obj, index)

        def getLocalizedName(self, index):
                """
                getLocalizedName: 
                @param : index
                the index of the action whose name is requested.
                Get the localized name of the specified action. Action names
                generally describe the user action, i.e. "click" or "press",
                rather than the result of invoking the action.
                @return : a string containing the name of the specified action.
                """
                return Atspi.Action.get_localized_name(self.obj, index)

        def get_nActions(self):
                return Atspi.Action.get_n_actions(self.obj)
        _nActionsDoc = \
                """
                nActions: a long containing the number of actions this object
                supports.
                """
        nActions = property(fget=get_nActions, doc=_nActionsDoc)

#END----------------------------------------------------------------------------

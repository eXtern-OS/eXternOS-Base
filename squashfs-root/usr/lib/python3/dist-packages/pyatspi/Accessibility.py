#Copyright (C) 2008 Codethink Ltd

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

from pyatspi.registry import *
Registry = Registry()

from pyatspi.application import *
from pyatspi.constants import *
from pyatspi.editabletext import *
from pyatspi.role import *
from pyatspi.state import *
from pyatspi.text import *
from pyatspi.document import *
from pyatspi.utils import *
from pyatspi.action import *
from pyatspi.component import *
from pyatspi.collection import *
from pyatspi.hypertext import *
from pyatspi.image import *
from pyatspi.selection import *
from pyatspi.table import *
from pyatspi.tablecell import *
from pyatspi.value import *
from pyatspi.appevent import *
from pyatspi.interface import *

def Accessible_getitem(self, i):
        len=self.get_child_count()
        if i < 0:
                i = len + i
        if i < 0 or i >= len:
                raise IndexError
        return self.get_child_at_index(i)

def Accessible_str(self):
        '''
        Gets a human readable representation of the accessible.
        
        @return: Role and name information for the accessible
        @rtype: string
        '''
        try:
                return '[%s | %s]' % (self.getRoleName(), self.name)
        except Exception:
                return '[DEAD]'
        
def pointToList(point):
        return (point.x, point.y)

# TODO: Figure out how to override Atspi.Rect constructor and remove this class
def getInterface(func, obj):
        ret = func(obj)
        if ret:
                return ret
        raise NotImplementedError

def getEventType(event):
        try:
                return event.pyType
        except:
                event.pyType = EventType(event.rawType)
                return event.pyType

def DeviceEvent_str(self):
        '''
        Builds a human readable representation of the event.

        @return: Event description
        @rtype: string
        '''
        if self.type == KEY_PRESSED_EVENT:
            kind = 'pressed'
        elif self.type == KEY_RELEASED_EVENT:
            kind = 'released'
        return '''\
%s
\thw_code: %d
\tevent_string: %s
\tmodifiers: %d
\tid: %d
\ttimestamp: %d
\tis_text: %s''' % (kind, self.hw_code, self.event_string, self.modifiers,
                        self.id, self.timestamp, self.is_text)

def Event_str(self):
        '''
        Builds a human readable representation of the event including event type,
        parameters, and source info.

        @return: Event description
        @rtype: string
        '''
        return '%s(%s, %s, %s)\n\tsource: %s\n\thost_application: %s' % \
               (self.type, self.detail1, self.detail2, self.any_data,
                self.source, self.host_application)
  
### Accessible ###
Accessible = Atspi.Accessible
Atspi.Accessible.getChildAtIndex = Atspi.Accessible.get_child_at_index
Atspi.Accessible.getAttributes = Atspi.Accessible.get_attributes_as_array
Atspi.Accessible.getApplication = Atspi.Accessible.get_application
Atspi.Accessible.__getitem__ = Accessible_getitem
Atspi.Accessible.__len__ = Atspi.Accessible.get_child_count
Atspi.Accessible.__bool__ = lambda x: True
Atspi.Accessible.__nonzero__ = lambda x: True
Atspi.Accessible.__str__ = Accessible_str
Atspi.Accessible.childCount = property(fget=Atspi.Accessible.get_child_count)
Atspi.Accessible.getChildCount = Atspi.Accessible.get_child_count
Atspi.Accessible.getIndexInParent = Atspi.Accessible.get_index_in_parent
Atspi.Accessible.getLocalizedRoleName = Atspi.Accessible.get_localized_role_name
Atspi.Accessible.getRelationSet = Atspi.Accessible.get_relation_set
Atspi.Accessible.getRole = Atspi.Accessible.get_role
Atspi.Accessible.getRoleName = Atspi.Accessible.get_role_name
Atspi.Accessible.getState = Atspi.Accessible.get_state_set
del Atspi.Accessible.children
Atspi.Accessible.description = property(fget=Atspi.Accessible.get_description)
Atspi.Accessible.objectLocale = property(fget=Atspi.Accessible.get_object_locale)
Atspi.Accessible.name = property(fget=Atspi.Accessible.get_name)
Atspi.Accessible.isEqual = lambda a,b: a == b
Atspi.Accessible.parent = property(fget=Atspi.Accessible.get_parent)
Atspi.Accessible.setCacheMask = Atspi.Accessible.set_cache_mask
Atspi.Accessible.clearCache = Atspi.Accessible.clear_cache

Atspi.Accessible.id = property(fget=Atspi.Accessible.get_id)
Atspi.Accessible.toolkitName = property(fget=Atspi.Accessible.get_toolkit_name)
Atspi.Accessible.toolkitVersion = property(fget=Atspi.Accessible.get_toolkit_version)
Atspi.Accessible.atspiVersion = property(fget=Atspi.Accessible.get_atspi_version)

Atspi.Accessible.queryAction = lambda x: Action(getInterface(Atspi.Accessible.get_action_iface, x))
Atspi.Accessible.queryCollection = lambda x: Collection(getInterface(Atspi.Accessible.get_collection_iface, x))
Atspi.Accessible.queryComponent = lambda x: Component(getInterface(Atspi.Accessible.get_component_iface, x))
Atspi.Accessible.queryDocument = lambda x: Document(getInterface(Atspi.Accessible.get_document_iface, x))
Atspi.Accessible.queryEditableText = lambda x: EditableText(getInterface(Atspi.Accessible.get_editable_text_iface, x))
Atspi.Accessible.queryHyperlink = lambda x: getInterface(Atspi.Accessible.get_hyperlink, x)
Atspi.Accessible.queryHypertext = lambda x: Hypertext(getInterface(Atspi.Accessible.get_hypertext_iface, x))
Atspi.Accessible.queryImage = lambda x: Image(getInterface(Atspi.Accessible.get_image_iface, x))
Atspi.Accessible.querySelection = lambda x: Selection(getInterface(Atspi.Accessible.get_selection_iface, x))
Atspi.Accessible.queryTable = lambda x: Table(getInterface(Atspi.Accessible.get_table_iface, x))
Atspi.Accessible.queryTableCell = lambda x: TableCell(getInterface(Atspi.Accessible.get_table_cell, x))
Atspi.Accessible.queryText = lambda x: Text(getInterface(Atspi.Accessible.get_text_iface, x))
Atspi.Accessible.queryValue = lambda x: Value(getInterface(Atspi.Accessible.get_value_iface, x))

# Doing this here since otherwise we'd have import recursion
interface.queryAction = lambda x: Action(getInterface(Atspi.Accessible.get_action, x.obj))
interface.queryCollection = lambda x: Collection(getInterface(Atspi.Accessible.get_collection, x.obj))
interface.queryComponent = lambda x: Component(getInterface(Atspi.Accessible.get_component, x.obj))
interface.queryDocument = lambda x: Document(getInterface(Atspi.Accessible.get_document, x.obj))
interface.queryEditableText = lambda x: EditableText(getInterface(Atspi.Accessible.get_editable_text, x.obj))
interface.queryHyperlink = lambda x: getInterface(Atspi.Accessible.get_hyperlink, x.obj)
interface.queryHypertext = lambda x: Hypertext(getInterface(Atspi.Accessible.get_hypertext, x.obj))
interface.queryImage = lambda x: Image(getInterface(Atspi.Accessible.get_image, x.obj))
interface.querySelection = lambda x: Selection(getInterface(Atspi.Accessible.get_selection, x.obj))
interface.queryTable = lambda x: Table(getInterface(Atspi.Accessible.get_table, x.obj))
interface.queryTableCell = lambda x: Table(getInterface(Atspi.Accessible.get_table_cell, x.obj))
interface.queryText = lambda x: Text(getInterface(Atspi.Accessible.get_text, x.obj))
interface.queryValue = lambda x: Value(getInterface(Atspi.Accessible.get_value, x.obj))

### hyperlink ###
Hyperlink = Atspi.Hyperlink
Atspi.Hyperlink.getObject = Atspi.Hyperlink.get_object
Atspi.Hyperlink.getURI = Atspi.Hyperlink.get_uri
Atspi.Hyperlink.isValid = Atspi.Hyperlink.is_valid
Atspi.Hyperlink.endIndex = property(fget=Atspi.Hyperlink.get_end_index)
Atspi.Hyperlink.nAnchors = property(fget=Atspi.Hyperlink.get_n_anchors)
Atspi.Hyperlink.startIndex = property(fget=Atspi.Hyperlink.get_start_index)

### DeviceEvent ###
Atspi.DeviceEvent.__str__ = DeviceEvent_str

### event ###
Atspi.Event.host_application = property(fget=lambda x: x.source.get_application())
Atspi.Event.rawType = Atspi.Event.type
Atspi.Event.source_name = property(fget=lambda x: x.source.name)
Atspi.Event.source_role = property(fget=lambda x: x.source.getRole())
Atspi.Event.type = property(fget=getEventType)
Atspi.Event.__str__ = Event_str

### RelationSet ###
Atspi.Relation.getRelationType = Atspi.Relation.get_relation_type
Atspi.Relation.getNTargets = Atspi.Relation.get_n_targets
Atspi.Relation.getTarget = Atspi.Relation.get_target
RELATION_NULL = Atspi.RelationType.NULL
RELATION_LABEL_FOR = Atspi.RelationType.LABEL_FOR
RELATION_LABELLED_BY = Atspi.RelationType.LABELLED_BY
RELATION_CONTROLLER_FOR = Atspi.RelationType.CONTROLLER_FOR
RELATION_CONTROLLED_BY = Atspi.RelationType.CONTROLLED_BY
RELATION_MEMBER_OF = Atspi.RelationType.MEMBER_OF
RELATION_TOOLTIP_FOR = Atspi.RelationType.TOOLTIP_FOR
RELATION_NODE_CHILD_OF = Atspi.RelationType.NODE_CHILD_OF
RELATION_NODE_PARENT_OF = Atspi.RelationType.NODE_PARENT_OF
RELATION_EXTENDED = Atspi.RelationType.EXTENDED
RELATION_FLOWS_TO = Atspi.RelationType.FLOWS_TO
RELATION_FLOWS_FROM = Atspi.RelationType.FLOWS_FROM
RELATION_SUBWINDOW_OF = Atspi.RelationType.SUBWINDOW_OF
RELATION_EMBEDS = Atspi.RelationType.EMBEDS
RELATION_EMBEDDED_BY = Atspi.RelationType.EMBEDDED_BY
RELATION_POPUP_FOR = Atspi.RelationType.POPUP_FOR
RELATION_PARENT_WINDOW_OF = Atspi.RelationType.PARENT_WINDOW_OF
RELATION_DESCRIPTION_FOR = Atspi.RelationType.DESCRIPTION_FOR
RELATION_DESCRIBED_BY = Atspi.RelationType.DESCRIBED_BY
RELATION_DETAILS = Atspi.RelationType.DETAILS
RELATION_DETAILS_FOR = Atspi.RelationType.DETAILS_FOR
RELATION_ERROR_MESSAGE = Atspi.RelationType.ERROR_MESSAGE
RELATION_ERROR_FOR = Atspi.RelationType.ERROR_FOR

# Build a dictionary mapping relation values to names based on the prefix of the enum constants.

RELATION_VALUE_TO_NAME = dict(((value, name[9:].lower().replace('_', ' ')) 
                               for name, value 
                               in globals().items()
                               if name.startswith('RELATION_')))

### ModifierType ###
MODIFIER_SHIFT = Atspi.ModifierType.SHIFT
MODIFIER_SHIFTLOCK = Atspi.ModifierType.SHIFTLOCK
MODIFIER_CONTROL = Atspi.ModifierType.CONTROL
MODIFIER_ALT = Atspi.ModifierType.ALT
MODIFIER_META = Atspi.ModifierType.META
MODIFIER_META2 = Atspi.ModifierType.META2
MODIFIER_META3 = Atspi.ModifierType.META3
MODIFIER_NUMLOCK = Atspi.ModifierType.NUMLOCK

### EventType ###
KEY_PRESSED_EVENT = Atspi.EventType.KEY_PRESSED_EVENT
KEY_RELEASED_EVENT = Atspi.EventType.KEY_RELEASED_EVENT
BUTTON_PRESSED_EVENT = Atspi.EventType.BUTTON_PRESSED_EVENT
BUTTON_RELEASED_EVENT = Atspi.EventType.BUTTON_RELEASED_EVENT

### KeySynthType ###
KEY_PRESS = Atspi.KeySynthType.PRESS
KEY_PRESSRELEASE = Atspi.KeySynthType.PRESSRELEASE
KEY_RELEASE = Atspi.KeySynthType.RELEASE
KEY_STRING = Atspi.KeySynthType.STRING
KEY_SYM = Atspi.KeySynthType.SYM

### cache ###
cache = Atspi.Cache
setTimeout = Atspi.set_timeout

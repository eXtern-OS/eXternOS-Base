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

# Constants used in the Component interface to get screen coordinates
DESKTOP_COORDS = 0
WINDOW_COORDS = 1

# Constants used to synthesize mouse events
MOUSE_B1P = 'b1p'
MOUSE_B1R = 'b1r'
MOUSE_B1C = 'b1c'
MOUSE_B1D = 'b1d'
MOUSE_B2P = 'b2p'
MOUSE_B2R = 'b2r'
MOUSE_B2C = 'b2c'
MOUSE_B2D = 'b2d'
MOUSE_B3P = 'b3p'
MOUSE_B3R = 'b3r'
MOUSE_B3C = 'b3c'
MOUSE_B3D = 'b3d'
MOUSE_ABS = 'abs'
MOUSE_REL = 'rel'

# events that clear cached properties
CACHE_EVENTS = ['object:property-change:accessible-name',
                'object:property-change:accessible-description',
                'object:property-change:accessible-role',
                'object:property-change:accessible-parent']

CACHE_PROPERTIES = ''

# This was placed into at-spi-corba because it apparently had a bug where
# one could not register for all the subevents of an event given only an
# AT-SPI event class (ie, first part of the event name).  Pyatspi2 does not
# have this issue, but will leave the tree as-is for now, and some programs
# pass it to registerEventListener, so the constant needs to stay.
# Keys are event names having subevents and values are the subevents
# under the key event; handlers *can* be registered for events not in this tree
EVENT_TREE = {
  'terminal':
    ['terminal:line-changed',
     'terminal:columncount-changed',
     'terminal:linecount-changed',
     'terminal:application-changed',
     'terminal:charwidth-changed'
     ],
  'document':
    ['document:load-complete',
     'document:reload',
     'document:load-stopped',
     'document:attributes-changed'
     'document:page-changed'
     ],
  'object': 
    ['object:property-change',
     'object:bounds-changed',
     'object:link-selected',
     'object:state-changed',
     'object:children-changed',
     'object:visible-data-changed',
     'object:selection-changed',
     'object:model-changed',
     'object:active-descendant-changed',
     'object:row-inserted',
     'object:row-reordered',
     'object:row-deleted',
     'object:column-inserted',
     'object:column-reordered',
     'object:column-deleted',
     'object:text-bounds-changed',
     'object:text-selection-changed',
     'object:text-changed',
     'object:text-attributes-changed',
     'object:text-caret-moved',  
     'object:attributes-changed'],
  'object:text-changed' :
    ['object:text-changed:insert',
    'object:text-changed:delete'],
  'object:property-change' :
    ['object:property-change:accessible-parent', 
    'object:property-change:accessible-name',
    'object:property-change:accessible-description',
    'object:property-change:accessible-value',
    'object:property-change:accessible-role',
    'object:property-change:accessible-table-caption',
    'object:property-change:accessible-table-column-description',
    'object:property-change:accessible-table-column-header',
    'object:property-change:accessible-table-row-description',
    'object:property-change:accessible-table-row-header',
    'object:property-change:accessible-table-summary'],
  'object:children-changed' :
    ['object:children-changed:add',
    'object:children-changed:remove'],
  'object:state-changed' :
    ['object:state-changed:'],
  'mouse' :
    ['mouse:abs',
    'mouse:rel',
    'mouse:button'],
  'mouse:button' :
    ['mouse:button:1p',
    'mouse:button:1r',
    'mouse:button:2p',
    'mouse:button:2r',
    'mouse:button:3p',
    'mouse:button:3r'],
  'window' :
    ['window:minimize',
    'window:maximize',
    'window:restore',
    'window:close',
    'window:create',
    'window:reparent',
    'window:desktop-create',
    'window:desktop-destroy',
    'window:activate',
    'window:deactivate',
    'window:raise',
    'window:lower',
    'window:move',
    'window:resize',
    'window:shade',
    'window:unshade',
    'window:restyle'],
  'focus' :
    ['focus:']
}

from pyatspi.state import *

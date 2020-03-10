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

from pyatspi.atspienum import *

#------------------------------------------------------------------------------

class Role(AtspiEnum):
        _enum_lookup = {
                0:'ROLE_INVALID',
                1:'ROLE_ACCELERATOR_LABEL',
                2:'ROLE_ALERT',
                3:'ROLE_ANIMATION',
                4:'ROLE_ARROW',
                5:'ROLE_CALENDAR',
                6:'ROLE_CANVAS',
                7:'ROLE_CHECK_BOX',
                8:'ROLE_CHECK_MENU_ITEM',
                9:'ROLE_COLOR_CHOOSER',
                10:'ROLE_COLUMN_HEADER',
                11:'ROLE_COMBO_BOX',
                12:'ROLE_DATE_EDITOR',
                13:'ROLE_DESKTOP_ICON',
                14:'ROLE_DESKTOP_FRAME',
                15:'ROLE_DIAL',
                16:'ROLE_DIALOG',
                17:'ROLE_DIRECTORY_PANE',
                18:'ROLE_DRAWING_AREA',
                19:'ROLE_FILE_CHOOSER',
                20:'ROLE_FILLER',
                21:'ROLE_FOCUS_TRAVERSABLE',
                22:'ROLE_FONT_CHOOSER',
                23:'ROLE_FRAME',
                24:'ROLE_GLASS_PANE',
                25:'ROLE_HTML_CONTAINER',
                26:'ROLE_ICON',
                27:'ROLE_IMAGE',
                28:'ROLE_INTERNAL_FRAME',
                29:'ROLE_LABEL',
                30:'ROLE_LAYERED_PANE',
                31:'ROLE_LIST',
                32:'ROLE_LIST_ITEM',
                33:'ROLE_MENU',
                34:'ROLE_MENU_BAR',
                35:'ROLE_MENU_ITEM',
                36:'ROLE_OPTION_PANE',
                37:'ROLE_PAGE_TAB',
                38:'ROLE_PAGE_TAB_LIST',
                39:'ROLE_PANEL',
                40:'ROLE_PASSWORD_TEXT',
                41:'ROLE_POPUP_MENU',
                42:'ROLE_PROGRESS_BAR',
                43:'ROLE_PUSH_BUTTON',
                44:'ROLE_RADIO_BUTTON',
                45:'ROLE_RADIO_MENU_ITEM',
                46:'ROLE_ROOT_PANE',
                47:'ROLE_ROW_HEADER',
                48:'ROLE_SCROLL_BAR',
                49:'ROLE_SCROLL_PANE',
                50:'ROLE_SEPARATOR',
                51:'ROLE_SLIDER',
                52:'ROLE_SPIN_BUTTON',
                53:'ROLE_SPLIT_PANE',
                54:'ROLE_STATUS_BAR',
                55:'ROLE_TABLE',
                56:'ROLE_TABLE_CELL',
                57:'ROLE_TABLE_COLUMN_HEADER',
                58:'ROLE_TABLE_ROW_HEADER',
                59:'ROLE_TEAROFF_MENU_ITEM',
                60:'ROLE_TERMINAL',
                61:'ROLE_TEXT',
                62:'ROLE_TOGGLE_BUTTON',
                63:'ROLE_TOOL_BAR',
                64:'ROLE_TOOL_TIP',
                65:'ROLE_TREE',
                66:'ROLE_TREE_TABLE',
                67:'ROLE_UNKNOWN',
                68:'ROLE_VIEWPORT',
                69:'ROLE_WINDOW',
                70:'ROLE_EXTENDED',
                71:'ROLE_HEADER',
                72:'ROLE_FOOTER',
                73:'ROLE_PARAGRAPH',
                74:'ROLE_RULER',
                75:'ROLE_APPLICATION',
                76:'ROLE_AUTOCOMPLETE',
                77:'ROLE_EDITBAR',
                78:'ROLE_EMBEDDED',
                79:'ROLE_ENTRY',
                80:'ROLE_CHART',
                81:'ROLE_CAPTION',
                82:'ROLE_DOCUMENT_FRAME',
                83:'ROLE_HEADING',
                84:'ROLE_PAGE',
                85:'ROLE_SECTION',
                86:'ROLE_REDUNDANT_OBJECT',
                87:'ROLE_FORM',
                88:'ROLE_LINK',
                89:'ROLE_INPUT_METHOD_WINDOW',
                90:'ROLE_TABLE_ROW',
                91:'ROLE_TREE_ITEM',
                92:'ROLE_DOCUMENT_SPREADSHEET',
                93:'ROLE_DOCUMENT_PRESENTATION',
                94:'ROLE_DOCUMENT_TEXT',
                95:'ROLE_DOCUMENT_WEB',
                96:'ROLE_DOCUMENT_EMAIL',
                97:'ROLE_COMMENT',
                98:'ROLE_LIST_BOX',
                99:'ROLE_GROUPING',
                100:'ROLE_IMAGE_MAP',
                101:'ROLE_NOTIFICATION',
                102:'ROLE_INFO_BAR',
                103:'ROLE_LEVEL_BAR',
                104:'ROLE_TITLE_BAR',
                105:'ROLE_BLOCK_QUOTE',
                106:'ROLE_AUDIO',
                107:'ROLE_VIDEO',
                108:'ROLE_DEFINITION',
                109:'ROLE_ARTICLE',
                110:'ROLE_LANDMARK',
                111:'ROLE_LOG',
                112:'ROLE_MARQUEE',
                113:'ROLE_MATH',
                114:'ROLE_RATING',
                115:'ROLE_TIMER',
                116:'ROLE_STATIC',
                117:'ROLE_MATH_FRACTION',
                118:'ROLE_MATH_ROOT',
                119:'ROLE_SUBSCRIPT',
                120:'ROLE_SUPERSCRIPT',
                121:'ROLE_DESCRIPTION_LIST',
                122:'ROLE_DESCRIPTION_TERM',
                123:'ROLE_DESCRIPTION_VALUE',
                124:'ROLE_FOOTNOTE',
                125:'ROLE_LAST_DEFINED',
        }

ROLE_ACCELERATOR_LABEL = Role(1)
ROLE_ALERT = Role(2)
ROLE_ANIMATION = Role(3)
ROLE_APPLICATION = Role(75)
ROLE_ARROW = Role(4)
ROLE_ARTICLE = Role(109)
ROLE_AUDIO = Role(106)
ROLE_AUTOCOMPLETE = Role(76)
ROLE_BLOCK_QUOTE = Role(105)
ROLE_CALENDAR = Role(5)
ROLE_CANVAS = Role(6)
ROLE_CAPTION = Role(81)
ROLE_CHART = Role(80)
ROLE_CHECK_BOX = Role(7)
ROLE_CHECK_MENU_ITEM = Role(8)
ROLE_COLOR_CHOOSER = Role(9)
ROLE_COLUMN_HEADER = Role(10)
ROLE_COMBO_BOX = Role(11)
ROLE_COMMENT = Role(97)
ROLE_DATE_EDITOR = Role(12)
ROLE_DEFINITION = Role(108)
ROLE_DESCRIPTION_LIST = Role(121)
ROLE_DESCRIPTION_TERM = Role(122)
ROLE_DESCRIPTION_VALUE = Role(123)
ROLE_DESKTOP_FRAME = Role(14)
ROLE_DESKTOP_ICON = Role(13)
ROLE_DIAL = Role(15)
ROLE_DIALOG = Role(16)
ROLE_DIRECTORY_PANE = Role(17)
ROLE_DOCUMENT_EMAIL = Role(96)
ROLE_DOCUMENT_FRAME = Role(82)
ROLE_DOCUMENT_PRESENTATION = Role(93)
ROLE_DOCUMENT_SPREADSHEET = Role(92)
ROLE_DOCUMENT_TEXT = Role(94)
ROLE_DOCUMENT_WEB = Role(95)
ROLE_DRAWING_AREA = Role(18)
ROLE_EDITBAR = Role(77)
ROLE_EMBEDDED = Role(78)
ROLE_ENTRY = Role(79)
ROLE_EXTENDED = Role(70)
ROLE_FILE_CHOOSER = Role(19)
ROLE_FILLER = Role(20)
ROLE_FOCUS_TRAVERSABLE = Role(21)
ROLE_FONT_CHOOSER = Role(22)
ROLE_FOOTER = Role(72)
ROLE_FOOTNOTE = Role(124)
ROLE_FORM = Role(87)
ROLE_FRAME = Role(23)
ROLE_GLASS_PANE = Role(24)
ROLE_GROUPING = Role(99)
ROLE_HEADER = Role(71)
ROLE_HEADING = Role(83)
ROLE_HTML_CONTAINER = Role(25)
ROLE_ICON = Role(26)
ROLE_IMAGE = Role(27)
ROLE_IMAGE_MAP = Role(100)
ROLE_INFO_BAR = Role(102)
ROLE_INPUT_METHOD_WINDOW = Role(89)
ROLE_INTERNAL_FRAME = Role(28)
ROLE_INVALID = Role(0)
ROLE_LABEL = Role(29)
ROLE_LANDMARK = Role(110)
ROLE_LAST_DEFINED = Role(125)
ROLE_LAYERED_PANE = Role(30)
ROLE_LEVEL_BAR = Role(103)
ROLE_LINK = Role(88)
ROLE_LIST = Role(31)
ROLE_LIST_BOX = Role(98)
ROLE_LIST_ITEM = Role(32)
ROLE_LOG = Role(111)
ROLE_MARQUEE = Role(112)
ROLE_MATH = Role(113)
ROLE_MATH_FRACTION = Role(117)
ROLE_MATH_ROOT = Role(118)
ROLE_MENU = Role(33)
ROLE_MENU_BAR = Role(34)
ROLE_MENU_ITEM = Role(35)
ROLE_NOTIFICATION = Role(101)
ROLE_OPTION_PANE = Role(36)
ROLE_PAGE = Role(84)
ROLE_PAGE_TAB = Role(37)
ROLE_PAGE_TAB_LIST = Role(38)
ROLE_PANEL = Role(39)
ROLE_PARAGRAPH = Role(73)
ROLE_PASSWORD_TEXT = Role(40)
ROLE_POPUP_MENU = Role(41)
ROLE_PROGRESS_BAR = Role(42)
ROLE_PUSH_BUTTON = Role(43)
ROLE_RADIO_BUTTON = Role(44)
ROLE_RADIO_MENU_ITEM = Role(45)
ROLE_RATING = Role(114)
ROLE_REDUNDANT_OBJECT = Role(86)
ROLE_ROOT_PANE = Role(46)
ROLE_ROW_HEADER = Role(47)
ROLE_RULER = Role(74)
ROLE_SCROLL_BAR = Role(48)
ROLE_SCROLL_PANE = Role(49)
ROLE_SECTION = Role(85)
ROLE_SEPARATOR = Role(50)
ROLE_SLIDER = Role(51)
ROLE_SPIN_BUTTON = Role(52)
ROLE_SPLIT_PANE = Role(53)
ROLE_STATIC = Role(116)
ROLE_STATUS_BAR = Role(54)
ROLE_SUBSCRIPT = Role(119)
ROLE_SUPERSCRIPT = Role(120)
ROLE_TABLE = Role(55)
ROLE_TABLE_CELL = Role(56)
ROLE_TABLE_COLUMN_HEADER = Role(57)
ROLE_TABLE_ROW = Role(90)
ROLE_TABLE_ROW_HEADER = Role(58)
ROLE_TEAROFF_MENU_ITEM = Role(59)
ROLE_TERMINAL = Role(60)
ROLE_TEXT = Role(61)
ROLE_TIMER = Role(115)
ROLE_TITLE_BAR = Role(104)
ROLE_TOGGLE_BUTTON = Role(62)
ROLE_TOOL_BAR = Role(63)
ROLE_TOOL_TIP = Role(64)
ROLE_TREE = Role(65)
ROLE_TREE_ITEM = Role(91)
ROLE_TREE_TABLE = Role(66)
ROLE_UNKNOWN = Role(67)
ROLE_VIDEO = Role(107)
ROLE_VIEWPORT = Role(68)
ROLE_WINDOW = Role(69)

ROLE_NAMES = {
        ROLE_INVALID:'invalid',
        ROLE_ACCELERATOR_LABEL:'accelerator label',
        ROLE_ALERT:'alert',
        ROLE_ANIMATION:'animation',
        ROLE_ARROW:'arrow',
        ROLE_CALENDAR:'calendar',
        ROLE_CANVAS:'canvas',
        ROLE_CHECK_BOX:'check box',
        ROLE_CHECK_MENU_ITEM:'check menu item',
        ROLE_COLOR_CHOOSER:'color chooser',
        ROLE_COLUMN_HEADER:'column header',
        ROLE_COMBO_BOX:'combo box',
        ROLE_DATE_EDITOR:'dateeditor',
        ROLE_DESKTOP_ICON:'desktop icon',
        ROLE_DESKTOP_FRAME:'desktop frame',
        ROLE_DIAL:'dial',
        ROLE_DIALOG:'dialog',
        ROLE_DIRECTORY_PANE:'directory pane',
        ROLE_DRAWING_AREA:'drawing area',
        ROLE_FILE_CHOOSER:'file chooser',
        ROLE_FILLER:'filler',
        ROLE_FONT_CHOOSER:'font chooser',
        ROLE_FRAME:'frame',
        ROLE_GLASS_PANE:'glass pane',
        ROLE_HTML_CONTAINER:'html container',
        ROLE_ICON:'icon',
        ROLE_IMAGE:'image',
        ROLE_INTERNAL_FRAME:'internal frame',
        ROLE_LABEL:'label',
        ROLE_LAYERED_PANE:'layered pane',
        ROLE_LIST:'list',
        ROLE_LIST_ITEM:'list item',
        ROLE_MENU:'menu',
        ROLE_MENU_BAR:'menu bar',
        ROLE_MENU_ITEM:'menu item',
        ROLE_OPTION_PANE:'option pane',
        ROLE_PAGE_TAB:'page tab',
        ROLE_PAGE_TAB_LIST:'page tab list',
        ROLE_PANEL:'panel',
        ROLE_PASSWORD_TEXT:'password text',
        ROLE_POPUP_MENU:'popup menu',
        ROLE_PROGRESS_BAR:'progress bar',
        ROLE_PUSH_BUTTON:'push button',
        ROLE_RADIO_BUTTON:'radio button',
        ROLE_RADIO_MENU_ITEM:'radio menu item',
        ROLE_ROOT_PANE:'root pane',
        ROLE_ROW_HEADER:'row header',
        ROLE_SCROLL_BAR:'scroll bar',
        ROLE_SCROLL_PANE:'scroll pane',
        ROLE_SEPARATOR:'separator',
        ROLE_SLIDER:'slider',
        ROLE_SPLIT_PANE:'split pane',
        ROLE_SPIN_BUTTON:'spin button',
        ROLE_STATUS_BAR:'status bar',
        ROLE_TABLE:'table',
        ROLE_TABLE_CELL:'table cell',
        ROLE_TABLE_COLUMN_HEADER:'table column header',
        ROLE_TABLE_ROW_HEADER:'table row header',
        ROLE_TEAROFF_MENU_ITEM:'tear off menu item',
        ROLE_TERMINAL:'terminal',
        ROLE_TEXT:'text',
        ROLE_TOGGLE_BUTTON:'toggle button',
        ROLE_TOOL_BAR:'tool bar',
        ROLE_TOOL_TIP:'tool tip',
        ROLE_TREE:'tree',
        ROLE_TREE_TABLE:'tree table',
        ROLE_UNKNOWN:'unknown',
        ROLE_VIEWPORT:'viewport',
        ROLE_WINDOW:'window',
        ROLE_HEADER:'header',
        ROLE_FOOTER:'footer',
        ROLE_PARAGRAPH:'paragraph',
        ROLE_RULER:'ruler',
        ROLE_APPLICATION:'application',
        ROLE_AUTOCOMPLETE:'autocomplete',
        ROLE_EDITBAR:'edit bar',
        ROLE_EMBEDDED:'embedded component',
        ROLE_ENTRY:'entry',
        ROLE_CHART:'chart',
        ROLE_CAPTION:'caption',
        ROLE_DOCUMENT_FRAME:'document frame',
        ROLE_HEADING:'heading',
        ROLE_PAGE:'page',
        ROLE_SECTION:'section',
        ROLE_REDUNDANT_OBJECT:'redundant object',
        ROLE_FORM:'form',
        ROLE_LINK:'link',
        ROLE_INPUT_METHOD_WINDOW:'input method window',
        ROLE_TABLE_ROW:'table row',
        ROLE_TREE_ITEM:'tree item',
        ROLE_DOCUMENT_SPREADSHEET:'document spreadsheet',
        ROLE_DOCUMENT_PRESENTATION:'document presentation',
        ROLE_DOCUMENT_TEXT:'document text',
        ROLE_DOCUMENT_WEB:'document web',
        ROLE_DOCUMENT_EMAIL:'document email',
        ROLE_COMMENT:'comment',
        ROLE_LIST_BOX:'list box',
        ROLE_GROUPING:'grouping',
        ROLE_IMAGE_MAP:'image map',
        ROLE_NOTIFICATION:'notification',
        ROLE_INFO_BAR:'info bar',
        ROLE_LEVEL_BAR:'level bar',
        ROLE_TITLE_BAR:'title bar',
        ROLE_BLOCK_QUOTE:'block quote',
        ROLE_AUDIO:'audio',
        ROLE_VIDEO:'video',
        ROLE_DEFINITION:'definition',
        ROLE_ARTICLE:'article',
        ROLE_LANDMARK:'landmark',
        ROLE_LOG:'log',
        ROLE_MARQUEE:'marquee',
        ROLE_MATH:'math',
        ROLE_RATING:'rating',
        ROLE_TIMER:'timer',
        ROLE_STATIC:'static',
        ROLE_MATH_FRACTION:'math fraction',
        ROLE_MATH_ROOT: 'math root',
        ROLE_SUBSCRIPT: 'subscript',
        ROLE_SUPERSCRIPT: 'superscript',
}

#END----------------------------------------------------------------------------

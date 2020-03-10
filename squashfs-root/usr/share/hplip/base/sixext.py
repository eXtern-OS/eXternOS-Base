"""Utilities for writing code that runs on Python 2 and 3"""
import sys
import types
from .six import *
__version__ = "1.0"

def _add_doc(func, doc):
    """Add documentation to a function."""
    func.__doc__ = doc


class _MovedItems_addon(types.ModuleType):
    """Lazy loading of moved objects"""

_moved_attributes_addon = [

    MovedModule("builtins", "__builtin__"),
    MovedModule("configparser", "ConfigParser"),
    MovedModule("copyreg", "copy_reg"),
    MovedModule("dbm_gnu", "gdbm", "dbm.gnu"),
    MovedModule("http_cookiejar", "cookielib", "http.cookiejar"),
    MovedModule("http_cookies", "Cookie", "http.cookies"),
    MovedModule("html_entities", "htmlentitydefs", "html.entities"),
    MovedModule("html_parser", "HTMLParser", "html.parser"),
    MovedModule("http_client", "httplib", "http.client"),
    MovedModule("email_mime_multipart", "email.MIMEMultipart", "email.mime.multipart"),
    MovedModule("email_mime_text", "email.MIMEText", "email.mime.text"),
    MovedModule("email_mime_base", "email.MIMEBase", "email.mime.base"),
    MovedModule("BaseHTTPServer", "BaseHTTPServer", "http.server"),
    MovedModule("CGIHTTPServer", "CGIHTTPServer", "http.server"),
    MovedModule("SimpleHTTPServer", "SimpleHTTPServer", "http.server"),
    MovedModule("cPickle", "cPickle", "pickle"),
    MovedModule("queue", "Queue"),
    MovedModule("reprlib", "repr"),
    MovedModule("socketserver", "SocketServer"),
    MovedModule("_thread", "thread", "_thread"),
    MovedModule("tkinter", "Tkinter"),
    MovedModule("tkinter_dialog", "Dialog", "tkinter.dialog"),
    MovedModule("tkinter_filedialog", "FileDialog", "tkinter.filedialog"),
    MovedModule("tkinter_scrolledtext", "ScrolledText", "tkinter.scrolledtext"),
    MovedModule("tkinter_simpledialog", "SimpleDialog", "tkinter.simpledialog"),
    MovedModule("tkinter_tix", "Tix", "tkinter.tix"),
    MovedModule("tkinter_ttk", "ttk", "tkinter.ttk"),
    MovedModule("tkinter_constants", "Tkconstants", "tkinter.constants"),
    MovedModule("tkinter_dnd", "Tkdnd", "tkinter.dnd"),
    MovedModule("tkinter_colorchooser", "tkColorChooser",
                "tkinter.colorchooser"),
    MovedModule("tkinter_commondialog", "tkCommonDialog",
                "tkinter.commondialog"),
    MovedModule("tkinter_tkfiledialog", "tkFileDialog", "tkinter.filedialog"),
    MovedModule("tkinter_font", "tkFont", "tkinter.font"),
    MovedModule("tkinter_messagebox", "tkMessageBox", "tkinter.messagebox"),
    MovedModule("tkinter_tksimpledialog", "tkSimpleDialog",
                "tkinter.simpledialog"),
    MovedModule("urllib_robotparser", "robotparser", "urllib.robotparser"),
    MovedModule("urllib2_parse", "urllib2", "urllib.parse"),
    MovedModule("urllib2_error", "urllib2", "urllib.error"),
    MovedModule("urllib2_request", "urllib2", "urllib.request"),
    MovedModule("urllib_request", "urllib", "urllib.request"),
    MovedModule("urllib_parse", "urllib", "urllib.parse"),
    MovedModule("urllib_error", "urllib", "urllib.error"),
    MovedModule("xmlrpc_client", "xmlrpclib", "xmlrpc.client"),
    MovedModule("winreg", "_winreg"),
    MovedModule("email_mime_image", "email.MIMEImage", "email.mime.image"),
    MovedModule("email_encoders", "email.Encoders", "email.encoders"),
    MovedModule("sha", "sha", "hashlib"),

    MovedAttribute("cStringIO", "cStringIO", "io", "StringIO"),
    MovedAttribute("filter", "itertools", "builtins", "ifilter", "filter"),
    MovedAttribute("filterfalse", "itertools", "itertools", "ifilterfalse", "filterfalse"),
    MovedAttribute("input", "__builtin__", "builtins", "raw_input", "input"),
    MovedAttribute("map", "itertools", "builtins", "imap", "map"),
    MovedAttribute("range", "__builtin__", "builtins", "xrange", "range"),
    MovedAttribute("reload_module", "__builtin__", "imp", "reload"),
    MovedAttribute("reduce", "__builtin__", "functools"),
    MovedAttribute("StringIO", "StringIO", "io"),
    MovedAttribute("UserString", "UserString", "collections"),
    MovedAttribute("xrange", "__builtin__", "builtins", "xrange", "range"),
    MovedAttribute("zip", "itertools", "builtins", "izip", "zip"),
    MovedAttribute("zip_longest", "itertools", "itertools", "izip_longest", "zip_longest"),


]

for attr in _moved_attributes_addon:
    setattr(_MovedItems_addon, attr.name, attr)
del attr


moves = sys.modules[__name__ + ".moves"] = _MovedItems_addon("moves")


import io
class xStringIO(io.BytesIO):
    if PY3:
        def makefile(self, x):
            return self
    else:
        def makefile(self, x, y):
            return self 

if PY3:

    def to_bytes_latin(s):
        return s.encode("latin-1")


    def to_bytes_utf8(s):
        return s.encode("utf-8")


    def to_string_utf8(s):
        return s.decode("utf-8", 'ignore')


    def to_string_latin(s):
        return s.decode("latin-1", 'ignore')


    def to_unicode(s, enc=None):
        return str(s)


    def from_unicode_to_str(s,enc=''):
        return s


    def to_long(i):
        return i


    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO

    import subprocess


else:
    def to_bytes_latin(s):
        return s


    def to_bytes_utf8(s):
        return s


    def to_string_utf8(s):
        return s


    def to_string_latin(s):
        return s


    def to_unicode(s, enc=None):
        if enc:
            return unicode(s, enc)#, "unicode_escape")
        else:
            return unicode(s)#, "unicode_escape")


    def from_unicode_to_str(s,enc='utf-8'):
        return s.encode(enc)


    def to_long(i):
        return long(i)


    import cStringIO
    StringIO = BytesIO = cStringIO.StringIO
    import commands as subprocess



_add_doc(to_bytes_utf8, """Byte literal""")
_add_doc(to_bytes_latin, """Byte literal""")
_add_doc(to_string_utf8, """String literal""")
_add_doc(to_string_latin, """String literal""")
_add_doc(to_unicode, """Text literal""")



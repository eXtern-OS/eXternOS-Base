import os
import re
import dbus
import subprocess

CONSOLE_SETUP_DEFAULT = "/etc/default/keyboard"

class UnknownProxyTypeError(dbus.DBusException):
    " an unknown proxy type was passed "
    pass
class InvalidKeyboardTypeError(dbus.DBusException):
    " an invalid keyboard was set "
    pass
class PermissionDeniedError(dbus.DBusException):
    " permission denied by policy "
    pass

def authWithPolicyKit(sender, connection, priv, interactive=1):
    #print ("_authWithPolicyKit()")
    system_bus = dbus.SystemBus()
    obj = system_bus.get_object("org.freedesktop.PolicyKit1", 
                                "/org/freedesktop/PolicyKit1/Authority", 
                                "org.freedesktop.PolicyKit1.Authority")
    policykit = dbus.Interface(obj, "org.freedesktop.PolicyKit1.Authority")
    #print ("priv: ", priv)
    subject = ('system-bus-name', 
               { 'name' : dbus.String(sender, variant_level = 1) }
               )
    details = { '' : '' }
    flags = dbus.UInt32(interactive) #   AllowUserInteraction = 0x00000001
    cancel_id = ''
    (ok, notused, details) = policykit.CheckAuthorization(subject,
                                                          priv, 
                                                          details,
                                                          flags,
                                                          cancel_id)
    #print ("ok: ", ok)
    return ok

def get_keyboard_from_etc():
    """ 
    helper that reads /etc/default/console-setup and gets the 
    keyboard settings there
    """
    model = ""
    layout = ""
    variant = ""
    options = ""
    try:
        f = open(CONSOLE_SETUP_DEFAULT)
        for line in f:
            if line.startswith("XKBMODEL="):
                model = line.split("=")[1].strip('"\n')
            elif line.startswith("XKBLAYOUT="):
                layout = line.split("=")[1].strip('"\n')
            elif line.startswith("XKBVARIANT="):
                variant = line.split("=")[1].strip('"\n')
            elif line.startswith("XKBOPTIONS="):
                options = line.split("=")[1].strip('"\n')

        f.close()
        print (model, layout, variant, options)
    except Exception:
        print ("Couldn't read ", CONSOLE_SETUP_DEFAULT)

    return (model, layout, variant, options)

def run_setupcon():
    """
    helper that runs setupcon to activate the settings, taken from 
    oem-config (/usr/lib/oem-config/console/console-setup-apply)
    """
    ret = subprocess.call(["setupcon","--save-only"])
    subprocess.Popen(["/usr/sbin/update-initramfs","-u"])
    return (ret == 0)

def set_keyboard_to_etc(model, layout, variant, options):
    """ 
    helper that writes /etc/default/console-setup 
    """
    # if no keyboard model is set, try to guess one
    # this is based on the "console-setup.config" code that
    # defaults to pc105
    if not model:
        model = "pc105"
        if layout == "us":
            model = "pc104"
        elif layout == "br":
            model = "abnt2"
        elif layout == "jp":
            model = "jp106"

    # verify the settings
    if not verify_keyboard_settings(model, layout, variant, options):
        #print ("verify_keyboard failed")
        raise InvalidKeyboardTypeError("Invalid keyboard set")

    # FIXME: what to do if not os.path.exists(CONSOLE_SETUP_DEFAULT)
    content = []
    for line in open(CONSOLE_SETUP_DEFAULT):
        if line.startswith("XKBMODEL="):
            line = 'XKBMODEL="%s"\n' % model
        elif line.startswith("XKBLAYOUT="):
            line = 'XKBLAYOUT="%s"\n' % layout
        elif line.startswith("XKBVARIANT="):
            line = 'XKBVARIANT="%s"\n' % variant
        elif line.startswith("XKBOPTIONS="):
            line = 'XKBOPTIONS="%s"\n' % options
        content.append(line)
    # if something changed, write 
    if content != open(CONSOLE_SETUP_DEFAULT).readlines():
        #print ("content changed, writing")
        open(CONSOLE_SETUP_DEFAULT+".new","w").write("".join(content))
        os.rename(CONSOLE_SETUP_DEFAULT+".new", 
                  CONSOLE_SETUP_DEFAULT)

    if not run_setupcon():
        #print ("setupcon failed")
        return False

    return True

def verify_keyboard_settings(model, layout, variant, options):
    " helper that verfies the settings "
    # check against char whitelist
    allowed = "^[0-9a-zA-Z:,_]*$"
    for s in (model, layout, variant, options):
        if not re.match(allowed, s):
            #print ("illegal chars in '%s'" % s)
            return False
    # check if 'ckbcomp' can compile it
    cmd = ["ckbcomp"]
    if model:
        cmd += ["-model",model]
    if layout:
        cmd += ["-layout", layout]
    if variant:
        cmd += ["-variant", variant]
    if options:
        cmd += ["-option", options]
    ret = subprocess.call(cmd, stdout=open(os.devnull))
    return (ret == 0)

def verify_proxy(proxy_type, proxy):
    """
    This verifies a proxy string. It works by whitelisting
    certain charackters: 0-9a-zA-Z:/?=-;~+
    """
    # protocol://host:port/stuff
    verify_str = "%s://[a-zA-Z0-9.-]+:[0-9]+/*$" % proxy_type

    if not re.match(verify_str, proxy):
            return False
    return True

def verify_no_proxy(proxy):
    """
    This verifies a proxy string. It works by whitelisting
    certain charackters: 0-9a-zA-Z:/?=-;~+
    """
    # protocol://host:port/stuff
    verify_str = "[a-zA-Z0-9.-:,]+" 

    if not re.match(verify_str, proxy):
            return False
    return True


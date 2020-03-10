# ImConfig.py (c) 2012-2018 Canonical
# Author: Gunnar Hjalmarsson <gunnarhj@ubuntu.com>
#
# Released under the GPL
#

import os
import subprocess
import locale

class ImConfig(object):
    
    def __init__(self):
        pass

    def available(self):
        return os.path.exists('/usr/bin/im-config')

    def getAvailableInputMethods(self):
        inputMethods = sorted(subprocess.check_output(['im-config', '-l']).decode().split())
        inputMethods.append('none')
        return inputMethods

    def getCurrentInputMethod(self):
        (systemConfig, userConfig, autoConfig) = \
          subprocess.check_output(['im-config', '-m']).decode().split()[:3]
        if userConfig != 'missing':
            return userConfig

        """
        no saved user configuration
        let's ask the system and save the system configuration as the user ditto
        """
        system_conf = ''
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            return None
        try:
            loc = locale.getlocale(locale.LC_CTYPE)[0]
        except ValueError:
            return None
        desktop = os.environ.get('XDG_CURRENT_DESKTOP')
        if not desktop:
            return None
        found = None
        for val in desktop.split(':'):
            if val in ['Unity', 'MATE', 'GNOME']:
                found = True
                break
        if found and desktop.split(':')[0] != 'GNOME-Flashback' \
          or loc and loc[:3] in ['zh_', 'ja_', 'ko_', 'vi_']:
            system_default = autoConfig
        else:
            system_default = 'none'
        if systemConfig == 'default':
            system_conf = system_default
        elif os.path.exists('/etc/X11/xinit/xinputrc'):
            for line in open('/etc/X11/xinit/xinputrc'):
                if line.startswith('run_im'):
                    system_conf = line.split()[1]
                    break
        if not system_conf:
            system_conf = system_default
        self.setInputMethod(system_conf)
        return system_conf

    def setInputMethod(self, im):
        subprocess.call(['im-config', '-n', im])
    
if __name__ == '__main__':
    im = ImConfig()
    print('available input methods: %s' % im.getAvailableInputMethods())
    print('current method: %s' % im.getCurrentInputMethod())
    print("setting method 'fcitx'")
    im.setInputMethod('fcitx')
    print('current method: %s' % im.getCurrentInputMethod())
    print('removing ~/.xinputrc')
    im.setInputMethod('REMOVE')

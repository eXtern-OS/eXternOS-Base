
from .Helpers import _, _n

class AbstractUI(object):
    # generic dialogs
    def error(self, summary, msg):
        return False
    def yesNoQuestion(self, summary, msg, title, default='no'):
        pass
    def message(self, summary, msg):
        return True
    
    # specific dialogs
    def askEnableSections(self, sections):
        " generic implementation, can be overridden "
        return self.yesNoQuestion(_("Enable additional components"),
                                  _n("Do you want to enable the following "
                                         "component: '%s'?",
                                         "Do you want to enable the following "
                                         "components: '%s'?",
                                         len(sections)) % ", ".join(sections))
    def askEnableChannel(self, channel, channel_info_html):
        " generic implementation, can be overridden "
        return self.yesNoQuestion(_("Enable additional software channel"),
                                  _("Do you want to enable the following "
                                    "software channel: '%s'?") % channel)
    def askInstallPackage(self):
        pass

    # install/update progress 
    def doUpdate(self):
        pass
    def doInstall(self, pkglist):
        pass

    # UI specific actions for enabling stuff

    # FIXME: the next two functions shoud go into generic code
    #        that checks for the availablility of tools
    #        like gksu or kdesudo and uses them 
    #        appropriately
    def doEnableSection(self, sections):
        pass
    def doEnableChannel(self, channelpath, channelkey):
        pass

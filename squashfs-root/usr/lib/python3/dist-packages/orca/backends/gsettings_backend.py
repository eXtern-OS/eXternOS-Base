# Orca
#
# Copyright 2015 Canonical Ltd.
# Author: Luke Yelavich <luke.yelavich@canonical.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., Franklin Street, Fifth Floor,
# Boston MA  02110-1301 USA.

"""GSettings backend for Orca settings"""

__id__        = "$Id$"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2015 Canonical Ltd."
__license__   = "LGPL"

from gi.repository.Gio import Settings
import os
from orca import settings, acss, debug

# This stores the internal Orca settings name to gsettings key name mapping,
# and the GSettings data type. NOTE: strv is an array of strings.
orcaToGSettingsMapGeneral = {
'orcaModifierKeys'             : ['orca-modifier-keys', 'strv'],
'enableEchoByCharacter'        : ['enable-echo-by-character', 'bool'],
'enableEchoByWord'             : ['enable-echo-by-word', 'bool'],
'enableEchoBySentence'         : ['enable-echo-by-sentence', 'bool'],
'enableKeyEcho'                : ['enable-key-echo', 'bool'],
'enableAlphabeticKeys'         : ['enable-alphabetic-keys', 'bool'],
'enableNumericKeys'            : ['enable-numeric-keys', 'bool'],
'enablePunctuationKeys'        : ['enable-punctuation-keys', 'bool'],
'enableSpace'                  : ['enable-space', 'bool'],
'enableModifierKeys'           : ['enable-modifier-keys', 'bool'],
'enableFunctionKeys'           : ['enable-function-keys', 'bool'],
'enableActionKeys'             : ['enable-action-keys', 'bool'],
'enableNavigationKeys'         : ['enable-navigation-keys', 'bool'],
'enableDiacriticalKeys'        : ['enable-diacritical-keys', 'bool'],
'keyboardLayout'               : ['keyboard-layout', 'int'],
'profile'                      : ['profile', 'strv'],
'progressBarUpdateInterval'    : ['progress-bar-update-interval', 'int'],
'progressBarVerbosity'         : ['progress-bar-verbosity', 'int'],
'ignoreStatusBarProgressBars'  : ['ignore-status-bar-progress-bars', 'bool'],
'enableMouseReview'            : ['enable-mouse-review', 'bool'],
'mouseDwellDelay'              : ['mouse-dwell-delay', 'int'],
'skipBlankCells'               : ['skip-blank-cells', 'bool'],
'largeObjectTextLength'        : ['large-object-text-length', 'int'],
'structuralNavigationEnabled'  : ['structural-navigation-enabled', 'bool'],
'wrappedStructuralNavigation'  : ['wrapped-structural-navigation', 'bool'],
'chatMessageVerbosity'         : ['chat-message-verbosity', 'int'],
'chatSpeakRoomName'            : ['chat-speak-room-name', 'bool'],
'chatAnnounceBuddyTyping'      : ['chat-announce-buddy-typing', 'bool'],
'chatRoomHistories'            : ['chat-room-histories', 'bool'],
'rewindAndFastForwardInSayAll' : ['rewind-and-fast-forward-in-say-all', 'bool'],
'structNavInSayAll'            : ['struct-nav-in-say-all', 'bool'],
'presentDateFormat'            : ['present-date-format', 'string'],
'presentTimeFormat'            : ['present-time-format', 'string'],
'spellcheckSpellError'         : ['spellcheck-spell-error', 'bool'],
'spellcheckSpellSuggestion'    : ['spellcheck-spell-suggestion', 'bool'],
'spellcheckPresentContext'     : ['spellcheck-present-context', 'bool'],
'findResultsVerbosity'         : ['find-results-verbosity', 'int'],
'findResultsMinimumLength'     : ['find-results-minimum-length', 'int'],
'structNavTriggersFocusMode'   : ['struct-nav-triggers-focus-mode', 'bool'],
'caretNavTriggersFocusMode'    : ['caret-nav-triggers-focus-mode', 'bool'],
'layoutMode'                   : ['layout-mode', 'bool']
}

# These settings are not found in settings.py, but are present in app and
# toolkit scripts.
orcaToGSettingsMapGeneralApp = {
'caretNavigationEnabled' : ['caret-navigation-enabled', 'bool'],
'sayAllOnLoad'           : ['say-all-on-load', 'bool'],
'inferLiveRegions'       : ['infer-live-regions', 'bool']
}

orcaToGSettingsMapGeneralBraille = {
'enabledBrailledTextAttributes'  : ['enabled-brailled-text-attributes', 'string'],
'brailleProgressBarUpdates'      : ['braille-progress-bar-updates', 'bool'],
'enableBraille'                  : ['enable-braille', 'bool'],
'enableBrailleMonitor'           : ['enable-braille-monitor', 'bool'],
'enableBrailleContext'           : ['enable-braille-context', 'bool'],
'enableFlashMessages'            : ['enable-flash-messages', 'bool'],
'brailleFlashTime'               : ['braille-flash-time', 'int'],
'flashIsPersistent'              : ['flash-is-persistent', 'bool'],
'flashIsDetailed'                : ['flash-is-detailed', 'bool'],
'enableContractedBraille'        : ['enable-contracted-braille', 'bool'],
'brailleContractionTable'        : ['braille-contraction-table', 'string'],
'disableBrailleEOL'              : ['disable-braille-eol', 'bool'],
'brailleRolenameStyle'           : ['braille-rolename-style', 'int'],
'brailleSelectorIndicator'       : ['braille-selector-indicator', 'int'],
'brailleLinkIndicator'           : ['braille-link-indicator', 'int'],
'textAttributesBrailleIndicator' : ['text-attributes-braille-indicator', 'int'],
'brailleVerbosityLevel'          : ['braille-verbosity-level', 'int'],
'brailleAlignmentStyle'          : ['braille-alignment-style', 'int']
}

orcaToGSettingsMapGeneralSound = {
'enableSound'               : ['enable-sound', 'bool'],
'soundVolume'               : ['sound-volume', 'double'],
'beepProgressBarUpdates'    : ['beep-progress-bar-updates', 'bool'],
'playSoundForRole'          : ['play-sound-for-role', 'bool'],
'playSoundForState'         : ['play-sound-for-state', 'bool'],
'playSoundForPositionInSet' : ['play-sound-for-position-in-set', 'bool'],
'playSoundForValue'         : ['play-sound-for-value', 'bool']
}

orcaToGSettingsMapGeneralSpeech = {
'speechServerFactory'          : ['speech-server-factory', 'string'],
'speechServerInfo'             : ['speech-server-info', 'strv'],
'enableSpeech'                 : ['enable-speech', 'bool'],
'enabledSpokenTextAttributes'    : ['enabled-spoken-text-attributes', 'string'],
'enableTutorialMessages'       : ['enable-tutorial-messages', 'bool'],
'enableMnemonicSpeaking'       : ['enable-mnemonic-speaking', 'bool'],
'enablePositionSpeaking'       : ['enable-position-speaking', 'bool'],
'enableSpeechIndentation'      : ['enable-speech-indentation', 'bool'],
'onlySpeakDisplayedText'       : ['only-speak-displayed-text', 'bool'],
'presentToolTips'              : ['present-tool-tips', 'bool'],
'speakBlankLines'              : ['speak-blank-lines', 'bool'],
'speakProgressBarUpdates'        : ['speak-progress-bar-updates', 'bool'],
'readFullRowInGUITable'        : ['read-full-row-in-gui-table', 'bool'],
'readFullRowInDocumentTable'   : ['read-full-row-in-document-table', 'bool'],
'readFullRowInSpreadSheet'     : ['read-full-row-in-spreadsheet', 'bool'],
'speakCellCoordinates'         : ['speak-cell-coordinates', 'bool'],
'speakCellSpan'                : ['speak-cell-span', 'bool'],
'speakCellHeaders'             : ['speak-cell-headers', 'bool'],
'speakSpreadsheetCoordinates'  : ['speak-spreadsheet-coordinates', 'bool'],
'speakMultiCaseStringsAsWords' : ['speak-multi-case-strings-as-words', 'bool'],
'speakNumbersAsDigits'         : ['speak-numbers-as-digits', 'bool'],
'speakMisspelledIndicator'     : ['speak-misspelled-indicator', 'bool'],
'useColorNames'                : ['use-color-names', 'bool'],
'sayAllStyle'                  : ['say-all-style', 'int'],
'capitalizationStyle'          : ['capitalization-style', 'string'],
'verbalizePunctuationStyle'    : ['verbalize-punctuation-style', 'int'],
'speechVerbosityLevel'         : ['speech-verbosity-level', 'int'],
'messagesAreDetailed'          : ['messages-are-detailed', 'bool'],
'enablePauseBreaks'            : ['enable-pause-breaks', 'bool']
}

class Backend:

    def __init__(self, prefsDir):
        self.baseSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/')
        self.voiceDefaults = {}

    def saveDefaultSettings(self, general, pronunciations, keybindings):
        # GSettings stores the defaults, no need to do anything here, except
        # for voice defaults, as the defaults can vary between speech
        # backends.
        if general.__contains__('voices'):
            self.voiceDefaults = general['voices']

    def getAppSettings(self, appName):
        prefs = {}
        profiles = {}

        availableProfiles = self.baseSettings.get_strv('profiles')

        for profile in availableProfiles:
            profileSettings = {}
            generalSettings = {}
            voiceSettings = {}
            pronunciationSettings = {}
            keybindingSettings = {}

            profileBaseSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/' % profile)
            profileApps = profileBaseSettings.get_strv('apps')

            if appName in profileApps:
                generalSettings = self._getGeneralSettings(profile, appName)
                voiceSettings = self._getVoiceSettings(profile, appName)

                if voiceSettings != {}:
                    generalSettings['voices'] = voiceSettings

                pronunciationSettings = self._getPronunciations(profile, appName)
                keybindingSettings = self._getKeybindings(profile, appName)

                profileSettings['general'] = generalSettings
                profileSettings['keybindings'] = keybindingSettings
                profileSettings['pronunciations'] = pronunciationSettings
                profiles[profile] = profileSettings

        if profiles != {}:
            prefs['profiles'] = profiles

        return prefs

    def saveAppSettings(self, appName, profile, general, pronunciations, keybindings):
        profiles = self.baseSettings.get_strv('profiles')

        if profile in profiles:
            profileBaseSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/' % profile)
            apps = profileBaseSettings.get_strv('apps')

            if appName not in apps:
                apps.append(appName)
                profileBaseSettings.set_strv('apps', apps)

            self._saveGeneralSettings(general, profile, appName)

            if general.__contains__('voices'):
                self._saveVoiceSettings(general['voices'], profile, appName)

            self._savePronunciations(pronunciations, profile, appName)
            self._saveKeybindings(keybindings, profile, appName)

    def saveProfileSettings(self, profile, general,
                                  pronunciations, keybindings):
        if profile is None:
            profile = 'default'

        profiles = self.baseSettings.get_strv('profiles')

        if profile not in profiles:
            profiles.append(profile)
            self.baseSettings.set_strv('profiles', profiles)

        self._saveGeneralSettings(general, profile)

        if general.__contains__('voices'):
            self._saveVoiceSettings(general['voices'], profile)

        self._savePronunciations(pronunciations, profile)
        self._saveKeybindings(keybindings, profile)

    def getGeneral(self, profile='default'):
        profiles = self.baseSettings.get_strv('profiles')
        startingProfile = self.baseSettings.get_strv('starting-profile')
        generalSettings = {}
        voiceSettings = {}

        generalSettings['startingProfile'] = startingProfile

        if profile in profiles:
            profileGeneralSettings = Settings(schema_id='org.gnome.orca.general', path='/org/gnome/orca/profile/%s/' % profile)

            generalSettings = self._getGeneralSettings(profile)
            voiceSettings = self._getVoiceSettings(profile)
            generalSettings['voices'] = voiceSettings

        generalSettings['activeProfile'] = profileGeneralSettings.get_strv('profile')

        self.baseSettings.set_strv('active-profile', generalSettings['activeProfile'])

        return generalSettings

    def getPronunciations(self, profile='default'):
        profiles = self.baseSettings.get_strv('profiles')
        pronunciationSettings = {}

        if profile in profiles:
            pronunciationSettings = self._getPronunciations(profile)

        return pronunciationSettings

    def getKeybindings(self, profile='default'):
        profiles = self.baseSettings.get_strv('profiles')
        keybindingSettings = {}

        if profile in profiles:
            keybindingSettings = self._getKeybindings(profile)

        return keybindingSettings

    def isFirstStart(self):
        """ Check if we're in first start. """

        return self.baseSettings.get_boolean('first-start')

    def _setProfileKey(self, key, value):
        # This method is currently used for setting the startingProfile setting only.
        if key == 'startingProfile':
            self.baseSettings.set_strv('starting-profile', value)

    def setFirstStart(self, value=False):
        """Set firstStart. This user-configurable settting is primarily
        intended to serve as an indication as to whether or not initial
        configuration is needed."""
        self.baseSettings.set_boolean('first-start', value)

    def availableProfiles(self):
        """ List available profiles. """
        profileList = self.baseSettings.get_strv('profiles')
        profiles = []

        for profile in profileList:
            profileSettings = Settings(schema_id='org.gnome.orca.general', path='/org/gnome/orca/profile/%s/' % profile)
            profiles.append(profileSettings.get_strv('profile'))

        return profiles

    def _getGSetting(self, gSetting, gSettingName, gSettingType):
        """Uses the GSettings get method suitable for the given
        data type."""
        if gSettingType == 'bool':
            return gSetting.get_boolean(gSettingName)
        elif gSettingType == 'int':
            return gSetting.get_int(gSettingName)
        elif gSettingType == 'string':
            return gSetting.get_string(gSettingName)
        elif gSettingType == 'strv':
            settingStrv = gSetting.get_strv(gSettingName)
            if settingStrv == []:
                return None
            return settingStrv
        elif gSettingType == 'double':
            return gSetting.get_double(gSettingName)

    def _setGSetting(self, gSetting, gSettingName, gSettingType, gSettingVal):
        """Uses the GSettings set method suitable for the given
        data type."""
        if gSettingVal is None:
            return
        debug.println(debug.LEVEL_FINEST, 'INFO: Gsettings backend: Setting %s of type %s with value %s' % (gSettingName, gSettingType, gSettingVal))
        if gSettingType == 'bool':
            gSetting.set_boolean(gSettingName, gSettingVal)
        elif gSettingType == 'int':
            gSetting.set_int(gSettingName, gSettingVal)
        elif gSettingType == 'string':
            gSetting.set_string(gSettingName, gSettingVal)
        elif gSettingType == 'strv':
            gSetting.set_strv(gSettingName, gSettingVal)
        elif gSettingType == 'double':
            gSetting.set_double(gSettingName, gSettingVal)

    def _getGeneralSettings(self, profile, app=None):
        generalSettings = {}

        if app is not None and app != '':
            generalGSettings = Settings(schema_id='org.gnome.orca.general', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecificGSettings = Settings(schema_id='org.gnome.orca.general.app', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            speechGeneralGSettings = Settings(schema_id='org.gnome.orca.general.speech', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            brailleGeneralGSettings = Settings(schema_id='org.gnome.orca.general.braille', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            soundGeneralGSettings = Settings(schema_id='org.gnome.orca.general.sound', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecific = True
        else:
            generalGSettings = Settings(schema_id='org.gnome.orca.general', path='/org/gnome/orca/profile/%s/' % profile)
            speechGeneralGSettings = Settings(schema_id='org.gnome.orca.general.speech', path='/org/gnome/orca/profile/%s/' % profile)
            brailleGeneralGSettings = Settings(schema_id='org.gnome.orca.general.braille', path='/org/gnome/orca/profile/%s/' % profile)
            soundGeneralGSettings = Settings(schema_id='org.gnome.orca.general.sound', path='/org/gnome/orca/profile/%s/' % profile)
            appSpecific = False

        for setting in orcaToGSettingsMapGeneral.keys():
            gSetting = orcaToGSettingsMapGeneral.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]

            # GSettings will always return a value, even if the user has not
            # Set one, but if a setting is not set for an app, we don't want
            # to set anything, so the global setting is used, which may be
            # different from the default.
            if appSpecific == True:
                if generalGSettings.get_user_value(gSettingName) is not None:
                    gSettingsVal = self._getGSetting(generalGSettings, gSettingName, gSettingType)
                    debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                    generalSettings[setting] = gSettingsVal
            else:
                gSettingsVal = self._getGSetting(generalGSettings, gSettingName, gSettingType)
                debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                generalSettings[setting] = gSettingsVal

        for setting in orcaToGSettingsMapGeneralSpeech.keys():
            gSetting = orcaToGSettingsMapGeneralSpeech.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]

            # GSettings will always return a value, even if the user has not
            # Set one, but if a setting is not set for an app, we don't want
            # to set anything, so the global setting is used, which may be
            # different from the default.
            if appSpecific == True:
                if speechGeneralGSettings.get_user_value(gSettingName) is not None:
                    gSettingsVal = self._getGSetting(speechGeneralGSettings, gSettingName, gSettingType)
                    debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                    generalSettings[setting] = gSettingsVal
            else:
                gSettingsVal = self._getGSetting(speechGeneralGSettings, gSettingName, gSettingType)
                debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                generalSettings[setting] = gSettingsVal

        for setting in orcaToGSettingsMapGeneralSound.keys():
            gSetting = orcaToGSettingsMapGeneralSound.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]

            # GSettings will always return a value, even if the user has not
            # Set one, but if a setting is not set for an app, we don't want
            # to set anything, so the global setting is used, which may be
            # different from the default.
            if appSpecific == True:
                if soundGeneralGSettings.get_user_value(gSettingName) is not None:
                    gSettingsVal = self._getGSetting(soundGeneralGSettings, gSettingName, gSettingType)
                    debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                    generalSettings[setting] = gSettingsVal
            else:
                gSettingsVal = self._getGSetting(soundGeneralGSettings, gSettingName, gSettingType)
                debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                generalSettings[setting] = gSettingsVal

        for setting in orcaToGSettingsMapGeneralBraille.keys():
            gSetting = orcaToGSettingsMapGeneralBraille.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]

            # GSettings will always return a value, even if the user has not
            # Set one, but if a setting is not set for an app, we don't want
            # to set anything, so the global setting is used, which may be
            # different from the default.
            if appSpecific == True:
                if brailleGeneralGSettings.get_user_value(gSettingName) is not None:
                    gSettingsVal = self._getGSetting(brailleGeneralGSettings, gSettingName, gSettingType)
                    debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                    generalSettings[setting] = gSettingsVal
            else:
                gSettingsVal = self._getGSetting(brailleGeneralGSettings, gSettingName, gSettingType)
                debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                generalSettings[setting] = gSettingsVal

        if appSpecific == True:
            for setting in orcaToGSettingsMapGeneralApp.keys():
                gSetting = orcaToGSettingsMapGeneralApp.get(setting)
                gSettingName = gSetting[0]
                gSettingType = gSetting[1]
                if appSpecificGSettings.get_user_value(gSettingName) is not None:
                    gSettingsVal = self._getGSetting(appSpecificGSettings, gSettingName, gSettingType)
                    debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting %s of type %s = %s' % (gSettingName, gSettingType, gSettingsVal))
                    generalSettings[setting] = gSettingsVal

        return generalSettings

    def _getVoiceSettings(self, profile, app=None):
        voiceSettings = {}

        if app is not None and app != '':
            appSpecific = True
        else:
            appSpecific = False

        for voice in ['default', 'uppercase', 'hyperlink', 'system']:
            if appSpecific == True:
                voiceGSettings = Settings(schema_id='org.gnome.orca.voice', path='/org/gnome/orca/profile/%s/app/%s/voice/%s/' % (profile, app, voice))
                voiceGSettingsFamily = Settings(schema_id='org.gnome.orca.voice.family', path='/org/gnome/orca/profile/%s/app/%s/voice/%s/' % (profile, app, voice))
            else:
                voiceGSettings = Settings(schema_id='org.gnome.orca.voice', path='/org/gnome/orca/profile/%s/voice/%s/' % (profile, voice))
                voiceGSettingsFamily = Settings(schema_id='org.gnome.orca.voice.family', path='/org/gnome/orca/profile/%s/voice/%s/' % (profile, voice))

            # Used to quickly determine whether a voice's settings have been
            # set and are different from the defaults
            voiceEstablished = voiceGSettings.get_boolean('established')

            voiceSetting = {}
            voiceSettingFamily = {}

            if appSpecific == False and self.voiceDefaults.__contains__(voice):
                voiceSetting = self.voiceDefaults[voice].copy()

            if voiceEstablished == True:
                if appSpecific == False and voiceSetting.__contains__('established'):
                    voiceSetting.pop('established')
                for setting in ['average-pitch', 'gain', 'rate']:
                    if voiceGSettings.get_user_value(setting) is not None:
                        gSettingsVal = voiceGSettings.get_double(setting)
                        debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting voice setting for voice %s with name %s = %s' % (voice, setting, gSettingsVal))
                        voiceSetting[setting] = gSettingsVal

                if voiceGSettingsFamily.get_boolean('family-set') == True:
                    for setting in ['name', 'locale', 'dialect']:
                        gSettingsVal = voiceGSettingsFamily.get_string(setting)
                        debug.println(debug.LEVEL_FINEST, 'INFO: GSettings backend: Getting voice family setting for voice %s with name %s = %s' % (voice, setting, gSettingsVal))
                        voiceSettingFamily[setting] = gSettingsVal
                    voiceSetting['family'] = voiceSettingFamily

            # The JSON backend uses acss the same way, not sure why, so will
            # just duplicate here to be compatible.
            if voiceSetting != {}:
                if appSpecific == True:
                    voiceSettings[voice] = voiceSetting
                else:
                    voiceSettings[voice] = acss.ACSS(voiceSetting)

        return voiceSettings

    def _getPronunciations(self, profile, app=None):
        pronunciationSettings = {}

        if app is not None and app != '':
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecific = True
        else:
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/' % profile)
            appSpecific = False

        pronunciations = baseGSettings.get_strv('pronunciations')
        for pronunciation in pronunciations:
            if appSpecific == True:
                pronunciationSetting = Settings(schema_id='org.gnome.orca.pronunciation', path='/org/gnome/orca/profile/%s/app/%s/pronunciation/%s/' % (profile, app, pronunciation))
            else:
                pronunciationSetting = Settings(schema_id='org.gnome.orca.pronunciation', path='/org/gnome/orca/profile/%s/pronunciation/%s/' % (profile, pronunciation))

            actualSetting = pronunciationSetting.get_string('actual')
            replacementSetting = pronunciationSetting.get_string('replacement')
            pronunciationSettings[pronunciation] = [actualSetting, replacementSetting]

        return pronunciationSettings

    def _getKeybindings(self, profile, app=None):
        keybindingSettings = {}

        if app is not None and app != '':
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecific = True
        else:
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/' % profile)
            appSpecific = False

        keybindings = baseGSettings.get_strv('keybindings')
        for keybinding in keybindings:
            if appSpecific == True:
                keybindingSetting = Settings(schema_id='org.gnome.orca.keybinding', path='/org/gnome/orca/profile/%s/app/%s/keybinding/%s/' % (profile, app, keybinding))
            else:
                keybindingSetting = Settings(schema_id='org.gnome.orca.keybinding', path='/org/gnome/orca/profile/%s/keybinding/%s/' % (profile, keybinding))

            keySetting = keybindingSetting.get_string('key')
            modMaskSetting = keybindingSetting.get_string('mod-mask')
            modUsedSetting = keybindingSetting.get_string('mod-used')
            clickCountSetting = keybindingSetting.get_string('click-count')
            keybindingSettings[keybinding] = [[keySetting, modMaskSetting, modUsedSetting, clickCountSetting]]

        return keybindingSettings

    def _saveGeneralSettings(self, generalSettings, profile, app=None):
        if app is not None and app != '':
            generalGSettings = Settings(schema_id='org.gnome.orca.general', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            speechGeneralGSettings = Settings(schema_id='org.gnome.orca.general.speech', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            brailleGeneralGSettings = Settings(schema_id='org.gnome.orca.general.braille', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            soundGeneralGSettings = Settings(schema_id='org.gnome.orca.general.sound', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecificGSettings = Settings(schema_id='org.gnome.orca.general.app', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecific = True
        else:
            generalGSettings = Settings(schema_id='org.gnome.orca.general', path='/org/gnome/orca/profile/%s/' % profile)
            speechGeneralGSettings = Settings(schema_id='org.gnome.orca.general.speech', path='/org/gnome/orca/profile/%s/' % profile)
            brailleGeneralGSettings = Settings(schema_id='org.gnome.orca.general.braille', path='/org/gnome/orca/profile/%s/' % profile)
            soundGeneralGSettings = Settings(schema_id='org.gnome.orca.general.sound', path='/org/gnome/orca/profile/%s/' % profile)
            appSpecific = False

        for setting in orcaToGSettingsMapGeneral.keys():
            gSetting = orcaToGSettingsMapGeneral.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]
            self._setGSetting(generalGSettings, gSettingName, gSettingType, generalSettings.get(setting))

        for setting in orcaToGSettingsMapGeneralSpeech.keys():
            gSetting = orcaToGSettingsMapGeneralSpeech.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]
            self._setGSetting(speechGeneralGSettings, gSettingName, gSettingType, generalSettings.get(setting))

        for setting in orcaToGSettingsMapGeneralSound.keys():
            gSetting = orcaToGSettingsMapGeneralSound.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]
            self._setGSetting(soundGeneralGSettings, gSettingName, gSettingType, generalSettings.get(setting))

        for setting in orcaToGSettingsMapGeneralBraille.keys():
            gSetting = orcaToGSettingsMapGeneralBraille.get(setting)
            gSettingName = gSetting[0]
            gSettingType = gSetting[1]
            self._setGSetting(brailleGeneralGSettings, gSettingName, gSettingType, generalSettings.get(setting))

        if appSpecific == True:
            for setting in orcaToGSettingsMapGeneralApp.keys():
                gSetting = orcaToGSettingsMapGeneralApp.get(setting)
                gSettingName = gSetting[0]
                gSettingType = gSetting[1]
                self._setGSetting(appSpecificGSettings, gSettingName, gSettingType, generalSettings.get(setting))

    def _saveVoiceSettings(self, voiceSettings, profile, app=None):
        if app is not None and app != '':
            appSpecific = True
        else:
            appSpecific = False

        for voice in ['default', 'uppercase', 'hyperlink', 'system']:
            if appSpecific == True:
                voiceGSettings = Settings(schema_id='org.gnome.orca.voice', path='/org/gnome/orca/profile/%s/app/%s/voice/%s/' % (profile, app, voice))
                voiceFamilyGSettings = Settings(schema_id='org.gnome.orca.voice.family', path='/org/gnome/orca/profile/%s/app/%s/voice/%s/' % (profile, app, voice))
            else:
                voiceGSettings = Settings(schema_id='org.gnome.orca.voice', path='/org/gnome/orca/profile/%s/voice/%s/' % (profile, voice))
                voiceFamilyGSettings = Settings(schema_id='org.gnome.orca.voice.family', path='/org/gnome/orca/profile/%s/voice/%s/' % (profile, voice))

            if voiceSettings.__contains__(voice):
                if voiceSettings[voice].get('established') is None:
                    for setting in ['average-pitch', 'gain', 'rate']:
                        if voiceSettings[voice].get(setting) is not None:
                            if appSpecific == True:
                                voiceGSettings.set_double(setting, voiceSettings[voice].get(setting))
                            else:
                                if voiceSettings[voice].get(setting) is not self.voiceDefaults[voice].get(setting):
                                    voiceGSettings.set_double(setting, voiceSettings[voice].get(setting))
                                    setEstablished = True

                    if appSpecific == True:
                        voiceGSettings.set_boolean('established', True)
                    elif appSpecific == False and setEstablished == True:
                        voiceGSettings.set_boolean('established', True)

                    if voiceSettings[voice].__contains__('family'):
                        for setting in ['name', 'locale', 'dialect']:
                            voiceFamilyGSettings.set_string(setting, voiceSettings[voice]['family'].get(setting))
                        voiceFamilyGSettings.set_boolean('family-set', True)

    def _savePronunciations(self, pronunciations, profile, app=None):
        if app is not None and app != '':
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecific = True
        else:
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/' % profile)
            appSpecific = False

        pronunciationList = baseGSettings.get_strv('pronunciations')
        for pronunciation in pronunciations.keys():
            if appSpecific == True:
                pronunciationSettings = Settings(schema_id='org.gnome.orca.pronunciation', path='/org/gnome/orca/profile/%s/app/%s/pronunciation/%s/' % (profile, app, pronunciation))
            else:
                pronunciationSettings = Settings(schema_id='org.gnome.orca.pronunciation', path='/org/gnome/orca/profile/%s/pronunciation/%s/' % (profile, pronunciation))

            if pronunciation not in pronunciationList:
                pronunciationList.append(pronunciation)
                pronunciationVal = pronunciations[pronunciation]
                pronunciationSettings.set_string('actual', pronunciationVal[0])
                pronunciationSettings.set_string('replacement', pronunciationVal[1])

        # Now we remove any deleted pronunciations from GSettings.
        for pronunciation in pronunciationList:
            if pronunciation not in pronunciations.keys():
                if appSpecific == True:
                    pronunciationSettings = Settings(schema_id='org.gnome.orca.pronunciation', path='/org/gnome/orca/profile/%s/app/%s/pronunciation/%s/' % (profile, app, pronunciation))
                else:
                    pronunciationSettings = Settings(schema_id='org.gnome.orca.pronunciation', path='/org/gnome/orca/profile/%s/pronunciation/%s/' % (profile, pronunciation))

                pronunciationList.remove(pronunciation)

                pronunciationSettings.reset('actual')
                pronunciationSettings.reset('replacement')

        if pronunciationList == []:
            baseGSettings.reset('pronunciations')
        else:
            baseGSettings.set_strv('pronunciations', pronunciationList)

    def _saveKeybindings(self, keybindings, profile, app=None):
        if app is not None and app != '':
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/app/%s/' % (profile, app))
            appSpecific = True
        else:
            baseGSettings = Settings(schema_id='org.gnome.orca', path='/org/gnome/orca/profile/%s/' % profile)
            appSpecific = False

        keybindingList = baseGSettings.get_strv('keybindings')
        for keybinding in keybindings.keys():
            if appSpecific == True:
                keybindingSettings = Settings(schema_id='org.gnome.orca.keybinding', path='/org/gnome/orca/profile/%s/app/%s/keybinding/%s/' % (profile, app, keybinding))
            else:
                keybindingSettings = Settings(schema_id='org.gnome.orca.keybinding', path='/org/gnome/orca/profile/%s/keybinding/%s/' % (profile, keybinding))

            if keybinding not in keybindingList:
                keybindingList.append(keybinding)

            keybindingVal = keybindings[keybinding][0]
            keybindingSettings.set_string('key', keybindingVal[0])
            keybindingSettings.set_string('mod-mask', keybindingVal[1])
            keybindingSettings.set_string('mod-used', keybindingVal[2])
            keybindingSettings.set_string('click-count', keybindingVal[3])

        # Now we remove any deleted keybindings from Gsettings.
        for keybinding in keybindingList:
            if keybinding not in keybindings.keys():
                if appSpecific == True:
                    keybindingSettings = Settings(schema_id='org.gnome.orca.keybinding', path='/org/gnome/orca/profile/%s/app/%s/keybinding/%s/' % (profile, app, keybinding))
                else:
                    keybindingSettings = Settings(schema_id='org.gnome.orca.keybinding', path='/org/gnome/orca/profile/%s/keybinding/%s/' % (profile, keybinding))

                keybindingList.remove(keybinding)

                keybindingSettings.reset('key')
                keybindingSettings.reset('mod-mask')
                keybindingSettings.reset('mod-used')
                keybindingSettings.reset('click-count')

        if keybindingList == []:
            baseGSettings.reset('keybindings')
        else:
            baseGSettings.set_strv('keybindings', keybindingList)

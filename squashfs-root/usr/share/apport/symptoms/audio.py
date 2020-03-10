# Sound/audio related problem troubleshooter/triager
# Written by David Henningsson 2010, david.henningsson@canonical.com
# Copyright Canonical Ltd 2010
# License: BSD (see /usr/share/common-licenses/BSD )

description = 'Sound/audio related problems'

import apport
from apport.hookutils import *
import re
import os
import sys
import subprocess

sys.path.append('/usr/share/apport/symptoms/')
from _audio_data import *
from _audio_checks import *

def ask_jack_and_card(report, ui):
    ''' Reports what jack and/or card the user has a problem with 
        Returns (package, card, isOutput, jack) tuple '''
    cards = parse_cards()
    jacks = []
    for c in cards:
       for j in c.jacks:
            jacks.append((c,j))
 
    # Ask for a specific jack   
    if len(jacks) > 0:
        choices = ["%s (%s)" % (j.pretty_name(), c.pretty_name()) 
            for c,j in jacks]
        choices.append("It's not listed here")
        nr = ui.choice('What hardware are you having a problem with?\n',
            choices)
        if nr is None:
            raise StopIteration
        nr = nr[0]
        if (nr < len(jacks)):
            c,j = jacks[nr]
            report['Symptom_Card'] = c.pretty_name()
            report['Symptom_Jack'] = j.pretty_name()
            return (None, c, j.isOutput(), j)

    # Okay, not a specific jack, let's ask for sound cards
    choices = []
    interfaces = ['PCI/internal', 'USB', 'Firewire', 'Bluetooth']
    for c in cards:
        choices.append("Playback from %s" % c.pretty_name())
        choices.append("Recording from %s" % c.pretty_name())
    choices.extend(["%s device not listed here" % i for i in interfaces])
    nr = ui.choice("What audio device are you having a problem with?",
        choices)
    if nr is None:
        raise StopIteration
    nr = nr[0]
    if int(nr / 2) < len(cards):
        report['Symptom_Card'] = c.pretty_name()
        return (None, cards[int(nr/2)], nr % 2 == 0, None)

    # card not detected by alsa, nor pulse
    nr = nr - 2 * len(cards)
    report['Title'] = "%s sound card not detected" % interfaces[nr]
    
    if interfaces[nr] == 'Firewire':
        if not ui.yesno('External firewire cards require manual setup.\n'
            'Documentation is here: https://help.ubuntu.com/community/HowToJACKConfiguration\n'
            'Would you like to continue reporting a bug anyway?'):
            raise StopIteration
        return ('libffado1', None, None, None)    
    
    return ('alsa-base', None, None, None)


def symptom_fails_after_a_while(report, ui, card, isOutput, jack):
    pa_start_logging()
    ui.information("Please try to reproduce the problem now. Close this dialog\n"
        "when the problem has appeared.")
    pa_finish_logging(report)
    report['Title'] = get_hw_title(card, isOutput, jack, "fails after a while")
    return 'alsa-base'

def symptom_distortion(report, ui, card, isOutput, jack):
    check_volumes(report, ui, card, isOutput, jack, 0)
    p = check_test_tones(report, ui, card, isOutput, jack)
    report['Title'] = get_hw_title(card, isOutput, jack, "Sound is distorted")
    return p

def symptom_background_noise(report, ui, card, isOutput, jack):
    check_volumes(report, ui, card, isOutput, jack)
    p = check_test_tones(report, ui, card, isOutput, jack)
    report['Title'] = get_hw_title(card, isOutput, jack, "Background noise or low volume")
    return p
    
def symptom_underrun(report, ui, card, isOutput, jack):
    pa_start_logging()
    p = check_test_tones(report, ui, card, isOutput, jack)
    if p is None:
       ui.information("Please try to reproduce the problem now. Close this dialog\n"
        "when the problem has appeared.")
    pa_finish_logging(report)
    report['Title'] = get_hw_title(card, isOutput, jack, "Underruns, dropouts or crackling sound")
    return p

def symptom_mixer(report, ui, card, isOutput, jack):
    pa_start_logging()
    ui.information("If there is a range of the mixer slider that's particularly\n"
        "problematic, please place the slider in that range before continuing.\n"
        "Also describe the problem in the bug report. Thank you!")
    pa_finish_logging(report)
    report['Title'] = get_hw_title(card, isOutput, jack, "volume slider problem")
    return 'alsa-base'

def symptom_user(report, ui, card, isOutput, jack):
    check_audio_users(report, ui)
    check_devices_in_use(report, ui)
    report['Title'] = get_hw_title(card, isOutput, None, "sound not working for all users")
    return 'alsa-base'
        
def symptom_no_sound(report, ui, card, isOutput, jack):
    check_volumes(report, ui, card, isOutput, jack)
    check_devices_in_use(report, ui)
    p = check_test_tones(report, ui, card, isOutput, jack)
    report['Title'] = get_hw_title(card, isOutput, jack, "No sound at all")
    return p

def symptom_fallback(report, ui, card, isOutput, jack):
    check_volumes(report, ui, card, isOutput, jack)
    p = check_test_tones(report, ui, card, isOutput, jack)
    report['Title'] = get_hw_title(card, isOutput, jack, 
        "Playback problem" if isOutput else "Recording problem")
    return 'alsa-base'

def symptom_noautomute(report, ui, card, isOutput, jack):
    check_volumes(report, ui, card, isOutput, jack)
    if jack is not None:
        ui.information("Now, please make sure the jack is NOT plugged in.\n"
            "After having done that, close this dialog.\n")
        report['Symptom_JackUnplugged'] = card.get_codecinfo()

        ui.information("Now, please plug the jack in.\n"
            "After having done that, close this dialog.\n")
        report['Symptom_JackPlugged'] = card.get_codecinfo()
    report['Title'] = get_hw_title(card, isOutput, jack, "No automute" if isOutput else "No autoswitch")
    return 'alsa-base'


def ask_symptom(report, ui, isOutput):
    ''' returns a function to call next, or StopIteration '''
    dirstr = "output" if isOutput else "input"

    symptom_map = [
        ('No sound at all', symptom_no_sound), 
        ('Only some of %ss are working' % dirstr, symptom_fallback),
        ('No auto-%s between %ss' % ("mute" if isOutput else "switch", dirstr), symptom_noautomute), 
        ('Volume slider, or mixer problems', symptom_mixer),
        ('Sound has bad quality (e g crackles, distortion, high noise levels etc)', None),
        ('Sound works for a while, then breaks', symptom_fails_after_a_while),
        ('Sound works for some users but not for others', symptom_user),
        ('None of the above', symptom_fallback)]

    symptom_badquality_map = [
        ('Digital clip or distortion, or "overdriven" sound', symptom_distortion),
        ('Underruns, dropouts, or "crackling" sound', symptom_underrun),
        ('High background noise, or volume is too low', symptom_background_noise)]
    
    problem = ui.choice('What particular problem do you observe?',
        [a for a,b in symptom_map])
    if problem is None:
        raise StopIteration
    desc, func = symptom_map[problem[0]]

    # subquestion for bad quality sound
    if func is None: 
        problem = ui.choice('In what way is the sound quality bad?',
            [a for a,b in symptom_badquality_map])
        if problem is None:
            raise StopIteration
        desc, func = symptom_badquality_map[problem[0]]

    report['Symptom_Type'] = desc
    return func


def run(report, ui):

    # is pulseaudio installed and running?
    package = check_pulseaudio_running(report, ui)
    if package is not None:
        return package

    # Hardware query
    (package, card, isOutput, jack) = ask_jack_and_card(report, ui)
    if package is not None:
        return package

    # Check that the pulseaudio profile is correctly set
    package, channelcount = check_pulseaudio_profile(report, ui, card, isOutput, jack)
    if package is not None:
        return package

    # Symptom query
    problem_func = ask_symptom(report, ui, isOutput)
    package = problem_func(report, ui, card, isOutput, jack)
    if package is not None:
        return package

    # Hopefully we don't come here, but if we do, use ALSA as fallback.
    return 'alsa-base'



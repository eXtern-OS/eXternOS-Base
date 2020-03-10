# Sound/audio related problem troubleshooter/triager
# Written by David Henningsson 2011, david.henningsson@canonical.com
# Copyright Canonical Ltd 2011
# License: BSD (see /usr/share/common-licenses/BSD )

import apport
from apport.hookutils import *
from _audio_mixercontrol import *
from _audio_data import *

def check_audio_users(report, ui):
    a = get_users_in_group('audio')
    report['Symptom_AudioUsers'] = ', '.join(a)
    try:
        a.remove('pulse')
    except:
        pass

    if len(a) > 0:
        yn = ui.yesno('The following users or programs can access the sound card '
            'exclusively, and even when not logged in:\n\n%s\n\n'
            'This can cause problems even for other users.\n'
            'You can fix this by uninstalling the relevant programs or by '
            'unchecking the "Use Audio Devices" checkbox for the user '
            'in the "users and groups" dialog. Do you want to continue troubleshooting?' %
            ', '.join(a))
        if not yn:
            raise StopIteration


def check_volumes(report, ui, card, isOutput, jack, maxdb=None):
    try:
        aname = 'hw:'+card.alsa_shortname
    except:
        return # this is a PA card only, can't check alsa stuff
    
    if jack is None:
        controlnames = card.get_controlnames(isOutput)
    else:
        controlnames = jack.get_controlnames()
    
    levels = set()
    mcl = MixerControlList(aname, report)
    for c in mcl.controls:
        cname = c.get_pretty_name()
        if not cname in controlnames: 
            continue
        for p in c.pchans:
            if ('muted' in c.pchans[p]) and c.pchans[p]['muted']:
                    levels.add(cname + ' is muted\n')
            if ('percent' in c.pchans[p]) and c.pchans[p]['percent'] < 70: 
                    levels.add(cname + ' is at {0}%\n'.format(c.pchans[p]['percent']))
            if (maxdb is not None) and ('dB' in c.pchans[p]) and (c.pchans[p]['dB'] > maxdb):
                    levels.add(cname + ' is at {0} dB\n'.format(c.pchans[p]['dB']))
            
    if len(levels) > 0:
        if not ui.yesno('The following mixer control(s) might be incorrectly set: \n' + '\n'.join(levels) +
         'Please try to fix that (e g by running \n"alsamixer -D ' +
         aname + '" in a terminal) and see if that solves the problem.\n' 
         'Would you like to continue troubleshooting anyway?\n'):
            raise StopIteration
    return


def check_pulseaudio_running(report, ui):
    ''' Possible outcomes: None if pulseaudio is running, 
        pulseaudio if installed but not running, or
        alsa-base if pulseaudio is not installed. '''
    if subprocess.call(['pgrep', '-u', str(os.getuid()), '-x', 'pulseaudio']) == 0:
        return None 
    if subprocess.call(['pgrep', '-u', 'pulse', '-x', 'pulseaudio']) == 0:
        ui.information('PulseAudio is running as a system-wide daemon.\n'
         'This mode of operation is not supported by Ubuntu.\n'
         'If this is not intentional, ask for help on answers.launchpad.net.')
        raise StopIteration
    try:
        if apport.packaging.get_version('pulseaudio'):
            if ui.yesno('PulseAudio seems to have crashed. '
             'Do you wish to report a bug?'):
                return 'pulseaudio'
            raise StopIteration
    except ValueError:
        pass

    # PulseAudio is not installed, so fall back to ALSA
    return 'alsa-base'


def check_pulseaudio_profile(report, ui, card, isOutput, jack):
    ''' Returns package, channelmap '''
    # ensure card was detected by PA
    if not 'pa_card' in card.__dict__:
        report['Title'] = get_hw_title(card, isOutput, jack, 
            "Pulseaudio fails to detect card")
        return 'pulseaudio', None
        
    ssname, ssprofile, channelcount = get_pa_default_profile(isOutput)

    if not card.has_sink_or_source(ssname):
        if not ui.yesno("You don't seem to have configured PulseAudio to use "
         'the card you want %s from (%s).\n You can fix '
         'that using pavucontrol or the GNOME volume control. ' 
         'Continue anyway?' % ("output" if isOutput else "input", card.pretty_name())):
            raise StopIteration
        
    if isOutput and (jack is not None) and (channelcount < jack.needed_channelcount()):
        if not ui.yesno("You don't seem to have configured PulseAudio "
         'for surround output (%s).\n You can fix that using pavucontrol '
         'or the GNOME volume control. Continue anyway?' % ssprofile):
            raise StopIteration

    return None, channelcount

 
def check_playback(report, ui, device_name, channelcount):
    ''' Returns package if it successfully finds one. '''

    ui.information('Next, a speaker test will be performed. For your safety,\n'
     'if you have headphones on, take them off to avoid damaging your ears.\n'
     'Close this dialog to hear the test tone. It should alternate between %d channels.'
     % channelcount)
    run_subprocess(report, 'Symptom_AlsaPlaybackTest', ['pasuspender', '--', 
        'speaker-test', '-l', '3', '-c', str(channelcount), '-b', '100000', 
        '-D', device_name, '-t', 'sine']) 
    result = ui.yesno('Were the test tones played back correctly?')
    report['Symptom_AlsaPlaybackTest'] = "ALSA playback test through %s %s" % (device_name, 'successful' if result else 'failed')
    if not result:
        return 'alsa-base'
 
    ui.information('Close this dialog to hear the second test tone. It should alternate between channels.')
    run_subprocess(report, 'Symptom_SpeakerTestPulse', ['speaker-test', '-l', '3', 
        '-c', str(channelcount), '-b', '100000', '-D', 'pulse', '-t', 'sine'])
    result = ui.yesno('Were the test tones played back correctly?')
    report['Symptom_PulsePlaybackTest'] = 'PulseAudio playback test %s' % ('successful' if result else 'failed')
    if not result:
        return 'pulseaudio'

    return None

def check_recording(report, ui, device_name, channelcount, tmpfile):
    ui.information('Next, up to two recording tests will be performed. Close this dialog to \n'
        'start recording some sounds. After some seconds, the recorded sound should be \n'
        'played back to you through the default sound output.')
    if os.path.exists(tmpfile):
        run_subprocess(report, 'Symptom_RemoveRecording', ['rm', tmpfile])
    run_subprocess(report, 'Symptom_AlsaRecordingTest', ['pasuspender', '--', 
        'arecord', '-q', '-f', 'cd', '-d', '7', '-D', device_name, tmpfile]) 
    run_subprocess(report, 'Symptom_AlsaRecordingPlayback', ['paplay', tmpfile])
    result = ui.yesno('Was the sound recorded correctly?')
    report['Symptom_AlsaRecordingTest'] = "ALSA recording test through %s %s" % (device_name, 'successful' if result else 'failed')
    if not result:
        return 'alsa-base'

    ui.information('Close this dialog to record some sounds for the second test.\n'
        'After some seconds, the recorded sound should be \n'
        'played back to you through the default sound output.')
    run_subprocess(report, 'Symptom_RemoveRecording', ['rm', tmpfile])
    run_subprocess(report, 'Symptom_PulseAudioRecordingTest', [
        'arecord', '-q', '-f', 'cd', '-d', '7', '-D', 'pulse', tmpfile]) 
    run_subprocess(report, 'Symptom_PulseAudioRecordingPlayback', ['paplay', tmpfile])
    result = ui.yesno('Was the sound recorded correctly?')
    report['Symptom_PulseAudioRecordingTest'] = "PulseAudio recording test through %s %s" % (device_name, 'successful' if result else 'failed')
    if not result:
        return 'pulseaudio'

    return None



def check_devices_in_use(report, ui):
    report['Symptom_DevicesInUse'] = root_command_output(['fuser','-v'] + glob.glob('/dev/snd/*'))



def check_test_tones(report, ui, card, isOutput, jack):
    channelcount = 2
    if jack is not None: 
        channelcount = jack.needed_channelcount()+1
    try:
        aname = 'plughw:' + card.alsa_shortname
    except:
        return 'pulseaudio'

    if isOutput:
       return check_playback(report, ui, aname, channelcount)
    else: 
       return check_recording(report, ui, aname, channelcount, '/tmp/audio_symptom_test.wav')


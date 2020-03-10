# Written by David Henningsson <david.henningsson@canonical.com>
# Copyright Canonical Ltd 2011. 
# Licensed under GPLv3.

import re
import os
import subprocess
from apport.hookutils import *

class SoundCard:
    def init_alsa(self, index, name, longname):
        self.alsa_index = index
        self.alsa_shortname = name
        self.alsa_longname = longname
        self.jacks = parse_jacks(index)

    def init_pa(self, pactl_card):
        self.pa_card = pactl_card
        self.pa_properties = pactl_card['Properties']
        self.pa_longname = self.pa_properties['device.description']
        if not 'jacks' in self.__dict__:
            self.jacks = []

    def pretty_name(self):
        try:
            return '%s - %s' % (self.pa_longname, self.pa_properties['alsa.card_name'])
        except:
            if not 'pa_longname' in self.__dict__:
                return self.alsa_longname
            return self.pa_longname

    def has_sink_or_source(self, ssname):
        # TODO: Check that this works for bluetooth as well,
        # and/or implement something more sophisticated
        try:
            a, b, ssname = ssname.partition(".")
            return self.pa_card['Name'].find(ssname) != -1
        except:
            return False

    def get_controlnames(self, isOutput):
        if isOutput:
            return set(["PCM", "Hardware Master", "Master", "Master Front", "Front"])
        else:
            return set(["Capture"])

    def get_codecinfo(self):
        try:
            s = ""
            for codecpath in glob.glob('/proc/asound/card%s/codec*' % self.alsa_index):
                if os.path.isfile(codecpath):    
                    s = s + read_file(codecpath)
            return s
        except:
            return ""


class Jack:
    def isOutput(self):
        if self.jack_type.find("Out") != -1: 
            return True
        if self.jack_type == "Speaker":
            return True
        return False

    def needed_channelcount(self):
        if self.jack_type == "Line Out": 
            try:
                colormap = {'Orange': 3, 'Black': 5, 'Grey': 7}
                return colormap[self.color]
            except:
                pass
        return 1

            
    def get_controlnames(self):
        if self.isOutput():
            # Do not localize
            c = set(["PCM", "Hardware Master", "Master", "Master Front", "Front"])
            if self.jack_type == "Speaker":
                c |= set(["Speaker", "Desktop Speaker"])
            nc = self.needed_channelcount()
            if nc >= 3:
                c |= set(["Center", "LFE", "Surround"])
            if nc >= 7:
                c.add("Side")

        else:
            c = set(["Capture", self.jack_type])
            if self.jack_type.find("Mic"):
                c.add(self.jack_type+" Boost")
        return c

    def pretty_name(self):
        # Hmm, this is not going to be easy to localize.
        jack_type = self.jack_type
        if jack_type == 'HP Out':
            jack_type = 'Headphone Out'
        color = self.color
        if (color != 'Unknown'):
            jack_type = '%s %s' % (color, jack_type)
    
        if self.jack_conns == 'Fixed':
            return '%s, Internal' % jack_type
        if self.connectivity == 'Sep':
            return '%s, %s, Docking station' % (jack_type, self.location)
        return '%s, %s' % (jack_type, self.location)

def parse_jacks(alsa_card_index):
    ''' Returns list of jacks on a specific card. '''
    result = []
    dirname = '/proc/asound/card%d' % int(alsa_card_index)
    for fname in os.listdir(dirname):
        if not fname.startswith('codec#'):
            continue
        codecname = ''
        for line in open(os.path.join(dirname,fname)):

            m = re.search('Codec: (.*)', line)
            if m:
                codecname = m.groups(1)[0]

            m = re.search('Pin Default 0x(.*?): \[(.*?)\] (.*?) at (.*?) (.*)', line)
            if m:
                item = Jack()
                item.codecname = codecname
                item.hex_value = m.groups(1)[0] 
                item.jack_conns = m.groups(1)[1] 
                item.jack_type = m.groups(1)[2] 
                item.connectivity = m.groups(1)[3]
                item.location = m.groups(1)[4]
                if not item.jack_conns == 'N/A':
                    result.append(item)
                continue

            m = re.search('Conn = (.*?), Color = (.*)', line)
            if m:
                item.connection = m.groups(1)[0]
                item.color = m.groups(1)[1]
    return result

def parse_alsa_cards():
    ''' Returns list of SoundCard as seen by alsa '''
    # Parse /proc/asound/cards
    alsacards = []
    try:
        for card in open('/proc/asound/cards'):
            m = re.search(' (\d+) \[(\w+)\s*\]: (.+)', card)
            if not m is None:
                s = SoundCard()
                s.init_alsa(*tuple(m.groups(1)))
                alsacards.append(s)
    except:
        pass
    return alsacards

def parse_pactl_list(pactlvalues):
    ''' Returns a structured version of pactl list '''
    # Not perfect, but good enough for its purpose
    result = dict()
    for line in pactlvalues.splitlines():
        m = re.match('^(\w+) #(\d+)', line)
        if m:
            category = m.groups(1)[0]
            index = int(m.groups(1)[1])
            if not category in result:
                result[category] = dict()
            curitem = dict()
            result[category][index] = curitem
            continue
        m = re.match('^\t(\w+.*?): (.*)', line)
        if m:
            curname = m.groups(1)[0]
            curvalue = m.groups(1)[1]
            curitem[curname] = curvalue
            continue
        m = re.match('^\t(\w+.*?):', line)
        if m:
            curname = m.groups(1)[0]
            curitem[curname] = dict()
            continue
        m = re.match('^\t\t(\w+.*?) = "(.*)"', line)
        if m:
            curpropname = m.groups(1)[0]
            curpropvalue = m.groups(1)[1]
            curitem[curname][curpropname] = curpropvalue
    return result

def add_pa_cards(cards, pactlvalues):
    if not 'Card' in pactlvalues:
        return cards

    for pa_card in pactlvalues['Card'].values():
        s = None
        try:
            index = pa_card['Properties']['alsa.card']
            for c in cards:
                if index == c.alsa_index: 
                    s = c
        except:
            pass

        if not s:
            s = SoundCard()
            cards.append(s)
        s.init_pa(pa_card)

    return cards

def get_pa_default_profile(isOutput):
    ''' Returns sinkname,sinkprofile,channelcount '''
    pactlstat = command_output(['pactl', 'info'])
    ss = "Default %s: (.*)" % ("Sink" if isOutput else "Source")

    for line in pactlstat.splitlines():
        m = re.match(ss, line)
        if m:
            sink = m.groups(1)[0]
            sinkname, dummy, sinkprofile = sink.rpartition(".")
            if dummy == '': 
                sinkname = sinkprofile
                sinkprofile = "analog-stereo" # easy processing later
            continue
    
    # TODO: handle missing sinkname/sinkprofile match?
    
    # calculate channel count
    a = sinkprofile.split('-')
    cc = 2
    if 'mono' in a:
        cc = 1
    elif 'surround' in a:
        try:
            # e g surround-51 => 51 => 5+1 => 6
            cc = int(a[len(a)-1])
            cc = cc/10 + cc % 10
        except:
            cc = 2

    return sinkname, sinkprofile, cc


def get_hw_title(card, isOutput, jack, text):
    a = []
    if jack is not None:
        # Get motherboard/system name
        try:
            f = open("/sys/class/dmi/id/product_name")
            a.append(''.join(f.readlines()).strip())
        except:
            pass
        a.append(jack.codecname)
        a.append(jack.pretty_name())

    else:
        try:
            a.append(card.alsa_longname)
        except:
            a.append(card.pretty_name())
        a.append("playback" if isOutput else "recording")

    return "[%s] %s" % (', '.join(a), text)


def get_users_in_group(groupname):
    match = "%s:(.*?):(.*?):(.*)" % groupname
    for line in open("/etc/group"):
        m = re.match(match, line)
        if not m:
            continue
        s = m.groups(1)[2]
        return s.split(',')
    # group does not exist
    return []

def pa_start_logging():
    command_output(['pacmd','set-log-level','4'])
    command_output(['pacmd','set-log-time','1'])

def pa_finish_logging(report):
    command_output(['pacmd','set-log-level','1'])
    command_output(['pacmd','set-log-time','0'])
    s = recent_syslog(re.compile("pulseaudio"))
    report['Symptom_PulseAudioLog'] = s
    return s

def run_subprocess(report, reportkey, args):
    ''' Helper function to run a subprocess.  
        Returns stdout and writes stderr, if any, to the report. '''

    # avoid localized strings
    env = os.environ
    env['LC_MESSAGES'] = 'C'
    sub_mon = subprocess.Popen(args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        universal_newlines=True)
    sub_out, sub_err = sub_mon.communicate()
    if sub_err is not None and (len(str(sub_err).strip()) > 0):
        report[reportkey+'Stderr'] = ' '.join(sub_err)
    return sub_out


def parse_cards():
    cards = parse_alsa_cards()
    pactlvalues = run_subprocess(dict(), 'PactlList',  ['pactl', 'list'])
    pactl_parsed = parse_pactl_list(pactlvalues)    
    cards = add_pa_cards(cards, pactl_parsed)
    return cards

'''test Main'''
if __name__ == '__main__':
    cards = parse_cards()
    for c in cards:
        print(c.pretty_name())
        for j in c.jacks:
            print(j.pretty_name())

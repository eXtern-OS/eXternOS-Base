# Written by David Henningsson <david.henningsson@canonical.com>
# Copyright Canonical Ltd 2010. 
# Licensed under GPLv3.

from _audio_data import run_subprocess
import re

class MixerControl: 
    ''' A simple mixer control '''
    def parse_amixer(self, amixer_data):
        self.name = amixer_data[0][len("Simple mixer control "):]
        self.amixer_dict = {}
        for line in amixer_data:
            s = line.split(":")
            if (len(s) != 2):
                continue
            self.amixer_dict[s[0].strip()] = s[1].strip()
        self.caps = set(self.amixer_dict['Capabilities'].split(" "))
        if not 'Playback channels' in self.amixer_dict:
            pchan_set = set()
        else:
            pchan_set = set(self.amixer_dict['Playback channels'].split(" - "))

        self.has_dB = True
        self.pchans = {}
        for c in pchan_set:
            self.pchans[c] = {}
            s = self.amixer_dict[c]
            m = re.search("\[([\-0-9.]+)dB\]", s)
            if m is None:
                self.has_dB = False
            else:
                self.pchans[c]['dB'] = float(m.group(1))
            if re.search("\[on\]", s):
                self.pchans[c]['muted'] = False
            if re.search("\[off\]", s):
                self.pchans[c]['muted'] = True
            m = re.search(" ?(\d+) ", s)
            if m is not None:
                self.pchans[c]['value'] = int(m.group(1))
            m = re.search("\[([\-0-9.]+)%\]", s)
            if m is not None:
                self.pchans[c]['percent'] = float(m.group(1))

    def __init__(self, amixer_data, device_name):
        self.device_name = device_name
        self.parse_amixer(amixer_data)

    def get_pretty_name(self):
        s = self.name.split("'")
        t = int(s[2].split(",")[1])
        s = s[1] 
        if (t > 0):
            return s + " " + str(t)
        return s

    def get_caps(self):
        return self.caps

    def do_get(self):
        s = run_subprocess(("amixer", "-D", self.device_name, "sget", 
           self.name))
        self.parse_amixer(s.splitlines())

    def do_set(self, *args):
        run_subprocess(("amixer", "-D", self.device_name, "--", "sset", 
           self.name) + args)

    def get_pstate(self):
        self.do_get()
        return self.pchans
            
    def set_dB(self, level):
        s = '{0:.4f}dB'.format(level)
        if ("pswitch" in self.caps) or ("pswitch-joined" in self.caps):
            self.do_set(s, "unmute")
        else:
            self.do_set(s)

    def set_mute(self, is_muted):
        if is_muted:
            self.do_set("mute")
        else: 
            self.do_set("unmute")

    def set_original(self):
        for (k,v) in self.pchans.iteritems():
            t = [] # t = [k] didn't work
            if 'value' in v: t.append(str(v['value']))
            if 'muted' in v: t.append("mute" if v['muted'] else "unmute")
            if len(t) <= 0: return
            self.do_set(*t)
       
class MixerControlList:
    def __init__(self, device_name, report):
        self.device_name = device_name
        self.parse_amixer(report)

    def parse_amixer(self, report):
        r = run_subprocess(report, "Symptom_amixer", ["amixer", "-D", self.device_name, "scontents"])
        self.controls = []
        s = []
        for line in r.splitlines():
            if (s != []) and (not line.startswith(" ")):
               self.controls.append(MixerControl(s, self.device_name))
               s = []
            s.append(line)
   
        if (s != []):
            self.controls.append(MixerControl(s, self.device_name))

    def get_control_cap(self, cap_list):
        result = []
        for c in self.controls:
            if len(c.get_caps().intersection(set(cap_list))) > 0:
                result.append(c)
        return result

    def restore_all(self):
        for c in self.controls:
            c.set_original()



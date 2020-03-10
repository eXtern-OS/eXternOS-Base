'''Detect if the current session is running under wayland'''

import os


def add_info(report, ui):
    if os.environ.get('WAYLAND_DISPLAY'):
        report.setdefault('Tags', '')
        report['Tags'] += ' wayland-session'

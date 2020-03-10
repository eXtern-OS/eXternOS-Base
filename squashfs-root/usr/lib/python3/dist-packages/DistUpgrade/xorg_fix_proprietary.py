#!/usr/bin/python
#
# this script will examine /etc/xorg/xorg.conf and
# transition from broken proprietary drivers to the free ones

import sys
import os
import logging
import time
import shutil

# main xorg.conf
XORG_CONF = "/etc/X11/xorg.conf"


def replace_driver_from_xorg(old_driver, new_driver, xorg=XORG_CONF):
    """
    this removes old_driver driver from the xorg.conf and substitutes it with
    the new_driver
    """
    if not os.path.exists(xorg):
        logging.warning("file %s not found" % xorg)
        return
    content = []
    with open(xorg) as xorg_file:
        for line in xorg_file:
            # remove comments
            s = line.split("#")[0].strip()
            # check for fglrx driver entry
            if (s.lower().startswith("driver") and
                    s.endswith('"%s"' % old_driver)):
                logging.debug("line '%s' found" % line.rstrip())
                line = '\tDriver\t"%s"\n' % new_driver
                logging.debug("replacing with '%s'" % line.rstrip())
            content.append(line)
    # write out the new version
    with open(xorg) as xorg_file:
        if xorg_file.readlines() != content:
            logging.info("saving new %s (%s -> %s)" %
                         (xorg, old_driver, new_driver))
            with open(xorg + ".xorg_fix", "w") as xorg_fix_file:
                xorg_fix_file.write("".join(content))
            os.rename(xorg + ".xorg_fix", xorg)


def comment_out_driver_from_xorg(old_driver, xorg=XORG_CONF):
    """
    this comments out a driver from xorg.conf
    """
    if not os.path.exists(xorg):
        logging.warning("file %s not found" % xorg)
        return
    content = []
    with open(xorg) as xorg_file:
        for line in xorg_file:
            # remove comments
            s = line.split("#")[0].strip()
            # check for old_driver driver entry
            if (s.lower().startswith("driver") and
                    s.endswith('"%s"' % old_driver)):
                logging.debug("line '%s' found" % line.rstrip())
                line = '#%s' % line
                logging.debug("replacing with '%s'" % line.rstrip())
            content.append(line)
    # write out the new version
    with open(xorg) as xorg_file:
        if xorg_file.readlines() != content:
            logging.info("saving new %s (commenting %s)" %
                         (xorg, old_driver))
            with open(xorg + ".xorg_fix", "w") as xorg_fix_file:
                xorg_fix_file.write("".join(content))
            os.rename(xorg + ".xorg_fix", xorg)


if __name__ == "__main__":
    if not os.getuid() == 0:
        print("Need to run as root")
        sys.exit(1)

    # we pretend to be do-release-upgrade so that apport picks up if we crash
    sys.argv[0] = "/usr/bin/do-release-upgrade"

    # setup logging
    logging.basicConfig(level=logging.DEBUG,
                        filename="/var/log/dist-upgrade/xorg_fixup.log",
                        filemode='w')

    logging.info("%s running" % sys.argv[0])

    if not os.path.exists(XORG_CONF):
        logging.info("No xorg.conf, exiting")
        sys.exit(0)

    # remove empty xorg.conf to help xorg and its auto probing logic
    # (LP: #439551)
    if os.path.getsize(XORG_CONF) == 0:
        logging.info("xorg.conf is zero size, removing")
        os.remove(XORG_CONF)
        sys.exit(0)

    # make a backup of the xorg.conf
    backup = XORG_CONF + ".dist-upgrade-" + time.strftime("%Y%m%d%H%M")
    logging.debug("creating backup '%s'" % backup)
    shutil.copy(XORG_CONF, backup)

    nvidia = False
    try:
        mods = [l.split()[0] for l in open('/proc/modules')]
    except IOError:
        sys.exit(0)
    for m in mods:
        if m == 'nvidia':
            nvidia = True
            break

    if not nvidia:
        with open(XORG_CONF) as xorg_conf_file:
            if "nvidia" in xorg_conf_file.read():
                logging.info("Removing nvidia from %s" % XORG_CONF)
                comment_out_driver_from_xorg("nvidia")

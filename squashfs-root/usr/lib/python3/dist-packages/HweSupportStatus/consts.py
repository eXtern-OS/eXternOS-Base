
import datetime
import gettext
gettext.install("update-manager")
from gettext import gettext as _


# the day on which the short support HWE stack goes EoL
HWE_EOL_DATE = datetime.date(2023, 4, 30)

# the day on which the next LTS first point release is available
# used to propose a release upgrade
NEXT_LTS_DOT1_DATE = datetime.date(2020, 7, 21)

# end of the month in which this LTS goes EoL
LTS_EOL_DATE = datetime.date(2023, 4, 30)


class Messages:
    UM_UPGRADE = _("""
There is a graphics stack installed on this system. An upgrade to a
configuration supported for the full lifetime of the LTS will become
available on %(date)s and can be installed by running 'update-manager'
in the Dash.
    """) % {'date': NEXT_LTS_DOT1_DATE.isoformat()}

    APT_UPGRADE = _("""
To upgrade to a supported (or longer-supported) configuration:

* Upgrade from Ubuntu 16.04 LTS to Ubuntu 18.04 LTS by running:
sudo do-release-upgrade %s

OR

* Switch to the current security-supported stack by running:
sudo apt-get install %s

and reboot your system.""")

    # this message is shown if there is no clear upgrade path via a
    # meta pkg that we recognize
    APT_SHOW_UNSUPPORTED = _("""
The following packages are no longer supported:
 %s

Please upgrade them to a supported HWE stack or remove them if you
no longer need them.
""")

    HWE_SUPPORTED = _("Your Hardware Enablement Stack (HWE) is "
                      "supported until %(month)s %(year)s.") % {
                          'month': LTS_EOL_DATE.strftime("%B"),
                          'year': LTS_EOL_DATE.year}

    HWE_SUPPORT_ENDS = _("""
Your current Hardware Enablement Stack (HWE) is going out of support
on %s.  After this date security updates for critical parts (kernel
and graphics stack) of your system will no longer be available.

For more information, please see:
http://wiki.ubuntu.com/1604_HWE_EOL
""") % HWE_EOL_DATE.isoformat()

    HWE_SUPPORT_HAS_ENDED = _("""
WARNING: Security updates for your current Hardware Enablement
Stack ended on %s:
 * http://wiki.ubuntu.com/1604_HWE_EOL
""") % HWE_EOL_DATE.isoformat()

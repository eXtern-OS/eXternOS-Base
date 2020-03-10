#!/bin/sh
#
# If we have an unicast .local domain, we immediately disable avahi to avoid
# conflicts with the multicast IP4LL .local domain

PATH=/bin:/usr/bin:/sbin:/usr/sbin

RUNDIR="/var/run/avahi-daemon/"
DISABLE_TAG="$RUNDIR/disabled-for-unicast-local"
NS_CACHE="$RUNDIR/checked_nameservers"

AVAHI_DAEMON_DETECT_LOCAL=1

test -f /etc/default/avahi-daemon && . /etc/default/avahi-daemon

if [ "$AVAHI_DAEMON_DETECT_LOCAL" != "1" ]; then
  exit 0
fi

ensure_rundir() {
  if [ ! -d ${RUNDIR} ] ; then 
    mkdir -m 0755 -p ${RUNDIR}
    chown avahi:avahi ${RUNDIR}
  fi
}

log_disable_warning() {
  if [ -x /usr/bin/logger ]; then
    logger -p daemon.warning -t avahi <<EOF
Avahi detected that your currently configured local DNS server serves
a domain .local. This is inherently incompatible with Avahi and thus
Avahi stopped itself. If you want to use Avahi in this network, please
contact your administrator and convince him to use a different DNS domain,
since .local should be used exclusively for Zeroconf technology.
For more information, see http://avahi.org/wiki/AvahiAndUnicastDotLocal
EOF
  fi
}

dns_reachable() {
  # If there are no nameserver entries in resolv.conf there is no dns reachable
  $(grep -q nameserver /etc/resolv.conf) || return 1;

  # If there is no local nameserver and no we have no global ip addresses
  # then we can't reach any nameservers
  if ! $(egrep -q "nameserver 127.0.0.1|::1" /etc/resolv.conf); then 
    if [ -x "$(which ip)" ]; then
      ADDRS=$(ip addr show scope global | grep inet)
      ROUTES=$(ip route show 0.0.0.0/0)
    elif [ -x "$(which ifconfig)" -a -x "$(which route)" ]; then
      # Get addresses of all running interfaces
      ADDRS=$(LC_ALL=C ifconfig | grep ' addr:')
      # Filter out all local addresses
      ADDRS=$(echo "${ADDRS}" | egrep -v ':127|Scope:Host|Scope:Link')
      # Check we have a default route
      ROUTES=$(route -n | grep '^0.0.0.0 ')
    fi
    if [ -z "${ADDRS}" -o -z "${ROUTES}" ] ; then
      return 1;
    fi
  fi

  return 0
}

dns_has_local() { 
  # Some magic to do tests 
  if [ -n "${FAKE_HOST_RETURN}" ] ; then
    if [ "${FAKE_HOST_RETURN}" = "true" ]; then
      return 0;
    else
      return 1;
    fi
  fi

  # Use timeout when calling host as workaround for LP: #1752411
  OUT=`LC_ALL=C timeout 5 host -t soa local. 2>&1`
  if [ $? -eq 0 ] ; then
    if echo "$OUT" | egrep -vq 'has no|not found'; then
      return 0
    fi
  else 
    # Checking the dns servers failed. Assuming no .local unicast dns, but
    # remove the nameserver cache so we recheck the next time we're triggered
    rm -f ${NS_CACHE}
  fi
  return 1
}

dns_needs_check() {
  TMP_CACHE="${NS_CACHE}.$$"
  RET=0

  ensure_rundir
  cat /etc/resolv.conf | grep "nameserver" | sort > ${TMP_CACHE} || return 0

  if [ -e ${NS_CACHE} ]; then 
    DIFFERENCE=$(diff -w ${NS_CACHE} ${TMP_CACHE})
    echo "${DIFFERENCE}" | grep -q '^>'
    ADDED=$?
    echo "${DIFFERENCE}" | grep -q '^<'
    REMOVED=$?
    # Avahi was disabled and no servers were removed, no need to recheck
    [ -e ${DISABLE_TAG} ] && [ ${REMOVED} -ne 0 ]  && RET=1
    # Avahi was enabled and no servers were added, no need to recheck
    [ ! -e ${DISABLE_TAG} ] && [ ${ADDED} -ne 0 ]  && RET=1
  fi

  mv ${TMP_CACHE} ${NS_CACHE}
  return ${RET};
}


enable_avahi () {
  # no unicast .local conflict, so remove the tag and start avahi again
  if [ -e ${DISABLE_TAG} ]; then
    rm -f ${DISABLE_TAG}
    if [ -d /run/systemd/system ]; then
      systemctl start avahi-daemon.socket avahi-daemon.service || true
    elif [ -x "/etc/init.d/avahi-daemon" ]; then
      /etc/init.d/avahi-daemon start || true
    fi
  fi
}

disable_avahi () {
  [ -e ${DISABLE_TAG} ] && return

  if [ -d /run/systemd/system ]; then
    systemctl stop avahi-daemon.socket avahi-daemon.service || true
    log_disable_warning
  elif [ -x "/etc/init.d/avahi-daemon" ]; then
    /etc/init.d/avahi-daemon stop || true
    log_disable_warning
  fi
  ensure_rundir
  touch ${DISABLE_TAG}
}

if ! dns_reachable ; then
  # No unicast dns server reachable, so enable avahi
  enable_avahi
  # And blow away the dns cache, so we force a recheck when the interface comes
  # up again
  rm -f ${NS_CACHE}
  exit 0
fi

# Check if the dns needs checking..
dns_needs_check || exit 0

if dns_has_local ; then
  # .local from dns server, disabling avahi
  disable_avahi
else
  # no .local from dns server, enabling avahi
  enable_avahi
fi

exit 0

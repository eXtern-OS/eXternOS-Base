#!/bin/sh

#
# (c) Copyright @2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Amarnath Chitumalla
#

LC_ALL=C
LANG=C

LOG_DIR=/var/spool/cups/tmp

# Default for number of days to keep old log files in /var/log/hp/tmp
LOGFILE_DAYS=3
MAXSIZE=1048576	# 1 GB

# Clears the logs which are less than 3 days.
if [ -d $LOG_DIR ]; then
	if ! [ -w $LOG_DIR ]; then
		exit 1
	else
		find $LOG_DIR -type f -name hp-\* -mtime +$LOGFILE_DAYS -print0  2>/dev/null | xargs -r -0 rm -f 2>/dev/null
	fi
else
	exit 1
fi


USAGE=`du -c $LOG_DIR 2>/dev/null |grep total |cut -d't' -f1`

# Clears the logs if size is greater than specified limit
while [ $USAGE -gt $MAXSIZE ]; do

	# changing the user specified LOGFILE_DAYS days to 1 days lesser.
	LOGFILE_DAYS=`expr $LOGFILE_DAYS "-" 1`

	# If same day logs are reaching Max size, deleting all log files.
	if [ $LOGFILE_DAYS -eq 0 ]; then
		find $LOG_DIR -type f -name hp-\* -print0 2>/dev/null | xargs -r -0 rm -f 2>/dev/null
		break
	else
		find $LOG_DIR -type f -name hp-\* -mtime +$LOGFILE_DAYS -print0 2>/dev/null | xargs -r -0 rm -f 2>/dev/null
	fi
	USAGE=`du -c $LOG_DIR 2>/dev/null |grep total |cut -d't' -f1`
done

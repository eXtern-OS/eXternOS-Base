
# aufs sample -- ULOOP driver

# Copyright (C) 2005-2010 Junjiro Okajima
#
# This program, aufs is free software; you can redistribute it and/or modify
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

KDIR = /lib/modules/$(shell uname -r)/build

UserLib = libuloop.a
UserAp = ulohttp ulobdev
Tgt= ${UserLib} ${UserAp}
UloopVars = /tmp/uloopvars.mk

all: drivers/block/uloop.ko ${Tgt}

# the environment variables are not inherited since 2.6.23
drivers/block/uloop.ko clean: MAKE += ULOOP_EXTRA_CFLAGS=-I${CURDIR}/include
drivers/block/uloop.ko clean: MAKE += -C ${KDIR} M=${CURDIR}/drivers/block CONFIG_BLK_DEV_ULOOP=m
drivers/block/uloop.ko:
	${MAKE} modules

clean:
	${MAKE} $@
	${RM} ${Tgt} ${UloopVars} *.o *~

UserCFLAGS = -g -Wall -D_FILE_OFFSET_BITS=64 -DNDEBUG -I${CURDIR}/include -UNDEBUG
libuloop.a: CFLAGS=${UserCFLAGS}
libuloop.a: libuloop.a(libuloop.o)

${UserAp}: CFLAGS += ${UserCFLAGS}
${UserAp}: LDLIBS += -L${CURDIR} -luloop
ulohttp: LDLIBS += -lcurl

-include priv.mk

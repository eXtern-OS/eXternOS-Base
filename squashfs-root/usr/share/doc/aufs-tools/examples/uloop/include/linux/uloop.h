/*
 * aufs sample -- ULOOP driver
 *
 * Copyright (C) 2005-2010 Junjiro Okajima
 *
 * This program, aufs is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#ifndef __ULOOP_H__
#define __ULOOP_H__

#include <linux/ioctl.h>
#include <linux/loop.h>
//#include <linux/unistd.h>
#ifndef __KERNEL__
#include <sys/types.h>
#endif

#define ULOOP_NAME	"uloop"
#define ULOOP_VERSION	"20071126"

/* loop filter variation */
#define LOOP_FILTER_ULOOP	(MAX_LO_CRYPT - 1)

/* ioctl */
#ifndef LOOP_CHANGE_FD
#define LOOP_CHANGE_FD	0x4C06
#endif
enum {UloCtlErr, UloCtlErr_Last};
enum {
	/* LOOP_CHANGE_FD is the last number in loop ioctl */
	UloCtl_Begin = (LOOP_CHANGE_FD & 0x0ff),
	UloCtl_SETBMP,
	UloCtl_READY,
	UloCtl_RCVREQ,
	UloCtl_SNDRES
};

struct ulo_ctl_setbmp {
	int	fd;
	int	pagesize;
};

struct ulo_ctl_ready {
	int		signum;
	struct pid	*pid;	/* the driver sets it automatically */
};

struct ulo_ctl_rcvreq {
	unsigned long long	start;
	int			size;
};

struct ulo_ctl_sndres {
	unsigned long long	start;
	int			size;
};

union ulo_ctl {
	struct ulo_ctl_setbmp	setbmp;
	struct ulo_ctl_ready	ready;
	struct ulo_ctl_rcvreq	rcvreq;
	struct ulo_ctl_sndres	sndres;
};

#define ULOCTL_Type	'L'
#define ULOCTL_SETBMP	_IOW(ULOCTL_Type, UloCtl_SETBMP, union ulo_ctl)
#define ULOCTL_READY	_IOR(ULOCTL_Type, UloCtl_READY, union ulo_ctl)
#define ULOCTL_RCVREQ	_IOR(ULOCTL_Type, UloCtl_RCVREQ, union ulo_ctl)
#define ULOCTL_SNDRES	_IOW(ULOCTL_Type, UloCtl_SNDRES, union ulo_ctl)

/* ---------------------------------------------------------------------- */

/* user library API */
#ifndef __KERNEL__
enum {ULO_DEV, ULO_CACHE, ULO_BITMAP, ULO_Last};
struct uloop {
	int fd[ULO_Last];
	int pagesize;
	unsigned long long tgt_size, cache_size;
};
extern const struct uloop *uloop;
#define ulo_dev_fd	({ uloop->fd[ULO_DEV]; })
#define ulo_cache_fd	({ uloop->fd[ULO_CACHE]; })
#define ulo_bitmap_fd	({ uloop->fd[ULO_BITMAP]; })

struct ulo_init {
	char *path[ULO_Last];
	int dev_flags;
	unsigned long long size;
};

int ulo_init(struct ulo_init *init);
typedef int (*ulo_cb_t)(unsigned long long start, int size, void *arg);
int ulo_loop(int sig, ulo_cb_t store, void *arg);
#endif

#endif /* __ULOOP_H__ */

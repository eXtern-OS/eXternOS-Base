/*
 * Copyright (C) 2005-2010 Junjiro R. Okajima
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

#include <linux/fs.h>
#include <linux/loop.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define _GNU_SOURCE
#include <getopt.h>

char *me;

void usage(FILE *f)
{
	fprintf(f, "%s [options] loop_dev [backend_file]\n"
		"-s, --set new_size_in_bytes\n"
		"\twhen backend_file is given, "
		"it will be expanded too while keeping the original contents\n",
		me);
}

struct option opts[] = {
	{
		.name		= "set",
		.has_arg	= 1,
		.flag		= NULL,
		.val		= 's'
	},
	{
		.name		= "help",
		.has_arg	= 0,
		.flag		= NULL,
		.val		= 'h'
	}
};

void err_size(char *name, __u64 old)
{
	fprintf(stderr, "size must be larger than current %s (%llu)\n",
		name, old);
}

int expand(char *fname, __u64 new)
{
	int err, fd;
	__u64 append;
	size_t sz;
	ssize_t ssz;
	const size_t one_g = 1 << 30;
	struct stat st;
	char *p;

	err = -1;
	fd = open(fname, O_WRONLY | O_APPEND);
	if (fd < 0)
		goto out_p;

	err = fstat(fd, &st);
	if (err)
		goto out_p;

	err = -1;
	if (new < st.st_size) {
		err_size(fname, st.st_size);
		goto out;
	}

	append = new - st.st_size;
	sz = append;
	if (sz > one_g)
		sz = one_g;
	while (1) {
		p = calloc(sz, 1);
		if (p)
			break;
		sz >>= 1;
		if (!sz) {
			errno = ENOMEM;
			goto out_p;
		}
	}

	err = 0;
	while (append > 0) {
		if (append < sz)
			sz = append;
		ssz = write(fd, p, sz);
		if (ssz == -1) {
			if (errno == EAGAIN || errno == EINTR)
				continue;
			err = -1;
			break;
		}
		append -= ssz;
	}
	free(p);
	if (err)
		goto out_p;

	err = fsync(fd);
	if (err)
		goto out_p;
	err = close(fd);
	if (!err)
		goto out; /* success */

 out_p:
	perror(fname);
 out:
	return err;
}

int main(int argc, char *argv[])
{
	int fd, err, c, i;
	__u64 old, new;
	FILE *out;
	char *dev;

	err = EINVAL;
	out = stderr;
	me = argv[0];
	new = 0;
	while ((c = getopt_long(argc, argv, "s:h", opts, &i)) != -1) {
		switch (c) {
		case 's':
			errno = 0;
			new = strtoull(optarg, NULL, 0);
			if (errno) {
				err = errno;
				perror(argv[i]);
				goto out;
			}
			break;

		case 'h':
			err = 0;
			out = stdout;
			goto err;

		default:
			perror(argv[i]);
			goto err;
		}
	}

	if (optind < argc)
		dev = argv[optind++];
	else
		goto err;

	fd = open(dev, O_RDONLY);
	if (fd < 0) {
		err = errno;
		perror(dev);
		goto out;
	}

	err = ioctl(fd, BLKGETSIZE64, &old);
	if (err) {
		err = errno;
		perror("ioctl BLKGETSIZE64");
		goto out;
	}

	if (!new) {
		printf("%llu\n", old);
		goto out;
	}

	if (new < old) {
		err = EINVAL;
		err_size(dev, old);
		goto out;
	}

	if (optind < argc) {
		err = expand(argv[optind++], new);
		if (err)
			goto out;
	}

	err = ioctl(fd, LOOP_SET_CAPACITY, new);
	if (err) {
		err = errno;
		perror("ioctl LOOP_SET_CAPACITY");
	}
	goto out;

 err:
	usage(out);
 out:
	return err;
}

# Copyright © 2012-2013 Piotr Ożarowski <piotr@debian.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
from functools import wraps
from glob import glob1
from os import remove, walk
from os.path import exists, isdir, join
from subprocess import Popen, PIPE
from shutil import rmtree, copytree
from dhpython.tools import execute
try:
    from shlex import quote
except ImportError:
    # shlex.quote is new in Python 3.3
    def quote(s):
        if not s:
            return "''"
        return "'" + s.replace("'", "'\"'\"'") + "'"

log = logging.getLogger('dhpython')


class Base:
    """Base class for build system plugins

    :attr REQUIRED_COMMANDS: list of command checked by default in :meth:is_usable,
        if one of them is missing, plugin cannot be used.
    :type REQUIRED_COMMANDS: list of strings
    :attr REQUIRED_FILES: list of files (or glob templates) required by given
        build system
    :attr OPTIONAL_FILES: dictionary of glob templates (key) and score (value)
        used to detect if given plugin is the best one for the job
    :type OPTIONAL_FILES: dict (key is a string, value is an int)
    :attr SUPPORTED_INTERPRETERS: set of interpreter templates (with or without
        {version}) supported by given plugin
    """
    DESCRIPTION = ''
    REQUIRED_COMMANDS = []
    REQUIRED_FILES = []
    OPTIONAL_FILES = {}
    SUPPORTED_INTERPRETERS = {'python', 'python3', 'python-dbg', 'python3-dbg',
                              'python{version}', 'python{version}-dbg'}

    def __init__(self, cfg):
        self.cfg = cfg

    def __repr__(self):
        return "BuildSystem(%s)" % self.NAME

    @classmethod
    def is_usable(cls):
        for command in cls.REQUIRED_COMMANDS:
            proces = Popen(['which', command], stdout=PIPE, stderr=PIPE)
            out, err = proces.communicate()
            if proces.returncode != 0:
                raise Exception("missing command: %s" % command)

    def detect(self, context):
        """Return certainty level that this plugin describes the right build system

        This method is using cls.{REQUIRED,OPTIONAL}_FILES only by default,
        please extend it in the plugin if more sofisticated methods can be used
        for given build system.

        :return: 0 <= certainty <= 100
        :rtype: int
        """
        result = 0

        required_files_num = 0
        self.DETECTED_REQUIRED_FILES = {}  # can be used in the plugin later
        for tpl in self.REQUIRED_FILES:
            found = False
            for ftpl in tpl.split('|'):
                res = glob1(context['dir'], ftpl)
                if res:
                    found = True
                    self.DETECTED_REQUIRED_FILES.setdefault(tpl, []).extend(res)
            if found:
                required_files_num += 1
        # add max 50 points depending on how many required files are available
        if self.REQUIRED_FILES:
            result += int(required_files_num / len(self.REQUIRED_FILES) * 50)

        self.DETECTED_OPTIONAL_FILES = {}
        for ftpl, score in self.OPTIONAL_FILES.items():
            res = glob1(context['dir'], ftpl)
            if res:
                result += score
                self.DETECTED_OPTIONAL_FILES.setdefault(ftpl, []).extend(res)
        if result > 100:
            return 100
        return result

    def clean(self, context, args):
        if self.cfg.test_tox:
            tox_dir = join(args['dir'], '.tox')
            if isdir(tox_dir):
                try:
                    rmtree(tox_dir)
                except Exception:
                    log.debug('cannot remove %s', tox_dir)

        for root, dirs, file_names in walk(context['dir']):
            for name in dirs:
                if name == '__pycache__':
                    dpath = join(root, name)
                    log.debug('removing dir: %s', dpath)
                    try:
                        rmtree(dpath)
                    except Exception:
                        log.debug('cannot remove %s', dpath)
                    else:
                        dirs.remove(name)
            for fn in file_names:
                if fn.endswith(('.pyc', '.pyo')):
                    fpath = join(root, fn)
                    log.debug('removing: %s', fpath)
                    try:
                        remove(fpath)
                    except Exception:
                        log.debug('cannot remove %s', fpath)

    def configure(self, context, args):
        raise NotImplementedError("configure method not implemented in %s" % self.NAME)

    def install(self, context, args):
        raise NotImplementedError("install method not implemented in %s" % self.NAME)

    def build(self, context, args):
        raise NotImplementedError("build method not implemented in %s" % self.NAME)

    def test(self, context, args):
        dirs_to_remove = set()
        for dname in ('test', 'tests'):
            src_dpath = join(args['dir'], dname)
            dst_dpath = join(args['build_dir'], dname)
            if isdir(src_dpath):
                if not exists(dst_dpath):
                    copytree(src_dpath, dst_dpath)
                    dirs_to_remove.add(dst_dpath + '\n')
                if not args['args'] and 'PYBUILD_TEST_ARGS' not in context['ENV']\
                   and (self.cfg.test_pytest or self.cfg.test_nose):
                    args['args'] = dname
        if dirs_to_remove:
            with open(join(args['home_dir'], 'build_dirs_to_rm_before_install'), 'w') as fp:
                fp.writelines(dirs_to_remove)
        if self.cfg.test_nose:
            return 'cd {build_dir}; {interpreter} -m nose {args}'
        elif self.cfg.test_pytest:
            return 'cd {build_dir}; {interpreter} -m pytest {args}'
        elif self.cfg.test_tox:
            return 'cd {build_dir}; tox -c {dir}/tox.ini -e py{version.major}{version.minor}'
        elif args['version'] == '2.7' or args['version'] >> '3.1' or args['interpreter'] == 'pypy':
            return 'cd {build_dir}; {interpreter} -m unittest discover -v {args}'

    def execute(self, context, args, command, log_file=None):
        if log_file is False and self.cfg.really_quiet:
            log_file = None
        command = command.format(**args)
        if 'PYTHONPATH' in args:
            env = dict(context['ENV'])
            env['PYTHONPATH'] = args['PYTHONPATH']
        else:
            env = context['ENV']
        log.info(command)
        return execute(command, context['dir'], env, log_file)


def shell_command(func):

    @wraps(func)
    def wrapped_func(self, context, args, *oargs, **kwargs):
        command = kwargs.pop('command', None)
        if not command:
            command = func(self, context, args, *oargs, **kwargs)
            if isinstance(command, int):  # final result
                return command
        if not command:
            log.warn('missing command '
                     '(plugin=%s, method=%s, interpreter=%s, version=%s)',
                     self.NAME, func.__name__,
                     args.get('interpreter'), args.get('version'))
            return command

        if self.cfg.quiet:
            log_file = join(args['home_dir'], '{}_cmd.log'.format(func.__name__))
        else:
            log_file = False

        quoted_args = dict((k, quote(v)) if k in ('dir', 'destdir')
                           or k.endswith('_dir') else (k, v)
                           for k, v in args.items())
        command = command.format(**quoted_args)

        output = self.execute(context, args, command, log_file)
        if output['returncode'] != 0:
            msg = 'exit code={}: {}'.format(output['returncode'], command)
            if log_file:
                msg += '\nfull command log is available in {}'.format(log_file)
            raise Exception(msg)
        return True

    return wrapped_func

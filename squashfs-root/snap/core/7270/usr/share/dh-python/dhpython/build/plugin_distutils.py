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
from glob import glob1
from os import remove
from os.path import exists, isdir, join
from shutil import rmtree
from dhpython.build.base import Base, shell_command

log = logging.getLogger('dhpython')
_setup_tpl = 'setup.py|setup-3.py'


def create_pydistutils_cfg(func):
    """distutils doesn't have sane command-line API - this decorator creates
    .pydistutils.cfg file to workaround it

    hint: if you think this is plain stupid, please don't read
    distutils/setuptools/distribute sources
    """

    def wrapped_func(self, context, args, *oargs, **kwargs):
        fpath = join(args['home_dir'], '.pydistutils.cfg')
        if not exists(fpath):
            with open(fpath, 'w', encoding='utf-8') as fp:
                lines = ['[clean]\n',
                         'all=1\n',
                         '[build]\n',
                         'build-lib={}\n'.format(args['build_dir']),
                         '[install]\n',
                         'install-layout=deb\n',
                         'install-scripts=/usr/bin\n',
                         'install-lib={}\n'.format(args['install_dir']),
                         '[easy_install]\n',
                         'allow_hosts=None\n']
                log.debug('pydistutils config file:\n%s', ''.join(lines))
                fp.writelines(lines)
        context['ENV']['HOME'] = args['home_dir']
        return func(self, context, args, *oargs, **kwargs)

    wrapped_func.__name__ = func.__name__
    return wrapped_func


class BuildSystem(Base):
    DESCRIPTION = 'Distutils build system'
    SUPPORTED_INTERPRETERS = {'python', 'python3', 'python{version}',
                              'python-dbg', 'python3-dbg', 'python{version}-dbg',
                              'pypy'}
    REQUIRED_FILES = [_setup_tpl]
    OPTIONAL_FILES = {'setup.cfg': 1,
                      'requirements.txt': 1,
                      'PKG-INFO': 10,
                      '*.egg-info': 10}

    def detect(self, context):
        result = super(BuildSystem, self).detect(context)
        if _setup_tpl in self.DETECTED_REQUIRED_FILES:
            context['args']['setup_py'] = self.DETECTED_REQUIRED_FILES[_setup_tpl][0]
        else:
            context['args']['setup_py'] = 'setup.py'
        return result

    @shell_command
    @create_pydistutils_cfg
    def clean(self, context, args):
        super(BuildSystem, self).clean(context, args)
        dpath = join(context['dir'], 'build')
        isdir(dpath) and rmtree(dpath)
        if exists(args['interpreter'].binary()):
            return '{interpreter} {setup_py} clean {args}'
        return 0  # no need to invoke anything

    @shell_command
    @create_pydistutils_cfg
    def configure(self, context, args):
        return '{interpreter} {setup_py} config {args}'

    @shell_command
    @create_pydistutils_cfg
    def build(self, context, args):
        return '{interpreter.binary_dv} {setup_py} build {args}'

    @shell_command
    @create_pydistutils_cfg
    def install(self, context, args):
        # remove egg-info dirs from build_dir
        for fname in glob1(args['build_dir'], '*.egg-info'):
            fpath = join(args['build_dir'], fname)
            rmtree(fpath) if isdir(fpath) else remove(fpath)

        return '{interpreter.binary_dv} {setup_py} install --root {destdir} {args}'

    @shell_command
    @create_pydistutils_cfg
    def test(self, context, args):
        if not self.cfg.custom_tests:
            fpath = join(args['dir'], args['setup_py'])
            with open(fpath, 'rb') as fp:
                if fp.read().find(b'test_suite') > 0:
                    # TODO: is that enough to detect if test target is available?
                    return '{interpreter} {setup_py} test {args}'
        return super(BuildSystem, self).test(context, args)

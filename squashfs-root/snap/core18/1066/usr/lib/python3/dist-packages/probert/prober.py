# Copyright 2015 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from probert.storage import Storage
from probert.network import Network


class Prober():
    def __init__(self, options, results={}):
        self.options = options
        self.results = results

        ''' build a list of probe_ methods of this class,
            excluding probe_all so we don't recurse.
            This allows probe_all method to call all probe_
            methods as we add it without maintaining a list
            in the code.
        '''
        exclude = ['probe_all']
        self.probes = [getattr(self, fn) for fn in
                       filter(lambda x: callable(getattr(self, x)) and
                              x.startswith('probe_') and
                              x not in exclude, dir(self))]

    def probe(self):
        # find out what methods to call by looking options
        for fn in [x for x in dir(self.options)
                   if self.options.__getattribute__(x) is True]:
            getattr(self, fn)()

    def probe_all(self):
        for fn in self.probes:
            fn()

    def probe_storage(self):
        storage = Storage()
        results = storage.probe()
        self.results['storage'] = results

    def probe_network(self):
        network = Network()
        results = network.probe()
        self.results['network'] = results

    def get_results(self):
        return self.results

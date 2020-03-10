var should = require('should');
var x11 = require('x11');
var async = require('async');
var EVMW = require('../lib/ewmh');
var get_property = require('x11-prop').get_property;
var os = require('os');

describe('setting properties...', function() {
    before(function(done) {
        var self = this;
        async.parallel(
            [
                function create_client_1(cb) {
                    x11.createClient(cb);
                },
                function create_client_2(cb) {
                    x11.createClient(cb);
                }
            ],
            function(err, displays) {
                should.not.exist(err);
                self.X1 = displays[0].client;
                self.root = displays[0].screen[0].root;
                self.X2 = displays[1].client;
                displays[1].screen[0].root.should.equal(self.root);
                self.ewmh = new EVMW(self.X1, self.root);
                self.wid1 = self.X1.AllocID();
                self.wid2 = self.X1.AllocID();
                self.wid3 = self.X1.AllocID();
                self.X2.ChangeWindowAttributes(self.root, { eventMask : x11.eventMask.PropertyChange });
                done();
            }
        );
    });

    it('set_supported should set _NET_SUPPORTED correctly', function(done) {
        var self = this;
        var atoms = [ '_NET_WM_ACTION_MOVE', '_NET_WM_ACTION_RESIZE', '_NET_WM_ACTION_MINIMIZE' ];
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms._NET_SUPPORTED);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                async.map(
                    atoms,
                    function(prop, cb) {
                        self.X1.InternAtom(false, prop, cb);
                    },
                    function(err, results) {
                        should.not.exist(err);
                        data.should.eql(results);
                        done();
                    }
                );
            });

        });

        this.ewmh.set_supported(atoms);
    });

    it('set_number_of_desktops should set _NET_NUMBER_OF_DESKTOPS correctly', function(done) {
        var self = this;
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms._NET_NUMBER_OF_DESKTOPS);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                data.should.eql([ 2 ]);
                done();
            });

        });

        this.ewmh.set_number_of_desktops(2);
    });

    it('set_current_desktop should set _NET_CURRENT_DESKTOP correctly', function(done) {
        var self = this;
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms._NET_CURRENT_DESKTOP);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                data.should.eql([ 1 ]);
                done();
            });

        });

        this.ewmh.set_current_desktop(1);
    });

    it('update_window_list should set _NET_CLIENT_LIST correctly', function(done) {
        var self = this;
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms._NET_CLIENT_LIST);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                data.should.eql([ self.wid1, self.wid2, self.wid3 ]);
                done();
            });

        });

        this.ewmh.update_window_list([ this.wid1, this.wid2, this.wid3 ]);
    });

    it('update_window_list should set _NET_CLIENT_LIST_STACKING correctly', function(done) {
        var self = this;
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms._NET_CLIENT_LIST_STACKING);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                data.should.eql([ self.wid1, self.wid3, self.wid1 ]);
                done();
            });

        });

        this.ewmh.update_window_list_stacking([ this.wid1, this.wid3, this.wid1 ]);
    });

    it('set_pid should set _NET_WM_PID correctly', function(done) {
        var self = this;
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms._NET_WM_PID);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                data.should.eql([ process.pid ]);
                done();
            });

        });

        this.ewmh.set_pid(this.root);
    });

    it('set_hostname should set WM_CLIENT_MACHINE correctly', function(done) {
        var self = this;
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms.WM_CLIENT_MACHINE);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                data.toString().should.eql(os.hostname());
                done();
            });

        });

        this.ewmh.set_hostname(this.root);
    });

    it('set_active_window should set _NET_ACTIVE_WINDOW correctly', function(done) {
        var self = this;
        this.X2.once('event', function(ev) {
            ev.atom.should.equal(self.X1.atoms._NET_ACTIVE_WINDOW);
            get_property(self.X1, self.root, ev.atom, function(err, data) {
                should.not.exist(err);
                data.should.eql([ self.wid2 ]);
                done();
            });

        });

        this.ewmh.set_active_window(this.wid2);
    });

    after(function(done) {
        async.each(
            [ this.X1, this.X2 ],
            function(X, cb) {
                X.terminate();
                X.on('end', cb);
            },
            done
        );
    });
});

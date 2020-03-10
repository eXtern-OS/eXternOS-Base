var should = require('should');
var async = require('async');
var x11 = require('x11');
var EVMW = require('../lib/ewmh');

describe('EWMH creation', function() {

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
                done();
            }
        );

    });

    it('should emit error in case another wm is listening for SubstructureRedirect  ', function(done) {
        var self = this;
        this.X2.ChangeWindowAttributes(this.root, { eventMask: this.X2.eventMask.SubstructureRedirect });
        setTimeout(function() {
            var ewmh = new EVMW(self.X1, self.root);
            ewmh.once('error', function(err) {
                should.exist(err);
                err.x11_error.message.should.equal('Bad access');
                self.X2.ChangeWindowAttributes(self.root, { eventMask: 0 });
                done();
            });
        }, 200);
    });

    it('should start listening for SubstructureRedirect events in root if no other wm', function(done) {
        var self = this;
        this.X2.InternAtom(false, '_NET_ACTIVE_WINDOW', function(err, atom) {
            should.not.exist(err);
            var ewmh = new EVMW(self.X1, self.root);
            var wid = self.X1.AllocID();
            ewmh.once('ActiveWindow', function(w) {
                w.should.equal(wid);
                done();
            });

            var raw = new Buffer(32);
            raw.writeInt8(33, 0); /* ClientMessage code */
            raw.writeInt8(32, 1); /* Format */
            raw.writeUInt16LE(0, 2); /* Seq n */
            raw.writeUInt32LE(wid, 4); /* Window ID */
            raw.writeUInt32LE(atom, 8); /* Message Type */
            raw.writeUInt32LE(1, 12); /* data[0] Message from an application */
            raw.writeUInt32LE(0, 16); /* data[1]: current time */
            raw.writeUInt32LE(0, 20); /* data[2] */
            raw.writeUInt32LE(0, 24); /* data[3] */
            raw.writeUInt32LE(0, 28); /* data[4] */
            self.X2.SendEvent(self.root, false, self.X2.eventMask.SubstructureRedirect, raw);
        });
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

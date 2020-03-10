var util = require('util');
var async = require('async');
var encoder = require('./encoder');

/*
 * @param X client
 * @param wid
 * @param prop (name or atom)
 * @param type (name or atom)
 * @param data
 * @param null_terminated (optional)
 * @param cb, function(err)
 */
function set_property(X, wid, prop, type, format, data, null_terminated, cb) {

    if (typeof null_terminated === 'function') {
        cb = null_terminated;
        null_terminated = undefined;
    }

    async.parallel(
        [
            function get_prop_atom(cb) {
                if (typeof prop === 'string') {
                    X.InternAtom(false, prop, cb);
                } else {
                    cb(undefined, prop);
                }
            },
            function get_type_atom(cb) {
                if (typeof type === 'string') {
                    X.InternAtom(false, type, cb);
                } else {
                    cb(undefined, type);
                }
            }
        ],
        function(err, results) {
            if (err) {
                if (cb) {
                    cb(err);
                }

                return;
            }


            _set_property(X, wid, results[0], results[1], format, data, null_terminated, cb);
        }
    );
}

function _set_property(X, wid, prop, type, format, data, null_terminated, cb) {
    var err;
    var encoded_data = encoder.encode(X.atom_names[type], data, null_terminated);
    if (util.isError(encoded_data)) {
        err = encoded_data;
    } else {
        X.ChangeProperty(0, wid, prop, type, format, encoded_data);
    }

    if (cb) {
        cb(err);
    }
}

module.exports = set_property;

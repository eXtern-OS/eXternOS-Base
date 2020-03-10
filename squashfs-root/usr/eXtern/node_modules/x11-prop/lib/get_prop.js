var util = require('util');
var async = require('async');
var decoder = require('./decoder');

/*
 * @param X client
 * @param wid
 * @param prop (name or atom)
 * @param type (name or atom) (optional)
 * @param cb. function(err, res)
 */
function get_property(X, wid, prop, type, cb) {
    if (typeof type === 'function') {
        cb = type;
        type = undefined;
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
                if (!type) {
                    /* AnyPropertyType */
                    type = 0;
                }

                if (typeof type === 'string') {
                    X.InternAtom(false, type, cb);
                } else {
                    cb(undefined, type);
                }
            }
        ],
        function(err, results) {
            if (err) {
                return cb(err);
            }

            _get_property(X, wid, results[0], results[1], cb);
        }
    );
}

function _get_property(X, wid, prop, type, cb) {

    /* If property is None just return */
    if (prop === 0) {
        return cb(undefined, []);
    }

    X.GetProperty(0, wid, prop, type, 0, 1000000000, function(err, prop_value) {
        if (err) {
            return cb(err);
        }

        /* AnyPropertyType in this case it means that there's no data */
        if (prop_value.type === 0) {
            return cb(undefined, []);
        }

        X.GetAtomName(prop_value.type, function(err, name) {
            if (err) {
                return cb(err);
            }

            var decoded_data = decoder.decode(name, prop_value.data);
            if (util.isError(decoded_data)) {
                cb(decoded_data);
            } else {
                /* If ATOM property, get their names so they're cached in x11 library */
                if (name === 'ATOM') {
                    async.each(
                        decoded_data,
                        function(atom, cb) {
                            X.GetAtomName(atom, cb);
                        },
                        function(err) {
                            if (err) {
                                cb(err);
                            } else {
                                cb(undefined, decoded_data, prop_value.type);
                            }
                        }
                    );
                } else {
                    cb(undefined, decoded_data, prop_value.type);
                }
            }
        });
    });
}

module.exports = get_property;

var Iconv = require('iconv').Iconv;
var xsettings = require('x11-xsettings');

exports.encode = function(type, data, null_terminated) {
    var result;
    var new_data;
    var length;
    switch (type) {
        case 'STRING':
            var converter = new Iconv('UTF-8', 'ISO-8859-1');
            new_data = [];
            length = 0;
            data.forEach(function(el, index) {
                var conv_buf = converter.convert(new Buffer(el));
                new_data.push(conv_buf);
                length += conv_buf.length;
                if ((index !== data.length - 1) || null_terminated) {
                    new_data.push(new Buffer([ 0 ]));
                    ++ length;
                }
            });

            result = Buffer.concat(new_data, length);
        break;

        case 'UTF8_STRING':
            new_data = [];
            length = 0;
            data.forEach(function(el, index) {
                new_data.push(new Buffer(el));
                length += el.length;
                if ((index !== data.length - 1) || null_terminated) {
                    new_data.push = new Buffer([ 0 ]);
                    ++ length;
                }
            });

            result = Buffer.concat(new_data, length);
        break;

        case 'ATOM':
        case 'INTEGER':
        case 'CARDINAL':
        case 'WINDOW':
            var len = data.length;
            if (len > 0) {
                result = new Buffer(4 * len);
                data.forEach(function(el, index) {
                    result.writeUInt32LE(el, 4 * index);
                });
            } else {
                result = [];
            }
        break;

        case 'WM_STATE':
            result = new Buffer(8);
            result.writeUInt32LE(data.state, 0);
            if (!data.icon) {
                data.icon = 0;
            }

            result.writeUInt32LE(data.icon, 4);
        break;

        case '_XSETTINGS_SETTINGS':
            result = xsettings.encode(data);
        break;

        default:
            result = new Error('Unsupported type: ' + type);
    }

    return result;
};

var Iconv = require('iconv').Iconv;
var xsettings = require('x11-xsettings');

exports.decode = function(type, data) {
    var i;
    var result;
    var init = 0;
    switch (type) {
        case 'STRING':
            result = [];
            var converter = new Iconv('ISO-8859-1', 'UTF-8');
            for (i = 0; i < data.length; ++i) {
                if (data[i] === 0) {
                    result.push(converter.convert(data.slice(init, i)));
                    init = i + 1;
                }
            }

            if (init < data.length) {
                result.push(converter.convert(data.slice(init)));
            }
        break;

        case 'UTF8_STRING':
            result = [];
            for (i = 0; i < data.length; ++i) {
                if (data[i] === 0) {
                    result.push(data.toString('utf8', init, i));
                    init = i + 1;
                }
            }

            if (init < data.length) {
                result.push(data.toString('utf8', init));
            }
        break;

        case 'ATOM':
        case 'INTEGER':
  	case 'CARDINAL':
        case 'WINDOW':
            result = [];
            for (i = 0; i < data.length; i += 4) {
               result.push(data.readUInt32LE(i));
            }

        break;

        case 'WM_STATE':
            if (data.length !== 8) {
                result = new Error('Invalid WM_STATE data. Length: ' + data.length);
            } else {
                result = {
                    state : data.readUInt32LE(0),
                    icon : data.readUInt32LE(4)
                };
            }
        break;

        case '_XSETTINGS_SETTINGS':
            result = xsettings.decode(data);
        break;

        default:
            result = new Error('Unsupported type: ' + type);
	}

    return result;
};

function pad4(len) {
  return ((len + 3) >> 2) << 2;
}

function decode(buf) {
  var offset = 0;
  var endian = buf[0];
  var readByte = function() {
    return buf[offset++];
  };
  var readInt = function() {
    var res;
    if (endian)
      res = buf.readUInt32BE(offset);
    else
      res = buf.readUInt32LE(offset);
    offset += 4;
    return res;
  };

  var readShort = function() {
    var res;
    if (endian)
      res = buf.readUInt16BE(offset);
    else
      res = buf.readUInt16LE(offset);
    offset += 2;
    return res;
  };

  var readString = function(len) {
    var pad = pad4(len);
    var str = buf.toString('utf8', offset, offset + len);
    offset += pad;
    return str;
  };

  var readValue = [
    function() { // int
      return readInt();
    },
    function () { // string
      return readString(readInt());
    },
    function() { // color
      var res = {};
      res.red   = readShort();
      res.blue  = readShort();
      res.green = readShort();
      var alpha = readShort();
      if (alpha != 65535)
        res.alpha = alpha;
      return res;
    }
  ];

  offset = 4;
  var serial = readInt();
  var nkeys  = readInt();
  var settings = {
    serial : serial
  };

  for (var i=0; i < nkeys; ++i) {
    setting = {};
    setting.type = readByte();
    readByte(); // unused
    var name = readString(readShort());
    setting.serial = readInt();
    setting.value  = readValue[setting.type]();
    settings[name] = setting;
  }
  return settings;
}

function encode(settings, endian) {

  var offset;
  var data;

  function writeByte(b) {
    data.writeUInt8(b, offset ++);
  }

  function writeShort(s) {
    if (endian) {
      data.writeUInt16BE(s, offset);
    } else {
      data.writeUInt16LE(s, offset);
    }

    offset += 2;
  }

  function writeInt(i) {
    if (endian) {
      data.writeUInt32BE(i, offset);
    } else {
      data.writeUInt32LE(i, offset);
    }

    offset += 4;
  }

  function writeString(name) {
    var len = data.write(name, offset);
    offset += pad4(len);
  }


  function encode_setting(name, setting) {
    var length = 8 + pad4(name.length);
    switch (setting.type) {
      case 0: // int
        length += 4;
      break;

      case 1: // string
        length += 4;
        length += pad4(setting.value.length);
      break;

      case 2: // color
        length += 8;
      break;
    }

    data = new Buffer(length);
    offset = 0;

    writeByte(setting.type, data);
    ++ offset;
    writeShort(name.length);
    writeString(name);
    writeInt(setting.serial);

    switch (setting.type) {
      case 0: // int
        writeInt(setting.value);
      break;

      case 1: // string
        writeInt(setting.value.length);
        writeString(setting.value);
      break;

      case 2: // color
        writeShort(setting.value.red);
        writeShort(setting.value.blue);
        writeShort(setting.value.green);
        writeShort(setting.value.alpha);
      break;
    }

    return data;
  }

  offset = 0;
  data = new Buffer(12);
  writeByte(endian);
  offset = 4;
  writeInt(settings.serial);
  var attrs = Object.keys(settings);
  writeInt(attrs.length - 1);

  var total_offset = offset;

  var setts = [ data ];
  attrs.forEach(function(attr) {
    if (attr !== 'serial') {
      setts.push(encode_setting(attr, settings[attr]));
      total_offset += offset;
    }
  });

  return Buffer.concat(setts, total_offset);
}

module.exports.encode = encode;
module.exports.decode = decode;

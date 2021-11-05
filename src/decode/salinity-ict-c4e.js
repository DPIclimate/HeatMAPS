function round(number, precision) {
    var shift = function (number, precision, reverseShift) {
        if (reverseShift) {
            precision = -precision;
        }
        var numArray = ("" + number).split("e");
        return +(numArray[0] + "e" + (numArray[1] ? (+numArray[1] + precision) : precision));
    };
    return shift(Math.round(shift(number, precision, false)), precision, true);
}

// From https://github.com/brady-aiello/Seeeduino_LoRaWAN_for_hybrid_gateways/blob/master/Seeeduino-LoRaWAN-GPS-app/payload_function.js
function readFloat32BE(payload, offset) {
    bytes = payload[offset] << 24 | payload[offset + 1] << 16 | payload[offset + 2] << 8 | payload[offset + 3];

    var sign = (bytes & 0x80000000) ? -1 : 1;
    var exponent = ((bytes >> 23) & 0xFF) - 127;
    var significand = (bytes & ~(-1 << 23));

    if (exponent == 128)
        return sign * ((significand) ? Number.NaN : Number.POSITIVE_INFINITY);

    if (exponent == -127) {
        if (significand == 0) return sign * 0.0;
        exponent = -126;
        significand /= (1 << 22);
    } else significand = (significand | (1 << 23)) / (1 << 23);

    return sign * significand * Math.pow(2, exponent);
}

function readInt32BE(payload, offset) {
    return payload[offset] << 24 | payload[offset + 1] << 16 | payload[offset + 2] << 8 | payload[offset + 3];
}

function readInt16BE(payload, offset) {
    var v = payload[offset] << 8 | payload[offset + 1];
    if (payload[offset] & 0x80) {
        v = 0xFFFF0000 | v;
    }
    return v;
}

//PAYLOAD DECODER ICT SNODE WITH SALINITY C4E (DPI decoder)
//V2 new board
function decodeUplink(input) {

    if (input.fPort != 1) {
        return {
            warnings: ["f_port was not 1, ignoring message."]
        }
    }

    var payload = input.bytes;

    // get data 
    var rtc = readInt32BE(payload, 0); // payload.slice(0, 4).readInt32BE(); //RTC 6
    var battery = readInt16BE(payload, 4); // payload.slice(4, 6).readInt16BE(); //batt 5
    var solar = readInt16BE(payload, 6); // payload.slice(6, 8).readInt16BE(); //solar 7
    var command = payload[9]; // payload.slice(9, 10).readInt8(); //command slot na
    var temperature = readFloat32BE(payload, 10); // payload.slice(10, 14).readFloatBE(); //temp 3
    var conductivity = readFloat32BE(payload, 14); // payload.slice(14, 18).readFloatBE(); //conductivity 1
    var salinity = readFloat32BE(payload, 18); // payload.slice(18, 22).readFloatBE(); //salinity 2
    var tdskcl = readFloat32BE(payload, 22); // payload.slice(22, 26).readFloatBE(); //TDS - KCl 4

    battery = battery / 1000;
    solar = solar / 1000;

    battery = round(battery, 2);
    solar = round(solar, 2);

    temperature = round(temperature, 2);
    conductivity = round(conductivity, 4);
    salinity = round(salinity, 2);
    tdskcl = round(tdskcl, 2)

    var data = {
        data: {
            salinity: salinity,
            conductivity: conductivity,
            temperature: temperature,
            tdskcl: tdskcl,
            battery: battery,
            rtc: rtc,
            solar: solar
        }
    };

    return data;
}

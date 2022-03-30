function payload2Float32(payload) {
    var sign = (payload & 0x80000000) ? -1 : 1;
    var exponent = ((payload >> 23) & 0xFF) - 127;
    var significand = (payload & ~(-1 << 23));
    if (exponent == 128) 
        return sign * ((significand) ? Number.NaN : Number.POSITIVE_INFINITY);
    if (exponent == -127) {
        if (significand === 0) return sign * 0.0;
        exponent = -126;
        significand /= (1 << 22);
    } else significand = (significand | (1 << 23)) / (1 << 23);
    return sign * significand * Math.pow(2, exponent);
}

function decodeUplink(input) {
  var payload = input.bytes;
  var RTC = (payload[0]<<24 | payload[1]<<16 | payload[2]<<8 | payload [3]);
  var battery = ((payload[4]<<8 | payload[5])/1000);
  var command = (payload[6]);
  var temperature = (Math.round(payload2Float32(payload[7]<<24 | payload[8]<<16 | payload[9]<<8 | payload[10]<<0)*100)/100);
  var conductivity = (Math.round(payload2Float32(payload[11]<<24 | payload[12]<<16 | payload[13]<<8 | payload[14]<<0)*100)/100);
  var salinity = (Math.round(payload2Float32(payload[15]<<24 | payload[16]<<16 | payload[17]<<8 | payload[18]<<0)*100)/100);
  var tdskcl = (Math.round(payload2Float32(payload[19]<<24 | payload[20]<<16 | payload[21]<<8 | payload[22]<<0)*100)/100);
  return {
      data: {
          rtc: RTC,
          battery: battery,
          temperature: temperature,
          conductivity: conductivity,
          salinity: salinity,
          tdskcl: tdskcl
      }
  }
}

from spatial_interpolation import pull_data, generate_map

TS_IDS = ['852912', '882564', '882600', '882601', '882602', 
        '882562', '852907', '882556', '882603', '851289']
TS_KEYS = ['VAHH1R8V29N77F5V', '7V8N0R6RNXAM38AY', 'H14YCHM913E9Q242', 
        'UT0R2RHPOKMKSLBP', 'SIJW6BRY6LF2QANF', 'QQRSK8OWK5V891XE',
        'T0TWZSVP10HEKE54', 'RVYDN22IYBB4YLIV', 'C96I124C9YD0DYPR',
        '621ISJJ2IMY6OMNJ']
timezone = "Australia/Sydney"
startTime = "2021-08-02 13:00:00"

dataset = pull_data.Data()
dataset.thingspeak_request(TS_IDS, TS_KEYS, timezone, start=startTime, date=True, results=5)
dataframe = dataset.parse_thingspeak_request(start=startTime)

print(dataframe)

mapExtent = [150.1166, 150.1832, -35.7089, -35.6697]
POI = "Salinity (g/Kg)"

si = generate_map.Map()
si.generate_map(POI, dataframe, extent=mapExtent)


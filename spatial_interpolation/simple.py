from spatial_interpolation import pull_data, generate_map

TS_IDS = ["852912", "882564"]
TS_KEYS = ["VAHH1R8V29N77F5V", "7V8N0R6RNXAM38AY"]
timezone = "Australia/Sydney"
startTime = "2021-08-01 16:00:00"

dataset = pull_data.Data()
dataset.thingspeak_request(TS_IDS, TS_KEYS, timezone, start=startTime, date=True, results=5)
dataframe = dataset.parse_thingspeak_request(start=startTime)

mapExtent = [150.1166, 150.1832, -35.7089, -35.6697]
POI = "Salinity (g/Kg)"

si = generate_map.Map()
#si.generate_interpolation(POI, dataframe)


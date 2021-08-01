import aiohttp
import asyncio
import json
import pandas as pd
import datetime 

class Data:
    def __init__(self):
        self.response = []
        self.statusCodes = []

    def thingspeak_request(self, ids, keys, timezone, start=None, end=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), date=False, results=10):
        urls = []
        if date:
            for ID, key in zip(ids, keys):
                urls.append(self.request("https://api.thingspeak.com"
                    "/channels/{}/feeds.json?api_key={}&start={}"
                    "&end={}&timezone={}".format(ID, key, start, end, timezone)))
        else:
            for ID, key in zip(ids, keys):
                urls.append(self.request("https://api.thingspeak.com"
                "/channels/{}/feeds.json?api_key={}&results={}&timezone={}".format(ID, key, results, timezone)))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*urls))
        loop.close()


    async def request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.statusCodes.append(response.status)
                self.response.append(await response.text())


    def parse_thingspeak_request(self, start, alignTime="30min", interpolateLimit=8):

        def date_range(startDate):
            # Create an array of datetime values between start and end of request
            dateRange = []
            date = datetime.datetime.strptime(startDate, "%Y-%m-%d %H:%M:%S")
            dateRange.append(date)
            while date < pd.Timestamp.now().round("30min"):
                date += datetime.timedelta(minutes=30)
                dateRange.append(date)
            return dateRange # TODO need to add an end date here

        dateRange = date_range(start)
        combinedDf = pd.DataFrame()
        for status, response in zip(self.statusCodes, self.response):
            if status == 200:
                # Bare dataframe with datetime values between the requested start and end
                dateDf = pd.DataFrame(dateRange, columns=["created_at"])
                dateDf["created_at"] = pd.to_datetime(dateDf.created_at).astype('datetime64[ns, Australia/Sydney]')

                # Load in JSON from thingspeak request
                jsonResponse = json.loads(str(response))
                info = jsonResponse["channel"] # JSON device info from thingspeak

                # Get the field names from thingspeak
                fieldNames = {k:v for k, v in info.items() if "field" in k}

                # Construct a device dataframe from the JSON response
                deviceDf = pd.json_normalize(jsonResponse, 'feeds')

                # Rename the column names based on thingspeak column names
                deviceDf.rename(columns=fieldNames, inplace=True)

                # Add device name column
                deviceName = {"device_name": info["name"]}
                deviceDf = deviceDf.assign(**deviceName)

                try:
                    # Add device coordinates from thingspeak
                    coords = {k:v for k, v in info.items() if "itude" in k}
                    deviceDf = deviceDf.assign(**coords)
                except KeyError:
                    print("No latitude and longitude coordinates found in thingspeak request")
                    pass

                # Convert dates into datetime object
                deviceDf["created_at"] = pd.to_datetime(deviceDf["created_at"]).dt.round(
                        alignTime).dt.tz_localize(None).astype('datetime64[ns, Australia/Sydney]')

                # Sort values by date and drop duplicates
                deviceDf = deviceDf.sort_values(by="created_at").drop_duplicates(
                    subset="created_at").reset_index(drop=True)

                # Merge device dataframe into preconstructed date dataframe with N/a's to fill missing values
                dateDf = pd.merge(dateDf, deviceDf, on="created_at", how="outer") 

                # Append to combined dataframe
                combinedDf = combinedDf.append(dateDf)
        
            else:
                print("A request returned an invalid response: {}".format(status))

        # Convert to datetime (fixes interpolation error)
        combinedDf["created_at"] = pd.to_datetime(combinedDf["created_at"], utc=True).dt.tz_localize(None);

        # Interpolate missing values from dataset
        combinedDf = combinedDf.interpolate(method="pad", limit=interpolateLimit)
        return combinedDf


if __name__ == "__main__":
    data = Data()
    data.thingspeak_request(["852912", "882564"], ["VAHH1R8V29N77F5V", "7V8N0R6RNXAM38AY"], "Australia/Sydney", results=5)
    data.parse_thingspeak_request()

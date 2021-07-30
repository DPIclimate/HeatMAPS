import aiohttp
import asyncio
import json
import pandas as pd

class Data:
    def __init__(self):
        self.response = []
        self.statusCodes = []
        self.values = []
        self.ids = []
        self.names = []
        self.keys = []
        self.startDate = None
        self.endDate = None

    def thingspeak_request(self, ids, names, keys, timezone, date=False, results=10):
        if not isinstance(ids, list):
            raise TypeError("Id's must be of type list")
        elif len(ids) == 0:
            raise TypeError("Id's must have a length greater than 0")
        else:
            self.ids = ids
        if not isinstance(names, list):
            raise TypeError("Names must be of type list")
        elif len(names) == 0:
            raise TypeError("Names must have a length greater than 0")
        else:
            self.names = names
        if not isinstance(keys, list):
            raise TypeError("Keys must be of type list")
        elif len(names) == 0:
            raise TypeError("Keys must have a length greater than 0")
        else:
            self.keys = keys 

        urls = []
        if date:
            if self.startDate is not None and self.endDate is not None:
                for ID, key in zip(self.ids, self.keys):
                    urls.append(self.request("https://api.thingspeak.com/channels/{}/feeds.json?api_key={}&start={}\
                            &end={}&timezone={}".format(id, key, self.startDate, self.endDate, timezone)))
        else:
            for ID, key in zip(self.ids, self.keys):
                urls.append(self.request("https://api.thingspeak.com/channels/{}/feeds.json?\
                        api_key={}&results={}&timezone={}".format(ID, key, results, timezone)))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*urls))
        loop.close()


    async def request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.statusCodes.append(response.status)
                self.response.append(await response.text())


    def parse_thingspeak_request(self):
        self.dataframe = pd.DataFrame()
        for status, response in zip(self.statusCodes, self.response):
            if status == 200:
                jsonResponse = json.loads(str(response))
                jsonKeys = jsonResponse["channel"]
                initialDf = pd.json_normalize(jsonResponse, 'feeds')
                print(initialDf)
                print(jsonKeys) 
            else:
                print("Request returned an invalid response: {}".format(status))



if __name__ == "__main__":
    data = Data()
    data.thingspeak_request(["852912"], [1], ["VAHH1R8V29N77F5V"], "Australia/Sydney", results=1)
    data.parse_thingspeak_request()

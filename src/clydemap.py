import aiohttp
import asyncio
import os
import sys
import json
import imageio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import cartopy
import cartopy.crs as ccrs
from scipy.interpolate import Rbf
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


class ClydeData:
    def __init__(self):
        self.siteIDS = ['852912', '882564', '882600', '882601', '882602', 
                '882562', '882556', '882603', '851289']
        self.buoyNames = [1, 3, 4, 5, 8, 9, 11, 12, 13]
        self.siteKeys = ['VAHH1R8V29N77F5V', '7V8N0R6RNXAM38AY', 'H14YCHM913E9Q242', 
                'UT0R2RHPOKMKSLBP', 'SIJW6BRY6LF2QANF', 'QQRSK8OWK5V891XE', 
                'RVYDN22IYBB4YLIV', 'C96I124C9YD0DYPR', '621ISJJ2IMY6OMNJ']
        self.jsonResults = []
        self.jsonStatus = []
        self.nResults = 1


    def construct_request(self):
        # Clear previous values and formulate async request from array of thingspeak URL's
        self.jsonResults.clear()
        self.jsonStatus.clear()
        urls = []

        dateDefined = input("Set start and end date? (y/n)")
        if (dateDefined != "y"):
            self.nResults = input("Set number of previous readings to convert:")
            for ID, KEY in zip(self.siteIDS, self.siteKeys):
                urls.append(self.request("https://api.thingspeak.com/channels/{}/feeds.json?api_key={}&results={}&timezone=Australia/Sydney".format(ID, KEY, self.nResults)))
        else:
            validDate = False
            while not(validDate):  
                startDate = input("Set the start date (format: YYYY-MM-DD HH:MM:SS):")
                endDate = input("Set the end date (format: YYYY-MM-DD HH:MM:SS):")
                checkFormat = "%Y-%m-%d %H:%M:%S"
                try: 
                    datetime.datetime.strptime(startDate, checkFormat)
                    datetime.datetime.strptime(endDate, checkFormat)
                    validDate = True
                except ValueError:
                    print("Please enter a valid date string")

            for ID, KEY in zip(self.siteIDS, self.siteKeys):
                urls.append(self.request("https://api.thingspeak.com/channels/{}/feeds.json?api_key={}&start={}&end={}&timezone=Australia/Sydney".format(ID, KEY, startDate, endDate)))

        loop = asyncio.get_event_loop() # Create new event loop
        loop.run_until_complete(asyncio.gather(*urls)) # Async request using array of urls
        loop.close() # Close event loop after async call is complete


    async def request(self, url):
        # Preform async request and append connection status (e.g. 200, 400) and json values to arrays
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                self.jsonStatus.append(resp.status) # Connection status
                self.jsonResults.append(await resp.text()) # JSON response

    
    def parse_request(self, parameter="Salinity"):
        # Create pandas dataframe with selected thingspeak data
        # Returns: pd.DataFrame object
        self.frame = pd.DataFrame(columns=["Site", "Date", "Salinity", "Temperature"])
        for result, status in zip(self.jsonResults, self.jsonStatus): 
            # Select json responses with non errors
            if(status == 200): # OK
                jResult = json.loads(str(result))
                df = pd.json_normalize(jResult, 'feeds')
                for msgTime, salinity, temperature in zip(df["created_at"], df["field1"], df["field3"]):
                    # Sort values by their respective index and add to overall pandas dataframe 
                    self.frame = self.frame.append({"Site": self.buoyNames[self.siteIDS.index(str(jResult["channel"]["id"]))],
                        "Date": msgTime, "Salinity": salinity, "Temperature": temperature}, ignore_index=True)
            else:
                print("Error connecting to buoy {}'s ThingSpeak channel.")
        return self.frame.sort_values(by=["Site", "Date"], ascending=[True, False])


class ClydeMap:
    def __init__(self):
        self.lat = np.array([-35.7089, -35.699416, -35.694544, -35.698588, -35.69605, -35.70423, -35.703899, 
                             -35.70753, -35.684953, -35.67092, -35.6697])
        self.long = np.array([150.1832, 150.178636, 150.1727, 150.168668, 150.159375, 150.14716, 150.1409484, 
                              150.13557, 150.125927, 150.12886, 150.1166])
        self.mapExtent = [150.1166, 150.1832, -35.7089, -35.6697]
        self.mapOverlay = plt.imread("../figures/overlays/bbmap_shadow.png")
        self.resolution = 100
        self.xInterp = np.linspace(self.long.min(), self.long.max(), num=self.resolution)
        self.yInterp = np.linspace(self.lat.min(), self.lat.max(), num=self.resolution)
        # Convert to 2D matrix (shape = resolution x resolution)
        self.xInterp, self.yInterp = np.meshgrid(self.xInterp, self.yInterp)


    
    def get_data(self, dataFrame):
        self.salinity = []
        self.timeCaptured = []
        for buoy, timestamp in zip(dataFrame["Site"].unique(), dataFrame["Date"]):
            self.salinity.append(dataFrame.loc[dataFrame["Site"] == buoy]["Salinity"].values)
            self.timeCaptured.append(dataFrame.loc[dataFrame["Site"] == buoy]["Date"].values)
        return self.salinity, self.timeCaptured


    def generate_interpolation(self, resolution, function, index):
        # Generate 2D interpolation
        # Create array of values between the max and min long / latitudes
        if(resolution != self.resolution):
            # Shape = resolution
            self.xInterp = np.linspace(self.long.min(), self.long.max(), num=resolution)
            self.yInterp = np.linspace(self.lat.min(), self.lat.max(), num=resolution)
            # Convert to 2D matrix (shape = resolution x resolution)
            self.xInterp, self.yInterp = np.meshgrid(self.xInterp, self.yInterp)

        print("Generating interpolation for timestamp {} out of {}.".format(index + 1, len(self.salinity[0])))

        self.values = []
        for reading in self.salinity:
            self.values.append(float(reading[index]))

        # Need a buffer on each side of the map to insure the entire heatmap is displayed 
        self.values.insert(0, self.values[0]+0.5) # Assume the ocean has higher salinity
        self.values.append(self.values[-1]-0.5) # Assume futher in the river has lower sal
        self.values = np.array(self.values)

        # Radial Basis Function (RBF)
        rbfInterp = Rbf(self.long, self.lat, self.values, function=function)
        return rbfInterp(self.xInterp, self.yInterp)
        
    
    def generate_map(self, interpolation, nResult, timeCaptured):
        
        fig, ax = plt.subplots(1, 1, figsize=(14, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
        
        # Interpolation plot
        interPlot = ax.imshow(interpolation, extent=(self.long.min(), self.long.max(), self.lat.max(), self.lat.min()), 
                              aspect='auto', cmap="RdYlBu", vmin=0, vmax=40, zorder=1)
        
        # Map plot / overlay
        ax.imshow(self.mapOverlay, extent=self.mapExtent, zorder=2)

        # Buoy position
        buoyPos = ax.scatter(self.long[1:-1], self.lat[1:-1], c="purple", edgecolors="orange", 
                             linewidth=2, s=120, zorder=4)
        
        # Accessory map 
        ax.set_global()
        ax.set_extent(self.mapExtent)
        plt.text(self.long[0]+0.001, self.lat[0]-0.0015, datetime.datetime.fromisoformat(timeCaptured[0][nResult]))
        gridLines = ax.gridlines(draw_labels=True, zorder=3)
        gridLines.xformatter = LONGITUDE_FORMATTER
        gridLines.yformatter = LATITUDE_FORMATTER
        gridLines.right_labels = False
        gridLines.top_labels = False
        cBar = plt.colorbar(interPlot)
        cBar.set_label("Salinity (g/kg)", fontsize=20)
        ax.set_aspect('auto', adjustable=None);
        
        # Save figure
        plt.tight_layout()
        plt.savefig("../figures/imgs/{}.png".format(nResult), dpi=100)
        plt.close('all')


    def compile_gif(self):
        # Compile gif from figures
        print("Constructing gif...")
        img_dir = "../figures/imgs"
        imgs = []

        imgFiles = []
        for file in os.listdir(img_dir):
            if file.endswith('.png'):
                imgFiles.append(file)
        
        for fName in sorted(imgFiles, key=lambda x: int(x.replace(".png", "")), reverse=True):
            kwargs = {'fps':5.0, 'quantizer': 'nq'}
            imgs.append(imageio.imread(os.path.join(img_dir, fName)))
        imageio.mimsave('../figures/gifs/clydemap.gif', imgs, 'GIF-FI', **kwargs)
        print("...gif has been created.")


if __name__ == "__main__":
    data = ClydeData()
    data.construct_request()
    dataFrame = data.parse_request()
    cMap = ClydeMap()
    salinity, timeCaptured = cMap.get_data(dataFrame)
    for i in range(len(salinity[0])):
        interpolation = cMap.generate_interpolation(100, 'linear', i)
        cMap.generate_map(interpolation, i, timeCaptured)
    cMap.compile_gif()


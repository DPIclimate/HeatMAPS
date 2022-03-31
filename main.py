# Networking 
import requests

# Object manipulation 
import json
import pandas as pd

# Timing 
import time
from datetime import datetime 

# Math 
from scipy.interpolate import Rbf
import numpy as np

# Plotting 
import matplotlib.pyplot as plt

# Geospatial 
import cartopy
import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

# Environmental 
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Logging
import logging


class Ubidots:
    def __init__(self, from_cache=True):
        self.df = pd.DataFrame(columns=["Date", "Variable", "Device", 
            "Latitude", "Longitude", "Value"])
        self.API_TOKEN = os.getenv("UBIDOTS_KEY")
        self.config = "config.json"
        self.from_cache = from_cache
        self.cache_dir = "cache"
        self.devices = {}
        self.harvest_areas = []
        self.voi = ["salinity", "temperature"] # Varaibles of interest

    def get_all_devices(self):
        # Get new device list from Ubidots and store in cache
        if not self.from_cache:
            log.info("Requesting all devices from Ubidots (not cache)")
            url = "https://industrial.api.ubidots.com.au/api/v2.0/devices/"
            res = requests.get(url, headers={"X-Auth-Token": self.API_TOKEN})
            if res.status_code == 200:
                with open(self.config, "r") as cf:
                    config = json.load(cf)
                    j_res = json.loads(res.text)
                    device_info = []
                    for device in j_res["results"]:
                        for c_device in config["devices"]:
                            if device["name"] == c_device["name"]:
                                variables = self.get_device_variables(device["id"])
                                device_info.append({
                                    "name": device["name"],
                                    "id": device["id"],
                                    "api_label": device["label"],
                                    "latitude": device["properties"]["_location_fixed"]["lat"],
                                    "longitude": device["properties"]["_location_fixed"]["lng"],
                                    "harvest_area": c_device["harvest_area"],
                                    "location": c_device["location"],
                                    "variables": variables
                                })
                    self.devices["devices"] = device_info
                with open(f"{self.cache_dir}/devices.json", "w") as cache:
                    json.dump(self.devices, cache, sort_keys=True, indent=4)
            else:
                log.error(f"Error requesting devices from ubidots: {res.status_code}, {res.text}")
                sys.exit(1)
        # Get device list from cache (saves a few calls to Ubidots)
        else:
            log.info(f"Requesting all devices from cache {self.cache_dir}/devices.json")
            with open(f"{self.cache_dir}/devices.json", "r") as cache:
                self.devices = json.load(cache)

    def get_device_variables(self, device_id):
        log.info(f"Requesting device variables from Ubidots for ID: {device_id}")
        url = f"https://industrial.api.ubidots.com.au/api/v2.0/devices/{device_id}/variables/"
        res = requests.get(url, headers={"X-Auth-Token": self.API_TOKEN})
        if res.status_code == 200:
            j_res = json.loads(res.text)
            variable_list = {}
            for variable in j_res["results"]:
                if variable["name"] in self.voi:
                    variable_list.update({variable["name"]: variable["id"]})
            return variable_list

    # Gets a list of unique harvest areas from devices object
    def list_harvest_areas(self):
        log.info(f"Listing harvest areas")
        for device in self.devices["devices"]:
            if not device["harvest_area"] in self.harvest_areas:
                self.harvest_areas.append(device["harvest_area"])   

    def resample(self, body, device_name, lat, long, variable):
        log.info(f"Requesting resampled data from Ubidots for {device_name}")
        url = "https://industrial.api.ubidots.com.au/api/v1.6/data/stats/resample/"
        res = requests.post(url, headers={"X-Auth-Token": self.API_TOKEN,
            "Content-Type": "application/json"}, json=body)

        if res.status_code == 200:
            j_res = json.loads(res.text)
            for item in j_res["results"]:
                ts = ""
                if item[0] != None:
                    ts = datetime.fromtimestamp(int(item[0] / 1000))
                v_sum = 0;
                v_n = 0;
                for value in item[1:]:
                    if value != None:
                        v_sum += value
                        v_n += 1
                avg = round((v_sum / v_n), 2)
                # Append to Dataframe
                self.df.loc[len(self.df.index)] = [ts, variable, device_name, lat, long, avg]
                    
        else:
            log.error(f"Error requesting resampled data from Ubidots. {res.status_code} {res.text}")
            sys.exit(1)

    def get_values(self, period="1H"):
        log.info(f"Getting latest values from Ubidots. Period = {period}")
        for var in self.voi:
            for ha in self.harvest_areas:
                variable_ids = []
                for device in self.devices["devices"]:
                    if ha == device["harvest_area"]:
                        body = {
                            "variables": [device["variables"][var]],
                            "aggregation": "mean",
                            "join_dataframes": "true",
                            "period": period,
                            "start": int((time.time() - 86400) * 1000), # Roughly 1 day
                            "end": int(time.time() * 1000) 
                        }
                         
                        self.resample(body, device["location"], 
                                device["latitude"], device["longitude"], var)


class Map:
    def __init__(self, df=pd.DataFrame(), variables = None):
        self.df = df
        if self.df.empty:
            log.info("Map dataframe not provided reverting to stored .csv")
            self.df = pd.read_csv("datasets/latest.csv")
        self.extent = [150.1166, 150.1832, -35.6697, -35.7089]
        self.overlay_path = "imgs/overlays/bbmap_shadow.png";
        self.leases_path = "shapefiles/oyster-leases.shp"
        self.output_dir = "public/clyde_river"
        self.voi = variables
        if self.voi == None:
            info.error("Variable list not provided to map")

    def generate(self, resolution=100):
        x = np.linspace(self.extent[0], self.extent[1], num = resolution)
        y = np.linspace(self.extent[2], self.extent[3], num = resolution)
        X, Y = np.meshgrid(x, y) 

        for variable in self.voi:
            log.info(f"Generating map of {variable}")

            # Little pandas magic to pull the latest value from each variable
            select_df = self.df.where(self.df["Variable"] == variable).groupby('Device').first()

            log.info(f"Latest reading {select_df['Date'][0]}")

            rbf_interp = Rbf(select_df["Longitude"], select_df["Latitude"],
                    select_df["Value"].values.astype(float), function="linear")
            interpolation = rbf_interp(X, Y)

            fig, ax = plt.subplots(1, 1, figsize=(14, 8), 
                    subplot_kw=dict(projection=ccrs.PlateCarree()))

            # Could be moved to config.json
            cmap = plt.cm.RdYlGn
            label = "Salinity (g/L)"
            v_min = 0
            v_max = 40
            if variable == "temperature":
                cmap = plt.cm.RdYlBu
                label = u"Temperature (\N{DEGREE SIGN}C)"
                v_min = 10
                v_max = 35

            # Underlying interpolation
            m = ax.imshow(interpolation, extent=self.extent, aspect="auto", 
                    cmap=cmap, vmin=v_min, vmax=v_max, zorder=1)

            # Map img overlay
            ax.imshow(plt.imread(self.overlay_path), extent=self.extent, zorder=2)

            # Oyster lease overlay
            ax.add_feature(ShapelyFeature(Reader(self.leases_path).geometries(),
                    ccrs.PlateCarree(), facecolor='grey', alpha=0.8), zorder=3)

            # Buoy overlay
            ax.scatter(select_df["Longitude"], select_df["Latitude"], c="#c33c39", 
                    edgecolor="w", linewidth=2, s=80, zorder=4)

            # Gridline and map setup
            ax.set_extent(self.extent)
            ax.set_aspect('auto', adjustable=None)
            gridLines = ax.gridlines(draw_labels=True, zorder=3)
            gridLines.xformatter = LONGITUDE_FORMATTER
            gridLines.yformatter = LATITUDE_FORMATTER
            gridLines.right_labels = False
            gridLines.top_labels = False 

            plt.colorbar(m, label=label) 

            plt.title(f"Generated at: {select_df['Date'][0]}")
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/latest-{variable}.png", dpi=300)
            plt.close()

if __name__ == "__main__":
    log = logging.getLogger("logger")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("log/debug.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    ubi = Ubidots()
    ubi.get_all_devices()
    ubi.list_harvest_areas()
    ubi.get_values()
    ubi.df.to_csv("datasets/latest.csv", index=False)

    m = Map(df = ubi.df, variables = ubi.voi)
    m.generate()


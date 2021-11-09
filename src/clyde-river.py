#!/bin/env python3
# Postgres
import psycopg2
import mysql.connector
from mysql.connector import connect

# Environment
from dotenv import load_dotenv, dotenv_values
import os
import sys

# Setup
from datetime import datetime, timedelta
from dateutil.tz import tzutc, tzlocal
import requests
import time
import json
import pandas as pd
import numpy as np

# Mapping 
from scipy.interpolate import Rbf
import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

load_dotenv()

# ---- Setup ----
# List of decomissioned buoy devids
decommissioned_buoys = ["clyde-salinity801", "clyde-salinity90c", "clyde-salinity502"]
no_solar_buoys = ["clyde-salinity20b", "clyde-salinity20c"]

# Set true to refresh all aspects of script
# Useful if decom buoys has been updated or devids have changed
refresh = False
debug = False


def postgres_connect():
    # Connect to postgres broker using .env file variables
    return psycopg2.connect(host=os.getenv("PG_HOST"),
                            port=os.getenv("PG_PORT"),
                            user=os.getenv("PG_USER"),
                            password=os.getenv("PG_PASSWORD"),
                            dbname=os.getenv("PG_DBNAME"))


def get_device_list():
    # Get relevent devices from broker table and append to array
    # If refresh is set to false the device list will use a premade txt file to speed up processing
    devices = []
    # Get buoy devid's and write to storage
    if not os.path.exists("log/device_list.txt") or refresh:
        # Get decomissioned buoys to exclude them from query
        decom_str = ""
        for buoy in decommissioned_buoys:
            decom_str = decom_str + f" AND devid != '{buoy}'"

        # Construct query to get relevent buoy devid's
        buoys_query = f"SELECT DISTINCT devid FROM msgs WHERE devid LIKE 'clyde-salinity%'" + decom_str

        connection = postgres_connect()
        with connection as con:
            with con.cursor() as cursor:
                cursor.execute(buoys_query)
                devlist = cursor.fetchall()
                # Append devices to text file and list
                with open("log/device_list.txt", 'w') as dl:
                    for (devid, ) in devlist:
                        dl.write(devid + "\n")
                        devices.append(devid)

    else:
        # Read from txt file and add to list
        with open("log/device_list.txt", "r") as dl:
            for line in dl:
                devices.append(line.rstrip())

    return devices


def get_latest_message(devices):
    msgs = []
    if not os.path.exists("log/latest_values.txt") or debug:
        with open("log/latest_values.txt", "w") as dl:
            for device in devices:
                # Get the latest value from each device, ignoring dups
                query = f"SELECT ts, msg FROM msgs WHERE devid = '{device}' AND ignore != TRUE ORDER BY UID DESC LIMIT 1;"
                connection = postgres_connect()
                with connection as con:
                    with con.cursor() as cursor:
                        cursor.execute(query)
                        res = cursor.fetchall()
                        for (ts, msg, ) in res:
                            local_date = ts.astimezone(tzlocal())
                            dl.write(device + "," + str(local_date) + "," + str(msg).replace("\'", "\"") + "\n")
                            msgs.append([device, local_date, msg])

    else: 
        # Read from txt file and get relevent values
        with open("log/latest_values.txt", "r") as dl:
            for line in dl:
                strp_line = line.rstrip()
                values = strp_line.split(",", 2)
                device = values[0]
                ts = datetime.strptime(values[1], "%Y-%m-%d %H:%M:%S%z")
                msg = json.loads(values[2])
                msgs.append([device, ts, msg])
                
    return msgs


def decode_messages(msgs):
    for device, ts, msg in msgs:

        # Get the devices app id to use as a decoder name as there is nosolar and with solar devices
        decoder_name = msg["end_device_ids"]["application_ids"]["application_id"]

        # Add msg to payload file
        with open("decode/payload.json", "w", encoding="utf-8") as pl:
            json.dump([msg], pl)

        os.system(f"node decode/decode.js decode/{decoder_name}.js ./payload.json > decode/decoded/{device}.json")
    

def get_coordinates(device, application):
    token = ""
    if application == "salinity-ict-c4e-nosolar":
        token = os.getenv("TTN_API_KEY_NOSOLAR")
    else:
        token = os.getenv("TTN_API_KEY_SOLAR")
    url = f"https://eu1.cloud.thethings.network/api/v3/applications/{application}/devices/{device}?field_mask=locations"

    req = requests.get(url, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
        })

    if req.status_code == 200:
        json_req = json.loads(req.text)
    else:
        return { "latitude": 0, "longitude": 0 }

    user = json_req["locations"]["user"]

    return {"latitude": user["latitude"], "longitude": user["longitude"]}


def decoded_to_dataframe(devices):
    df = pd.DataFrame()

    for device in devices:
        with open(f"decode/decoded/{device}.json", "r") as dd:
            data = json.load(dd)

            if device in no_solar_buoys:
                coords = get_coordinates(device, "salinity-ict-c4e-nosolar")
            else:
                coords = get_coordinates(device, "salinity-ict-c4e")

            jsonData = data[0]
            jsonData.update(coords)
            df = df.append(jsonData, ignore_index=True)

    print(df)

    return df


def dataframe_to_map(df, resolution=100, parameter="salinity", overlay_path="../figures/overlays/bbmap_shadow.png"):

    # Refine df to exclude rows where lat and long = 0 (i.e. They dont exist)
    df = df.loc[df["latitude"] * df["longitude"] != 0]

    # Exclude values where last reading was over 12 hours ago
    exclude_ts = datetime.now() - timedelta(hours=12)
    df = df[df["ts"] >= (time.mktime(exclude_ts.timetuple()) * 1000)]


    # Define the maps extent
    lng_min = 150.1166 
    lng_max = 150.1832
    lat_min = -35.6697
    lat_max = -35.7089
    extent = [lng_min, lng_max, lat_max, lat_min] 

    # Generate interpolation 
    x_interp = np.linspace(extent[0], extent[1], num=resolution)
    y_interp = np.linspace(extent[2], extent[3], num=resolution)
    x_interp, y_interp = np.meshgrid(x_interp, y_interp)

    values = df[parameter].values.astype(float)

    rbf_interp = Rbf(df["longitude"], df["latitude"], values, functon="linear")
    interpolation = rbf_interp(x_interp, y_interp)

    plt.rcParams.update({'font.size': 18})

    fig, ax = plt.subplots(1, 1, figsize=(14, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))

    new_cmap = plt.cm.RdYlBu
    #cm = plt.pcolormesh(np.random.randn(50, 50), cmap=new_cmap)

    map_interp = ax.imshow(interpolation, extent=extent, aspect="auto", cmap=new_cmap, 
        vmin=0, vmax=40, zorder=1)

    ax.imshow(plt.imread(overlay_path), extent=extent, zorder=2)

    oyster_leases = ShapelyFeature(Reader("../shapefiles/oyster-leases.shp").geometries(),
                                    ccrs.PlateCarree(), facecolor='grey', alpha=0.8)
    ax.add_feature(oyster_leases, zorder=3) 

    buoys = ax.scatter(df["longitude"], df["latitude"], c="#c33c39", edgecolor="w", linewidth=2, s=80, zorder=4)

    ax.set_global()
    ax.set_extent(extent)
    ax.set_aspect('auto', adjustable=None)

    gridLines = ax.gridlines(draw_labels=True, zorder=3)
    gridLines.xformatter = LONGITUDE_FORMATTER
    gridLines.yformatter = LATITUDE_FORMATTER
    gridLines.right_labels = False
    gridLines.top_labels = False

    colourBar = plt.colorbar(map_interp, label="Salinity (g/kg)")

    valid_time = datetime.fromtimestamp(int(df["ts"][0] / 1000))
    print(valid_time)
    plt.title(f"Generated at: {valid_time}")
    plt.tight_layout()
    plt.savefig("/var/www/html/salinity_latest.png")
    plt.close() 


def main():
    # Get devices from broker
    devices = get_device_list()

    # Get latest message for each device from broker
    msgs = get_latest_message(devices)

    # Decode raw payloads using decoder
    decode_messages(msgs)

    # Convert decoded payloads to a dataframe
    df = decoded_to_dataframe(devices)

    # Convet dataframe to map
    dataframe_to_map(df)


if __name__ == "__main__":
    main()


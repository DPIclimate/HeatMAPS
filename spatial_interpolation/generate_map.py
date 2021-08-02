from scipy.interpolate import Rbf
import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import datetime
import pandas as pd
import numpy as np

class Map:
    def __init__(self):
        self.extent = []
        self.overlayDir = None
        self.underlayDir = None
        self.resolution = 100
    

    def extent(self, extent):
        if len(extent) == 4 and isinstance(extent, list):
            self.extent = extent
        else:
            raise AssertionError("Extent must be an array of latitude and longitude coordinates formatted as: \
                [latitude_1, latitude_2, longitude_1, longitude 2]")
        return self.extent


    def image_overlay_dir(self, overlay):
        if isinstance(overlay, str):
            if len(overlay) >= 4:
                if overlay[-4:] != ".png":
                    raise TypeError("Image overlay must be a .png file")
            else:
                raise TypeError("Invalid image type (accepted types: .png)")
        else:
            raise TypeError("Image overlay must constist of a file directory of type string")
        self.overlayDir = overlay
        return self.overlayDir

    
    def image_underlay_dir(self, underlay):
        if isinstance(underlay, str):
            if len(underlay) >= 4:
                if underlay[-4:] != ".png":
                    raise TypeError("Image underlay must be a .png file")
            else:
                raise TypeError("Invalid image type (accepted types: .png)")
        else:
            raise TypeError("Image underlay must constist of a file directory of type string")
        self.underlayDir = underlay 
        return self.underlayDir


    def generate_map(self, POI, dataframe, extent, resolution=100, function='linear'):
        self.extent = extent
        longMin = float(dataframe["longitude"].min()) 
        longMax = float(dataframe["longitude"].max())
        latMin = float(dataframe["latitude"].min())
        latMax = float(dataframe["latitude"].max())

        xInterp = np.linspace(longMin, longMax, num=resolution)
        yInterp = np.linspace(latMin, latMax, num=resolution)
        xInterp, yInterp = np.meshgrid(xInterp, yInterp)

        for time in dataframe["created_at"].unique():

            values = dataframe.loc[dataframe["created_at"] == time][POI].values.astype(float)
            interp = Rbf(dataframe["longitude"].unique(), dataframe["latitude"].unique(), values, function=function)
            rbf = interp(xInterp, yInterp)

            fig, ax = plt.subplots(1, 1, figsize=(14, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
            interpolationMap = ax.imshow(rbf, extent=(longMin, longMax, latMin, latMax), aspect="auto", cmap="RdYlBu", 
                vmin=0, vmax=40, zorder=1)

            ax.set_global()
            ax.set_extent(self.extent)
            gridLines = ax.gridlines(draw_labels=True, zorder=3)
            gridLines.xformatter = LONGITUDE_FORMATTER
            gridLines.yformatter = LATITUDE_FORMATTER
            gridLines.right_labels = False
            gridLines.top_labels = False
            colourBar = plt.colorbar(interpolationMap)
            ax.set_aspect('auto', adjustable=None)
            
            plt.tight_layout()
            plt.savefig("../figures/imgs/{}.png".format(pd.to_datetime(time).strftime("%Y-%m-%d_%H-%M-%S")))
            plt.close()

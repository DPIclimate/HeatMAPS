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
        self.overlay = None
        self.underlay = None
        self.resolution = 100
    

    def set_extent(self, extent):
        if len(extent) == 4 and isinstance(extent, list):
            self.extent = extent
        else:
            raise AssertionError("Extent must be an array of latitude and longitude coordinates formatted as: \
                [latitude_1, latitude_2, longitude_1, longitude 2]")
        return self.extent


    def set_image_overlay(self, overlay):
        if isinstance(overlay, str):
            if len(overlay) >= 4:
                if overlay[-4:] != ".png":
                    raise TypeError("Image overlay must be a .png file")
            else:
                raise TypeError("Invalid image type (accepted types: .png)")
        else:
            raise TypeError("Image overlay must constist of a file directory of type string")
        self.overlay = plt.imread(overlay)
        return self.overlay

    
    def set_image_underlay(self, underlay):
        if isinstance(underlay, str):
            if len(underlay) >= 4:
                if underlay[-4:] != ".png":
                    raise TypeError("Image underlay must be a .png file")
            else:
                raise TypeError("Invalid image type (accepted types: .png)")
        else:
            raise TypeError("Image underlay must constist of a file directory of type string")
        self.underlay = plt.imread(underlay)
        return self.underlay


    def generate_map(self, POI, dataframe, extent=None, resolution=100, function='linear'):

        # No extent provided, use data from dataframe 
        if(extent == None):
            longMin = float(dataframe["longitude"].min()) 
            longMax = float(dataframe["longitude"].max())
            latMin = float(dataframe["latitude"].min())
            latMax = float(dataframe["latitude"].max())
            extent.append(longMin, longMax, latMin, latMax)
        
        # Generate interpolation 
        xInterp = np.linspace(extent[0], extent[1], num=resolution)
        yInterp = np.linspace(extent[2], extent[3], num=resolution)
        xInterp, yInterp = np.meshgrid(xInterp, yInterp)

        longitudes = dataframe["longitude"].dropna().unique()
        latitudes = dataframe["latitude"].dropna().unique()

        for time in dataframe["created_at"].unique():

            # For each timestamp create an interpolation
            values = dataframe.loc[dataframe["created_at"] == time][POI].values.astype(float)
            print(values)
            print(len(values), len(longitudes), len(latitudes))
            interp = Rbf(longitudes, latitudes, values, function=function)
            rbf = interp(xInterp, yInterp)

            # Setup plot
            fig, ax = plt.subplots(1, 1, figsize=(14, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))

            # Underlay is defined 
            if(hasattr(self.underlay, 'shape')):
                ax.imshow(self.underlay, extent=extent, zorder=0, alpha=0.5)

            # Plot interpolation on map
            interpolationMap = ax.imshow(rbf, extent=extent, aspect="auto", cmap="RdYlGn", 
                vmin=0, vmax=40, zorder=1)

            ## Overlay is defined
            if(hasattr(self.overlay, 'shape')):
                ax.imshow(self.overlay, extent=extent, zorder=2)

            ax.set_global()
            ax.set_extent(extent)
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

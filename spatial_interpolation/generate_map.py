from scipy.interpolate import Rbf
import datetime
import pandas as pd

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


    def generate_interpolation(self, POI, dataframe, resolution=100, function='linear'):
        xInterp = np.linspace(float(dataframe["longitude"].min()), float(dataframe["longitude"].max()), num=resolution)
        yInterp = np.linspace(float(dataframe["latitude"].min()), float(dataframe["latitude"].max()), num=resolution)
        xInterp, yInterp = np.meshgrid(xInterp, yInterp)

        for time in dataframe["created_at"].unique():
            values = dataframe.loc[dataframe["created_at"] == time][POI].values.astype(float)
            interp = Rbf(dataframe["longitude"].unique(), dataframe["latitude"].unique(), values, function=function)
            rbf = interp(xInterp, yInterp)
            # TODO mapping functions go here


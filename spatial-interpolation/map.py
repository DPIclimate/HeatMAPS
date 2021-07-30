
class Map:
    def __init__(self):
        self.extent = []
        self.latitudes = []
        self.longitudes = []
        self.overlayDir = None
        self.underlayDir = None
        self.resolution = 100
    

    def extent(self, extent):
        if len(extent) == 4 and isinstance(extent, list):
            self.extent = extent
        else raise AssertionError("Extent must be an array of latitude and longitude coordinates formatted as: \
                [latitude_1, latitude_2, longitude_1, longitude 2]")
        return self.extent
    

    def latitudes(self, latitudes):
        if not isinstance(latitudes, list):
            raise TypeError("Latitudes expects type list got {}".format(type(longitude)))
        elif len(latitudes) >= 0:
            raise TypeError("Latitudes length must be greater than 0")
        elif type(latitudes[0]) is not float:
            raise TypeError("Latitudes (input type: {}) must be of type float".format(type(latitudes[0])))
        else:
            self.latitudes = latitudes
        return self.latitudes


    def longitudes(self, longitudes):
        if not isinstance(longitudes, list):
            raise TypeError("Longitudes expects type list got {}".format(type(longitude)))
        elif len(longitudes) >= 0:
            raise TypeError("Longitudes length must be greater than 0")
        elif type(longitudes[0]) is not float:
            raise TypeError("Longitudes (input type: {}) must be of type float".format(type(longitudes[0])))
        else:
            self.longitudes = longitudes 
        return self.longitudes


    def device_names(self, ids):
        self.ids = ids
        return self.ids

    
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




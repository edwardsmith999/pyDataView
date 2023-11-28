import numpy as np

from .field import Field
from .VTKrawdata import VTK_RawData

class VTKField(Field):

    def __init__(self, fdir, fname):
        self.fname = fname
        Raw = VTK_RawData(fdir, self.fname)
        self.nperbin = Raw.nperbin  
        Field.__init__(self, Raw)
        if Raw.nperbin == 1:
            self.labels = ['component']
        elif Raw.nperbin == 3:
            self.labels = ['x', 'y', 'z']
        self.axislabels = ['x', 'y', 'z']
        self.plotfreq = Raw.plotfreq

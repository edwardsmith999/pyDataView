import numpy as np

from field import Field
from lammpsrawdata import LAMMPS_RawData

class LAMMPSField(Field):

    def __init__(self, fdir):
        Raw = LAMMPS_RawData(fdir, self.fname, self.readnames)
        self.nperbin = Raw.nperbin  
        Field.__init__(self, Raw)
        self.axislabels = ['x', 'y', 'z']


class LAMMPS_complexField(LAMMPSField):

    """
        Complex fields that inherit LAMMPSField AND contain LAMMPSField
        objects require extra calculations. "Read" and "average_data" routines
        are commonly overridden. Parameters for the complex field are usually
        inherited from one of the sub-fields.  
    """

    def inherit_parameters(self, subfieldobj):
        self.nperbin = subfieldobj.nperbin
        self.axislabels = subfieldobj.axislabels
        self.labels = subfieldobj.labels


# ----------------------------------------------------------------------------
# Simple fields

class LAMMPS_vField(LAMMPSField):
    fname = 'cplchunk'
    readnames = ['vx', 'vy', 'vz']
    labels = readnames


class LAMMPS_nField(LAMMPSField):
    fname = 'cplchunk'
    readnames = ['Ncount']
    labels = readnames


# ----------------------------------------------------------------------------
# Complex fields

class LAMMPS_dField(LAMMPS_complexField):

    def __init__(self, fdir):
        self.nField = LAMMPS_nField(fdir)
        Field.__init__(self, self.nField.Raw)
        self.inherit_parameters(self.nField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        gridvolumes = self.nField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        # Read 4D time series from startrec to endrec
        ndata = self.nField.read(startrec, endrec, binlimits=binlimits)
        #ndata = np.divide(ndata, float(self.plotfreq))

        density = np.divide(ndata, gridvolumes)
        
        return density

    def averaged_data(self,startrec,endrec,avgaxes=(),binlimits=None, **kwargs):

        nrecs = endrec - startrec + 1
        gridvolumes = self.nField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        # Read 4D time series from startrec to endrec
        ndata = self.nField.read(startrec, endrec, binlimits=binlimits)
        #mdata = np.divide(mdata,float(self.plotfreq))

        if (avgaxes != ()):
            ndata = np.sum(ndata,axis=avgaxes) 
            # gridvolumes should only be length=1 in time & component axis
            gridvolumes = np.sum(gridvolumes,axis=avgaxes) 

        density = np.divide(ndata,gridvolumes*nrecs)

        return density 

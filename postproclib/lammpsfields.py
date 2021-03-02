import numpy as np

from .field import Field
from .lammpsrawdata import LAMMPS_RawData

class LAMMPSField(Field):

    def __init__(self, fdir, fname):
        self.fname = fname
        Raw = LAMMPS_RawData(fdir, self.fname, self.readnames)
        self.nperbin = Raw.nperbin  
        Field.__init__(self, Raw)
        self.axislabels = ['x', 'y', 'z']
        self.plotfreq = Raw.plotfreq

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
        self.plotfreq = subfieldobj.plotfreq


# ----------------------------------------------------------------------------
# Simple fields

class LAMMPS_pField(LAMMPSField):
    #fname = 'cplchunk'
    readnames = ['vx', 'vy', 'vz']
    labels = readnames


class LAMMPS_mField(LAMMPSField):
    #fname = 'cplchunk'
    readnames = ['Ncount']
    labels = readnames


class LAMMPS_TField(LAMMPSField):
    #fname = 'cplchunk'
    readnames = ['temp']
    labels = readnames

class LAMMPS_PressureField(LAMMPSField):
    #fname = 'cplchunk'
    readnames = ['c_Pressure[1]', 'c_Pressure[2]', 'c_Pressure[3]']
    labels = readnames

class LAMMPS_ShearStressField(LAMMPSField):
    #fname = 'cplchunk'
    readnames = ['c_Pressure[4]', 'c_Pressure[5]', 'c_Pressure[6]']
    labels = readnames

class LAMMPS_KineticEnergyField(LAMMPSField):   
    readnames = ['c_myKE'] 
    labels = readnames
    
class LAMMPS_PotentialEnergyField(LAMMPSField):   
    readnames = ['c_eng'] 
    labels = readnames

    
# ----------------------------------------------------------------------------
# Complex fields
class LAMMPS_dField(LAMMPS_complexField):

    def __init__(self, fdir, fname):
        self.nField = LAMMPS_mField(fdir, fname)
        Field.__init__(self, self.nField.Raw)
        self.inherit_parameters(self.nField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        gridvolumes = self.nField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        # Read 4D time series from startrec to endrec
        ndata = self.nField.read(startrec, endrec, binlimits=binlimits)
        density = np.divide(ndata, gridvolumes)
        
        return density

    def averaged_data(self, startrec, endrec, avgaxes=(), binlimits=None, **kwargs):

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

#Velocity field
class LAMMPS_vField(LAMMPS_complexField):

    def __init__(self, fdir, fname):
        self.mField = LAMMPS_mField(fdir, fname)
        self.pField = LAMMPS_pField(fdir, fname)
        Field.__init__(self, self.pField.Raw)
        self.inherit_parameters(self.pField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        mdata = self.mField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        pdata = self.pField.read(startrec, endrec, binlimits=binlimits, **kwargs)

        # Divide and patch any NaNs
        vdata = np.divide(pdata, mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata 

    def averaged_data(self, startrec, endrec, avgaxes=(), binlimits=None, **kwargs):
        
        mdata = self.mField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        pdata = self.pField.read(startrec, endrec, binlimits=binlimits, **kwargs)

        if (avgaxes != ()):
            mdata = np.sum(mdata, axis=avgaxes) 
            pdata = np.sum(pdata, axis=avgaxes) 

        # Divide and patch any NaNs
        vdata = np.divide(pdata, mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata



# Momentum density field
class LAMMPS_momField(LAMMPS_complexField):
    
    def __init__(self, fdir, fname):
        self.pField = LAMMPS_pField(fdir, fname)
        Field.__init__(self,self.pField.Raw)
        self.inherit_parameters(self.pField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        gridvolumes = self.pField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        # Read 4D time series from startrec to endrec
        pdata = self.pField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        #pdata = np.divide(pdata,float(self.plotfreq))

        momdensity = np.divide(pdata,gridvolumes)
        
        return momdensity

    def averaged_data(self, startrec, endrec, binlimits=None, avgaxes=(), **kwargs):

        nrecs = endrec - startrec + 1
        gridvolumes = self.pField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes, axis=-1)

        # Read 4D time series from startrec to endrec
        pdata = self.pField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        #pdata = np.divide(pdata,float(self.plotfreq))

        if (avgaxes != ()):
            pdata = np.sum(pdata, axis=avgaxes) 
            # gridvolumes should only be length=1 in time & component axis 
            gridvolumes = np.sum(gridvolumes, axis=avgaxes) 
        
        momdensity = np.divide(pdata, gridvolumes*nrecs)

        return momdensity 

    
    
# Total Energy field
class LAMMPS_TotalEnergyField(LAMMPS_complexField):
    
    def __init__(self, fdir, fname):
        self.KEField = LAMMPS_KineticEnergyField(fdir, fname)
        self.PEField = LAMMPS_PotentialEnergyField(fdir, fname)
        Field.__init__(self, self.KEField.Raw)
        self.inherit_parameters(self.KEField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        KEdata = self.KEField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        PEdata = self.PEField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        Tdata = KEdata + PEdata

        return Tdata 

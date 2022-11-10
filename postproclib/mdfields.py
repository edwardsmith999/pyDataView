#! /usr/bin/env python
import numpy as np
from .field import Field
from .mdrawdata import MD_RawData
from .pplexceptions import DataMismatch, DataNotAvailable

# ============================================================================
# MDField base class

class MDField(Field):
      
    def __init__(self, fdir):
        Raw = MD_RawData(fdir, self.fname, self.dtype, 
                         self.nperbin)
        Field.__init__(self,Raw)
        self.header = self.Raw.header
        self.cpol_bins = bool(int(self.header.cpol_bins))
        if (self.cpol_bins):
            self.axislabels = ['r','theta','z']
        else:
            self.axislabels = ['x','y','z']


    def check_dtype(self, fdir):
        #Check dtype is correct -- included for backward
        #                          compatibility with old integer
        #                          format for mbins, mflux, etc
        # THIS FIX REQUIRED FOR ALL FILES MADE BEFORE 25/02/2015
        from .headerdata import MDHeaderData
        header = MDHeaderData(fdir)

        year = header.sim_date[:4]
        month = header.sim_date[4:6]
        day = header.sim_date[6:8]
        #print(day, month, year, int(year)<2015 , int(month)<2 , int(day) < 25)
        if (int(year)<2015 or (int(year) is 2015 and int(month)<2)):
            print("Results from before 25/02/2015 so assuming mbins uses integers")
            self.dtype = 'i'

# ============================================================================
# MDField derived classes, but calculated by the main code

class MD_dummyField(MDField):

    """
        Dummy field object
    """

    dtype = 'd'
    nperbin = 1

    def __init__(self, fdir):
        
        self.fname = ''
        MDField.__init__(self, fdir)
        self.labels = [""]
        self.nperbin = 1
        self.plotfreq = 1

class MD_exampleField(MDField):

    """
        A sample field object which changes in time and space
    """

    dtype = 'd'
    nperbin = 1

    def __init__(self, fdir):
        
        self.fname = ''
        MDField.__init__(self, fdir)
        self.labels = ["sample"]
        self.nperbin = 1
        self.plotfreq = 1
        self.Raw.maxrec = 100
        self.maxrec = self.Raw.maxrec

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        def test_data(x, y, z, A):
            return 2 - 2 * np.cos(x)*np.cos(y)*np.cos(z) - A * np.cos(x - 2*y + z)

        nrecs = endrec - startrec + 1

        A = 0.01*startrec%1
        x = np.linspace(0, 2*np.pi, self.Raw.nbins[0])
        y = np.linspace(0, 2*np.pi, self.Raw.nbins[1])
        z = np.linspace(0, 2*np.pi, self.Raw.nbins[2])

        X,Y,Z = np.meshgrid(x, y, z, indexing='ij')
        bins = test_data(X, Y, Z, A)

        array = np.empty((self.Raw.nbins[0],
                          self.Raw.nbins[1],
                          self.Raw.nbins[2],nrecs,self.nperbin))
        for rec in range(nrecs):
            array[:,:,:,rec,0] = bins

        # If bin limits are specified, return only those within range
        if (binlimits):
            array = self.trim_binlimits(binlimits, array)

        return array


class MD_mField(MDField):

    """
        MD_mField manages mass field data in the form of
        molecular counts with 1 integer data type per bin 
        e.g. fnames = [mbins], msnap  (default in [])
    """

    dtype = 'd'
    nperbin = 1

    def __init__(self, fdir, fname='mbins'):

        MDField.check_dtype(self, fdir)

        self.fname = fname
        MDField.__init__(self, fdir)
        self.labels = ["mag"]
        self.nperbin = self.Raw.nperbin
        if fname in ['mbins','mpoly','msolv']:
            self.plotfreq = int(self.Raw.header.Nmass_ave)
        elif fname == 'msnap':
            self.plotfreq = 1 #int(self.Raw.header.Nmflux_ave)





class MD_pField(MDField):

    """
        MD_pField manages velocity field data in the form of
        molecular velocity summed with 3 double
        precision real data type per bin
        e.g. fnames = [vbins], vsnap (default in [])
    """

    dtype = 'd'
    nperbin = 3

    def __init__(self, fdir, fname='vbins'):

        self.fname = fname
        MDField.__init__(self, fdir)
        self.labels = self.axislabels
        self.nperbin = self.Raw.nperbin
        if fname in ['vbins','vpoly','vsolv']:
            self.plotfreq = int(self.Raw.header.Nvel_ave)
        elif fname == 'vsnap':
            self.plotfreq = 1 #int(self.Raw.header.Nvflux_ave)


class MD_FField(MDField):

    """
        MD_FField manages Body Force field data in the form of
        applied Force per molecule summed with 3 double
        precision real data type per bin
        e.g. fnames = [Fext] (default in [])
    """

    dtype = 'd'
    nperbin = 3

    def __init__(self, fdir, fname='Fext'):

        self.fname = fname
        MDField.__init__(self, fdir)
        self.labels = self.axislabels 
        self.nperbin = self.Raw.nperbin
        self.plotfreq = int(self.Raw.header.Nvel_ave)


class MD_EField(MDField):

    """
        MD_EField manages energy field data in the form of
        molecular velocity squared and potential energy with 1 
        double precision real data type per bin            
        e.g. fnames = [Tbins], ebins, esnap, Fvext (default in [])
    """
    
    dtype = 'd'
    nperbin = 1

    def __init__(self, fdir, fname):

        self.fname = fname
        MDField.__init__(self, fdir)
        self.labels = ["mag"]
        self.nperbin = self.Raw.nperbin
        if fname == 'Tbins':
            self.plotfreq = int(self.Raw.header.NTemp_ave)
        elif fname == 'esnap':
            self.plotfreq = 1 #int(self.Raw.header.Neflux_ave)
        elif fname == 'Fvext':
            self.plotfreq = int(self.Raw.header.Neflux_ave)
        elif fname == 'ebins':
            self.plotfreq = int(self.Raw.header.Nenergy_ave)
        #Pressure scalar is written out as trace of pressure tensor
        elif fname == 'P':
            self.plotfreq = int(self.Raw.header.Nvflux_ave)
        else:
            'Unknown MD_EField type ', fname
            raise DataNotAvailable


class MD_comField(MDField):

    """
        MD_comField manages centre of mass field data in the 
        form of relative positions summed with 3 double
        precision real data type per bin
        e.g. fnames = [combins] (default in [])
    """

    dtype = 'd'
    nperbin = 3

    def __init__(self,fdir,fname='combin'):

        self.fname = fname
        MDField.__init__(self,fdir)
        self.labels = self.axislabels
        self.nperbin = self.Raw.nperbin
        if fname in ['combin']:
            self.plotfreq = int(self.Raw.header.Nvel_ave)

class MD_mfluxField(MDField):

    """
        MD_mfluxField manages mass flux field data in the form of
        molecular count over 6 cubic bin surfaces with 6 integer 
        data types per bin            
        e.g. fnames = [mflux], msurf, dsurf_mflux (default in [])
    """
    
    dtype = 'd'
    nperbin = 6

    def __init__(self,fdir,fname='mflux'):

        MDField.check_dtype(self, fdir)

        self.fname = fname
        MDField.__init__(self,fdir)
        self.labels = ["xbottom","ybottom","zbottom",
                        "xtop","ytop","ztop"]
        self.nperbin = self.Raw.nperbin
        self.plotfreq = int(self.Raw.header.Nmflux_ave)

class MD_PField(MDField):

    """
        MD_PField requires the specification of a filename by the
        user, allowing any of pVA or separate kinetic pVA_k
        and configurational parts pVA_c to be plotted with the same
        MDField class functionality.
        e.g. fnames = [pVA], pVA_k, pVA_c (default in [])
    """

    dtype = 'd'
    nperbin = 9

    def __init__(self,fdir,fname='pVA'):
        self.fname = fname
        if (fname in ("pVA","pVA_k","pVA_c")):
            MDField.__init__(self,fdir)
        else:
            print("Output type not recognised, should be pVA, pVA_k or pVA_c")
            raise DataMismatch

        x = self.axislabels[0]; y = self.axislabels[1]; z = self.axislabels[2]
        self.labels = [x+x,x+y,x+z,
                       y+x,y+y,y+z,
                       z+x,z+y,z+z]
        self.nperbin = self.Raw.nperbin
        self.plotfreq = int(self.Raw.header.Nstress_ave)

class MD_stressField(MD_PField):
   
    """
        PField multiplied by -1, useful for coupled output

    """ 

    def read(self,startrec,endrec,**kwargs):

        if (endrec > self.maxrec):
            quit('Record ' + str(endrec) + ' is greater than the maximum '
                 'available (' + str(self.maxrec) + '). Aborting.')
        
        grid_data = -1.0 * self.Raw.read(startrec,endrec,**kwargs) 
        return grid_data



class MD_hfVAField(MDField):

    """
        MD_heatfluxField requires the specification of a filename by the
        user, allowing any of hfVA or separate kinetic hfVA_k
        and configurational parts hfVA_c to be plotted with the same
        MDField class functionality.
        e.g. fnames = [hfVA], hfVA_k, hfVA_c (default in [])
    """

    dtype = 'd'
    nperbin = 3

    def __init__(self, fdir, fname='hfVA'):
        self.fname = fname
        if (fname in ("hfVA","hfVA_k","hfVA_c")):
            MDField.__init__(self,fdir)
        else:
            print("Output type not recognised, should be hfVA, hfVA_k or hfVA_c")
            raise DataMismatch

        x = self.axislabels[0]; y = self.axislabels[1]; z = self.axislabels[2]
        self.labels = ['x','y','z']
        self.nperbin = self.Raw.nperbin
        self.plotfreq = int(self.Raw.header.Nheatflux_ave)

class MD_pfluxField(MDField):

    """
        MD_vfluxField manages velocity flux field data in the form of
        velocity/stress sum over 6 cubic bin surfaces with 18 double 
        precision real data types per bin
        e.g. fnames = totalflux, vflux, psurface, dsurf_vflux (no default)
    """

    dtype = 'd'
    nperbin = 18

    def __init__(self,fdir,fname):

        if (fname in ("psurface","vflux", "dsurf_vflux")):
            self.fname = fname
            self.labels = ["xxbottom","yxbottom","zxbottom",
                           "xybottom","yybottom","zybottom",
                           "xzbottom","yzbottom","zzbottom",
                           "xxtop","yxtop","zxtop",
                           "xytop","yytop","zytop",
                           "xztop","yztop","zztop"]
            MDField.__init__(self,fdir)
            self.nperbin = self.Raw.nperbin
            self.plotfreq = int(self.Raw.header.Nvflux_ave)
        elif fname in ("total"):
            raise DataNotAvailable
        else:
            print(("Output type '" + fname  +"' not recognised in MD_pfluxField" +
                   " should be psurface, vflux or dsurf_vflux"))
            raise DataNotAvailable



class MD_efluxField(MDField):

    """
        MD_efluxField manages energy flux field data in the form of
        energy/esurface sum over 6 cubic bin surfaces with 6 double 
        precision real data types per bin
        e.g. fnames = eflux, esurface, dsurf_eflux (no default)
    """

    dtype = 'd'
    nperbin = 6

    def __init__(self,fdir,fname):

        if (fname in ("esurface","eflux","dsurf_eflux")):
            self.fname = fname
            self.labels = ["xbottom","ybottom","zbottom",
                           "xtop","ytop","ztop"]
            MDField.__init__(self,fdir)
            self.nperbin = self.Raw.nperbin
            self.plotfreq = int(self.Raw.header.Neflux_ave)
        else:
            print("Output type not recognised, should be esurface, eflux")
            raise DataNotAvailable

# ============================================================================

class MD_complexField(MDField):

    """
        Complex fields that inherit MDField AND contain MDField objects, require 
        extra calculations. "Read" and "average_data" routines are commonly 
        overridden. Parameters for the complex field are usually inherited from
        one of the sub-fields.
    """

    def inherit_parameters(self, subfieldobj):
        self.header = subfieldobj.Raw.header
        self.nperbin = subfieldobj.nperbin
        self.cpol_bins = subfieldobj.cpol_bins
        self.plotfreq = subfieldobj.plotfreq
        self.axislabels = subfieldobj.axislabels
        self.labels = subfieldobj.labels


class MD_vField(MD_complexField):

    def __init__(self,fdir,rectype='bins'):
        if (rectype == 'bins'):
            self.mField = MD_mField(fdir,fname='mbins')
            self.pField = MD_pField(fdir,fname='vbins')
        elif (rectype == 'snap'):
            self.mField = MD_mField(fdir,fname='msnap')
            self.pField = MD_pField(fdir,fname='vsnap')
        else:
            print(("Record type ", rectype, " not understood"))
            raise DataNotAvailable

        Field.__init__(self,self.pField.Raw)
        self.inherit_parameters(self.pField)
        self.labels = ["u", "v", "w"]
        if (self.mField.plotfreq == self.pField.plotfreq):
            self.plotfreq = self.pField.plotfreq
        else:
            print("Error in MD_vfield -- Nmass_ave differs from Nvel_ave")
            raise DataMismatch


    def read(self, startrec, endrec, **kwargs):

        mdata = self.mField.read(startrec, endrec, **kwargs)
        pdata = self.pField.read(startrec, endrec, **kwargs)

        # Divide and patch any NaNs
        vdata = np.divide(pdata, mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata 

    def averaged_data(self,startrec,endrec,avgaxes=(),**kwargs):
        
        mdata = self.mField.read(startrec, endrec, **kwargs)
        pdata = self.pField.read(startrec, endrec, **kwargs)

        if (avgaxes != ()):
            mdata = np.sum(mdata, axis=avgaxes) 
            pdata = np.sum(pdata, axis=avgaxes) 

        # Divide and patch any NaNs
        vdata = np.divide(pdata,mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata

class MD_Centre_of_Mass_Field(MD_complexField):

    def __init__(self,fdir):
        self.mField = MD_mField(fdir)
        self.comField = MD_comField(fdir)
        Field.__init__(self,self.comField.Raw)
        self.inherit_parameters(self.comField)
        self.plotfreq = self.comField.plotfreq

    def read(self,startrec,endrec,**kwargs):

        mdata = self.mField.read(startrec,endrec,**kwargs)
        comdata = self.comField.read(startrec,endrec,**kwargs)

        # Divide and patch any NaNs
        vdata = np.divide(comdata,mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata 

    def averaged_data(self,startrec,endrec,avgaxes=(),**kwargs):
        
        mdata = self.mField.read(startrec,endrec,**kwargs)
        comdata = self.comField.read(startrec,endrec,**kwargs)

        if (avgaxes != ()):
            mdata = np.sum(mdata,axis=avgaxes) 
            comdata = np.sum(comdata,axis=avgaxes) 

        # Divide and patch any NaNs
        vdata = np.divide(comdata,mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata

class MD_rhouuField(MD_complexField):

    def __init__(self, fdir):

        # Get mean velocity and density field
        self.fdir = fdir
        self.vField = MD_vField(self.fdir)
        self.momField = MD_momField(self.fdir)
        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ['rhouu','rhouv','rhouw',
                       'rhovu','rhovv','rhovw',
                       'rhowu','rhowv','rhoww']
        self.nperbin = 9

    def read(self, startrec, endrec, **kwargs):

        vdata = self.vField.read(startrec, endrec, **kwargs)
        momdata = self.momField.read(startrec, endrec, **kwargs)

        # Find outer product of v*v and reshape to 1x9 rather than 3x3
        rhouudata = np.einsum('abcdj,abcdk->abcdjk', momdata, vdata)
        vvshapelist = list(rhouudata.shape)
        newshape = tuple(vvshapelist[0:4]+[self.nperbin])
        rhouudata = np.reshape(rhouudata, newshape)

        return rhouudata

    def averaged_data(self, startrec, endrec, avgaxes=(), **kwargs):
        
        vdata = self.vField.read(startrec, endrec, **kwargs)
        momdata = self.momField.read(startrec, endrec, **kwargs)

        if (avgaxes != ()):
            #Get shape after axes have been removed
            indx = [x for x in [0, 1, 2, 3] if x not in avgaxes]
            vvshapelist = list(vdata.shape)
            newshape = tuple([vvshapelist[i] for i in indx]+[self.nperbin])

            #Remove axes from einsum expression
            ltrs = ["a", "b", "c", "d"]
            einsumstr = 'abcdj,abcdk->abcdjk'
            for a in avgaxes:
                einsumstr = einsumstr.replace(ltrs[a],"")

            #Calculate sum over average axes
            vdata = np.mean(vdata, axis=avgaxes) 
            momdata = np.mean(momdata, axis=avgaxes)

        # Find outer product of v*v and reshape to 1x9 rather than 3x3
        rhouudata = np.einsum(einsumstr, momdata, vdata)
        #print(avgaxes, einsumstr, indx, newshape, rhouudata.shape)
        rhouudata = np.reshape(rhouudata, newshape)

        return rhouudata

class MD_pVAField(MD_complexField):

    def __init__(self, fdir, fname, peculiar=True):

        self.fname = fname
        try:
            self.PField = MD_PField(fdir,fname)
        except DataNotAvailable:
            #If pVA file is not present, 
            # try getting from pVA_c and pVA_k
            if fname == 'pVA':
                print("Attempting to combine pVA_k and pVA_c")
                self.pkField = MD_PField(fdir,fname='pVA_k')
                self.pcField = MD_PField(fdir,fname='pVA_c')
                self.PField = self.pkField
                self.fname = 'pVA_ck'
            else:
                raise DataNotAvailable

        Field.__init__(self,self.PField.Raw)
        self.inherit_parameters(self.PField)
        self.peculiar = peculiar

    def read(self, startrec, endrec, peculiar=None, 
             verbose=False,**kwargs):

        # Read 4D time series from startrec to endrec
        if self.fname == 'pVA_ck':
            Pdata = (  self.pkField.read(startrec,endrec,**kwargs)
                     + self.pcField.read(startrec,endrec,**kwargs))
        else:
            Pdata = self.PField.read(startrec,endrec,**kwargs)

        # Take off square of peculiar momenta if specified
        if peculiar == None:
            peculiar = self.peculiar

        if (peculiar==True):

            if (self.fname=='pVA_k' or self.fname=='pVA_ck'):

                #Not sure if this is a good idea, might hide errors
                try:
                    rhouuField = MD_rhouuField(self.fdir)
                    rhouudata =  rhouuField.read(startrec,endrec,**kwargs)

                    # Remove square of streaming velocity
                    Pdata = Pdata - rhouudata
                except DataNotAvailable:
                    print("Velocity field not found, cannot subtract streaming velocity")

        return Pdata

    def averaged_data(self, startrec, endrec, avgaxes=(), 
                      peculiar=None, verbose=False,**kwargs):

        # Read 4D time series from startrec to endrec
        if self.fname == 'pVA_ck':
            Pdata = (  self.pkField.averaged_data(startrec, endrec, 
                                                  avgaxes=avgaxes, **kwargs)
                     + self.pcField.averaged_data(startrec, endrec, 
                                                  avgaxes=avgaxes, **kwargs))
        else:
            Pdata = self.PField.averaged_data(startrec, endrec, 
                                              avgaxes=avgaxes,**kwargs)

        # Take off square of peculiar momenta if specified
        if peculiar == None:
            peculiar = self.peculiar

        if (peculiar==True):

            if (self.fname=='pVA_k' or self.fname=='pVA_ck'):

                #Not sure if this is a good idea, might hide errors
                try:

                    rhouuField = MD_rhouuField(self.fdir)
                    rhouudata =  rhouuField.averaged_data(startrec, endrec, 
                                                        avgaxes=avgaxes, **kwargs)

                    # Remove square of streaming velocity
                    Pdata = Pdata - rhouudata
                except DataNotAvailable:
                    print("Velocity field not found, cannot subtract streaming velocity")

        return Pdata


class MD_TField(MD_complexField):

    def __init__(self, fdir, peculiar=True):
        self.mField = MD_mField(fdir)
        self.pField = MD_pField(fdir)
        self.KEField = MD_EField(fdir,fname='Tbins')
        Field.__init__(self,self.KEField.Raw)
        self.inherit_parameters(self.KEField)
        self.peculiar = peculiar

        #Check all records are consistent
        if self.mField.plotfreq == self.KEField.plotfreq:
            if peculiar:
                if (self.mField.plotfreq == self.pField.plotfreq):
                    self.plotfreq = self.KEField.plotfreq
                    self.axislabels = self.KEField.axislabels
                    self.labels = self.KEField.labels
                else:
                    print("Error in MD_Tfield -- Nmass_ave differs from Nvel_ave")
                    raise DataMismatch
            else:
                self.plotfreq = self.KEField.plotfreq
                self.axislabels = self.KEField.axislabels
                self.labels = self.KEField.labels

    def read(self, startrec, endrec, peculiar=None, **kwargs):

        mdata = self.mField.read(startrec, endrec, **kwargs)
        KEdata = self.KEField.read(startrec, endrec, **kwargs)

        # Temperature (no streaming consideration)
        Tdata = np.divide(KEdata,(3.0*mdata))
        Tdata[np.isnan(Tdata)] = 0.0

        # Remove average of streaming component
        if peculiar==None:
            peculiar = self.peculiar

        if (peculiar==True):
            pdata = self.pField.read(startrec, endrec, **kwargs)
            vdata = np.divide(pdata, mdata)
            vdata[np.isnan(vdata)] = 0.0
            v2data = np.sum((vdata**2.0),axis=4,keepdims=True)
            Tdata = Tdata - (1./3.)*v2data

        return Tdata 

    def averaged_data(self, startrec, endrec, 
                      avgaxes=(), peculiar=None, **kwargs):
        
        # Read 4D time series from startrec to endrec
        mdata = self.mField.read(startrec, endrec, **kwargs)
        KEdata = self.KEField.read(startrec, endrec, **kwargs)

        # Consider streaming velocity
        if peculiar == None:
            peculiar = self.peculiar

        if (peculiar):
            pdata = self.pField.read(startrec, endrec, **kwargs)
            vdata = np.divide(pdata, mdata)
            vdata[np.isnan(vdata)] = 0.0
            v2data = np.sum((vdata**2.0),axis=4,keepdims=True)

        if (avgaxes != ()):
            mdata = np.sum(mdata, axis=avgaxes) 
            KEdata = np.sum(KEdata, axis=avgaxes) 

        # Temperature (no streaming consideration)
        Tdata = np.divide(KEdata,(3.0*mdata))
        Tdata[np.isnan(Tdata)] = 0.0

        # Remove streaming velocity
        if (peculiar):
            if (avgaxes != ()):
                v2data = np.mean(v2data,axis=avgaxes) 
            Tdata = Tdata - (1./3.)*v2data

        return Tdata

class MD_rhoTField(MD_complexField):

    def __init__(self, fdir, peculiar=False):
        self.KEField = MD_EField(fdir,fname='Tbins')
        Field.__init__(self,self.KEField.Raw)
        self.inherit_parameters(self.KEField)
        self.peculiar = peculiar

        #Check all records are consistent
        if peculiar:
            quit('Peculiar not developed for MD_rhoTField')

        else:
            self.plotfreq = self.KEField.plotfreq
            self.axislabels = self.KEField.axislabels
            self.labels = self.KEField.labels

    def read(self, startrec, endrec, binlimits=None,
             peculiar=None, **kwargs):

        # Remove average of streaming component
        if peculiar == None:
            peculiar = self.peculiar

        binvolumes = self.KEField.Raw.get_gridvolumes(binlimits=binlimits)
        binvolumes = np.expand_dims(binvolumes, axis=-1)

        Tdata = self.KEField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        Tdata = np.divide(Tdata,float(self.plotfreq))

        if (peculiar):
            quit('Peculiar not developed for MD_rhoTField')

        # Energy (no streaming consideration)
        Tdata = np.divide(Tdata,binvolumes)

        return Tdata 

class MD_EnergyField(MD_complexField):

    def __init__(self, fdir, peculiar=False):
        self.mField = MD_mField(fdir)
        self.pField = MD_pField(fdir)
        self.EField = MD_EField(fdir,fname='ebins')
        Field.__init__(self,self.EField.Raw)
        self.inherit_parameters(self.EField)

        if ((self.mField.plotfreq != self.EField.plotfreq) ):
            print(("Error in MD_EField -- Nmass_ave " + 
                  "differs from Nenergy_ave"))
            raise DataMismatch

        if (peculiar and self.pField.plotfreq != self.EField.plotfreq):
            print(("Error in MD_EField -- Nvel_ave " +
                  "differs from Nenergy_ave and peculiar=True "))
            raise DataMismatch  

        self.plotfreq = self.EField.plotfreq
        self.axislabels = self.EField.axislabels
        self.labels = self.EField.labels
        self.peculiar = peculiar

    def read(self, startrec, endrec, peculiar=None, **kwargs):

        mdata = self.mField.read(startrec, endrec, **kwargs)
        Edata = self.EField.read(startrec, endrec, **kwargs)

        # Energy (no streaming consideration)
        Eout = np.divide(Edata,mdata)
        Eout[np.isnan(Eout)] = 0.0

        # Remove average of streaming component
        if peculiar == None:
            peculiar = self.peculiar

        if (peculiar):

            pdata = self.pField.read(startrec, endrec, **kwargs)
            vdata = np.divide(pdata, mdata)
            vdata[np.isnan(vdata)] = 0.0
            v2data = np.sum((vdata**2.0), axis=4, keepdims=True)
            Eout = Eout - v2data/2.

        return Eout 

    def averaged_data(self, startrec, endrec, 
                      avgaxes=(), peculiar=None, **kwargs):
        
        # Read 4D time series from startrec to endrec
        mdata = self.mField.read(startrec, endrec, **kwargs)
        Edata = self.EField.read(startrec, endrec, **kwargs)

        # Consider streaming velocity
        if peculiar == None:
            peculiar = self.peculiar

        if (peculiar):
            pdata = self.pField.read(startrec, endrec, **kwargs)
            vdata = np.divide(pdata,mdata)
            vdata[np.isnan(vdata)] = 0.0
            v2data = np.sum((vdata**2.0), axis=4, keepdims=True)

        if (avgaxes != ()):
            mdata = np.sum(mdata, axis=avgaxes) 
            Edata = np.sum(Edata, axis=avgaxes) 

        # Energy (no streaming consideration)
        Edata = np.divide(Edata, mdata)
        Edata[np.isnan(Edata)] = 0.0

        # Remove streaming velocity
        if (peculiar):
            if (avgaxes != ()):
                v2data = np.mean(v2data, axis=avgaxes) 
            Edata = Edata - v2data/2.

        return Edata



class MD_potEnergyField(MD_complexField):

    """
        The internal energy of the fluid
        worked out by subtracting kinetic
        energy from total collected energy
    """

    def __init__(self, fdir):
        self.mField = MD_mField(fdir)
        self.TField = MD_EField(fdir, fname='Tbins')
        self.EField = MD_EField(fdir, fname='ebins')
        Field.__init__(self,self.EField.Raw)
        self.inherit_parameters(self.EField)

        if (self.mField.plotfreq != self.EField.plotfreq):
            print(("Error in MD_EField -- Nmass_ave " + 
                  "differs from Nenergy_ave"))
            raise DataMismatch

        if (self.TField.plotfreq != self.EField.plotfreq):
            print(("Error in MD_EField -- NTave " +
                  "differs from Nenergy_ave "))
            raise DataMismatch  

        self.plotfreq = self.EField.plotfreq
        self.axislabels = self.EField.axislabels
        self.labels = self.EField.labels

    def read(self, startrec, endrec, **kwargs):

        mdata = self.mField.read(startrec, endrec, **kwargs)
        Tdata = self.TField.read(startrec, endrec, **kwargs)
        Edata = self.EField.read(startrec, endrec, **kwargs)
        potdata = Edata - Tdata/2.

        # Energy (no streaming consideration)
        potout = np.divide(potdata,mdata)
        potout[np.isnan(potout)] = 0.0

        return potout

    def averaged_data(self, startrec, endrec, 
                      avgaxes=(), **kwargs):
        
        # Read 4D time series from startrec to endrec
        mdata = self.mField.read(startrec, endrec, **kwargs)
        Tdata = self.TField.read(startrec, endrec, **kwargs)
        Edata = self.EField.read(startrec, endrec, **kwargs)
        potdata = Edata - Tdata/2.

        # Average
        if (avgaxes != ()):
            mdata = np.sum(mdata, axis=avgaxes) 
            potdata = np.sum(potdata, axis=avgaxes) 

        # Energy (no streaming consideration)
        potdata = np.divide(potdata, mdata)
        potdata[np.isnan(potdata)] = 0.0

        return potdata

class MD_rhoEnergyField(MD_complexField):

    def __init__(self, fdir, peculiar=False):
        self.momField = MD_momField(fdir)
        self.EField = MD_EField(fdir, fname='ebins')
        Field.__init__(self,self.EField.Raw)
        self.inherit_parameters(self.EField)

        self.plotfreq = self.EField.plotfreq
        self.axislabels = self.EField.axislabels
        self.labels = self.EField.labels
        self.peculiar = peculiar

    def read(self, startrec, endrec, 
             binlimits=None, peculiar=None, **kwargs):

        gridvolumes = self.EField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes, axis=-1)

        Edata = self.EField.read(startrec, endrec, **kwargs)
        Edata = np.divide(Edata,float(self.plotfreq))

        # Energy (no streaming consideration)
        Eout = np.divide(Eout, gridvolumes)

        # Remove average of streaming component
        if peculiar == None:
            peculiar = self.peculiar

        if (peculiar):
            quit('Peculiar not developed for MD_rhoEnergyField')

        return Eout 

    def averaged_data(self, startrec, endrec, avgaxes=(),
                      binlimits=None, peculiar=None, **kwargs):
        
        gridvolumes = self.EField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        Edata = self.EField.read(startrec, endrec, **kwargs)
        Edata = np.divide(Edata, float(self.plotfreq))

        # Consider streaming velocity
        if peculiar == None:
            peculiar = self.peculiar

        if (peculiar):
            quit('Peculiar not developed for MD_rhoEnergyField')

        if (avgaxes != ()):
            Edata = np.sum(Edata, axis=avgaxes) 
            gridvolumes = np.sum(gridvolumes, axis=avgaxes) 

        # Energy (no streaming consideration)
        Edata = np.divide(Edata, gridvolumes)

        return Edata



class MD_enthalpyField(MD_complexField):

    """
        The enthalpy of the fluid
        worked out adding internal energy
        to pressure times cell volume
    """

    def __init__(self, fdir, peculiar=False):
        self.pVAField = MD_pVAField(fdir,fname='pVA')
        self.EField =MD_potEnergyField(fdir)
        Field.__init__(self,self.EField.Raw)
        self.inherit_parameters(self.EField)

        if (self.pVAField.plotfreq != self.EField.plotfreq):
            print(("Error in MD_EField -- NpVA_ave " + 
                  "differs from Nenergy_ave"))
            raise DataMismatch

        self.plotfreq = self.EField.plotfreq
        self.axislabels = self.EField.axislabels
        self.labels = self.EField.labels
        self.peculiar = peculiar

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        Edata = self.EField.read(startrec, endrec, **kwargs)
        pVAdata = self.pVAField.read(startrec, endrec, **kwargs)
        P = np.zeros([pVAdata.shape[0],
                      pVAdata.shape[1],
                      pVAdata.shape[2],
                      pVAdata.shape[3],1])
        P[:,:,:,:,0] = (pVAdata[:,:,:,:,0] + pVAdata[:,:,:,:,4] + pVAdata[:,:,:,:,8])/3.
        gridvolumes = self.EField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        h = (Edata + P/gridvolumes)*gridvolumes

        return h

class MD_pVAheat_Field(MD_complexField):

    def __init__(self, fdir, peculiar=True):
        self.fdir = fdir
        self.vField = MD_vField(fdir)
        self.pVA = MD_pVAField(fdir,fname='pVA')

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ["Pi_dot_u","Pi_dot_v","Pi_dot_w"]
        self.nperbin = 3
        self.peculiar = peculiar

    def read(self, startrec, endrec, peculiar=None, **kwargs):

        if peculiar == None:
            peculiar = self.peculiar

        u = self.vField.read(startrec, endrec, **kwargs)
        Pi = self.pVA.read(startrec, endrec, peculiar=peculiar, **kwargs)

        Pi = np.reshape(Pi,[ Pi.shape[0],
                             Pi.shape[1],
                             Pi.shape[2],
                             Pi.shape[3], 3, 3],                                            
                             order='F')

        Pidotu = np.einsum('abcdij,abcdi->abcdj',Pi,u)

        return Pidotu

    def averaged_data(self, startrec, endrec, avgaxes=(), peculiar=None, **kwargs):

        if peculiar == None:
            peculiar = self.peculiar

        u = self.vField.averaged_data(startrec, endrec, 
                                      avgaxes=avgaxes, **kwargs)
        Pi = self.pVA.averaged_data(startrec, endrec, 
                                    avgaxes=avgaxes, peculiar=peculiar, **kwargs)

        newshape = list(Pi.shape[:-1]) + [3] + [3]
        Pi = np.reshape(Pi, newshape, order='F')

        #Remove axes from einsum expression
        einsumstr = 'abcdij,abcdi->abcdj'
        ltrs = ["a", "b", "c", "d"]
        for a in avgaxes:
            einsumstr = einsumstr.replace(ltrs[a],"")

        Pidotu = np.einsum(einsumstr, Pi, u)

        return Pidotu



class MD_energyadvct_Field(MD_complexField):

    def __init__(self,fdir):
        self.fdir = fdir

        # Other alternative (equivalent??) u * (rho e)
        #self.vField = MD_vField(fdir)
        #self.rhoeField = MD_rhoEnergyField(fdir)

        # (rho u) * e
        self.pField = MD_momField(fdir)
        self.eField = MD_EnergyField(fdir)

        Field.__init__(self,self.eField.Raw)
        self.inherit_parameters(self.eField)
        self.labels = ["rhouE","rhovE","rhowE"]
        self.nperbin = 3

    def read(self, startrec, endrec, **kwargs):

        rhou = self.pField.read(startrec, endrec, **kwargs)
        e = self.eField.read(startrec, endrec, **kwargs)
        rhoue = rhou*e

        return rhoue

    def averaged_data(self, startrec, endrec, avgaxes=(), **kwargs):

        rhou = self.pField.averaged_data(startrec, endrec, 
                                         avgaxes=avgaxes, **kwargs)
        e = self.eField.averaged_data(startrec, endrec, 
                                      avgaxes=avgaxes, **kwargs)
        rhoue = rhou*e

        return rhoue

class MD_heatfluxVAField(MD_complexField):

    def __init__(self, fdir, fname="hfVA", peculiar=True):

        self.fname = fname
        try:
            self.PField = MD_hfVAField(fdir, fname)
        except DataNotAvailable:
            #If hfVA file is not present, 
            # try getting from hfVA_c and hfVA_k
            if fname == 'hfVA':
                self.pkField = MD_hfVAField(fdir, fname='hfVA_k')
                self.pcField = MD_hfVAField(fdir, fname='hfVA_c')
                #Define pfield based on one of the fields (here kinetic)
                self.PField = self.pkField
                self.fname = 'hfVA_ck'
            else:
                raise DataNotAvailable

        Field.__init__(self,self.PField.Raw)
        self.inherit_parameters(self.PField )
        self.peculiar = peculiar

        if peculiar:
            self.pVAheatField = MD_pVAheat_Field(fdir)
            self.energyadvctField = MD_energyadvct_Field(fdir)

    def read(self, startrec, endrec, peculiar=None, **kwargs):

        # Read 4D time series from startrec to endrec
        if self.fname == 'hfVA_ck':
            Pdata = (  self.pkField.read(startrec, endrec, **kwargs)
                     + self.pcField.read(startrec, endrec, **kwargs))
        else:
            Pdata = self.PField.read(startrec, endrec, **kwargs)

        # Take off energy advection and stress heating if specified
        if peculiar == None:
            peculiar = self.peculiar

        if peculiar:
            if (self.fname is 'hfVA_k'):
                # Pdata = Pdata - energy (x) u
                energyadvctdata =  self.energyadvctField.read(startrec, endrec, **kwargs)
                Pdata = Pdata - energyadvctdata
            elif (self.fname is 'hfVA_c'):
                # Pi dot u
                pVAheatdata =  self.pVAheatField.read(startrec, endrec, **kwargs)
                Pdata = Pdata - pVAheatdata
            else:   
                # Pi dot u & energy (x) u
                pVAheatdata =  self.pVAheatField.read(startrec, endrec, **kwargs)
                energyadvctdata =  self.energyadvctField.read(startrec, endrec, **kwargs)
                Pdata = Pdata - (pVAheatdata + energyadvctdata)

        return Pdata

    def averaged_data(self, startrec, endrec, avgaxes=(), peculiar=None, **kwargs):

        # Read 4D time series from startrec to endrec
        if self.fname == 'hfVA_ck':
            Pdata = (  self.pkField.averaged_data(startrec, endrec, avgaxes=avgaxes, **kwargs)
                     + self.pcField.averaged_data(startrec, endrec, avgaxes=avgaxes, **kwargs))
        else:
            Pdata = self.PField.averaged_data(startrec, endrec, avgaxes=avgaxes, **kwargs)

        # Take off energy advection and stress heating if specified
        if peculiar == None:
            peculiar = self.peculiar

        if peculiar:
            if (self.fname is 'hfVA_k'):
                # Pdata = Pdata - energy (x) u
                energyadvctdata =  self.energyadvctField.averaged_data(startrec, endrec, 
                                                                       avgaxes=avgaxes, **kwargs)
                Pdata = Pdata - energyadvctdata
            elif (self.fname is 'hfVA_c'):
                # Pi dot u
                pVAheatdata =  self.pVAheatField.averaged_data(startrec, endrec, 
                                                               avgaxes=avgaxes, **kwargs)
                Pdata = Pdata - pVAheatdata
            else:   
                # Pi dot u & energy (x) u
                pVAheatdata =  self.pVAheatField.averaged_data(startrec, endrec, 
                                                               avgaxes=avgaxes, **kwargs)
                energyadvctdata =  self.energyadvctField.averaged_data(startrec, endrec, 
                                                                       avgaxes=avgaxes, **kwargs)
                Pdata = Pdata - (pVAheatdata + energyadvctdata)

        return Pdata

# Density field
class MD_dField(MD_complexField):
    
    def __init__(self,fdir,fname='mbins'):
        self.mField = MD_mField(fdir,fname)
        Field.__init__(self,self.mField.Raw)
        self.inherit_parameters(self.mField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        gridvolumes = self.mField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        # Read 4D time series from startrec to endrec
        mdata = self.mField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        mdata = np.divide(mdata, float(self.plotfreq))

        density = np.divide(mdata, gridvolumes)
        
        return density

    def averaged_data(self,startrec,endrec,avgaxes=(),binlimits=None, **kwargs):

        nrecs = endrec - startrec + 1
        gridvolumes = self.mField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        # Read 4D time series from startrec to endrec
        mdata = self.mField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        mdata = np.divide(mdata,float(self.plotfreq))

        #Check for missing or skipped records here
        if (mdata.shape[3] != nrecs):
            print("Missing record detected so normalising by number of records")
            nrecs = mdata.shape[3]

        if (avgaxes != ()):
            mdata = np.sum(mdata, axis=avgaxes) 
            # gridvolumes should only be length=1 in time & component axis
            gridvolumes = np.sum(gridvolumes, axis=avgaxes) 

        density = np.divide(mdata,gridvolumes*nrecs)

        return density 

# Momentum density field
class MD_momField(MD_complexField):
    
    def __init__(self, fdir, fname='vbins'):
        self.pField = MD_pField(fdir,fname)
        Field.__init__(self,self.pField.Raw)
        self.inherit_parameters(self.pField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        gridvolumes = self.pField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes,axis=-1)

        # Read 4D time series from startrec to endrec
        pdata = self.pField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        pdata = np.divide(pdata,float(self.plotfreq))

        momdensity = np.divide(pdata,gridvolumes)
        
        return momdensity

    def averaged_data(self, startrec, endrec, binlimits=None, avgaxes=(), **kwargs):

        nrecs = endrec - startrec + 1
        gridvolumes = self.pField.Raw.get_gridvolumes(binlimits=binlimits)
        gridvolumes = np.expand_dims(gridvolumes, axis=-1)

        # Read 4D time series from startrec to endrec
        pdata = self.pField.read(startrec, endrec, binlimits=binlimits, **kwargs)
        pdata = np.divide(pdata,float(self.plotfreq))

        if (avgaxes != ()):
            pdata = np.sum(pdata, axis=avgaxes) 
            # gridvolumes should only be length=1 in time & component axis 
            gridvolumes = np.sum(gridvolumes, axis=avgaxes) 
        
        momdensity = np.divide(pdata, gridvolumes*nrecs)

        return momdensity 


class MD_eFieldatsurface(MD_complexField):

    def __init__(self, fdir):

        self.EField = MD_EnergyField(fdir)
        Field.__init__(self,self.EField.Raw)
        self.inherit_parameters(self.EField)
        self.plotfreq = self.EField.plotfreq
        self.labels = ["xbottom","ybottom","zbottom",
                        "xtop","ytop","ztop"]
        self.nperbin = 6

    def read(self, startrec, endrec, **kwargs):

        edata   = self.EField.read(startrec, endrec, **kwargs)
        #Get v on surface
        esurface = np.zeros([edata.shape[0],
                             edata.shape[1],
                             edata.shape[2],
                             edata.shape[3], 6],order='F')

        for rec in range(endrec-startrec+1):
            esurface[:,:,:,rec,:] = self.cellcentre2surface(edata[:,:,:,rec])

        eeshapelist = list(edata.shape)
        newshape = tuple(eeshapelist[0:4]+[self.nperbin])
        esurface = np.reshape(esurface, newshape)

        if (binlimits):
            esurface = self.trim_binlimits(binlimits, esurface)

        return esurface


# Concentration of polymer field
class MD_polyconcField(MD_complexField):
    
    def __init__(self, fdir):
        self.mpolyField = MD_mField(fdir, fname='mpoly')
        self.msolvField = MD_mField(fdir, fname='msolv')
        Field.__init__(self, self.msolvField.Raw)
        self.inherit_parameters(self.msolvField)

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        mpoly = self.mpolyField.read(startrec, endrec, binlimits=binlimits)
        msolv = self.msolvField.read(startrec, endrec, binlimits=binlimits)
        mtotal = mpoly + msolv
        
        return np.divide(mpoly,mtotal)

    def averaged_data(self, startrec, endrec, avgaxes=(), binlimits=None, **kwargs):

        mpoly = self.mpolyField.averaged_data(startrec, endrec, 
                                              avgaxes=avgaxes, binlimits=binlimits)
        msolv = self.msolvField.averaged_data(startrec, endrec, 
                                              avgaxes=avgaxes, binlimits=binlimits)
        mtotal = mpoly + msolv
        
        return np.divide(mpoly,mtotal)

# ===============COMPLEX MD CV Fields ==================
class MD_CVmassField(MD_complexField):

    def __init__(self, fdir):

        try:
            self.msurf = MD_mfluxField(fdir, fname='msurf')
            self.interp_from_mbins = False
        except DataNotAvailable:
            #If no msurf, get from interp
            print("Warning, no msurf detected, interpolating from mbins")
            self.interp_from_mbins = True
            self.msurf = MD_mFieldatsurface(fdir, fname="mbins")

        Field.__init__(self, self.msurf.Raw)
        self.inherit_parameters(self.msurf)
        if self.interp_from_mbins:
            self.header.Nsurfm_ave = str( float(self.header.Nmass_ave) 
                                         *float(self.header.tplot)   )

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        # Read 4D time series from startrec to endrec
        msurf = self.msurf.read(startrec, endrec, binlimits=binlimits, **kwargs)  

        if self.interp_from_mbins:

            gridvolumes = self.msurf.Raw.get_gridvolumes(binlimits=binlimits)
            gridvolumes = np.expand_dims(gridvolumes,axis=-1)

            # Read 4D time series from startrec to endrec
            msurf = np.divide(msurf, float(self.plotfreq))
            rhosurf = np.divide(msurf, gridvolumes)
 
        else:
            time = float(self.header.delta_t) * float(self.header.Nsurfm_ave)
            A = []
            A.append(float(self.header.binsize2)*float(self.header.binsize3))
            A.append(float(self.header.binsize1)*float(self.header.binsize3))
            A.append(float(self.header.binsize1)*float(self.header.binsize2))

            rhosurf = np.empty(msurf.shape)
            for i in range(3):
                rhosurf[:,:,:,:,i]   = msurf[:,:,:,:,i]  /(time*A[i])
                rhosurf[:,:,:,:,i+3] = msurf[:,:,:,:,i+3]/(time*A[i])

        return rhosurf


class MD_mFieldatsurface(MD_complexField):

    def __init__(self, fdir, fname="density"):

        #Use density field mbins divided by volume
        if fname is "density":
            self.mField = MD_dField(fdir)
        elif fname is "mbins":
            self.mField = MD_mField(fdir)
        Field.__init__(self,self.mField.Raw)
        self.inherit_parameters(self.mField)
        self.plotfreq = self.mField.plotfreq
        self.labels = ["xbottom","ybottom","zbottom",
                       "xtop","ytop","ztop"]
        self.nperbin = 6

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        #Read the whole domain, interpolate and then trim
        mdata   = self.mField.read(startrec, endrec, binlimits=None, **kwargs)
        #Get v on surface
        msurface = np.zeros([mdata.shape[0],
                             mdata.shape[1],
                             mdata.shape[2],
                             mdata.shape[3], 6],order='F')

        for rec in range(endrec-startrec+1):
            msurface[:,:,:,rec,:] = self.cellcentre2surface(mdata[:,:,:,rec])

        mmshapelist = list(mdata.shape)
        newshape = tuple(mmshapelist[0:4]+[self.nperbin])
        msurface = np.reshape(msurface, newshape)

        if (binlimits):
            msurface = self.trim_binlimits(binlimits, msurface)

        return msurface



class MD_CVmomField(MD_complexField):

    def __init__(self, fdir):

        self.mfluxField = MD_mfluxField(fdir, fname='mflux')
        Field.__init__(self,self.mfluxField.Raw)
        self.inherit_parameters(self.mfluxField)

    def read(self, startrec, endrec, **kwargs):

        # Read 4D time series from startrec to endrec
        mflux = self.mfluxField.read(startrec, endrec, **kwargs)  

        time = float(self.header.delta_t) * float(self.header.Nmflux_ave)
        A = []
        A.append(float(self.header.binsize2)*float(self.header.binsize3))
        A.append(float(self.header.binsize1)*float(self.header.binsize3))
        A.append(float(self.header.binsize1)*float(self.header.binsize2))

        momflux = np.empty(mflux.shape)
        for i in range(3):
            momflux[:,:,:,:,i]   = mflux[:,:,:,:,i]  /(time*A[i])
            momflux[:,:,:,:,i+3] = mflux[:,:,:,:,i+3]/(time*A[i])

        return momflux


class MD_CVvField(MD_complexField):

    def __init__(self, fdir):

        self.mField = MD_mfluxField(fdir, fname='msurf')
        self.momField = MD_mfluxField(fdir, fname='mflux')
        Field.__init__(self,self.momField.Raw)
        self.inherit_parameters(self.momField)

        if (self.mField.plotfreq == self.momField.plotfreq):
            self.plotfreq = self.momField.plotfreq
        else:
            print("Error in MD_CVvField -- Nmass_ave*tplot differs from Nmflux_ave")
            raise DataMismatch

    def read(self,startrec,endrec,**kwargs):

        mdata   = self.mField.read(startrec, endrec, **kwargs)  
        momdata = self.momField.read(startrec, endrec, **kwargs)  

        # Divide and patch any NaNs
        vdata = np.divide(momdata, mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata 


    def averaged_data(self, startrec, endrec, avgaxes=(), **kwargs):
        
        mdata   = self.mField.read(startrec, endrec, **kwargs)  
        momdata = self.momField.read(startrec, endrec, **kwargs)  

        if (avgaxes != ()):
            mdata = np.sum(mdata, axis=avgaxes) 
            momdata = np.sum(momdata, axis=avgaxes) 

        # Divide and patch any NaNs
        vdata = np.divide(momdata, mdata) 
        vdata[np.isnan(vdata)] = 0.0

        return vdata

class MD_vFieldatsurface(MD_complexField):

    def __init__(self, fdir):

        self.vField = MD_vField(fdir)
        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.plotfreq = self.vField.plotfreq
        self.labels = ["xxbottom","yxbottom","zxbottom",
                       "xybottom","yybottom","zybottom",
                       "xzbottom","yzbottom","zzbottom",
                       "xxtop","yxtop","zxtop",
                       "xytop","yytop","zytop",
                       "xztop","yztop","zztop"]
        self.nperbin = 18

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        vdata   = self.vField.read(startrec, endrec, binlimits=None, **kwargs)
        #Get v on surface
        vsurface = np.zeros([vdata.shape[0],
                             vdata.shape[1],
                             vdata.shape[2],
                             vdata.shape[3], 6, 3],order='F')

        for dim in range(3):
            for rec in range(endrec-startrec+1):
                vsurface[:,:,:,rec,:,dim] = self.cellcentre2surface(vdata[:,:,:,rec,dim])

        vvshapelist = list(vdata.shape)
        newshape = tuple(vvshapelist[0:4]+[self.nperbin])
        vsurface = np.reshape(vsurface, newshape)

        if (binlimits):
            vsurface = self.trim_binlimits(binlimits, vsurface)
 
        return vsurface




class MD_rhouuCVField(MD_complexField):

    def __init__(self, fdir, velocity_loc="surfaceinterp"):

        self.velocity_loc = velocity_loc

        # Get mean velocity and density field
        self.fdir = fdir
        self.momField = MD_CVmomField(self.fdir)
        if self.velocity_loc is "centre":
            self.vField = MD_vField(fdir)
        elif self.velocity_loc is "surfaceinterp":
            self.vField = MD_vFieldatsurface(fdir)

        Field.__init__(self,self.momField.Raw)
        self.inherit_parameters(self.momField)
        self.labels = ["xxbottom","yxbottom","zxbottom",
                       "xybottom","yybottom","zybottom",
                       "xzbottom","yzbottom","zzbottom",
                       "xxtop","yxtop","zxtop",
                       "xytop","yytop","zytop",
                       "xztop","yztop","zztop"]
        self.nperbin = 18

    def read(self,startrec,endrec,**kwargs):
        momdata = self.momField.read(startrec, endrec, **kwargs)
        vdata = self.vField.read(startrec, endrec, **kwargs)

        # Find outer product of v*v and reshape to 1x18 rather than 6x3
        if self.velocity_loc is "centre":
            rhouudata = np.einsum('abcdj,abcdk->abcdjk', momdata, vdata)
            vvshapelist = list(rhouudata.shape)
            newshape = tuple(vvshapelist[0:4]+[self.nperbin])
            rhouudata = np.reshape(rhouudata, newshape)

        elif self.velocity_loc is "surfaceinterp":

            # Velocity rhouu combines different surface fluxes...
            #           rho uy * uy dSy     
            #   ________  rho uy * ux dSx 
            #   |      |    rho ux * uy dSy
            #   |      |      rho ux * ux dSx
            #   |______|
            #         
            rhouudata = np.zeros([vdata.shape[0],
                                  vdata.shape[1],
                                  vdata.shape[2],
                                  vdata.shape[3], self.nperbin],order='F')

            for dim in range(3):
                rhouudata[...,dim::3] = momdata*vdata[...,dim::3]

        return rhouudata

    def averaged_data(self, startrec, endrec, avgaxes=(), **kwargs):
        
        momdata = self.momField.read(startrec, endrec, **kwargs)
        vdata = self.vField.read(startrec, endrec, **kwargs)

        if (avgaxes != ()):
            #Get shape after axes have been removed
            indx = [x for x in [0, 1, 2, 3] if x not in avgaxes]
            vvshapelist = list(vdata.shape)
            newshape = tuple([vvshapelist[i] for i in indx]+[self.nperbin])

            #Calculate sum over average axes
            vdata = np.mean(vdata, axis=avgaxes) 
            momdata = np.mean(momdata, axis=avgaxes)

            #Setup einsum and arrays
            if self.velocity_loc is "centre":
                einsumstr = 'abcdi,abcdj->abcdij'

                #Remove axes from einsum expression
                ltrs = ["a", "b", "c", "d"]
                for a in avgaxes:
                    einsumstr = einsumstr.replace(ltrs[a],"")

                # Find outer product of v*v and reshape to 1x18 rather than 6x3
                rhouudata = np.einsum(einsumstr, momdata, vdata)
                rhouudata = np.reshape(rhouudata, newshape)

            elif self.velocity_loc is "surfaceinterp":
                rhouudata = np.zeros(newshape, order='F')
                # Find product of u and rho u on six surface
                for dim in range(3):
                    rhouudata[...,dim::3] = momdata*vdata[...,dim::3]

        return rhouudata


class MD_pCVField(MD_complexField):


    def __init__(self, fdir, fname, peculiar=True, moving_ref=False):

        self.fname = fname
        try:
            self.PField = MD_pfluxField(fdir, fname)
        except DataNotAvailable:
            #As combined CV pressure doesn't exist, 
            # try getting from psurface and vflux
            if fname == 'total':
                self.pkField = MD_pfluxField(fdir, fname='vflux')
                self.pcField = MD_pfluxField(fdir, fname='psurface')
                self.PField = self.pkField
            else:
                raise DataNotAvailable

        if moving_ref:
            self.pRefField = MD_pfluxField(fdir, fname='dsurf_vflux')

        Field.__init__(self,self.PField.Raw)
        self.inherit_parameters(self.PField)
        self.peculiar = peculiar
        self.moving_ref = moving_ref

    def read(self, startrec, endrec, peculiar=None,
             verbose=False, moving_ref=None, **kwargs):

        # Override peculiar momenta / moving_ref specifier if required
        if peculiar == None:
            peculiar = self.peculiar
        if moving_ref == None:
            moving_ref = self.moving_ref

        # Read 4D time series from startrec to endrec
        if self.fname in ['total', 'vflux']:
            # Read kinetic terms
            pflux = self.PField.read(startrec,endrec,**kwargs)

            # Take off peculiar momenta if specified
            if peculiar:
                rhouuField = MD_rhouuCVField(self.fdir)
                rhouudata = rhouuField.read(startrec, endrec, **kwargs)
                pflux = pflux - rhouudata

            #Add psurface if required
            if self.fname is 'total':
                pflux = pflux + self.pcField.read(startrec, endrec, **kwargs)
        else:
            #Otherwise just read psurface
            pflux = self.PField.read(startrec, endrec, **kwargs)

        if moving_ref:
            pflux = pflux - self.pRefField.read(startrec, endrec, **kwargs)

        return pflux

    def averaged_data(self, startrec, endrec, 
                      avgaxes=(), peculiar=None, 
                      moving_ref=None, **kwargs):

        # Override peculiar momenta / moving_ref specifier if required
        if peculiar == None:
            peculiar = self.peculiar
        if moving_ref == None:
            moving_ref = self.moving_ref

        # Read 4D time series from startrec to endrec
        if (avgaxes != ()):

            if self.fname in ['total', 'vflux']:
                # Read kinetic terms
                pflux = self.PField.averaged_data(startrec, endrec, 
                                                  avgaxes=avgaxes, **kwargs)

                # Take off peculiar momenta if specified
                if peculiar:
                    rhouuField = MD_rhouuCVField(self.fdir)
                    rhouudata = rhouuField.averaged_data(startrec, endrec, 
                                                  avgaxes=avgaxes, **kwargs)
                    pflux = pflux - rhouudata

                #Add psurface if required
                if self.fname is 'total':
                    pflux = pflux + self.pcField.averaged_data(startrec, endrec, 
                                                               avgaxes=avgaxes, **kwargs)
            else:
                #Otherwise just read psurface
                pflux = self.PField.averaged_data(startrec, endrec, 
                                                  avgaxes=avgaxes, **kwargs)

            if moving_ref:
                pflux = pflux - self.pRefField.averaged_data(startrec, endrec, 
                                                             avgaxes=avgaxes, **kwargs)

        return pflux


class MD_scalarPCVField(MD_complexField):

    def __init__(self, fdir, fname, peculiar=True):

        self.fname = "P"
        self.fdir = fdir
        self.PField = MD_pCVField(fdir, fname)

        Field.__init__(self,self.PField.Raw)
        self.inherit_parameters(self.PField)
        self.peculiar = peculiar
        self.labels = ["P"]
        self.nperbin = 1

    def read(self, startrec, endrec, peculiar=None,
             verbose=False, **kwargs):

        Pfield = self.PField.read(startrec, endrec, **kwargs)
        return (Pfield[...,[0]]+Pfield[...,[5]]+Pfield[...,[8]])/3.
        
#    def averaged_data(self, startrec, endrec, 
#                      avgaxes=(), peculiar=None, **kwargs):
#        Pfield = self.PField.averaged_data(startrec, endrec, 
#                                          avgaxes=avgaxes, **kwargs)

#        return (Pfield[...,0]+Pfield[...,5]+Pfield[...,8])/3.

class MD_eFieldatsurface(MD_complexField):

    def __init__(self, fdir):

        self.EField = MD_EnergyField(fdir)
        Field.__init__(self,self.EField.Raw)
        self.inherit_parameters(self.EField)
        self.plotfreq = self.EField.plotfreq
        self.labels = ["xbottom","ybottom","zbottom",
                        "xtop","ytop","ztop"]
        self.nperbin = 6

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        edata   = self.EField.read(startrec, endrec, binlimits=None, **kwargs)
        #Get v on surface
        esurface = np.zeros([edata.shape[0],
                             edata.shape[1],
                             edata.shape[2],
                             edata.shape[3], 6],order='F')

        for rec in range(endrec-startrec+1):
            esurface[:,:,:,rec,:] = self.cellcentre2surface(edata[:,:,:,rec])

        eeshapelist = list(edata.shape)
        newshape = tuple(eeshapelist[0:4]+[self.nperbin])
        esurface = np.reshape(esurface, newshape)


        return esurface



class MD_rhouECVField(MD_complexField):

    def __init__(self, fdir, velocity_loc="surfaceinterp"):

        self.velocity_loc = velocity_loc

        # Get mean velocity and density field
        self.fdir = fdir
        self.momField = MD_CVmomField(self.fdir)

        if self.velocity_loc is "centre":
            self.EField = MD_EnergyField(fdir)
        elif self.velocity_loc is "surfaceinterp":
            self.EField = MD_eFieldatsurface(fdir)

        Field.__init__(self, self.momField.Raw)
        self.inherit_parameters(self.momField)
        self.labels = ["xbottom","ybottom","zbottom",
                       "xtop","ytop","ztop"]
        self.nperbin = 6

    def read(self, startrec, endrec, **kwargs):
        momdata = self.momField.read(startrec, endrec, **kwargs)
        Edata = self.EField.read(startrec, endrec, **kwargs)

        # Find product of rho u e from 6 mflux surfaces 
        # time energy (or energy per surface)
        rhoue = momdata*Edata

        return rhoue

    def averaged_data(self, startrec, endrec, 
                      avgaxes=(), **kwargs):

        momdata = self.momField.averaged_data(startrec, endrec, 
                                              avgaxes=avgaxes, **kwargs)
        Edata = self.EField.averaged_data(startrec, endrec, 
                                          avgaxes=avgaxes, **kwargs)

        # Find product of rho u e from 6 mflux surfaces 
        # time energy (or energy per surface)
        rhoue = momdata*Edata

        print((np.sum(momdata), np.sum(Edata), np.sum(rhoue), momdata.shape, Edata.shape, rhoue.shape))

        return rhoue


class MD_CVStressheat_Field(MD_complexField):

    def __init__(self, fdir, peculiar=True, velocity_loc="surfaceinterp"):

        self.fdir = fdir
        self.velocity_loc = velocity_loc
        if self.velocity_loc is "centre":
            self.vField = MD_vField(fdir)
        elif self.velocity_loc is "surfaceinterp":
            self.vField = MD_vFieldatsurface(fdir)
        else:
            print(("velocity_loc type " + self.velocity_loc 
                  + " not recognised, should be 'centre' or 'surfaceinterp'"))
            raise DataMismatch
        self.pressureField = MD_pCVField(fdir, fname='total')
        Field.__init__(self, self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ["xbottom","ybottom","zbottom",
                       "xtop","ytop","ztop"]
        self.nperbin = 6
        self.peculiar = peculiar

    def read(self, startrec, endrec, peculiar=None, **kwargs):

        if peculiar == None:
            peculiar = self.peculiar

        u = self.vField.read(startrec,endrec,**kwargs)
        pressure = self.pressureField.read(startrec, endrec, 
                                           peculiar=peculiar, 
                                           binlimits=None, **kwargs)

        if self.velocity_loc == "centre":
            Pi = np.reshape(pressure,[ pressure.shape[0],
                                       pressure.shape[1],
                                       pressure.shape[2],
                                       pressure.shape[3], 6, 3],                                            
                                       order='F')
            Pidotu = np.einsum('abcdji,abcdi->abcdj',Pi,u)
        elif self.velocity_loc == "surfaceinterp":

            Pidotu = np.zeros([ u.shape[0],
                                u.shape[1],
                                u.shape[2],
                                u.shape[3], 6], order='F')

            for dim in range(6):
                Pidotu[...,dim] =( pressure[...,0+dim*3]*u[...,0+dim*3]
                                  +pressure[...,1+dim*3]*u[...,1+dim*3]
                                  +pressure[...,2+dim*3]*u[...,2+dim*3])

        return Pidotu


    def averaged_data(self, startrec, endrec, avgaxes=(), peculiar=None, **kwargs):

        if peculiar == None:
            peculiar = self.peculiar

        vdata = self.vField.read(startrec,endrec,**kwargs)
        pressure = self.pressureField.read(startrec, endrec, 
                                           peculiar=peculiar, 
                                           binlimits=None, **kwargs)

        if (avgaxes != ()):

            #Get shape after axes have been removed
            indx = [x for x in [0, 1, 2, 3] if x not in avgaxes]
            vvshapelist = list(vdata.shape)
            newshape = tuple([vvshapelist[i] for i in indx]+[self.nperbin])

            #Calculate sum over average axes
            vdata = np.mean(vdata, axis=avgaxes) 
            pressure = np.mean(pressure, axis=avgaxes)

            #Setup einsum and arrays
            if self.velocity_loc is "centre":
                #Remove axes from einsum expression
                einsumstr = 'abcdji,abcdi->abcdj'
                ltrs = ["a", "b", "c", "d"]
                for a in avgaxes:
                    einsumstr = einsumstr.replace(ltrs[a],"")

                shapelist = list(pressure.shape)
                Pi = np.reshape(pressure, shapelist[:-1]+[6]+[3], order='F')
                Pidotu = np.einsum(einsumstr, Pi, vdata)

            elif self.velocity_loc is "surfaceinterp":

                Pidotu = np.zeros(newshape, order='F')
                for dim in range(6):
                    Pidotu[...,dim] =( pressure[...,0+dim*3]*vdata[...,0+dim*3]
                                      +pressure[...,1+dim*3]*vdata[...,1+dim*3]
                                      +pressure[...,2+dim*3]*vdata[...,2+dim*3])

        return Pidotu


class MD_heatfluxCVField(MD_complexField):

    def __init__(self, fdir, fname="total", peculiar=True):

        self.eflux = MD_efluxField(fdir, 'eflux')
        self.esurface = MD_efluxField(fdir, 'esurface')

        Field.__init__(self, self.esurface.Raw)
        self.inherit_parameters(self.esurface)
        self.labels = ["xbottom","ybottom","zbottom",
                        "xtop","ytop","ztop"]
        self.nperbin = 6
        self.peculiar = peculiar
        self.fname = fname
        if peculiar:
            self.energyadvctField = MD_rhouECVField(fdir)
            self.CVStressheatField = MD_CVStressheat_Field(fdir)

    def read(self, startrec, endrec, peculiar=None, **kwargs):

        # Read 4D time series from startrec to endrec
        eflux = self.eflux.read(startrec, endrec, **kwargs)
        esurface = self.esurface.read(startrec, endrec, **kwargs)
        etotal = eflux + esurface

        # Take off square of peculiar energy advection and stress heating if specified
        if peculiar == None:
            peculiar = self.peculiar

        if peculiar:
            if (self.fname is 'eflux'):
                # Pdata = Pdata - energy (x) u
                energyadvctdata =  self.energyadvctField.read(startrec, endrec, **kwargs)
                etotal = etotal - energyadvctdata
            elif (self.fname is 'esurface'):
                # Pi dot u
                CVStressheatdata =  self.CVStressheatField.read(startrec, endrec, **kwargs)
                etotal = etotal - CVStressheatdata
            else:   
                # Pi dot u & energy (x) u
                energyadvctdata =  self.energyadvctField.read(startrec, endrec, **kwargs)
                CVStressheatdata =  self.CVStressheatField.read(startrec, endrec, **kwargs)
                etotal = etotal - (CVStressheatdata + energyadvctdata)

        return etotal

    def averaged_data(self, startrec, endrec, avgaxes=(), peculiar=None, **kwargs):

        # Read 4D time series from startrec to endrec
        eflux = self.eflux.averaged_data(startrec, endrec, avgaxes=avgaxes, **kwargs)
        esurface = self.esurface.averaged_data(startrec, endrec, avgaxes=avgaxes, **kwargs)
        etotal = eflux + esurface

        # Take off square of peculiar energy advection and stress heating if specified
        if peculiar == None:
            peculiar = self.peculiar

        if peculiar:
            if (self.fname is 'eflux'):
                # Pdata = Pdata - energy (x) u
                energyadvctdata = self.energyadvctField.averaged_data(startrec, 
                                                                      endrec, 
                                                                      avgaxes=avgaxes, 
                                                                      **kwargs)
                etotal = etotal - energyadvctdata
            elif (self.fname is 'esurface'):
                # Pi dot u
                CVStressheatdata =  self.CVStressheatField.averaged_data(startrec, 
                                                                         endrec, 
                                                                         avgaxes=avgaxes, 
                                                                         **kwargs)
                etotal = etotal - CVStressheatdata
            else:   
                # Pi dot u & energy (x) u
                energyadvctdata =  self.energyadvctField.averaged_data(startrec, 
                                                                       endrec, 
                                                                       avgaxes=avgaxes, 
                                                                       **kwargs)
                CVStressheatdata =  self.CVStressheatField.averaged_data(startrec, 
                                                                         endrec, 
                                                                         avgaxes=avgaxes, 
                                                                         **kwargs)
                etotal = etotal - (CVStressheatdata + energyadvctdata)

        return etotal



class MD_heatfluxapprox(MD_complexField):

    def __init__(self, fdir):

        self.dTdrField = MD_dTdrField(fdir)
        self.dudrField = MD_strainField(fdir)

        Field.__init__(self, self.dTdrField.Raw)
        self.inherit_parameters(self.dTdrField)
        self.labels = ["qx","qy","qz"]
        self.nperbin = 3

    def read(self, startrec, endrec, k=0.5, c=0., f=0., **kwargs):

        dTdr = self.dTdrField.read(startrec, endrec, **kwargs)
        dudr = self.dudrField.read(startrec, endrec, **kwargs)

        newshape = list(dudr.shape[:-1]) + [self.nperbin]
        q = np.empty(newshape)
        q[...,0] = c * dudr[...,1] * dTdr[...,1]
        q[...,1] = (k + 3. * f * np.power(dudr[...,1],2) ) * dTdr[...,1] 
        q[...,2] = 0.

        return q

    def averaged_data(self, startrec, endrec, avgaxes=(), k=0.5, c=0., f=0., **kwargs):

        dTdr = self.dTdrField.averaged_data(startrec, endrec, avgaxes=avgaxes, **kwargs)
        dudr = self.dudrField.averaged_data(startrec, endrec, avgaxes=avgaxes, **kwargs)

        newshape = list(dudr.shape[:-1]) + [self.nperbin]
        q = np.empty(newshape)
        q[...,0] = c * dudr[...,1] * dTdr[...,1]
        q[...,1] = (k + 3. * f * np.power(dudr[...,1],2) ) * dTdr[...,1] 
        q[...,2] = 0.

        return q

class MD_strainField(MD_complexField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = MD_vField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ["dudx","dudy","dudz",
                       "dvdx","dvdy","dvdz",
                       "dwdx","dwdy","dwdz"]
        self.nperbin = 9

    def read(self,startrec,endrec, preavgaxes=(3), 
             highpassfilter=0.0, binlimits=None,**kwargs):

        vdata = self.vField.read(startrec, endrec, 
                                 binlimits=None,**kwargs)

        if highpassfilter>0.0:

            import scipy as scp
            scp.ndimage.map_coordinates(vdata, vdata.shape, order=3, mode='nearest')
        
        straindata = self.grad(vdata,preavgaxes=preavgaxes,
                               dx=float(self.header.binsize1),
                               dy=float(self.header.binsize2),
                               dz=float(self.header.binsize3))

        if (binlimits):
            straindata = self.trim_binlimits(binlimits, straindata)

        return straindata

class MD_vortField(MD_complexField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = MD_vField(fdir)
        self.strainField = MD_strainField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.strainField)
        self.labels = ["x","y","z"]
        self.nperbin = 3

    def read(self,startrec,endrec, binlimits=None,**kwargs):
        dudr = self.strainField.read(startrec, endrec, 
                                      binlimits=None,**kwargs)

        vortdata = np.empty([dudr.shape[0],dudr.shape[1],
                             dudr.shape[2],dudr.shape[3],self.nperbin])
        vortdata[:,:,:,:,0] = ( dudr[:,:,:,:,7]
                               -dudr[:,:,:,:,5])
        vortdata[:,:,:,:,1] = ( dudr[:,:,:,:,2]
                               -dudr[:,:,:,:,6])
        vortdata[:,:,:,:,2] = ( dudr[:,:,:,:,3]
                               -dudr[:,:,:,:,1])

        if (binlimits):
            vortdata = self.trim_binlimits(binlimits, vortdata)

        return  vortdata


class MD_dissipField(MD_complexField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = MD_vField(fdir)
        self.strainField = MD_strainField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.strainField)
        self.labels = ["mag"]
        self.nperbin = 1

    def read(self,startrec,endrec, binlimits=None, 
                 highpassfilter=0.0, preavgaxes=(3),**kwargs):

        dudr = self.strainField.read(startrec, endrec, 
                                     highpassfilter=highpassfilter, 
                                     binlimits=None,**kwargs)

        dissipdata = np.empty([dudr.shape[0],dudr.shape[1],
                               dudr.shape[2],dudr.shape[3],self.nperbin])


        #From Viswanath 2006 D = \int_V |del u|^2 + |del v|^2 + |del w|^2 dV
        dissipdata[:,:,:,:,0] = (  np.power(dudr[:,:,:,:,0],2) 
                                 + np.power(dudr[:,:,:,:,1],2)
                                 + np.power(dudr[:,:,:,:,2],2)
                                 + np.power(dudr[:,:,:,:,3],2)
                                 + np.power(dudr[:,:,:,:,4],2)
                                 + np.power(dudr[:,:,:,:,5],2)
                                 + np.power(dudr[:,:,:,:,6],2)
                                 + np.power(dudr[:,:,:,:,7],2)
                                 + np.power(dudr[:,:,:,:,8],2))

        if (binlimits):
            dissipdata = self.trim_binlimits(binlimits, dissipdata)

        return  dissipdata


class MD_dTdrField(MD_complexField):

    def __init__(self,fdir,rectype='bins', peculiar=True):
        self.TField = MD_TField(fdir, peculiar=peculiar)

        Field.__init__(self,self.TField.Raw)
        self.inherit_parameters(self.TField)
        self.labels = ["dTdx","dTdy","dTdz"]
        self.nperbin = 3

    def read(self,startrec,endrec, preavgaxes=(3), binlimits=None,**kwargs):

        Tdata = self.TField.read(startrec, endrec, binlimits=None)
        dTdr = self.grad(Tdata,preavgaxes=preavgaxes)

        if (binlimits):
            dTdr = self.trim_binlimits(binlimits, dTdr)


        return dTdr



class MD_ufluctField(MD_complexField):

    """
        Subtract the laminar solutions from
        the velocity field
    """

    def __init__(self, fdir, rectype='bins'):
        self.vField = MD_vField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ["x","y","z"]
        self.nperbin = 3

    def read(self, startrec, endrec, binlimits=None, **kwargs):

        vdata = self.vField.read(startrec, endrec, **kwargs)

        def remove_laminar(vin, lims):
            v_laminar = np.linspace(-1.0, 1.0, self.Raw.nbins[wallnormaldir])
            return vin[:] - v_laminar[lims[0]:lims[1]]

        #Add u component of laminar flow in wallnormal direction
        wallnormaldir = 1
        lims = (0,self.Raw.nbins[wallnormaldir])
        u = np.copy(vdata)
        for plusrec in range(vdata.shape[3]):
            u[:,:,:,plusrec,0] = np.apply_along_axis(remove_laminar,wallnormaldir, 
                                                      vdata[:,:,:,plusrec,0],lims)

        if (binlimits):
            u = self.trim_binlimits(binlimits, u)


        return u

class MD_velsoundField(MD_complexField):

    def __init__(self,fdir):
        self.msurf = m1 = MD_mfluxField(fdir,'msurf')
        self.pressureField = MD_pCVField(fdir,fname='total')

        Field.__init__(self,self.pressureField.Raw)
        self.inherit_parameters(self.pressureField)
        self.labels = ["cxx","cxy","cxz",
                       "cyx","cyy","cyz",
                       "czx","czy","czz"]
        self.nperbin = 9

    def read(self,startrec,endrec, binlimits=None, **kwargs):

        msurfdata = self.msurf.read(startrec, endrec, binlimits=binlimits)
        Pdata = self.pressureField.read(startrec, endrec, binlimits=binlimits)

        Pi = np.reshape(Pdata,[ Pdata.shape[0],
                                Pdata.shape[1],
                                Pdata.shape[2],
                                Pdata.shape[3], 3, 6],                                            
                                order='F')

        #Get difference between top and bottom surface
        PdS = Pi[:,:,:,:,:,0:3]-Pi[:,:,:,:,:,3:6]
        mdS = msurfdata[:,:,:,:,0:3]-msurfdata[:,:,:,:,3:6]

        #Get speed of sound estimate
        c = np.zeros([Pdata.shape[0],
                      Pdata.shape[1],
                      Pdata.shape[2],
                      Pdata.shape[3],3,3])

        for i in range(3):
            c[:,:,:,:,i,:] = np.divide(PdS[:,:,:,:,i,:],mdS)

        c[~np.isfinite(c)] = 0.

        c = c.reshape([Pdata.shape[0],
                       Pdata.shape[1],
                       Pdata.shape[2],
                       Pdata.shape[3],9])

        return c


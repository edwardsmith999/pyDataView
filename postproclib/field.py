#! /usr/bin/env python
import numpy as np
import sys

from .pplexceptions import OutsideRecRange


class Field():

    """
        Abstract base class to be inherited by MDField, CFDField and CPLField.

        Authors: Ed Smith 2019 & David Trevelyan (2010-2014)

        Abstract base class template that generally specifies how data
        should be processed and returned in postprocessing routines.
        Field should be inherited by MDField (which will then, in turn,
        be inherited by MD_mField for mass, etc.). 

        Fields are, essentially, data reformatters. They must be instantiated
        with a RawData object, which is used to do the actual reading, and
        the methods in Field re-package that data in an easily plottable
        format.
    
        TOP-LEVEL EXAMPLE
        
            v = MD_vField(fdir)
            y, v3 = v.profile(axis=1)
            plt.plot(v3[:,0], y)
        
        This will instantiate a velocity field (see MDFields for details of 
        the complex inheritance and containment), read and store the data
        from multiple files to construct a velocity profile, and finally
        will plot the x-component of velocity against the y-axis.

        In line with RawData readers, axes correspond to:

            [ spatial ax1, spatial ax2, spatial ax3, record, component ] 
            [     0      ,      1     ,      2     ,    3  , 4 (&-1)   ] 

    """
    
    def __init__(self, RawDataObj):
        self.Raw = RawDataObj
        self.fdir = self.Raw.fdir
        self.grid = self.Raw.grid
        self.maxrec = self.Raw.maxrec

    def read(self,startrec,endrec,**kwargs):

        """
            TO BE OVERRIDDEN IN COMPLICATED FIELDS.
            Method that returns grid data that is read by Raw.
            
        """

        if (endrec > self.maxrec):
            print(('Record ' + str(endrec) + ' is greater than the maximum '
                  'available (' + str(self.maxrec) + ').'))
            raise OutsideRecRange

        grid_data = self.Raw.read(startrec,endrec,**kwargs)
        return grid_data
    
    def read_halo(self,startrec,endrec,**kwargs):

        """
            Method to read halo if Raw data reader supports it.          
        """
        try:
           return self.Raw.read_halo(startrec,endrec,**kwargs)
        except AttributeError:
            raise

    def averaged_data(self,startrec,endrec,avgaxes=(),**kwargs):

        """
            TO BE OVERRIDDEN IN ALL COMPLICATED FIELDS.
            Average the data in the user-specified way.
        """

        # Read 4D time series from startrec to endrec
        grid_data = self.read(startrec,endrec,**kwargs)
           
        # Average over axes
        if (avgaxes != ()):
            grid_data = np.mean(grid_data,axis=avgaxes) 

        #return avg_data
        return grid_data 

    def contour(self,axes,startrec=0,endrec=None,**kwargs):

        """
            NOT TO BE OVERRIDDEN UNLESS ABSOLUTELY NECESSARY
            Wrapper for averaged_data, returns easily plottable data 
        """

        avgaxes = [0,1,2,3]
        avgaxes.remove(axes[0])
        avgaxes.remove(axes[1])
        avgaxes = tuple(avgaxes)

        if (endrec==None): 
            endrec = self.maxrec

        data = self.averaged_data(startrec,endrec,avgaxes=avgaxes,**kwargs)
        # Need version 1.7.1 of numpy or higher
        X, Y = np.meshgrid(self.grid[axes[0]],self.grid[axes[1]],indexing='ij')
        return X, Y, data 
 
    def profile(self,axis,startrec=0,endrec=None,**kwargs):

        """
            NOT TO BE OVERRIDDEN UNLESS ABSOLUTELY NECESSARY
            Wrapper for averaged_data, returns easily plottable data 
        """

        avgaxes = [0,1,2,3]
        avgaxes.remove(axis)
        avgaxes = tuple(avgaxes)

        if (endrec==None): 
            endrec = self.maxrec

        data = self.averaged_data(startrec,endrec,avgaxes=avgaxes,**kwargs)
        return self.grid[axis], data

    def quiver(self,axes,components=None,startrec=0,endrec=None,**kwargs):

        """
            NOT TO BE OVERRIDDEN UNLESS ABSOLUTELY NECESSARY
            Wrapper for averaged_data, returns easily plottable data 
        """

        if (components==None):
            components = axes

        X, Y, data = self.contour(axes,startrec=startrec,endrec=endrec,**kwargs)

        #avgaxes = [0,1,2,3]
        #avgaxes.remove(axes[0])
        #avgaxes.remove(axes[1])
        #avgaxes = tuple(avgaxes)

        #if (endrec==None): 
        #    endrec = self.maxrec

        #data = self.averaged_data(startrec,endrec,avgaxes=avgaxes,**kwargs)

        # Need version 1.7.1 of numpy or higher
        #X, Y = np.meshgrid(self.grid[axes[0]],self.grid[axes[1]],indexing='ij')

        return X, Y, data[:,:,components]


    class AxisManager():

        def __init__(self):
            self.nreduced = 0
            self.axisactive = [True]*5

        def reduce_axes(self,axes):
            for axis in axes:
                self.nreduced += 1
                self.axisactive[axis] = False 

        def current_axis_number(self,axis_request):
            if (not self.axisactive[axis_request]):
                return None
            n = 0
            for otheraxis in range(axis_request):
                if (not self.axisactive[otheraxis]):
                    n += 1
            return int(axis_request - n)
        
        def current_axes_numbers(self,axes_request):
            newaxes = [] 
            for axis in list(axes_request):
                newaxes.append(self.current_axis_number(axis))
            return tuple(newaxes)

    def managed_mean(self, axismanager, data, avgaxes):
        newaxes = axismanager.current_axes_numbers(avgaxes)
        if (None in newaxes):
            sys.exit("Can't average over an axis that has been reduced")
        avgdata = np.mean(data, axis=newaxes) 
        axismanager.reduce_axes(avgaxes)
        return avgdata

    def managed_fft(self,axismanager, data, fftaxes):
        newaxes = axismanager.current_axes_numbers(fftaxes)
        if (None in newaxes):
            sys.exit("Can't fft over an axis that has been reduced")
        fftdata = np.fft.fftn(data,axes=newaxes)
        return fftdata

    def managed_energyfield(self,axismanager, data, fftaxes):
        
        def add_negatives(a):
            b = a
            for i in range(1,len(b)/2):
                b[i] += a[-i]
            return b

        newfftaxes = axismanager.current_axes_numbers(fftaxes)

        # Count N
        N = 1
        for axis in newfftaxes:
            N = N * data.shape[axis]

        # Initial energy in every wavenumber (pos and neg)
        E = np.abs(data)**2.0
         
        #Add negative contributions to positive wavenumbers
        nd = len(E.shape)
        slicer = [slice(None)]*nd
        for axis in newfftaxes:

            E = np.apply_along_axis(add_negatives,axis,E)
            # Discard negative parts after adding to positive
            k = E.shape[axis]
            mid = int(np.ceil(float(k)/2.0))
            cutout = np.s_[0:mid+1:1]
            slicer[axis] = cutout
            E = E[slicer]

            # Refresh slice for new axis calculation
            slicer[axis] = slice(None)

        return E/N

    def managed_window(self,axismanager, data, windowaxis):

        def window_axis_function(a, window):
            a = a * window
            return a

        newaxis = axismanager.current_axis_number(windowaxis)

        N = data.shape[newaxis]
        window = np.hanning(N)

        # Save "window summed and squared" (see Numerical Recipes)
        wss = np.sum(window**2.0)/float(N)

        # Apply window
        windoweddata = np.apply_along_axis(window_axis_function, 
                                           newaxis, data, window)

        return windoweddata, wss


    def trim_binlimits(self, binlimits, bins):

        """
            Trims a given field of bins based on binlimits
        """

        # Defaults
        lower = [0]*3
        upper = [i for i in bins.shape] 

        for axis in range(3):
            if (binlimits[axis] == None):
                continue
            else:
                lower[axis] = binlimits[axis][0] 
                upper[axis] = binlimits[axis][1] 

        return bins[lower[0]:upper[0],
                    lower[1]:upper[1],
                    lower[2]:upper[2], :, :]

    def power_spectrum(self,data=None,startrec=None,endrec=None,
                       preavgaxes=(), fftaxes=(),postavgaxes=(), 
                       windowaxis=None, verify_Parseval=True,
                       savefile=None,**kwargs):

        """
            Calculates power spectrum
        """

        # ---------------------------------------------------------------- 
        # Checks
        if (not isinstance(preavgaxes,tuple)):
            try:
                preavgaxes = tuple([preavgaxes])
            except:
                print('Failed to make preavgaxes and fftaxes a tuple')
        if (not isinstance(fftaxes,tuple)):
            try:
                fftaxes = tuple([fftaxes])
            except:
                print('Failed to make preavgaxes and fftaxes a tuple')
        if (not isinstance(postavgaxes,tuple)):
            try:
                postavgaxes = tuple([postavgaxes])
            except:
                print('Failed to make preavgaxes and fftaxes a tuple')

        if (4 in postavgaxes or 4 in fftaxes or 4 in preavgaxes):
            message = "WARNING: you're asking me to average or fft over "
            message += "each component of the field. I don't know how to "
            message += "deal with this right now. Aborting."
            sys.exit(message)

        if (windowaxis):
            if (windowaxis in preavgaxes or windowaxis in postavgaxes):
                message = "Warning: you're asking me to window over an axis "
                message += "that you're eventually going to average over. "
                message += "Aborting."
                sys.exit(message)
            if (windowaxis not in fftaxes):
                message = "Warning: you're asking me to window over an axis "
                message += "that won't be Fourier transformed. This makes no "
                message += "sense. Aborting."
        
        # ---------------------------------------------------------------- 
        # Do the process 
        if (startrec==None):
            startrec = 0

        if (endrec==None):
            endrec = self.maxrec
         
        axisman = self.AxisManager()
        if data == None:
            data = self.read(startrec, endrec,**kwargs)

        data = self.managed_mean(axisman, data, preavgaxes)

        if (windowaxis):
            data, wss = self.managed_window(axisman, data, windowaxis)

        if (verify_Parseval):
            Esumreal = np.sum(np.abs(data)**2.0)

        fftdata = self.managed_fft(axisman, data, fftaxes)
        energy = self.managed_energyfield(axisman, fftdata, fftaxes)

        if (verify_Parseval):
            Esumfft = np.sum(energy)
            ratio = abs(Esumreal - Esumfft)/Esumreal 
            perc = (1. - ratio)*100.
            print(('Parseval thm (discounting window): ' + "%9.6f"%perc + '%'))

        if (windowaxis):
            energy = energy / wss

        energy = self.managed_mean(axisman, energy, postavgaxes)

        if (savefile):
            with open(savefile,'w') as f:
                f.write(energy)
        
        return energy


    def grad(self, data, dx=None, 
                         dy=None, 
                         dz=None, preavgaxes=()):

        """
            Return the gradient of a vector field
        """

        # ---------------------------------------------------------------- 
        # Checks
        if (not isinstance(preavgaxes,tuple)):
            try:
                preavgaxes = tuple([preavgaxes])
            except:
                print('Failed to make preavgaxes in grad')

        #if (dxyz is None):
        #    dxyz=[self.Raw.dx,self.Raw.dy,self.Raw.dz]

        data = np.mean(data,axis=preavgaxes,keepdims=True)

        if (dx is None):
            dx=self.Raw.dx
        if (dy is None):
            dy=self.Raw.dy
        if (dz is None):
            dz=self.Raw.dz
        dxyz = (dx, dy, dz)

        ndims = data.shape[4]
        nonsingleton = [i!=1 for i in data.shape[0:3]]
        dxyz = [elem for i,elem in enumerate(dxyz) if nonsingleton[i]]

        gradv = np.zeros(list(data.shape[:-1]) + [3*ndims])
        for rec in range(gradv.shape[-2]):
            for ixyz in range(ndims):

                grad_temp = np.gradient(np.squeeze(data[:,:,:,rec,ixyz]), 
                                        dx, dy, dz)

                for jxyz in range(np.sum(nonsingleton)):
                    c = 3*ixyz + jxyz   
                    gradv[:,:,:,rec,c] = grad_temp[jxyz]

        return gradv


    def write(self, data, fdir, fname, startrec=0, endrec=None, **kwargs):


        """
            Write a 5D array of data in format specified by inhereting objects  
                data[nx,ny,nz,nrecs,ndata]
                where nx,ny and nz are number of cells in x,y and z respectivly
                  nrecs is the number of recs from startrec to endrec and
                  ndata is the number of datavalue for the current datatype 
                  (e.g. density has 1, velocity has 3, stress has 9, etc)

            Optional inputs:

                startrec - starting record to write of data array (integer)
                endrec   - record at which to finish (integer)
                fdir     - default directory to write data (string)
                fname    - filename to use (string)

            Return:
                
                None                
        """
        self.Raw.write(data, fdir, fname, startrec=startrec, 
                       endrec=endrec, **kwargs)

    def write_dx_file(self, startrec, endrec, writedir=None, 
                            component=0, norm=False, origin=None, **kwargs):

        """
           Write MD field to dx file format which is primarily
           useful for importing into VMD, see 
           http://www.ks.uiuc.edu/Research/vmd/plugins/molfile/dxplugin.html
           and format website http://www.opendx.org/index2.php
           NOTE -- VMD dx format assumes data points are located at the
                   cell vertices while Field class and it's children contain
                   cell centred data
        """

        #Get field data
        datamin = []; datamax = []
        for rec in range(startrec,endrec):

            data = self.read(startrec=rec,endrec=rec,**kwargs)

            if norm:
                if ((np.max(data[:,:,:,:,component])) > 1e-14):
                    data = (data-np.min(data[:,:,:,:,component])
                            /( np.max(data[:,:,:,:,component])
							  -np.min(data[:,:,:,:,component])))


            #Return minimum and maximum values
            datamin.append(np.min(data[:,:,:,:,component]))
            datamax.append(np.max(data[:,:,:,:,component]))

            Nx, Ny, Nz = data.shape[0], data.shape[1], data.shape[2]
            dx,dy,dz = [(self.grid[i][1] - self.grid[i][0]) for i in range(3)]
            Lx = float(Nx) * dx; Ly = float(Ny) * dy; Lz = float(Nz) * dz
            originx = np.min(self.grid[0])
            originy = np.min(self.grid[1])
            originz = np.min(self.grid[2])
            if origin != None:
                assert len(origin) == 3
                originx = origin[0] #-Ly/2
                originy = origin[1] #-Ly/2.0
                originz = origin[2] #-Lz/2.0
            data = self.cellcentre2vertex(data[:,:,:,0,component])

            Nx_v, Ny_v, Nz_v = data.shape[0], data.shape[1], data.shape[2]

            #Get file name
            if (writedir == None):
                writedir = self.fdir + '/vmd/vol_data/'

            dxFileName = writedir + 'DATA' + str(rec) + '.dx'

            #Write data
            with open(dxFileName,'w+') as f:

                # - - Write Header - -
                #dx_ = dx*1.25; dy_ = dy*1.25; dz_ = dz*1.25
                f.write("object 1 class gridpositions counts%8.0f%8.0f%8.0f\n" % (Nx_v,Ny_v,Nz_v))
                f.write("origin%16g%16g%16g\n" % (originx,originy,originz))
                f.write("delta %16g 0 0\n" % dx)
                f.write("delta 0 %16g 0\n" % dy)
                f.write("delta 0 0 %16g\n" % dz)
                f.write("object 2 class gridconnections counts%8.0f%8.0f%8.0f\n" % (Nx_v,Ny_v,Nz_v))
                f.write("object 3 class array type double rank 0 items%8.0f follows\n" % (Nx_v*Ny_v*Nz_v))

                # - - Write Data - -
                col=1
                for i in range(Nx_v):
                    for j in range(Ny_v):
                        for k in range(Nz_v):
                            f.write("%16E" %  data[i,j,k])
                            col=col+1
                            if (col>3):
                                f.write(' \n')
                                col=1

                # - - Write Footer - - 
                if (col != 1):
                    f.write('           \n')
                f.write('object "'+str(self).split('.')[1].split(' ')[0]+'" class field \n')

        return np.mean(datamin), np.mean(datamax)

    # Write ascii type field
    def write_asciifield(self,startrec,endrec,
                        writedir=None,maptocosine=True,
                        flipdir=[False,True,False],**kwargs):

        #Get file name
        if (writedir == None):
            writedir = self.fdir

        Nx, Ny, Nz = data.shape[0], data.shape[1], data.shape[2]
        Nxyz = [Nx,Ny,Nz]
        for n,flip in enumerate(flipdir):
            if flip:
                mindir[n] = Nxyz[n]
                maxdir[n] = 0
            else:
                mindir[n] = 0
                maxdir[n] = Nxyz[n] 

        data = self.read(startrec=startrec,endrec=endrec,**kwargs)

        outfiles =[]
        for rec in range(startrec,endrec):

            FileName = writedir + 'u' + str(rec) + '.asc'
            outfiles.append(FileName)
            with open(FileName,'w+') as f:
                for nx in range(mindir[0],maxdir[0]):
                    for ny in range(mindir[1],maxdir[1]):
                        for nz in range(mindir[2],maxdir[2]):
                            for ixyz in data.shape[4]:
                                if maptocosine:
                                    f.write(str(
                                                self.map_data_lineartocosine(
                                                data[nx,ny,nz,rec,ixyz],
                                                self.Raw.Ny,
                                                self.Raw.a,
                                                self.Raw.b))
                                            +"\n")
                                else:
                                    f.write(str(
                                                data[nx,ny,nz,rec,ixyz])
                                            +"\n")

        return outfiles


    # Write ascii type field
    def map_3Ddata_cosinetolinear(self,data,flipdir=[False,True,False],**kwargs):

        Nx, Ny, Nz = data.shape[0], data.shape[1], data.shape[2]
        Nxyz = [Nx,Ny,Nz]
        mindir = [0,0,0]; maxdir = [Nx,Ny,Nz]
        for n,flip in enumerate(flipdir):
            if flip:
                mindir[n] = Nxyz[n]
                maxdir[n] = 0
            else:
                mindir[n] = 0
                maxdir[n] = Nxyz[n] 

        lindata = np.empty(data.shape)
        for nx in range(mindir[0],maxdir[0]):
            for nz in range(mindir[2],maxdir[2]):
                for rec in range(data.shape[3]):
                    for ixyz in range(data.shape[4]):
                        print((nx,nz,rec,ixyz))
                        lindata[nx,:,nz,rec,ixyz] = self.map_data_cosinetolinear(
                                            data[nx,:,nz,rec,ixyz],
                                            self.Raw.Ny,
                                            self.Raw.a,
                                            self.Raw.b)

        return lindata

    def map_data_lineartocosine(self, values_on_linear_grid, Ny, a, b, plot=False):
        """
            Map data on a linear grid to a cosine grid 
        """
        import scipy.interpolate as interp
        ycells = np.linspace(0, Ny, Ny)
        ylin = np.linspace(a, b, Ny)
        ycos = 0.5*(b+a) - 0.5*(b-a)*np.cos((ycells*np.pi)/(Ny-1))
        values_on_cosine_grid = interp.griddata(ylin, values_on_linear_grid, 
                                                ycos, method='cubic',
                                                fill_value=values_on_linear_grid[-1])
        if plot:
            import matplotlib.pyplot as plt
            plt.plot(ylin,values_on_linear_grid,'o-',alpha=0.4,label='lineartocosine Before')

            plt.plot(ycos,values_on_cosine_grid,'x-',label='lineartocosine After')
            plt.legend()
            plt.show()
        return values_on_cosine_grid

    def map_data_cosinetolinear(self,values_on_cosine_grid,Ny,a,b):
            """
                Map data on a cosine grid to a linear grid 
            """
            import scipy.interpolate as interp
            ycells = np.linspace(0, Ny, Ny)
            ylin = np.linspace(a, b, Ny)
            ycos = 0.5*(b+a) - 0.5*(b-a)*np.cos((ycells*np.pi)/(Ny-1))
            #print(ycos.shape,values_on_cosine_grid.shape)
            #plt.plot(ycos,values_on_cosine_grid,'x-',label='cosinetolinear Before')
            values_on_linear_grid = interp.griddata(ycos, values_on_cosine_grid, 
                                                    ylin, method='cubic',
                                                    fill_value=values_on_cosine_grid[-1])
            #from scipy.ndimage import map_coordinates
            #values_on_linear_grid = interp2.map_coordinates(values_on_cosine_grid,ycos,output=ylin)
            #plt.plot(ylin,values_on_linear_grid,'o-',alpha=0.4,label='cosinetolinear After')
            #plt.legend()
            #plt.show()
            return values_on_linear_grid

    def field_interpolator(self, celldata):

        from scipy.interpolate import RegularGridInterpolator

        #Need to turn off bounds errors and fill values to allow extrapolation
        fn = RegularGridInterpolator((self.grid[0], self.grid[1], self.grid[2]),
                                     celldata, bounds_error=False, fill_value=None)

        return fn

    def interp_3Darrays(self, fn, x, y, z):
            """
                We need array data as a list of lists
            """

            #We need array data as a list of lists
            pts = []
            for i, xp in enumerate(x):
                for j, yp in enumerate(y):
                    for k, zp in enumerate(z):
                        pts.append([xp, yp, zp])
   
            #Interpolate and reshape
            data = fn(pts)
            interpdata = data.reshape(x.size, y.size, z.size)
            return interpdata


    def cellcentre2vertex(self, celldata, method="zoom"):

        """
           Routine to return grid data on an array one larger than the existing
           cell centred data - currently uses zoom for simplicity

        """
        if method is "zoom":
            import scipy.ndimage
            Nx, Ny, Nz = celldata.shape[0], celldata.shape[1], celldata.shape[2]
            vertexdata = scipy.ndimage.zoom(celldata,((Nx+1)/float(Nx),
                                                      (Ny+1)/float(Ny),
                                                      (Nz+1)/float(Nz)))

        elif method is "interp":

            #Define values
            xg = self.grid[0]
            yg = self.grid[1]
            zg = self.grid[2]
            dx = xg[1]-xg[0]
            dy = yg[1]-yg[0]
            dz = zg[1]-zg[0]

            #Get interpolator
            fn = self.field_interpolator(celldata)

            #Get grid of courner nodes
            Nx, Ny, Nz = celldata.shape[0], celldata.shape[1], celldata.shape[2]

            assert Nx == self.grid[0].size
            assert Ny == self.grid[1].size
            assert Nz == self.grid[2].size
            x = np.linspace(self.grid[0][0]-0.5*dx, self.grid[0][-1]+0.5*dx, Nx+1)
            y = np.linspace(self.grid[1][0]-0.5*dy, self.grid[1][-1]+0.5*dy, Ny+1)
            z = np.linspace(self.grid[2][0]-0.5*dz, self.grid[2][-1]+0.5*dz, Nz+1)

            vertexdata = self.interp_3Darrays(fn, x, y, z)
        else:
            raise exception("Unknown method")


        return vertexdata

    def cellcentre2surface(self, celldata, method="interp"):

        if method is "interp":

            surfacedata = np.zeros((celldata.shape[0], 
                                    celldata.shape[1], 
                                    celldata.shape[2],6))

            #Get grid of centre abd surface values
            Nx, Ny, Nz = celldata.shape[0], celldata.shape[1], celldata.shape[2]
            assert Nx == self.grid[0].size
            assert Ny == self.grid[1].size
            assert Nz == self.grid[2].size
            xg = self.grid[0]
            yg = self.grid[1]
            zg = self.grid[2]
            dx = xg[1]-xg[0]
            dy = yg[1]-yg[0]
            dz = zg[1]-zg[0]
            xs = np.linspace(self.grid[0][0]-0.5*dx, self.grid[0][-1]+0.5*dx, Nx+1)
            ys = np.linspace(self.grid[1][0]-0.5*dy, self.grid[1][-1]+0.5*dy, Ny+1)
            zs = np.linspace(self.grid[2][0]-0.5*dz, self.grid[2][-1]+0.5*dz, Nz+1)

            #Get interpolator
            fn = self.field_interpolator(celldata)

            # x surfaces   xs, y, z
            data = self.interp_3Darrays(fn, xs, yg, zg)
            surfacedata[:,:,:,0] = data[:-1,:,:] #Bottom
            surfacedata[:,:,:,3] = data[1:,:,:]  #Top


            # y surfaces   x, ys, z
            data = self.interp_3Darrays(fn, xg, ys, zg)
            surfacedata[:,:,:,1] = data[:,:-1,:] #Bottom
            surfacedata[:,:,:,4] = data[:,1:,:]  #Top

            # z surfaces   x, y, zs
            data = self.interp_3Darrays(fn, xg, yg, zs)
            surfacedata[:,:,:,2] = data[:,:,:-1] #Bottom
            surfacedata[:,:,:,5] = data[:,:,1:]  #Top

        else:
            raise exception("Unknown method")

        return surfacedata

        # Innards
#        for i in range(1,Nx):
#            for j in range(1,Ny):
#                for k in range(1,Nz):
#                    vertexdata[i,j,k] = np.mean(celldata[i-1:i+2,j-1:j+2,k-1:k+2])



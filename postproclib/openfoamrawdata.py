#! /usr/bin/env python
import numpy as np
import os
import sys

from .rawdata import RawData
from .headerdata import openfoam_HeaderData
from .pplexceptions import DataNotAvailable, OutsideRecRange

from .OF_field_parser import parse_internal_field
from .OF_mesh_parser import FoamMesh


class OpenFOAM_RawData(RawData):
    
    def __init__(self, fdir, fname, nperbin, parallel_run=None):

        if (fdir[-1] != '/'): fdir += '/'
        self.fdir = fdir
        #Define a mesh object using OFpp library
        #which can handle binary formats
        self.MeshObj = FoamMesh(fdir)
        self.parallel_run = parallel_run
        if parallel_run==None:
            self.procxyz = self.get_proc_topology()
            self.procs = int(np.product(self.procxyz))
            if self.procs != 1:
                self.parallel_run = True
            else:
                self.parallel_run = False
        elif parallel_run:
            self.parallel_run = parallel_run
            self.procxyz = self.get_proc_topology()
            self.procs = int(np.product(self.procxyz))
        elif not parallel_run:
            self.parallel_run = parallel_run
            self.procxyz = np.ones(3)
            self.procs = 1
        else:
            raise TypeError("parallel_run must be a True, False or None") 

        self.grid = self.get_grid()
        self.reclist = self.get_reclist()
        self.maxrec = len(self.reclist) - 1 # count from 0
        self.fname = fname
        self.npercell = nperbin #self.get_npercell()
        #Mock header data needed for vmdfields
        self.header = openfoam_HeaderData(fdir)
        self.delta_t = self.header.headerDict['controlDict']["deltaT"]
        #If viscosity found by normal process, use this, otherwise look in constants
        try:
            self.nu = self.header.headerDict['transportProperties']["nu"]  
        except KeyError:
            self.nu = self.get_nu()
 
        tplot = 1
        skip = 1
        initialstep = 0
        #This variables have no meaning in a pure CFD calculation
        #so would need to be set by a coupled run. Horrible
        #hack included here to do this is cpl file present...
        try: 
            with open('./cpl/COUPLER.in') as f:
                fs = f.read()
                indx = fs.find("TIMESTEP_RATIO")
                self.Nave = int(fs[indx:].split("\n")[1])
        except IOError:
            self.Nave = 1
        self.header.vmd_skip = str(skip)
        self.header.vmd_start = str(initialstep)
        vmdmaxrec = self.maxrec*tplot*skip*self.Nave
        self.header.vmd_end = str(vmdmaxrec)
        self.header.Nsteps = str(vmdmaxrec)

        #The rest makes sense
        self.header.tplot = str(tplot)
        self.header.delta_t = str(self.delta_t)
        self.header.initialstep = str(initialstep)


    def get_npercell(self):
     
        # Read first record (reclist[0]) as example 
        if self.parallel_run:
            fpath = self.fdir+"/processor0/"+self.reclist[0]+self.fname
        else:
            fpath = self.fdir+self.reclist[0]+self.fname 
        #E.S. THIS DOES NOT WORK FOR PRESSURE (OR ANYTHING WITH 1 PER CELL)
        #(ALSO WHY DO WE NEED THIS?)
        with open(fpath, 'r') as f:
            while True:
                line = f.readline()
                if ('(' in line and ')' in line):
                    break
            npercell = len(line.split())

        return npercell
            

    def reshape_list_to_grid(self, inputlist, nperpoint):
        # Lists from OpenFOAM seem to be written in Fortran order, for some
        # reason
        array = np.reshape(
                           inputlist, 
                           (self.ngx, self.ngy, self.ngz, nperpoint), 
                           order='F'
                          ) 
        return array

    def reshape_list_to_cells(self, inputlist, npercell, glob=False):
        # Lists from OpenFOAM seem to be written in Fortran order, for some
        # reason
        if glob:
            x = int(self.ncx)
            y = int(self.ncy)
            z = int(self.ncz)
        else:
            x = int(self.ncx/float(self.procxyz[0]))
            y = int(self.ncy/float(self.procxyz[1]))
            z = int(self.ncz/float(self.procxyz[2]))

        array = np.reshape(inputlist, (x, y, z,npercell), order='F') 
        return array

#    def read_list(self, fobj):

#        flist = []
#        for line in fobj:
#            if line[0] == '(' and ')' in line:
#                values = line.split('(')[-1].split(')')[0].split()
#                flist.append([float(i) for i in values])
#        return flist

#    def read_list_named_entry(self, fobj, entryname):

#        def read_list_from_here(fobj):

#            nitems = int(fobj.next())
#            checkopenbracket = fobj.next()
#            if (checkopenbracket[0] != '('):
#                raise 

#            herelist = []
#            for lineno in range(nitems):
#                line = fobj.next()
#                if line[0] == '(' and ')' in line:
#                    values = line.split('(')[-1].split(')')[0].split()
#                    herelist.append([float(i) for i in values])
#                else:
#                    herelist.append(float(line))

#            checkclosebracket = fobj.next()
#            if (checkclosebracket[0] != ')'):
#                raise
#    
#            return herelist
#            
#        # Find entryname
#        for line in fobj:
#            if (entryname in line):
#                if "nonuniform List" in line:
#                    flist = read_list_from_here(fobj)
#                    return flist
#                elif " uniform 0" in line:
#                    flist = [0]
#                    return flist
#                else:
#                    # Else check for fixed values or skip next
#                    # 4 lines until start of list<vector>
#                    for count in range(5):
#                        nline = fobj.next()

#                        if " uniform" in nline:
#                            flist = nline.split("(")[1].split(")")[0].split(" ") 
#                            #print(entryname, " is fixed value in file", flist)
#                            return flist
#    
#                        elif "nonuniform List" in nline:
#                            flist = read_list_from_here(fobj)
#                            return flist

#        return []


    #These are a re-write of the above reading the whole file to
    #memory instead of using next
    def read_list(self, fobj):

        fobj_list = fobj.read().splitlines()
        flist = []
        for line in fobj_list:
            try:
                if (line[0] == '(') and (')' in line):
                    values = line.split('(')[-1].split(')')[0].split()
                    flist.append([float(i) for i in values])
            except IndexError:
                pass

        return flist

    def read_list_from_here(self, fobj_list, kwl):

        nitems = int(fobj_list[kwl+1])
        checkopenbracket = fobj_list[kwl+2]
        if (checkopenbracket[0] != '('):
            raise 

        herelist = []
        for lineno in range(nitems):
            line = fobj_list[kwl+3+lineno]
            try:
                if (line[0] == '(') and (')' in line):
                    values = line.split('(')[-1].split(')')[0].split()
                    herelist.append([float(i) for i in values])
                else:
                    herelist.append(float(line))
            except IndexError:
                pass

        checkclosebracket = fobj_list[kwl+4+lineno]
        if (checkclosebracket[0] != ')'):
            raise

        return herelist

    def read_list_on_line(self, line, entryname):
        indx = line.find("(")
        #Check for vectors
        if line[indx+1:].find("(") != -1:
            flist = []
            for term in line[indx+1:].split('('):
                vec = term.replace("(","").replace(")","").replace(";","").split()
                if vec == []:
                    continue
                flist.append([float(v) for v in vec])
            return flist
        #Otherwise a list of scalars on this line
        else:
            flist = line[indx:].replace("(","").replace(")","").replace(";","").split()
            return [float(i) for i in flist]

    def read_list_named_entry(self, fobj, entryname):

        fobj_list = fobj.read().splitlines()
        # Find entryname
        for i, line in enumerate(fobj_list):
            if (entryname in line):
                if "nonuniform List" in line:
                    if (("(" in line) and (")" in line)):
                        flist = self.read_list_on_line(line, entryname)
                    else:
                        flist = self.read_list_from_here(fobj_list, i)
                    return flist
                elif " uniform 0" in line:
                    flist = [0]
                    return flist
                else:
                    # Else check for fixed values or skip next
                    # 4 lines until start of list<vector>
                    for count in range(5):
                        nline = fobj_list[i+1+count]

                        if " uniform" in nline:
                            flist = nline.split("(")[1].split(")")[0].split(" ") 
                            #print(entryname, " is fixed value in file", flist)
                            return flist
    
                        elif "nonuniform List" in nline:
                            flist = self.read_list_from_here(fobj_list, i+count+1)
                            return flist

        return []


    def read_cells(self, fobj, ncells):

        def read_list(fobj, nitems, line):

            #Check not all on same line
            if nitems < 20:
                if (("(" in line) and (")" in line)):
                    print(line)
                    flist = self.read_list_on_line(line, entryname)
                    print(flist)
                return flist

            checkopenbracket = next(fobj)
            if (checkopenbracket[0] != '('):
                raise

            herelist = []
            for lineno in range(nitems):
                line = next(fobj)
                herelist.append(float(line))

            checkclosebracket = next(fobj)
            if (checkclosebracket[0] != ')'):
                raise
    
            return herelist

        found = False
        entryname = str(ncells)
        for line in fobj:
            if (entryname in line):
                flist = read_list(fobj, ncells, line)
                found = True

        #If entryname is not found in file, data is not available
        if (not found):
            print(("Entry for number of cells ", entryname, " not consistent with file ", fobj.name ))
            raise IOError

        return flist


    def get_proc_topology(self):

        """
            OpenFOAM processor topology
        """

        # Try to get grid shape (linear)
        try:
            fobj = open(self.fdir+'/system/decomposeParDict','r')
        except IOError:
            return np.ones(3)

        alltxt = fobj.readlines()
        for n,line in enumerate(alltxt):
            if line[0:12] == 'simpleCoeffs':
                procentry = alltxt[n+2]
                procstr = (procentry.split('(')[1]
                           .replace(')','')
                           .replace(';','')
                           .split())
                break

        #Convert to int array
        procsxyz = np.empty(3)
        for i in range(len(procstr)):
            procsxyz[i]= procstr[i]

        return procsxyz

    def get_grid(self):

        """
            OpenFOAM writes data at cell centers
        """

        # Try to get grid shape (linear)
        try:
            fobj = open(self.fdir+'constant/polyMesh/blockMeshDict','r')
        except IOError:
            try: 
                fobj = open(self.fdir+'system/blockMeshDict','r')
            except IOError:
                raise DataNotAvailable

        while True:
            line = fobj.readline()
            if line[0:6] == 'blocks':
                fobj.readline()
                hexentry = fobj.readline()
                nxyz = hexentry.split('(')[2].split(')')[0].split()
                break


        # Number of grid points is 1 more than number of cells
        #self.ngx = int(int(nxyz[0])/float(self.procxyz[0])) + 1
        self.ngx = int(nxyz[0]) + 1 
        self.ngy = int(nxyz[1]) + 1
        self.ngz = int(nxyz[2]) + 1
        # Number of cells of openfoam output 
        self.ncx = self.ngx - 1
        self.ncy = self.ngy - 1
        self.ncz = self.ngz - 1

        # Read list of points and reshape to assumed linear grid
        try:
            fobj = open(self.fdir+'constant/polyMesh/points','r')
        except IOError:
            raise DataNotAvailable

        # Read openfoam list of points
        try:
            pointslist = self.read_list(fobj)
        except UnicodeDecodeError:
            pointslist = self.MeshObj.points #Pointlist supports binary

        # Reshape to structured grid, 3 values (x,y,z pos) for each point 
        points = self.reshape_list_to_grid(np.array(pointslist), 3)

        # Extract useful quantities from structured grid
        dummy = 0; x = 0; y = 1; z = 2 
        self.dx = points[1,dummy,dummy,x] - points[0,dummy,dummy,x]
        self.dy = points[dummy,1,dummy,y] - points[dummy,0,dummy,y]
        self.dz = points[dummy,dummy,1,z] - points[dummy,dummy,0,z]
        self.xL = points[-1,dummy,dummy,x] - points[0,dummy,dummy,x]
        self.yL = points[dummy,-1,dummy,y] - points[dummy,0,dummy,y]
        self.zL = points[dummy,dummy,-1,z] - points[dummy,dummy,0,z]

        #Get size of grid on each processor
        if self.parallel_run:
            self.minx = np.empty(self.procs)
            self.maxx = np.empty(self.procs)
            self.miny = np.empty(self.procs)
            self.maxy = np.empty(self.procs)
            self.minz = np.empty(self.procs)
            self.maxz = np.empty(self.procs)
            self.cellmap = []
            for proc in range(self.procs):
                fdir = self.fdir+"processor" + str(proc) + "/"
                fpath = fdir + "/constant/polyMesh/cellProcAddressing"

                #cellProcAddressing = parse_internal_field(fpath)
                with open(fpath,'r') as fobj:
                    nperprocx = int(self.ncx/float(self.procxyz[0]))
                    nperprocy = int(self.ncy/float(self.procxyz[1]))
                    nperprocz = int(self.ncz/float(self.procxyz[2]))

                    celllist = self.read_cells(fobj, nperprocx*nperprocy*nperprocz)
                    #Mapping from local to global cells
                    self.cellmap.append(celllist)

                    #Keep min/max process method to get halos
                    ctemp = self.reshape_list_to_cells(celllist, 1)

                # This will only work for proc decompositions in x
                # I have no idea how OpenFOAM maps 3D processor
                # layouts to processor folder naming in general
                # Here we use current processor topology 
                # THIS DOES NOT WORK WITH VARIABLE Z PROCESSORS!!!!!!!!!!!
                self.minx[proc] = ctemp[0,0,0,0]    #Minimum index in domain
                self.maxx[proc] = np.max(ctemp[:,0,0,0])+1  # Maximum index in x
                # Minimum index in y, minus minx and in blocks of x dimension
                self.miny[proc] = np.min(ctemp[0,:,0,0]-self.minx[proc])/ctemp.shape[0] 
                self.maxy[proc] = np.max(ctemp[0,:,0,0]-self.minx[proc])/ctemp.shape[0]+1
                # Minimum index in z, minus minx and in blocks of x*y dimension
                self.minz[proc] = np.min(ctemp[0,0,:,0]-self.minx[proc])/(ctemp.shape[0]*ctemp.shape[1]) 
                self.maxz[proc] = np.max(ctemp[0,0,:,0]-self.minx[proc])/(ctemp.shape[0]*ctemp.shape[1])+1
                # THIS DOES NOT WORK WITH VARIABLE Z PROCESSORS!!!!!!!!!!!

                #print(proc, self.minx[proc],self.maxx[proc],self.miny[proc],
                #            self.maxy[proc],self.minz[proc],self.maxz[proc],
                #            nperprocx,nperprocy,nperprocz,ctemp.shape)

        # Return list of cell-centre locations in each direction
        gridx = np.linspace(self.dx/2., self.xL - self.dx/2., num=self.ncx)
        gridy = np.linspace(self.dy/2., self.yL - self.dy/2., num=self.ncy)
        gridz = np.linspace(self.dz/2., self.zL - self.dz/2., num=self.ncz)
        
        grid = [gridx,gridy,gridz]

        return grid 

    def get_reclist(self, skip_inital=False):

        #Read only one of the processor outputs assuming same in each
        if self.parallel_run:
            fdir = self.fdir+"/processor0/"
        else:
            fdir = self.fdir

        records = []
        for filename in os.listdir(fdir):
            try:
                rectime = float(filename)
                records.append(filename)
            except ValueError:
                pass

        #If only initial field data found, raise error
        if (records == []):# or records == ['0']):
            raise DataNotAvailable
       
        def get_float(name):
            return float(name)
        records = sorted(records, key=get_float)
        # Ignore initial field stored in folder "0" 
        if skip_inital:
            return [rectime+'/' for rectime in records[1:]]
        else:
            return [rectime+'/' for rectime in records[:]]

    def read(self, startrec, endrec, binlimits=None, verbose=False, **kwargs):

        nrecs = endrec - startrec + 1

        # Allocate storage (despite ascii read!)
        odata = np.zeros((self.ncx,self.ncy,self.ncz,nrecs,self.npercell))

        # Loop through files and insert data
        for plusrec in range(0,nrecs):

            if self.parallel_run:
                olist = np.zeros([self.ncx*self.ncy*self.ncz,self.npercell])
                for proc in range(self.procs):
                    fdir = self.fdir+"processor" + str(proc) + "/"
                    fpath = fdir + self.reclist[startrec+plusrec] + self.fname

                    try:
#                        #Switch to OpenFOAM pp which handles binary
#                        vtemp = parse_internal_field(fpath)

#                        if (vtemp.shape[0] == 1):
#                            odata[:,:,:,plusrec,:] = vtemp[0,:]
#                        else:
#                            # Loop through cellProcAddress mapping and assign
#                            # values to global cells
#                            for i in range(len(vlist)):
#                                olist[int(self.cellmap[proc][i]),:] = vtemp.ravel()[i]
#                            odata[:,:,:,plusrec,:] = self.reshape_list_to_cells(olist.T.ravel(), self.npercell, glob=True)

                        with open(fpath,'r') as fobj:
                            try:
                                vlist = self.read_list_named_entry(fobj, 'internalField')
                            except UnicodeDecodeError:
                                print("OpenFOAM Binary data cannot be read in parallel, " +
                                      "use reconstructPar, delete processor* folders " +
                                      "and run pyDataView again.")
                                sys.exit(1)
                            #Case when field is constant has a single value
                            if len(vlist) is self.npercell:
                                for dim in range(self.npercell):
                                    odata[:,:,:,plusrec,dim] = float(vlist[dim])
                            else:
                                # Loop through cellProcAddress mapping and assign
                                # values to global cells
                                for i in range(len(vlist)):
                                    olist[int(self.cellmap[proc][i]),:] = vlist[i]

                                #Reshape global list to cells
                                vtemp = self.reshape_list_to_cells(olist.T.ravel(), self.npercell, glob=True)
                                odata[:,:,:,plusrec,:] = vtemp

                    except IOError:
                        raise
#                        if use_pyfoam:
#                            # Commented this out as it's slower than custom routines...
#                            try:
#                                from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
#                                with ParsedParameterFile(fpath) as f:
#                                    odata[:,:,:,plusrec,:] = np.array(f['internalField']).reshape([self.ncx, self.ncy, self.ncz, self.npercell])
#                            except ImportError:
#                                print("Failed to load PyFoam, falling back on PyDataView reader")

#                        else:
#                            raise
    
                    #Try a quick read based on assumed data format, otherwise switch 
#                    try:
#                        data = np.genfromtxt(fpath, skip_footer=self.ncx*self.ncz+36, skip_header=22) #64 by 64 footer of 4134
#                        print(data.shape, self.ncx,self.ncy,self.ncz,nrecs,self.npercell)
#                        vtemp = data.reshape(self.ncx,self.ncy,self.ncz,self.npercell)
#                        odata[:,:,:,plusrec,:] = vtemp

#                    except:
#                        print("Quick read failed")
#                        raise


            else:
                fpath = self.fdir + self.reclist[startrec+plusrec] + self.fname

                #Switch to OpenFOAM pp which handles binary
                vtemp = parse_internal_field(fpath)
                if (type(vtemp) == np.ndarray):
                    if (vtemp.shape[0] == 1):
                        odata[:,:,:,plusrec,:] = vtemp[0,:]
                    elif vtemp.shape[0] == 0:
                        odata[:,:,:,plusrec,:] = 0.
                    else:
                        odata[:,:,:,plusrec,:] = self.reshape_list_to_cells(vtemp, self.npercell)
                elif (type(vtemp) == float):
                    odata[:,:,:,plusrec,:] = vtemp
#                with open(fpath,'r') as fobj:
#                    vlist = self.read_list_named_entry(fobj, 'internalField')
#    
#                    #Case when field is constant has a single value
#                    if len(vlist) is self.npercell:
#                        for dim in range(self.npercell):
#                            odata[:,:,:,plusrec,dim] = float(vlist[dim])
#                    elif len(vlist) == 0:
#                        odata[:,:,:,plusrec,:] = 0.
#                    else:
#                        vtemp = self.reshape_list_to_cells(vlist, self.npercell)
#                        odata[:,:,:,plusrec,:] = vtemp 
                
        # If bin limits are specified, return only those within range
        if (binlimits):

            if (verbose):
                print(('odata.shape = {0:s}'.format(str(odata.shape))))
                print(('Extracting bins {0:s}'.format(str(binlimits))))

            # Defaults
            lower = [0]*3
            upper = [i for i in odata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            odata = odata[lower[0]:upper[0],
                          lower[1]:upper[1],
                          lower[2]:upper[2], :, :]
         
        return odata

    def read_halo(self, startrec, endrec, haloname, **kwargs):


        """
            Warning -- there is no processor to cell 
            mapping for halo cells so these are obtained
            by assuming fixed domain size
        """

        nrecs = endrec - startrec + 1

        # Allocate storage (despite ascii read!)
        odata = np.empty((self.ncx,1,self.ncz,nrecs,self.npercell))

        # Loop through files and insert data
        for plusrec in range(0,nrecs):

            if self.parallel_run:
                for proc in range(self.procs):
                    fdir = self.fdir+"processor" + str(proc) + "/"
                    fpath = fdir + self.reclist[startrec+plusrec] + self.fname

                    with open(fpath,'r') as fobj:
                        #Skip to line with cplrecvMD
                        vlist = self.read_list_named_entry(fobj, haloname)
                        if len(vlist) is self.npercell:
                            for dim in range(self.npercell):
                                odata[:,:,:,plusrec,dim] = float(vlist[dim])
                        elif len(vlist) == 0:
                            odata[:,:,:,plusrec,:] = 0.
                        else:
                            npx = int(self.procxyz[0])
                            npz = int(self.procxyz[2])
                            nx = int(self.ncx/float(npx))
                            nz = int(self.ncz/float(npz))
                            vtemp = np.reshape(vlist, (nx, 1, nz, self.npercell), order='F')

                            #Assume it must be slip as function of x and z only
#                            minx = proc%npx*nx
#                            maxx = (proc%npx+1)*nx
#                            minz = np.floor(proc/npx)*nz
#                            maxz = np.floor(proc/npx+1)*nz

                            minz = int(np.floor(proc/npx)*nz)
                            maxz = int(np.floor(proc/npx+1)*nz)
                            minx = int(proc%npx*nx)
                            maxx = int((proc%npx+1)*nx)

                            #Use processor extents to slot into array
                            odata[minx:maxx, 0:1, minz:maxz, plusrec, :] = vtemp

            else:
                fpath = self.fdir + self.reclist[startrec+plusrec] + self.fname
                with open(fpath,'r') as fobj:
                    vlist = self.read_list_named_entry(fobj, 'internalField')
                    if len(vlist) is self.npercell:
                        for dim in range(self.npercell):
                            odata[:,:,:,plusrec,dim] = float(vlist[dim])
                    elif len(vlist) == 0:
                        odata[:,:,:,plusrec,:] = 0.
                    else:
                        vtemp = self.reshape_list_to_cells(vlist, self.npercell)
                        odata[:,0:1,:,plusrec,:] = vtemp

            return odata

    def get_nu(self):

        # Read constant transport properties file 
        fpath = self.fdir+'constant/transportProperties'
        with open(fpath, 'r') as f:
            while True:
                line = f.readline()
                if (line[0:2] == 'nu'):
                    break
            nu = float(line.split(']')[-1].split(';')[0]) 
        
        return nu


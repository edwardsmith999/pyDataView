
import numpy as np
import os
import struct
import glob

from scipy.io import FortranFile

from .headerdata import *
from .postproc import PostProc
from .pplexceptions import NoResultsInDir

class DummyReader:

    def __init__(self, fname="./dummy"):
        self.fname = fname
        self.maxrec = 0

    def read_pos(self, start, end):
        steps = end-start+1
        return np.zeros([1, 3, steps])


class VMDReader:

    def __init__(self, fdir, fname="newest"):

        self.fdir = fdir
        self.n = self.read_header()
        #Either take whichever file has been created most recently
        if fname is "newest":
            self.fname = self.check_files()
        elif "vmd_temp" in fname:
            self.fname = self.check_files(ftmp="vmd_temp.dcd", fout="IGNOREFILE")
        elif "vmd_out" in fname:
            self.fname = self.check_files(fout="vmd_out.dcd", ftmp="IGNOREFILE")
        else:
            raise IOError("fname", fname, " is not recognised in VMDReader") 

    def read_header(self, headername="/simulation_header"):

        #Load number of molecules data
        fname = self.fdir + headername
        with open(fname,"r") as f:
            for l in f:
                if "globalnp" in l:
                    n = int(l.split(";")[2])
                    break

        return n

    def check_files(self, dsize=4, ftmp="vmd_temp.dcd", fout="vmd_out.dcd"):

        #Check which MD files are available
        ftmp = self.fdir + "/" + ftmp#"/vmd_temp.dcd"
        fout = self.fdir + "/" + fout#"/vmd_out.dcd"
        #If both, check if temp is newer
        self.use_temp=False

        print(ftmp, fout, os.path.exists(ftmp), os.path.exists(fout))
        if (os.path.exists(ftmp) and os.path.exists(fout)):
            if (os.path.getmtime(ftmp) > os.path.getmtime(fout)):
                self.use_temp=True
        elif (os.path.exists(ftmp)):
            self.use_temp=True

        #Get size of file
        if (self.use_temp):
            fname = ftmp
        elif (os.path.exists(fout)):
            fname = fout
        else:
            self.data_found = False
            self.maxrec = 0
            return None

        self.data_found = True
        filesize = os.path.getsize(fname)
        self.maxrec = int(np.floor(filesize/(3.*self.n*dsize)))-1

        return fname

    def read_pos(self, start, end):

        if start != 0:
            print("WARNING - NON ZERO START IN READ POS NOT FULLY TESTED")

        steps = end-start+1
        if (self.data_found):
            pos = np.zeros([self.n, 3, steps])
        else:
            print("NO DATA FOUND")
            return np.zeros([self.n,3, 1])

        #Tries to load record rec from vmd_temp.dcd or vmd_out.dcd
        #Numpy fromfile does not work on final dcd as insists on using Fortran 
        #unformatted which is an archaic binary format incompatible
        #with stream, etc. Need to keep like this so VMD still works
        #Load data
        read_success = False
        if (self.use_temp):
            offset = 3 * start * self.n
            print("Loading MD data from " + self.fname, " at offset ", offset)
            data = np.fromfile(self.fname, dtype=np.single, offset=offset)

            cntrec = 0
            for rec in range(start, end+1):
                si = 3*self.n*(rec-start)
                ei = 3*self.n*(rec-start+1)
                print("Loading record ", rec)
                for ixyz in range(3):
                    pos[:,ixyz,cntrec] = data[si+self.n*ixyz:si+self.n*(ixyz+1)]
                cntrec += 1
            read_success = True

        elif (os.path.exists(self.fname)):
            print("Loading MD data from " + self.fname)
            with FortranFile(self.fname, 'r') as f:
                h1 = f.read_record('i4')
                h2 = f.read_record('i4')
                Nb = f.read_record('i4')
                if (Nb[0] != self.n):
                    raise IOError(self.fname + " is not in expected format")

                #No Seek offered so read and discard up to start
#                    if (start != 0):
#                        for rec in range(start):
#                            pos[:,0,0] = f.read_record('f4')
#                            pos[:,1,0] = f.read_record('f4')
#                            pos[:,2,0] = f.read_record('f4')

                #Then read data
                cntrec = 0; datacorrupt = False
                for rec in range(start, end+1):
                    for ixyz in range(3):
                        #Corrupted data beyond a point causes TypeError
                        #so best to exit
                        try:
                            data = f.read_record('f4')
                            #Check n to handle case where 
                            #extra record between timesteps
                            if data.size == self.n:
                                pos[:,ixyz,cntrec] = data
                            else:
                                print(rec, "Extra record of size = ", data.size, " with N mols = ", self.n)
                                pos[:,ixyz,cntrec] = f.read_record('f4')
                        except TypeError as e:
                            print("Corruped data at record=", rec, " in " 
                                  + self.fname, " Error is ", e)
                            datacorrupt = True
                    if datacorrupt:
                        break
                    cntrec += 1

            read_success = True

        if (not read_success):
            raise IOError("Failed to read data from" + self.fname)

        return pos



    def read_moltype(self, fname="vmd_out.psf"):
                   
        #Load tag data (assumes same ordering)
        #tagDict = {"free": 0, "fixed": 1, "fixed_slide": 2, "teth": 3, "thermo": 4, 
        #            "teth_thermo": 5, "teth_slide": 6, "teth_thermo_slide": 7}     

        fpsf = self.fdir + "/" +  fname
        if (os.path.exists(fpsf)):
            with open(fpsf) as f:
                rd = True
                moltype = []
                for l in f:
                    if (rd and "!NATOM" in l):
                        N = int(l.replace("!NATOM",""))
                        rd = False
                        continue
                    elif (rd):
                        continue
                    if "!NBOND" in l:
                        continue
                    try:
                        molno = int(l.split()[0])-1
                    except ValueError:
                        molno = int(l.split()[0].replace("\x00",""))-1
                        #raise
                    except IndexError:
                        print("Line not molecules in ", fname, " skipping")
                        continue    
      
                    moltype.append(l.split()[1])

            return moltype
        else:
            return None

class final_state:

    def __init__(self, fname= "./final_state", tether_tags = [3,5,6,7,10], verbose=False):
        self.fname = fname
        self.tether_tags = tether_tags
        self.maxrec = 0 #Final state file is a single record

        #Get filesize and read headersize
        self.size = os.path.getsize(fname)
        self.headersize = np.fromfile(fname, dtype=np.int64, offset=self.size-8)
        with open(fname, "rb") as f:
            f.seek(self.headersize[0])
            self.binaryheader = f.read()

        self.read_header(verbose=verbose)

    def read_header(self, verbose=False):

        #Assume 14 doubles and work out integers
        self.ndbls = 14; self.ntrlint=4
        self.noints = int((len(self.binaryheader) - self.ndbls*8)/4)-self.ntrlint
        self.fmtstr = str(self.noints) + "i"+str(self.ndbls) +"d"+ str(self.ntrlint) + "i"
        self.hdata = list(struct.unpack(self.fmtstr, self.binaryheader))
        self.htypes = ["globalnp", "initialunits1", 
                      "initialunits2", "initialunits3", 
                      "Nsteps", "tplot", "seed1", "seed2",
                      "periodic1", "periodic2", "periodic3",
                      "potential_flag","rtrue_flag","solvent_flag",
                      "nmonomers","npx","npy","npz"]

        nproc = int(self.hdata[15])*int(self.hdata[16])*int(self.hdata[17])
        self.nproc = nproc
        [self.htypes.append("procnp"+str(p)) for p in range(nproc)]
        [self.htypes.append("proctethernp"+str(p)) for p in range(nproc)]
        [self.htypes.append(i) for i in 
                        ["globaldomain1", "globaldomain2",
                        "globaldomain3", "density", "rcutoff",
                        "delta_t", "elapsedtime", "simtime", 
                        "k_c","R_0", "eps_pp", "eps_ps", 
                        "eps_ss", "delta_rneighbr",
                        "mie_potential","global_numbering",
                        "headerstart","fileend"]]

        self.headerDict = {}
        for i in range(len(self.hdata)):
            if verbose:
                print(i, self.htypes[i], self.hdata[i])
            self.headerDict[self.htypes[i]]=self.hdata[i]

        if verbose:
            for k, i in self.headerDict.items():
                print(k,i)

    def read_moldata(self):

        #Read the rest of the data
        data = np.fromfile(self.fname, dtype=np.double, count=int(self.headersize/8))

        #Allocate arrays
        h = self.headerDict
        returnDict = {}
        N = h["globalnp"]#self.N
        self.n = N
        self.tag = np.zeros(N)
        self.r = np.zeros([N,3])
        self.v = np.zeros([N,3])
        self.rtether = np.zeros([N,3])
        self.Ntethered = 0

        returnDict["tag"] = self.tag
        returnDict["r"] = self.r
        returnDict["v"] = self.v
        returnDict["rtether"] = self.rtether

        #Create arrays for molecular removal
        self.Nnew = N
        self.delmol = np.zeros(N)
        self.molecules_deleted=False

        if (h["rtrue_flag"]):
            self.rtrue = np.zeros([N,3])
            returnDict["rtrue"] = self.rtrue
        if (h["mie_potential"]):
            self.moltype = np.zeros(N)
            returnDict["moltype"] = self.moltype
        if (h["global_numbering"]):
            self.globnum = np.zeros(N)
            returnDict["globnum"] = self.globnum
        if (h["potential_flag"]):
            self.potdata = np.zeros([N,8])
            returnDict["potdata"] = self.potdata

        i = 0
        for n in range(N):
            self.tag[n] = data[i]; i += 1
            self.r[n,:] = data[i:i+3]; i += 3
            self.v[n,:] = data[i:i+3]; i += 3

            if (h["rtrue_flag"]):
                self.rtrue[n,:] = data[i:i+3]; i += 3
            if (self.tag[n] in self.tether_tags):
                self.rtether[n,:] = data[i:i+3]; i += 3
                self.Ntethered += 1
            if (h["mie_potential"]):
                self.moltype[n] = data[i]; i += 1
            if (h["global_numbering"]):
                self.globnum[n] = data[i]; i += 1
            if (h["potential_flag"]):
                self.potdata[n,:] = data[i:i+8]; i += 8
        
        return returnDict


    def read_pos(self, start, end):

        returnDict = self.read_moldata()
        r = returnDict["r"]
        pos = np.zeros([r.shape[0],r.shape[1],1])
        pos[:,:,0] = r
        return pos

    def plot_molecules(self, ax=None):

        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(projection='3d')
        ax.scatter(self.r[:,0], self.r[:,1], self.r[:,2], c=self.tag[:])

    def remove_molecules(self, rpos, radius, rdim=0):

        h = self.headerDict
        N = h["globalnp"]

        rmapped = np.zeros(3)
        for n in range(N):
            rmapped[:] = self.r[n,:] - rpos[:]
            #Set zero along direction
            if (rdim != 3):
                rmapped[rdim] = 0.
            #Spherical or cylindrical radius
            rspherical2 = np.dot(rmapped,rmapped)    #Get position in spherical coordinates
            rspherical = np.sqrt(rspherical2)
            #theta = np.acos(rmapped[2]/rspherical)
            #phi = np.atan(rmapped[1]/rmapped[0])
            if (rspherical < radius and self.delmol[n] != 1):
                print(n, self.Nnew, rspherical, radius)
                self.delmol[n] = 1           
                self.Nnew -= 1                   
                self.molecules_deleted = True

    def write_moldata(self, outfile=None, verbose=False):

        #Default to same filename with a 2
        if (outfile is None):
            outfile = self.fname + "2"

        h = self.headerDict
        N = h["globalnp"]

        #Values are the number of values per molecule including all 
        vals = (7 + 3*h["rtrue_flag"] + h["mie_potential"]
                + h["global_numbering"] + 8*h["potential_flag"])
        data = np.zeros(N*vals+ 3*self.Ntethered)

        #Start a new global numbering if any molecules have been deleted
        if (self.molecules_deleted):
            newglob = 1

        #Loop and write all data
        i = 0
        for n in range(N):

            if self.delmol[n] == 1:
                continue

            data[i] = self.tag[n]; i += 1
            data[i:i+3] = self.r[n,:]; i += 3
            data[i:i+3] = self.v[n,:]; i += 3
            #print(n, i, data[i-7:i])

            if (h["rtrue_flag"]):
                data[i:i+3] = self.rtrue[n,:]; i += 3
            if (tag[n] in self.tether_tags):
                data[i:i+3] = self.rtether[n,:]; i += 3
            if (h["mie_potential"]):
                data[i] = self.moltype[n]; i += 1
            if (h["global_numbering"]):
                if (self.molecules_deleted):
                    data[i] = newglob; newglob += 1; i += 1
                else:
                    data[i] = self.globnum[n]; i += 1
            if (h["potential_flag"]):
                data[i:i+8] = self.potdata[n,:]; i += 8

        #Write data to file
        data.tofile(open(outfile, "w+"))

        #If number of molecules has changed, reset to 1x1x1 processors
        if (self.Nnew != h["globalnp"]):
            print("N=", N, "Nnew=", self.Nnew)
            h["globalnp"] = self.Nnew
            h["npx"] = 1; h["npy"] = 1; h["npz"] = 1
            h["procnp0"] = self.Nnew
            proctethernp = 0
            for p in range(self.nproc):
                proctethernp += h["proctethernp"+str(p)]
            h["proctethernp0"] = proctethernp
            delindx = []

        #Update hdata
        for i in range(len(self.hdata)):
            if (verbose or self.hdata[i] != self.headerDict[self.htypes[i]]):
                    print("UPDATE", i, self.htypes[i], "before=", self.hdata[i], 
                          "after=", self.headerDict[self.htypes[i]])
            self.hdata[i] = self.headerDict[self.htypes[i]]
            if self.molecules_deleted:
                if (   ("procnp" in self.htypes[i] and self.htypes[i] != "procnp0")
                    or ("proctethernp" in self.htypes[i] and self.htypes[i] != "proctethernp0")):
                    print("Flagged for Delete", i, self.htypes[i], self.hdata[i]) 
                    delindx.append(i)

        #Delete all other processor tallies if molecules removed
        if self.molecules_deleted:
            for indx in sorted(delindx, reverse=True):
                print("Deleting", self.htypes[indx], self.hdata[indx]) 
                del self.htypes[indx]
                del self.hdata[indx]

        #Update binaryheader
        self.fmtstr = str(self.noints-len(delindx)) + "i"+str(self.ndbls) +"d"+ str(self.ntrlint) + "i"
        binaryheader = struct.pack(self.fmtstr, *self.hdata)

        #Write header at end of file
        #self.size = os.path.getsize(outfile)
        with open(outfile, "ab") as f:
            #f.seek(self.headersize[0])
            f.write(binaryheader)


class XYZReader:

    def __init__(self, fdir):
        raise RuntimeError("XYZReader not yet developed")




def read_grid(rec, filename="./results/surface.grid", ny=64, nz=64):
    data = np.fromfile(filename, dtype=np.float64)
    N = ny*nz
    Nrecs = int(data.shape[0]/N)
    r = data.reshape([Nrecs,ny,nz])

    #First two records are positions in y and z
    rec_ = rec+3

    # plot ! note the parent parameter
    x = []; y = []; z = []
    for i in range(nz):
        if (i%2 == 0):
            d = -1
        else:
            d = 1
        x.append(r[rec_,::d,i])
        y.append(r[0,::d,i])
        z.append(r[1,::d,i])

    for j in range(ny):
        if (j%2 == 0):
            d = -1
        else:
            d = 1
        x.append(r[rec_,j,::d])
        y.append(r[0,j,::d])
        z.append(r[1,j,::d,])

    x = np.array(x)#.ravel()
    y = np.array(y)#.ravel()
    z = np.array(z)#.ravel()

    return x, y, z


class MolAllPostProc(PostProc):

    def __init__(self, resultsdir, **kwargs):
        self.resultsdir = resultsdir
        self.plotlist = {} #collections.OrderedDict
        self.error = {}
        self.name = self.resultsdir.split('/')[-2]

        # Check directory exists before instantiating object and check 
        # which files associated with plots are in directory
        self.potentialfiles = ( "final_state", "initial_state", 
                                "vmd_out.dcd","vmd_temp.dcd",
                                "all_cluster.xyz", "surface.xyz") 

        if (not os.path.isdir(self.resultsdir)):
            print(("Directory " +  self.resultsdir + " not found"))
            raise IOError
            
        self.fields_present = []
        for fname in self.potentialfiles:
            if (glob.glob(self.resultsdir+fname)):
                self.fields_present.append(fname)
            if (glob.glob(self.resultsdir+fname+'.*')):
                self.fields_present.append(fname.strip().split('.')[0])

        self.fieldfiles1 = list(set(self.fields_present) & set(self.potentialfiles))

        try:
            Header1 = MDHeaderData(self.resultsdir)
        except IOError:
            raise NoResultsInDir

        if 'final_state' in (self.fieldfiles1):
            fs = final_state(resultsdir+"./final_state")
            self.plotlist.update({'final_state':fs})

        if 'vmd_out.dcd' in (self.fieldfiles1):
            vmdr = VMDReader(resultsdir, fname="vmd_out")
            self.plotlist.update({'vmd_out.dcd':vmdr})

        if 'vmd_temp.dcd' in (self.fieldfiles1):
            vmdr = VMDReader(resultsdir, fname="vmd_temp")
            self.plotlist.update({'vmd_temp.dcd':vmdr})

        if 'all_cluster.xyz' in (self.fieldfiles1):
            xyz = XYZReader(resultsdir, fname="all_cluster")
            self.plotlist.update({'all_cluster.xyz':xyz})

        if (len(self.plotlist) == 0):
            raise NoResultsInDir

        #choices = glob.glob(fdir+"*_state").replace(fdir,"")
        #choices += glob.glob(fdir+"*.dcd").replace(fdir,"")
        #choices += glob.glob(fdir+"*.xyz").replace(fdir,"")

        
#        for c in self.fieldfiles1:
#            if c is "final_state":
#                self.pos = self.fs.read_moldata()
#            elif ".dcd" in mtype:
#                self.dcd = VMDReader(self.fdir, fname=mtype.replace(".dcd",""))
#                self.pos = self.dcd.read_pos()
#            elif ".xyz" in mtype:
#                self.pos = self.xyz.read_pos()
#            self.redraw()

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from mpl_toolkits import mplot3d

    fdir = "/home/es205/codes/flowmol/runs/chebychev_CL/eij_wall1p0_stress/run1/results/"

    molall = MolAllPostProc(fdir)

    print(molall)

    fig = plt.figure(); ax = []
    ax.append(fig.add_subplot(1,2,1,projection='3d'))
    ax.append(fig.add_subplot(1,2,2,projection='3d'))

    #Create a final state object
    fs = molall.plotlist["final_state"]#final_state(fdir+"./final_state", verbose=True)

    #read the data
    D = fs.read_moldata()
    r = D["r"]
    tag = D["tag"]
    #Plot it
    ax[0].scatter(r[:,0], r[:,1], r[:,2], c=tag[:])
    
    #Load data from VMD object
    rec = 0
    vmdr = molall.plotlist["vmd_temp.dcd"]#VMDReader(fdir)
    pos = vmdr.read_pos(0, vmdr.maxrec)
    moltype = vmdr.read_moltype()    
    typeDict = {"Ar":[0.5, 0.5, 0., 1.], "S":[1.,0.,0.4,1.]}
    c = [typeDict[m] for m in moltype]
    ax[1].scatter(pos[:,0,rec], pos[:,1,rec], pos[:,2,rec], c=c)

    plt.show()


import numpy as np
import os
import struct
import glob
from operator import itemgetter
from scipy.io import FortranFile

from .headerdata import *
from .postproc import PostProc
from .pplexceptions import NoResultsInDir

# Currently these are helper functions used in both final state
# and vmd reader, ideally these would be part of a generic base class

def read_monomers(fdir, filename='monomers'):

    """
        Concat list of all monomers from monomers.00000X files, 
        each written by a processor rank, and store everything 
        in RAM if poss
    """
    chains = []
    rankfiles = glob.glob(fdir + filename + '_*')
    if (rankfiles):
        for rankfile in rankfiles:
            #print('Getting info from file ' + str(rankfile) + ' of ' + 
            #      str(len(rankfiles)))
            with open(rankfile,'r') as f:
                chains = chains + [list(map(int,line.split())) for line in f]
        # Sort the data into chains (second column is chainID)
        #chains.sort(key=itemgetter(1))
        #print('Sorting monomers into chains...')
    else:
        pass
        #print("No monomer files found, assuming atomistic case")

    return np.array(chains)

def get_connections(chains, pos, maxdist=5.0):

    """ 
        Setup connection array from monomer chains data
        Connectivity needs to be for example
        Point 0 will be connected with 1 and 2, point 
        1 with 4 and point 2 with 3 and 4.
        Given by command:   
     
        toconnect = np.array([[0,1], [0,2], [1,4], [2,3], [2,4]])

    """
    if (chains.size == 0):
        #Default with no connections to 0 connected to 0
        toconnect = np.array([[0,0]])
    else:
        toconnect = []
        for i in range(chains.shape[0]-1):
            if (chains[i,1] != 0):
                if (chains[i,1] == chains[i+1,1]):
                    #Check for periodic boundary wraparound
                    dist = np.abs(np.linalg.norm(pos[chains[i,0]-1,:]-pos[chains[i+1,0]-1,:]))
                    if (dist < maxdist):
                        toconnect.append([chains[i,0], chains[i+1,0]])
#                    if (np.abs(pos[chains[i,0]-1,0]-pos[chains[i+1,0],0]) < maxdist or
#                        np.abs(pos[chains[i,0],1]-pos[chains[i+1,0],1]) < maxdist or
#                        np.abs(pos[chains[i,0],2]-pos[chains[i+1,0],2]) < maxdist ):

        #Subtract 1 as Python is zero indexed
        toconnect = np.array(toconnect)-1

    #If nothing found that can be connected
    if (toconnect.shape[0]==0):
        toconnect = np.array([[0,0]])

    return toconnect


def read_grid(rec, filename="./results/surface.grid", ny=100, nz=100):
    data = np.fromfile(filename, dtype=np.float64)
    N = ny*nz
    Nrecs = int(data.shape[0]/N)
    r = data.reshape([Nrecs,ny,nz])

    #First two records are positions in y and z
    #Next one is skipped to match VMD output
    rec_ = rec+3

    xn = np.zeros(2*ny*nz)
    yn = np.zeros(2*ny*nz)
    zn = np.zeros(2*ny*nz)

    # plot ! note the parent parameter
    #x = []; y = []; z = []
    m = 0
    for i in range(nz):
        if (i%2 == 0):
            d = -1
        else:
            d = 1
        xn[m:m+ny] = r[rec_,::d,i]
        yn[m:m+ny] = r[0,::d,i]
        zn[m:m+ny] = r[1,::d,i]
        m += ny
        #print(i, "rec =", m, " of ", xn.size)

        #x.append(r[rec_,::d,i])
        #y.append(r[0,::d,i])
        #z.append(r[1,::d,i])

    for j in range(ny-1,-1,-1):
        if (j%2 == 0):
            d = 1
        else:
            d = -1

        xn[m:m+nz] = r[rec_,j,::d]
        yn[m:m+nz] = r[0,j,::d]
        zn[m:m+nz] = r[1,j,::d]
        m += nz


        #print(j, "rec =", m, " of ", xn.size)

        #x.append(r[rec_,j,::d])
        #y.append(r[0,j,::d])
        #z.append(r[1,j,::d,])

   # print(type(x), type(x[0]))

    x = xn #np.array(x)#.ravel()
    y = yn #np.array(y)#.ravel()
    z = zn #np.array(z)#.ravel()

    return x, y, z


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
        #self.n, self.nprocs = self.read_header()
        self.header = MDHeaderData(fdir)
        self.n = int(self.header.globalnp)
        self.nprocs = int(self.header.npx)*int(self.header.npy)*int(self.header.npz)
        self.Lxyz = np.array([float(self.header.globaldomain1),
                              float(self.header.globaldomain2),
                              float(self.header.globaldomain3)])
        self.labels = ["White", "Red", "tag", "moltype"]
        #Either take whichever file has been created most recently
        if fname is "newest":
            self.fname = self.check_files()
        elif "vmd_temp" in fname:
            self.fname = self.check_files(ftmp="vmd_temp.dcd", fout="IGNOREFILE")
        elif "vmd_out" in fname:
            self.fname = self.check_files(fout="vmd_out.dcd", ftmp="IGNOREFILE")
        else:
            raise IOError("fname", fname, " is not recognised in VMDReader") 

#    def read_header(self, headername="/simulation_header"):

#        #Load number of molecules data
#        fname = self.fdir + headername
#        with open(fname,"r") as f:
#            for l in f:
#                if "globalnp" in l:
#                    n = int(l.split(";")[2])
#                    break
#            for l in f:
#                if "npx" in l:
#                    npx = int(l.split(";")[2])
#                if "npy" in l:
#                    npy = int(l.split(";")[2])
#                if "npz" in l:
#                    npz = int(l.split(";")[2])
#                    nproc = npx*npy*npz
#                    break
#        return n, nproc

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
                #print("Loading record ", rec)
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
                                #print(rec, "Extra record of size = ", data.size, " with N mols = ", self.n)
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

    def read_psf(self, readdindex, fname="vmd_out.psf"):
                   
        #Code to read vmd_out.psf.# where # is the processor number
        if (readdindex == 5):
            moltype = np.empty(self.n, dtype='|S2')
            moltype[:] = "Ar" #Defaul of Argon (LJ) molecules
        elif (readdindex == 4):
            moltype = np.zeros(self.n)

        for i in range(1,self.nprocs+1):
            if self.nprocs != 1:
                fpsf = self.fdir + "/" +  fname + "." + str(i)
                if i == 1:
                    rd = True
            else:
                fpsf = self.fdir + "/" +  fname
                rd = True
            print("Reading file", fpsf, " for ", i, " of ", self.nprocs)
            if (os.path.exists(fpsf)):
                with open(fpsf) as f:
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
                        #Save moltype string in array
                        try:
                            psftype = l.split()[readdindex]
                            moltype[molno] = psftype
                        except ValueError:
                            #old format didn't encode tags so still string
                            moltype[molno] = 0
            else:
                continue

        return moltype

    def read_moltype(self):

        return self.read_psf(5)

    def read_tags(self):

        #Load tag data (assumes same ordering)
        #tagDict = {"free": 0, "fixed": 1, "fixed_slide": 2, "teth": 3, "thermo": 4, 
        #            "teth_thermo": 5, "teth_slide": 6, "teth_thermo_slide": 7}   
        return self.read_psf(4)



    def read_chains(self, pos):

        chains = read_monomers(self.fdir)
        return get_connections(chains, pos)

#        """
#            This is copied from flowmol_inputs 
#            and aims to draw all the connections
#        """

#        raise RuntimeError("read_chains not yet developed")

#        #This needs to be the global molecular numbers
#        #which I think can be obtained from the psf files
#        #globalno = np.fromfile(self.resultsdir + "/initial_dump_globalno",  dtype=np.int32)
#        #sortind = globalno.argsort()

#        try:
#            #This needs to be per processor
#            m = np.genfromtxt(self.resultsdir +"/monomers_00000001")
#            indx = m[sortind,0]-1
#            chainID = m[sortind,1]
#            subchainID = m[sortind,2]
#            rs = rt[sortind,:]
#            moltypes = moltype[sortind]
#            polyindx = indx[chainID!=0].astype("int")
#            rchains = rs[polyindx]
#            nmon = int(self.header.nmonomers)
#            #This prevents connections over the whole domain
#            rcutoff = 5 #0.5*min(float(header.globaldomain1),
#                        #      float(header.globaldomain2),
#                        #      float(header.globaldomain3)) 
#            for i in polyindx[::nmon]:
#                #if (i - globalno[i]-1 > 1e-7):
#                #    print("Molecules not ordered by indices, cannot draw chains")
#                #    break
#                #print("chain no = ", chainID[i], i, globalno[i]-1, moltypes[i:i+nmon], subchainID[i:i+nmon])
#                #self.axes.plot(rt[i:i+nmon,0], rt[i:i+nmon,1], rt[i:i+nmon,2], '-', lw=2.)
#                maxmoltype = moltypes.max()
#                for n in range(i,i+nmon-2):
#                    r12 = rt[n,:]-rt[n+1,:]
#                    if (np.linalg.norm(r12) < rcutoff):
#                        self.axes.plot(rt[n:n+2,0], rt[n:n+2,1], rt[n:n+2,2], '-',
#                                       c=cm.RdYlBu_r(moltypes[n]/maxmoltype), lw=2.)

#        except OSError as e:
#            print("OSError ", e)
#            pass
#        except IOError:
#            raise

class final_state:

    def __init__(self, fdir="./results/", fname= "./final_state", 
                       tether_tags = [3,5,6,7,10], verbose=False):

        self.fdir = fdir
        self.fname = fname
        self.tether_tags = tether_tags
        self.maxrec = 0 #Final state file is a single record
        self.labels = ["White", "Red", 'moltype', 'tag', 
                        "v1", "v2", "v3",
                        "globnum", 
                        "potdata1", "potdata2", "potdata3", "potdata4",
                        "rtether1", "rtether2", "rtether3",
                        "rtrue1", "rtrue2", "rtrue3"]

        #Get filesize and read headersize
        self.size = os.path.getsize(fdir+fname)

        #Empty final state can cause problems
        if self.size == 0:
            return
        self.headersize = np.fromfile(fdir+fname, dtype=np.int64, offset=self.size-8)
        with open(fdir+fname, "rb") as f:
            f.seek(self.headersize[0])
            self.binaryheader = f.read()

        self.read_header(verbose=verbose)
        self.dataloaded = False

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
            for k, i in list(self.headerDict.items()):
                print(k,i)

    def read_moldata(self, forcereload=False):

        #This prevents reload
        if self.dataloaded and not forcereload:
            return self.MolDict
        else:
            returnDict = {}

        #Read the rest of the data
        data = np.fromfile(self.fdir+self.fname, 
                           dtype=np.double, 
                           count=int(self.headersize/8))

        #Allocate arrays
        h = self.headerDict
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

        self.dataloaded = True
        self.MolDict = returnDict
        return returnDict


    def read_pos(self, start, end):

        returnDict = self.read_moldata()
        r = returnDict["r"]
        pos = np.zeros([r.shape[0],r.shape[1],1])
        pos[:,:,0] = r
        return pos

    def read_moltype(self):

        D = self.read_moldata()
        if "moltype" in D:
            return D["moltype"]
        else:
            return np.zeros(self.n)

    def read_tags(self):

        D = self.read_moldata()
        if "tag" in D:
            return D["tag"]
        else:
            return np.zeros(self.n)

    def read_chains(self, pos):

        chains = read_monomers(self.fdir)
        return get_connections(chains, pos)

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
            outfile = self.fdir+self.fname + "2"

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
            fs = final_state(resultsdir, "./final_state")
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


        #Check directory above for intialstate folder
        if "results" in self.resultsdir:
            fname = glob.glob(self.resultsdir+os.sep+".."+os.sep+"initial_state")
            #print(self.resultsdir.replace("results","")+"initial_state", fname)
            if (fname):
                self.fieldfiles1.append(fname[0])
                initstate = final_state("", fname[0])
                self.plotlist.update({'../initial_state':initstate})

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

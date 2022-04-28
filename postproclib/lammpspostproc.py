import os
from .lammpsfields import *
from .postproc import PostProc
from .pplexceptions import NoResultsInDir 

class LAMMPS_PostProc(PostProc):

    """ 
        Post processing class for LAMMPS runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir

        # Check directory exists before trying to instantiate object
        if (not os.path.isdir(self.resultsdir)):
            print(("Directory " +  self.resultsdir + " not found"))
            raise IOError

        possibles = {'vsum': LAMMPS_pField,
                     'nsum': LAMMPS_mField,
                     'Density': LAMMPS_dField,
                     'Velocity': LAMMPS_vField,
                     'Momentum': LAMMPS_momField,
                     'Temperature': LAMMPS_TField,
                     'Pressure': LAMMPS_PressureField,
                     'Shear Stess': LAMMPS_ShearStressField,
        	         'Kinetic Energy': LAMMPS_KineticEnergyField,    
                     'Potential Energy': LAMMPS_PotentialEnergyField,
                     'Total Energy': LAMMPS_TotalEnergyField
                    }


        #Try to get fnames from log.lammps
        fname = ""
        logfile = self.resultsdir + "/log.lammps"
        if (os.path.isfile(logfile)):
            with open(logfile, "r") as f:
                n = "3dgrid"
                for l in f:
                    if ("chunk/atom bin/3d") in l:
                       n=l.split()[1]
                    if n in l and "ave/chunk" in l:
                       indx = l.find("file")
                       if indx != -1:
                           fname = l[indx:].split()[1]
                       else:
                           print(("logfile ", logfile, " appears to be corrupted " + 
                                 "so cannot determine output filename"))
        else:
            pass
            #print("logfile ", logfile, " not found")
            #raise NoResultsInDir

        if fname == "":
            print("fname not defined, trying 3dgrid")
            fname = "3dgrid"


        self.plotlist = {}
        if os.path.exists(fname):
            for key, field in list(possibles.items()): 
                print(key, field, self.resultsdir)
                try:
                    self.plotlist[key] = field(self.resultsdir, fname)
                except IOError:
                    pass
                except ValueError:
                    pass 

        if (len(self.plotlist) == 0):
            raise NoResultsInDir

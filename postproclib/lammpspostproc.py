import os
from lammpsfields import *
from postproc import PostProc
from pplexceptions import NoResultsInDir 

class LAMMPS_PostProc(PostProc):

    """ 
        Post processing class for CFD runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir

        # Check directory exists before trying to instantiate object
        if (not os.path.isdir(self.resultsdir)):
            print("Directory " +  self.resultsdir + " not found")
            raise IOError

        possibles = {'LAMMPS Velocity': LAMMPS_vField,
                     'LAMMPS Number': LAMMPS_nField,
                     'LAMMPS Number Density': LAMMPS_dField}

        self.plotlist = {}
        for key, field in possibles.items(): 
            #print(key, field, self.resultsdir)
            try:
                self.plotlist[key] = field(self.resultsdir)
            except IOError:
                pass 

        if (len(self.plotlist) == 0):
            raise NoResultsInDir

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

        possibles = {'vsum': LAMMPS_pField,
                     'nsum': LAMMPS_mField,
                     'Density': LAMMPS_dField,
                     'Velocity': LAMMPS_vField,
                     'Momentum': LAMMPS_momField,
                     'Temperature': LAMMPS_TField,
                     'Pressure': LAMMPS_PressureField}

        self.plotlist = {}
        for key, field in possibles.items(): 
            #print(key, field, self.resultsdir)
            try:
                self.plotlist[key] = field(self.resultsdir)
            except IOError:
                pass 

        if (len(self.plotlist) == 0):
            raise NoResultsInDir

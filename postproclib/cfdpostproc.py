import os
from cfdfields import *
from postproc import PostProc
from pplexceptions import NoResultsInDir 

class CFD_PostProc(PostProc):

    """ 
        Post processing class for CFD runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir
        self.plotlist = {} 

        # Check directory exists before instantiating object and check 
        # which files associated with plots are in directory
        if (not os.path.isdir(self.resultsdir)):
            print("Directory " +  self.resultsdir + " not found")
            raise IOError

        try:
            fobj = open(self.resultsdir + 'report','r') 
        except IOError:
            raise NoResultsInDir

        possibles = {'CFD Velocity': CFD_vField,
                     'CFD Pressure': CFD_PField,
                     'CFD mugradv': CFD_mugradvField,
                     'CFD Stress': CFD_StressField,
                     'CFD Strain': CFD_strainField,
                     'CFD Vorticity': CFD_vortField,
                     'CFD Dissipation': CFD_dissipField}

        self.plotlist = {}
        for key, field in possibles.items(): 
            try:
                self.plotlist[key] = field(self.resultsdir)
            except AssertionError:
                pass 


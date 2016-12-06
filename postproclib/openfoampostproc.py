import os
from openfoamfields import *
from postproc import PostProc
from pplexceptions import NoResultsInDir 

class OpenFOAM_PostProc(PostProc):

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

        # Raise if no results in directory
        try:
            fobj = open(self.resultsdir + '0/U','r') 
        except IOError:
            raise NoResultsInDir

        possibles = {'U': OpenFOAM_vField, 
                     'P': OpenFOAM_PField}

        self.plotlist = {}
        for key, field in possibles.items(): 
            try:
                self.plotlist[key] = field(self.resultsdir)
            except AssertionError:
                pass 


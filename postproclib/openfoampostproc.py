import os
from openfoamfields import *
from postproc import PostProc
from pplexceptions import NoResultsInDir 
import glob

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
                     'P': OpenFOAM_PField,
                     'eps': OpenFOAM_epsField,
                     'F': OpenFOAM_FField}

        self.plotlist = {}
        for key, field in possibles.items(): 
            try:
                self.plotlist[key] = field(self.resultsdir)
            except AssertionError:
                pass 
        #Try to parse any other files
        files = glob.glob(self.resultsdir + '0/*')
        for filename in files:
            with open(filename) as f:
                for line in f:
                    if "class" in line:
                        fname = filename.split("/")[-1]
                        if "volScalarField" in line:
                            S = OpenFOAM_ScalarField(self.resultsdir, fname, **kwargs)
                        elif "volVectorField":
                            S = OpenFOAM_VectorField(self.resultsdir, fname, **kwargs)
                        elif "volSymmTensorField":
                            S = OpenFOAM_SymmTensorField(self.resultsdir, fname, **kwargs)
                        else:
                            continue
                        print(filename, fname, S)

            self.plotlist.update({fname:S})


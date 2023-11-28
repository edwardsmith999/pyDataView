import os
import glob

from .VTKfields import *
from .postproc import PostProc
from .pplexceptions import NoResultsInDir 

class VTK_PostProc(PostProc):

    """ 
        Post processing class for VTK files runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir

        # Check directory exists before trying to instantiate object
        if (not os.path.isdir(self.resultsdir)):
            print(("Directory " +  self.resultsdir + " not found"))
            raise IOError

        files = glob.glob(resultsdir+"/*.vtr")
        fnames = set([f.replace(resultsdir,"").replace("/","").split(".")[0] 
                     for f in files])
        

        self.plotlist = {}
        for fname in fnames:
            print(self.resultsdir, fname)
            try:
                self.plotlist[fname] = VTKField(self.resultsdir, fname)
            except IOError:
                pass
            except ValueError:
                pass 

        if (len(self.plotlist) == 0):
            raise NoResultsInDir

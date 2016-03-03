import os
import glob
from channelflowfields import *
from postproc import PostProc
from pplexceptions import NoResultsInDir

class channelflow_PostProc(PostProc):

    """ 
        Post processing class for channelflow runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir
        self.plotlist = {} 

        # Check directory exists before instantiating object and check 
        # which files associated with plots are in directory
        if (not os.path.isdir(self.resultsdir)):
            print("Directory " +  self.resultsdir + " not found")
            raise IOError

        possibles = {'channelflow Velocity': Channelflow_vField,
                     'Channelflow strain': Channelflow_strainField,
                     'Channelflow uu': Channelflow_uuField,
                     'Channelflow vorticity': Channelflow_vortField,
                     'Channelflow Dissipation': Channelflow_dissipField}
        
        if (not glob.glob(self.resultsdir+'*.h5')):
            raise NoResultsInDir

        self.plotlist = {}
        for key, field in possibles.items():
            try:
                self.plotlist[key] = field(self.resultsdir)
            except AssertionError:
                pass 

        if (len(self.plotlist) == 0):
            raise NoResultsInDir

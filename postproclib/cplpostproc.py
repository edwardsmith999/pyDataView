import os
from .cplfields import *
from .postproc import PostProc
from .pplexceptions import NoResultsInDir, DataNotAvailable
from .mdpostproc import MD_PostProc
from .cfdpostproc import CFD_PostProc
from .serial_cfdpostproc import Serial_CFD_PostProc
from .openfoampostproc import OpenFOAM_PostProc

# Results directory paths for each code
resultsdirs = {
                'flowmol': 'flowmol/results', 
                'lammps': 'lammps/', 
                'serialcouette': 'couette_serial/results/', 
                'openfoam': 'openfoam/', 
                'transflow': 'couette_data/'
              }



# Field classes that are associated with velocity for each code
vfieldtypes = { 
                'flowmol': 
                    mdfields.MD_vField, 
                'lammps': 
                    lammpsfields.LAMMPS_vField, 
                'serialcouette': 
                    serial_cfdfields.Serial_CFD_vField,
                'openfoam': 
                    openfoamfields.OpenFOAM_vField,
                'transflow': 
                    cfdfields.CFD_vField
              }

# Field classes that are associated with momentum for each code
momfieldtypes = { 
                'flowmol': 
                    mdfields.MD_momField, 
                'serialcouette': 
                    serial_cfdfields.Serial_CFD_momField,
                'lammps': 
                    lammpsfields.LAMMPS_momField, 
                'openfoam': 
                    openfoamfields.OpenFOAM_momField,
                'transflow': 
                    None
              }

# Field classes that are associated with stress for each code
stressfieldtypes = { 
                     'flowmol': 
                         mdfields.MD_stressField, 
                     'lammps': 
                         None, 
                     'serialcouette': 
                         serial_cfdfields.Serial_CFD_StressField,
                     'openfoam': 
                         openfoamfields.OpenFOAM_mugradvField,
                     'transflow': 
                         cfdfields.CFD_mugradvField
                   }


# CPL Field classes that could potentially be constructed  
possible_fields = {
                    'CPL Velocity': CPL_vField,
                    'CPL Momentum': CPL_momField,
                    'CPL Stress': CPL_stressField
                  }
# And their associated field class dictionary
type_dicts = {
                'CPL Velocity': vfieldtypes,
                'CPL Momentum': momfieldtypes,
                'CPL Stress': stressfieldtypes 
             }


# All possible pairings (Surely this should be done with itertools permute?)
possible_pairs = [  
                    {'MD':'flowmol', 'CFD':'serialcouette'},
                    {'MD':'flowmol', 'CFD':'openfoam'},
                    {'MD':'flowmol', 'CFD':'transflow'},
                    {'MD':'lammps', 'CFD':'openfoam'}
                 ]

class CPL_PostProc(PostProc):

    """ 
        Post processing class for Coupled runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir
        # Check directory exists before instantiating object and check 
        # which files associated with plots are in directory
        if (not os.path.isdir(self.resultsdir)):
            print(("Directory " +  self.resultsdir + " not found"))
            raise IOError

        self.plotlist = {}
        try:
            fobj = open(self.resultsdir + 'cpl/coupler_header','r')
        except IOError:
            raise NoResultsInDir

        for pair in possible_pairs: 

            MDkey = pair['MD']
            CFDkey = pair['CFD'] 

            for CPLkey, CPLfieldtype in list(possible_fields.items()):

                print(('Attempting to construct ' + str(CPLfieldtype) 
                      + ' for ' + MDkey + ' and ' + CFDkey))

                try:
                    self.plotlist[CPLkey] = CPLfieldtype(self.resultsdir,
                                                         MDFieldType=type_dicts[CPLkey][MDkey],
                                                         CFDFieldType=type_dicts[CPLkey][CFDkey],
                                                         mddir=resultsdirs[MDkey],
                                                         cfddir=resultsdirs[CFDkey])

                except AssertionError:
                    pass
                except DataNotAvailable:
                    pass
                except IOError:
                    pass
                except TypeError:
                    pass

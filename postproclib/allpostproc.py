import os

from .mdpostproc import MD_PostProc
from .lammpspostproc import LAMMPS_PostProc
from .cfdpostproc import CFD_PostProc
from .cplpostproc import CPL_PostProc
from .channelflowpostproc import channelflow_PostProc
from .openfoampostproc import OpenFOAM_PostProc
from .serial_cfdpostproc import Serial_CFD_PostProc
from .pplexceptions import NoResultsInDir
try:
    from .VTKpostproc import VTK_PostProc
    vispyfound = True
except ImportError:
    vispyfound = False

class All_PostProc:
    
    def __init__(self, fdir):

        if not os.path.isdir(fdir):
            print(("Requested directory ", fdir, " does not exist."))
            fdir = './'

        self.plotlist = {}

        try:
            CPL_PP = CPL_PostProc(fdir)
            self.plotlist.update(CPL_PP.plotlist)
            print(CPL_PP)
            print("Coupled case, only plotting coupled field")
            return
        except NoResultsInDir:
            pass

        try:
            MD_PP = MD_PostProc(fdir)
            self.plotlist.update(MD_PP.plotlist)
            print(MD_PP)
        except NoResultsInDir:
            pass

        try:
            LAMMPS_PP = LAMMPS_PostProc(fdir)
            self.plotlist.update(LAMMPS_PP.plotlist)
            print(LAMMPS_PP)
        except NoResultsInDir:
            pass

        try:
            CFD_PP = CFD_PostProc(fdir)
            self.plotlist.update(CFD_PP.plotlist)
            print(CFD_PP)
        except NoResultsInDir:
            pass

        try:
            CF_PP = channelflow_PostProc(fdir)
            self.plotlist.update(CF_PP.plotlist)
            print(CF_PP)
        except NoResultsInDir:
            pass

        try:
            SCFD_PP = Serial_CFD_PostProc(fdir)
            self.plotlist.update(SCFD_PP.plotlist)
            print(SCFD_PP)
        except NoResultsInDir:
            pass

        try:
            OF_PP = OpenFOAM_PostProc(fdir)
            self.plotlist.update(OF_PP.plotlist)
            print(OF_PP)
        except NoResultsInDir:
            pass

        if vispyfound:
            try:
                VTK_PP = VTK_PostProc(fdir)
                self.plotlist.update(VTK_PP.plotlist)
                print(VTK_PP)
            except NoResultsInDir:
                pass

        if (len(self.plotlist) == 0):
            raise NoResultsInDir



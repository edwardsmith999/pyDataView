# -*- encoding: utf-8 -*-
import os
import numpy as np
import sys
import math as maths
import glob
#import collections

from .mdfields import *
from .headerdata import *
from .postproc import PostProc
from .pplexceptions import NoResultsInDir, DataMismatch

    
class MD_PostProc(PostProc):

    """ 
        Post processing class for MD runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir
        self.plotlist = {} #collections.OrderedDict
        self.error = {}
        self.name = self.resultsdir.split('/')[-2]

        # Check directory exists before instantiating object and check 
        # which files associated with plots are in directory
        self.potentialfiles = ( "mslice", "mbins", "msnap","vslice", "vbins", 
                                "vsnap","pvirial", "pVA", "pVA_k","pVA_c", 
                                "visc", "mflux","vflux", "pplane", "psurface",
                                "esnap", "eflux", "eplane","esurface", "Fvext", 
                                "viscometrics", "rdf", "rdf3d", "ssf", "Fext",
                                "Tbins", "vPDF", "msolv", "mpoly", "vsolv",
                                "vpoly", "ebins","hfVA","hfVA_k","hfVA_c",
                                "msurf", "dsurf_mflux", "dsurf_vflux", 
                                "dsurf_eflux", "combin", "P")        

        if (not os.path.isdir(self.resultsdir)):
            print(("Directory " +  self.resultsdir + " not found"))
            raise IOError
            
        self.fields_present = []
        for fname in self.potentialfiles:
            if (glob.glob(self.resultsdir+fname)):
                self.fields_present.append(fname)
            if (glob.glob(self.resultsdir+fname+'.*')):
                self.fields_present.append(fname.strip().split('.')[0])

        self.fieldfiles1 = list(set(self.fields_present) & set(self.potentialfiles))

        try:
            Header1 = MDHeaderData(self.resultsdir)
        except IOError:
            raise NoResultsInDir

        #Dummy top value in visuliser
        m1 = MD_exampleField(self.resultsdir)
        self.plotlist.update({'An Example':m1})

        #Mass
        if 'mbins' in (self.fieldfiles1):
            m1 = MD_mField(self.resultsdir, **kwargs)
            self.plotlist.update({'mbins':m1})
            d1 = MD_dField(self.resultsdir, **kwargs)
            self.plotlist.update({'rho':d1})

        if 'msolv' in (self.fieldfiles1):
            m1 = MD_mField(self.resultsdir, fname='msolv', **kwargs)
            self.plotlist.update({'msolv':m1})
            d1 = MD_dField(self.resultsdir, fname='msolv', **kwargs)
            self.plotlist.update({'rho_solv':d1})

        if 'mpoly' in (self.fieldfiles1):
            m1 = MD_mField(self.resultsdir, fname='mpoly', **kwargs)
            self.plotlist.update({'mpoly':m1})
            d1 = MD_dField(self.resultsdir, fname='mpoly', **kwargs)
            self.plotlist.update({'rho_poly':d1})
            m1 = MD_polyconcField(self.resultsdir, **kwargs)
            self.plotlist.update({'C_solv':m1})

        #Momentum
        if 'vbins' in (self.fieldfiles1):
            M1 = MD_pField(self.resultsdir, **kwargs)
            self.plotlist.update({'vbins':M1})
            M1 = MD_momField(self.resultsdir, **kwargs)
            self.plotlist.update({'rho u':M1})

        if 'vsolv' in (self.fieldfiles1):
            M1 = MD_pField(self.resultsdir,fname='vsolv',**kwargs)
            self.plotlist.update({'vsolv':M1})
            M1 = MD_momField(self.resultsdir,fname='vsolv',**kwargs)
            self.plotlist.update({'rho u_solv':M1})

        if 'vpoly' in (self.fieldfiles1):
            M1 = MD_pField(self.resultsdir,fname='vpoly',**kwargs)
            self.plotlist.update({'vpoly':M1})
            M1 = MD_momField(self.resultsdir,fname='vpoly',**kwargs)
            self.plotlist.update({'rho u_poly':M1})

        #Centre of mass
        if 'combin' in (self.fieldfiles1):
            M1 = MD_comField(self.resultsdir,**kwargs)
            self.plotlist.update({'combin':M1})

        if ('combin' in (self.fieldfiles1) and
            'mbins' in (self.fieldfiles1)):
            M1 = MD_Centre_of_Mass_Field(self.resultsdir,**kwargs)
            self.plotlist.update({'centre of mass':M1})

        #Scalar pressure
        if 'P' in (self.fieldfiles1):
            KE1 = MD_EField(self.resultsdir,fname='P', **kwargs)
            self.plotlist.update({'P':KE1})



        #Kinetic energy
        if 'Tbins' in (self.fieldfiles1):
            KE1 = MD_EField(self.resultsdir,fname='Tbins', **kwargs)
            self.plotlist.update({'Tbins':KE1})

        #Mass snapshots
        if 'msnap' in (self.fieldfiles1):
            m1 = MD_mField(self.resultsdir,fname='msnap', **kwargs)
            self.plotlist.update({'msnap':m1})
            m1 = MD_dField(self.resultsdir,fname='msnap', **kwargs)
            self.plotlist.update({'rho_snap':m1})

        #Surface mass
        if 'msurf' in (self.fieldfiles1):
            m1 = MD_mfluxField(self.resultsdir,'msurf', **kwargs)
            self.plotlist.update({'msurf':m1})

            m1 = MD_CVmassField(self.resultsdir)
            self.plotlist.update({'rho_surf':m1})

            if ('vflux'   in (self.fieldfiles1) and
               'psurface' in (self.fieldfiles1) and
                'mbins'   in (self.fieldfiles1)):
                m1 = MD_velsoundField(self.resultsdir, **kwargs)
                self.plotlist.update({'c':m1})


        #Velocity snapshots
        if 'vsnap' in (self.fieldfiles1):
            v1 = MD_pField(self.resultsdir,fname='vsnap', **kwargs)
            self.plotlist.update({'vsnap':v1})
            v1 = MD_momField(self.resultsdir,fname='vsnap', **kwargs)
            self.plotlist.update({'rhou_snap':v1})
            

        #VA stress
        if 'pVA_k' in (self.fieldfiles1):
            P1 = MD_pVAField(self.resultsdir,fname='pVA_k', peculiar=False, **kwargs)
            self.plotlist.update({'VA_mvv_k':P1})
            P1 = MD_pVAField(self.resultsdir,fname='pVA_k', **kwargs)
            self.plotlist.update({'pVA_k':P1})
        if 'pVA_c' in (self.fieldfiles1):
            P1 = MD_pVAField(self.resultsdir,fname='pVA_c', **kwargs)
            self.plotlist.update({'pVA_c':P1})
        if (('pVA'   in self.fieldfiles1) or 
            ('pVA_k' in self.fieldfiles1 and 
             'pVA_c' in self.fieldfiles1    )):
            P1 = MD_pVAField(self.resultsdir,fname='pVA', **kwargs)
            self.plotlist.update({'pVA':P1})

            #Pressure Heating term
            if 'vbins' in self.fieldfiles1:
                P1 = MD_pVAheat_Field(self.resultsdir, **kwargs)
                self.plotlist.update({'pVA_stressheat':P1}) 

        #VA Heatflux
        if 'hfVA_k' in (self.fieldfiles1):
            try:
                P1 = MD_hfVAField(self.resultsdir,fname='hfVA_k', **kwargs)
                self.plotlist.update({'hfVA_k':P1})
            except DataNotAvailable:
                pass
                
        if 'hfVA_c' in (self.fieldfiles1):
            try:
                P1 = MD_hfVAField(self.resultsdir,fname='hfVA_c', **kwargs)
                self.plotlist.update({'hfVA_c':P1})
            except DataNotAvailable:
                pass
        if (('hfVA'   in self.fieldfiles1) or 
            ('hfVA_k' in self.fieldfiles1 and 
             'hfVA_c' in self.fieldfiles1    )):
            try:
                P1 = MD_heatfluxVAField(self.resultsdir,fname='hfVA', **kwargs)
                self.plotlist.update({'q':P1})
            except DataNotAvailable:
                pass

        #CV fluxes
        if 'mflux' in (self.fieldfiles1):
            flux1 = MD_mfluxField(self.resultsdir,'mflux', **kwargs)
            self.plotlist.update({'mflux':flux1})
            rhouCV = MD_CVmomField(self.resultsdir)
            self.plotlist.update({'rhou CV':rhouCV})

        if (('mflux' in self.fieldfiles1) and 
            ('vbins' in self.fieldfiles1)     ):
            rhouuCV =  MD_rhouuCVField(self.resultsdir)
            self.plotlist.update({'rhouu CV':rhouuCV})

        if (('mflux' in self.fieldfiles1) and 
            ('msurf' in self.fieldfiles1)     ):
            try:
                uCV =  MD_CVvField(self.resultsdir)
                self.plotlist.update({'u CV':uCV})
            except DataMismatch:
                pass


        if 'vflux' in (self.fieldfiles1):
            flux1 = MD_pfluxField(self.resultsdir,'vflux', **kwargs)
            self.plotlist.update({'vflux':flux1})
            flux1 = MD_pCVField(self.resultsdir,'vflux', peculiar=True, **kwargs)
            self.plotlist.update({'CVPressure_k':flux1})

        #External forces
        if 'Fext' in (self.fieldfiles1):
            Fext1 = MD_FField(self.resultsdir,'Fext', **kwargs)
            self.plotlist.update({'Fext':Fext1})

        #CV energy snapshot
        if 'esnap' in (self.fieldfiles1):
            esnap1 = MD_EField(self.resultsdir,'esnap', **kwargs)
            self.plotlist.update({'esnap':esnap1})

        if 'ebins' in (self.fieldfiles1):
            ebins = MD_EField(self.resultsdir,'ebins', **kwargs)
            self.plotlist.update({'ebins':ebins})

            try:
                E = MD_EnergyField(self.resultsdir, **kwargs)
                self.plotlist.update({'Energy':E})
            except DataMismatch:
                pass

            try:
                E = MD_rhoEnergyField(self.resultsdir, **kwargs)
                self.plotlist.update({'rhoEnergy':E})
            except DataMismatch:
                pass

        #Time evolving CV fluxes
        if 'dsurf_mflux' in (self.fieldfiles1):
            flux1 = MD_mfluxField(self.resultsdir,'dsurf_mflux', **kwargs)
            self.plotlist.update({'dsurf_mflux':flux1})

        if 'dsurf_vflux' in (self.fieldfiles1):
            flux1 = MD_pfluxField(self.resultsdir,'dsurf_vflux', **kwargs)
            self.plotlist.update({'dsurf_vflux':flux1})

        if 'dsurf_eflux' in (self.fieldfiles1):
            flux1 = MD_efluxField(self.resultsdir,'dsurf_eflux', **kwargs)
            self.plotlist.update({'dsurf_eflux':flux1})


        if ('ebins' in self.fieldfiles1 and
            'vbins' in self.fieldfiles1):
            try:
                rhoue =  MD_energyadvct_Field(self.resultsdir, **kwargs)
                self.plotlist.update({'rhouE':rhoue})
            except DataMismatch:
                pass

        if ('ebins' in self.fieldfiles1 and
            'Tbins' in self.fieldfiles1):
            try:
                U =  MD_potEnergyField(self.resultsdir, **kwargs)
                self.plotlist.update({'U':U})
            except DataMismatch:
                pass

        if (('ebins' in self.fieldfiles1 and 'Tbins' in self.fieldfiles1) and 
           (('pVA'   in self.fieldfiles1) or 
            ('pVA_k' in self.fieldfiles1 and 'pVA_c' in self.fieldfiles1 ))):
            try:
                h =  MD_enthalpyField(self.resultsdir, **kwargs)
                self.plotlist.update({'h':h})
            except DataMismatch:
                pass

        #CV stresses
        if 'psurface' in (self.fieldfiles1):
            stress1 = MD_pfluxField(self.resultsdir,'psurface', **kwargs)
            #stress1 = MD_pCVField(self.resultsdir,'psurface', **kwargs)
            self.plotlist.update({'psurface':stress1})

        #Total CV stress and stress Heating
        if ('vflux'   in (self.fieldfiles1) and
           'psurface' in (self.fieldfiles1)):
            stress1 = MD_pCVField(self.resultsdir,'total', peculiar=False,**kwargs)
            self.plotlist.update({'vflux+psurface':stress1})

        #Total CV stress and stress Heating
        if ('vflux'   in (self.fieldfiles1) and
           'psurface' in (self.fieldfiles1) and
           'dsurf_vflux' in (self.fieldfiles1)):
            stress1 = MD_pCVField(self.resultsdir,'total', peculiar=False, 
                                  moving_ref=True,**kwargs)
            self.plotlist.update({'vflux+psurface+dsurf_vflux':stress1})


        #Total CV stress and stress Heating
        if ('vflux'   in (self.fieldfiles1) and
           'psurface' in (self.fieldfiles1) and
            'mbins'   in (self.fieldfiles1) and
            'vbins'   in (self.fieldfiles1)):
            stress1 = MD_pCVField(self.resultsdir,'total', **kwargs)
            self.plotlist.update({'CV_pressure':stress1})
            stress1 = MD_CVStressheat_Field(self.resultsdir, **kwargs)
            self.plotlist.update({'stressheat CV':stress1})
            stress1 = MD_scalarPCVField(self.resultsdir,'total', **kwargs)
            self.plotlist.update({'P':stress1})
            stress1 = MD_scalarPCVField(self.resultsdir,'psurface', **kwargs)
            self.plotlist.update({'P^C':stress1})
            stress1 = MD_scalarPCVField(self.resultsdir,'vflux', **kwargs)
            self.plotlist.update({'P^K':stress1})

        if ('ebins' in self.fieldfiles1 and
            'mflux' in self.fieldfiles1):
            try:
                rhoue =  MD_rhouECVField(self.resultsdir, **kwargs)
                self.plotlist.update({'rhouE CV':rhoue})
            except DataMismatch:
                pass

        #CV energy fluxes
        if 'eflux' in (self.fieldfiles1):
            eflux1 = MD_efluxField(self.resultsdir,'eflux', **kwargs)
            self.plotlist.update({'eflux':eflux1})

        #CV surface power
        if 'esurface' in (self.fieldfiles1):
            energy1 = MD_efluxField(self.resultsdir,'esurface', **kwargs)
            self.plotlist.update({'esurface':energy1})


        #Heat flux
        if (('esurface' in self.fieldfiles1) and
            ('psurface' in self.fieldfiles1) and 
            ('vbins' in self.fieldfiles1  )    ):
            try:
                P1 = MD_heatfluxCVField(self.resultsdir, **kwargs)
                self.plotlist.update({'q_CV':P1})
            except DataNotAvailable:
                pass

        #CV Energy due to external body 
        if 'Fvext' in (self.fieldfiles1):
            Fvext1 = MD_EField(self.resultsdir,'Fvext', **kwargs)
            self.plotlist.update({'Fvext':Fvext1})

        #Velocity
        if ('mbins' in (self.fieldfiles1) and 'vbins' in (self.fieldfiles1)):
            try:
                v1 = MD_vField(self.resultsdir, **kwargs)
                self.plotlist.update({'u':v1})
                v1 = MD_ufluctField(self.resultsdir, **kwargs)
                self.plotlist.update({'u^\prime':v1})
                v1 = MD_vFieldatsurface(self.resultsdir, **kwargs)
                self.plotlist.update({'u at surface':v1})

            except DataMismatch:
                pass

            try:
                v1 = MD_rhouuField(self.resultsdir, **kwargs)
                self.plotlist.update({'rhouu':v1})
            except DataMismatch:
                pass

        #strain
        if ('mbins' in (self.fieldfiles1) and 'vbins' in (self.fieldfiles1)):
            try:
                v1 = MD_strainField(self.resultsdir, **kwargs)
                self.plotlist.update({'Strain':v1})
            except DataMismatch:
                pass


        #Vorticity
        if ('mbins' in (self.fieldfiles1) and 'vbins' in (self.fieldfiles1)):
            try:
                v1 = MD_vortField(self.resultsdir, **kwargs)
                self.plotlist.update({'Vorticity':v1})
            except DataMismatch:
                pass

        #Dissipation
        if ('mbins' in (self.fieldfiles1) and 'vbins' in (self.fieldfiles1)):
            try:
                v1 = MD_dissipField(self.resultsdir, **kwargs)
                self.plotlist.update({'Dissipation':v1})
            except DataMismatch:
                pass

        #Velocity snapshot
        if ('msnap' in (self.fieldfiles1) and 'vsnap' in (self.fieldfiles1)):
            try:
                v1 = MD_vField(self.resultsdir,rectype='snap', **kwargs)
                self.plotlist.update({'u_snap':v1})
            except DataMismatch:
                pass
        #Temperature
        if ('mbins' in (self.fieldfiles1) and 
            'vbins' in (self.fieldfiles1) and 
            'Tbins' in (self.fieldfiles1)):
            try:
                T1 = MD_TField(self.resultsdir, **kwargs)
                self.plotlist.update({'T':T1})
            except DataMismatch:
                pass
            try:
                T1 = MD_rhoTField(self.resultsdir, **kwargs)
                self.plotlist.update({'rhoT':T1})
            except DataMismatch:
                pass
            try:
                T1 = MD_TField(self.resultsdir, peculiar=False, **kwargs)
                self.plotlist.update({'T_peculiar':T1})
            except DataMismatch:
                pass
            #Derivative of temperature heatflux
            try:
                T1 = MD_dTdrField(self.resultsdir, **kwargs)
                self.plotlist.update({'dTdr':T1})
            except DataMismatch:
                pass
            except DataNotAvailable:
                pass

            #Analytical form of heatflux
            try:
                q1 = MD_heatfluxapprox(self.resultsdir, **kwargs)
                self.plotlist.update({'q_approx':q1})
            except DataMismatch:
                pass
            except DataNotAvailable:
                pass

        if (len(self.plotlist) == 0):
            raise NoResultsInDir

        #Encode latex names
#        for key in self.plotlist.keys():
#            print(key,latex_encode(key))
#            self.plotlist[latex_encode(key)] = self.plotlist.pop(key)

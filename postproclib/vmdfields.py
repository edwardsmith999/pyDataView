#! /usr/bin/env python2.7

#Opens VMD with overlayed fields
import os
import numpy as np
import csv
import sys
import shutil
import glob

from .mdpostproc import MD_PostProc
from .mdfields import (MD_mField, MD_vField, MD_TField, 
                      MD_momField, MD_dField)
from .headerdata import MDHeaderData
from .writecolormap import WriteColorMap
sys.path.insert(0,'../')
from misclib import Chdir
from .vmd_reformat import VmdReformat


class VMDFields:
    
    """
        Class to create reformat mass, momentum, temperature, etc 
        fields and run VMD with molecules coloured by these fields
    """

    def __init__(self, fieldobj, fdir=None, scriptdir=None):

        if fdir == None:
            self.fdir = fieldobj.fdir
        else:
            self.fdir = os.path.join(fdir, '')
        if scriptdir == None:
            self.scriptdir = os.path.dirname(os.path.realpath(__file__))+"/"
        else:
            self.scriptdir = scriptdir
        self.fieldobj = fieldobj
        self.pwd = os.path.join(os.path.dirname(__file__))
        self.vmdfile = 'vmd_out.dcd'

        #Read Header
        self.header = fieldobj.Raw.header #MDHeaderData(fdir)

        #Check simulation progress file to check if run 
        #is still going or has finished prematurely (crashed)
        with open(self.fdir+'simulation_progress', 'r') as f:
            simulation_time = f.readline()
        for i in dir(self.header):
            print(i, i.find('initialstep') == 0)
            if (i.find('Nsteps') == 0):
                self.Nsteps = int(vars(self.header)[i])
            if (i.find('initialstep') == 0):
                self.initialstep = int(vars(self.header)[i])

        if (int(simulation_time)-self.initialstep < self.Nsteps):
            self.Nsteps = int(simulation_time)
            self.finished = False
        else:
            self.finished = True

        #Get vmd skip
        vmd_skip_found = False
        for i in dir(self.header):
            if (i.find('vmd_skip') == 0):
                self.vmd_skip = int(vars(self.header)[i])
                vmd_skip_found = True

        if (not vmd_skip_found):
            self.vmd_skip = 1

        #Get VMD intervals from header
        self.starts = []; self.ends = []
        for i in dir(self.header):
            if (i.find('vmd_start') == 0):
                start = int(vars(self.header)[i])
                if (start < int(simulation_time)-self.initialstep):
                    self.starts.append(start)
            if (i.find('vmd_end') == 0):
                end = int(vars(self.header)[i])
                if (end < float(simulation_time)-self.initialstep):
                    self.ends.append(end)

        #If part way though an interval, set maximum to last iteration run
        if (len(self.starts) > len(self.ends)):
            self.ends.append(int(simulation_time)-self.initialstep)

        #Shift by initialrecord

        #Get averaging time per record
        self.Nave = str(self.fieldobj.plotfreq)

    def copy_tclfiles(self):
        
        """
            Create VMD vol_data folder
        """

        self.vmd_dir = self.fdir + '/vmd/'
        self.vol_dir = self.vmd_dir + '/vol_data/'
        if not os.path.exists(self.vol_dir):
            os.makedirs(self.vol_dir)

        def listdir_nohidden(path):
            return glob.glob(os.path.join(path, '*'))

        #Copy tcl scripts to vmd folder
        self.vmdtcl = self.scriptdir + '/vmd_tcl/'
        if listdir_nohidden(self.vmdtcl) == []:
            sys.exit("Error in copy_tclfiles -- Directory " 
                      + self.vmdtcl +
                     " is empty or not found ")
        for filepath in listdir_nohidden(self.vmdtcl):
            filename = filepath.split('/')[-1]
            print(filepath, self.vmd_dir+ '/' +filename)
            shutil.copyfile(filepath, self.vmd_dir+ '/' +filename )

    def reformat(self):

        # If simulation has not finish and temp is newer than out
        # call reformat to update vmd_out.dcd
        reformat = False
        if not self.finished:
            if (os.path.isfile(self.fdir+self.vmdfile)):
                filetime = os.path.getmtime(self.fdir+self.vmdfile)
            else:
                filetime = 0.

            if (os.path.isfile(self.fdir+self.vmdfile.replace('out','temp'))):
                temptime = os.path.getmtime(self.fdir+self.vmdfile.replace('out','temp'))
            else:
                temptime = 0.
                
            if temptime > filetime:
                print('Attempting to reformat vmd_out.dcd from vmd_temp.dcd')
                reformat = True

        else:
            if not os.path.isfile(self.fdir+self.vmdfile):
                print(self.fdir+self.vmdfile)
                print('Run has finished but vmd_out.dcd is missing')
                sys.exit(1)

        if reformat:
            self.reformat_vmdtemp()

    def write_vmd_header(self):

        #Write VMD intervals
        print('Writing VMD Header')
        with open(self.vol_dir + '/vmd_header','w+') as f:
            f.write(self.header.tplot + '\n')
            f.write(self.header.delta_t + '\n')
            f.write(self.Nave + '\n')
            f.write(str(self.vmd_skip) + '\n')

    def write_vmd_intervals(self):

        #Write VMD intervals
        print('Writing VMD intervals data')
        self.starts.sort(); self.ends.sort()
        self.vmdintervals = list(zip(self.starts, self.ends))
        with open(self.vol_dir + '/vmd_intervals','w+') as f:
            for i in self.vmdintervals:
                f.write(str(i[0]) + '\n' + str(i[1]) + '\n')

    #Write range of dx files based on VMD intervals
    def write_dx_range(self, component=0, clims=None):

        #Clean previous files
        outdir = self.fdir+"./vmd/vol_data/"
        filelist = [ f for f in os.listdir(outdir + ".") if f.endswith(".dx") ]
        for f in filelist:
            os.remove(outdir+f)

        #Write range of files in all intervals
        print('Writing dx files intervals data',self.vmdintervals)
        clims_array = []
        for i in self.vmdintervals:
            fieldrecstart = i[0]/(int(self.header.tplot)*int(self.Nave))
            fieldrecend   = i[1]/(int(self.header.tplot)*int(self.Nave))
            if (fieldrecend > self.fieldobj.maxrec):
                fieldrecend = self.fieldobj.maxrec
            #If limits are not specified, store time history for all intervals and average
            if (clims == None):
                clims_array.append(self.fieldobj.write_dx_file(fieldrecstart, 
                                                               fieldrecend,
                                                               component=component, norm=True))
            elif (len(clims) != 2):
                quit("Error in write_dx_range - clims should be tuple length 2 of form (cmin,cmax)")
            else:
                dummy = self.fieldobj.write_dx_file(fieldrecstart, 
                                                    fieldrecend, 
                                                    component=component)

        #Write maximum and minimum values for colourbar
        if (clims == None):
            clims = np.max(clims_array,axis=0)
	    #clims[1] = np.min(clims_array,axis=1)
        with open(self.vol_dir + '/colour_range','w+') as f:
            f.write(str(clims[0]) + '\n' + str(clims[1]) + '\n')

    def writecolormap(self,cmap='RdYlBu_r'):
        cmap_writer = WriteColorMap(cmap,1024)
        cmap_writer.write(self.vol_dir)

    def reformat_vmdtemp(self):

        """ 
            If run has not finished, attempt to build and
            run fortran code to reorder temp files to a
            useful form
        """

        print("Attempting to reformat " + self.vmdfile.replace('out','temp') + 
              " in " + self.fdir + " to " + self.vmdfile   )

        VMDreformobj = VmdReformat(os.path.abspath(self.fdir)+'/', 
                                   fname=self.vmdfile.replace('out','temp'), 
                                   scriptdir=self.scriptdir)
        VMDreformobj.reformat()

if __name__ == "__main__":

    fdir='../../MD_dCSE/src_code/results/'

    fieldtypes = {'mbins','vbins','Tbins',
                  'density','momentum','CV_config',
                  'CV_kinetic','CV_total'}

    ppObj = MD_PostProc(fdir)

    if(len(sys.argv) == 1):
        print("No field type specified, options include: " 
              + str(fieldtypes) + " Setting default vbins")
        objtype = 'vbins'
        component = 0
    elif(sys.argv[1] in ['--help', '-help', '-h']):
        print("Available field types include")
        print(ppObj)
        sys.exit()
    else:
        objtype = sys.argv[1]
        if(len(sys.argv) == 2):
            print("No components direction specified, setting default = 0")
            component = 0
        else:
            component = sys.argv[2]

    try:
        fobj = ppObj.plotlist[objtype]
    except KeyError:
        print("Field not recognised == available field types include")
        print(ppObj)
        sys.exit()
    except:
        raise

    vmdobj = VMDFields(fobj,fdir)
    vmdobj.reformat()
    vmdobj.write_vmd_header()
    vmdobj.write_vmd_intervals()
    vmdobj.write_dx_range(component=component)
    vmdobj.writecolormap('RdYlBu')
    with Chdir(fdir + './vmd/'):
        print(fdir)
        command = "vmd -e " + "./plot_MD_field.vmd"
        os.system(command)

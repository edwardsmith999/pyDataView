#! /usr/bin/env python2.7

# Gets number of molecules from header file and 
# calls fortran routine vmd_reformat.exe to convert 
# vmd.temp into readable files
# Written by David Trevelyan 
# Edited by Edward Smith 25/11/14

import os

from .pplexceptions import ScriptMissing

class Chdir:          
    """
       Wrapper to move from current directory to new directory
       and return when using with

       Example usage:

       with Chdir('./../'):
           os.system('./a.out')
    """
    def __init__( self, newpath ):  
        self.savedPath = os.getcwd()

        #Check for abs or relative path
        if (newpath[0] == "/"):
            self.newpath = newpath
        elif (newpath[0] != "."):
            self.newpath = './' + newpath
        else:
            self.newpath = newpath

    def __enter__( self ):
        os.chdir(self.newpath)

    def __exit__( self, etype, value, traceback):
        os.chdir(self.savedPath )

class VmdReformat:

    def __init__(self, fdir, fname, scriptdir):

        self.fdir = fdir
        self.fname = fname
        self.scriptdir = scriptdir
        self.Reformatted = False

        headerfile = self.fdir + 'simulation_header'

        # Extract np from header
        fobj = open(headerfile,'r')
        self.np = 0
        while self.np==0:
            line = fobj.readline().split(';')
            if (line[1].strip() == 'globalnp'):
                self.np   = int(line[2].strip())

        self.domain = [0, 0, 0]
        for ixyz in range(3):
            while self.domain[ixyz]==0:
                line = fobj.readline().split(';')
                if (line[1].strip() == 'globaldomain(' + str(ixyz+1) + ')'):
                    self.domain[ixyz]   = float(line[2].strip())

        if not os.path.isfile(self.scriptdir + 'vmd_reformat.f90'):
            print('Error -- vmd_reformat.f90 is missing from ' +  self.scriptdir)
            raise ScriptMissing

    def reformat(self):

        #Remove previous file
        try:
            os.remove(str(self.fdir) + str(self.fname).replace('temp','out'))
        except OSError:
            pass

        # Build and call VMD_reformat with np from header
        with Chdir(self.scriptdir):
            os.system('mpif90 -O3 -o vmd_reformat.exe vmd_reformat.f90')
            cmd = ('./vmd_reformat.exe ' + str(self.fdir) 
                                   + ' ' + str(self.fname) 
                                   + ' ' + str(self.np)
                                   + ' ' + str(self.domain[0])
                                   + ' ' + str(self.domain[1])
                                   + ' ' + str(self.domain[2]))
            print(cmd)
            os.system(cmd)

        #Check if sucessful
        try:
            with open(self.fdir + '/' + self.fname.replace('temp','out')): pass
            self.Reformatted = True
        except IOError:
            print('Reformat unsuccessful')
            raise

    def run_vmd(self):

        if self.Reformatted:
            try:
                with open('./'   + self.fdir + '/' + self.fname.replace('temp','out')): pass
                os.system('vmd ' + self.fdir + '/' + self.fname.replace('temp','out'))
            except IOError:
                print('vmd_out.dcd file missing in run_vmd  -- have you called reformat?')
        else: 
            print('VmdReformat.reformat() must be called before VmdReformat.run_vmd()')

if __name__ == "__main__": 

    scriptdir = os.path.join(os.path.dirname(__file__))
    filepath = scriptdir + '/../results/'
    filename = 'vmd_temp.dcd'

    VMDobj = VmdReformat(filepath, filename, scriptdir)
    VMDobj.reformat()
    VMDobj.run_vmd()



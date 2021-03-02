#! /usr/bin/env python
import glob
import os
import re

"""
	Automatically read and store variables in a header file formatted
	as follows:
		
		description ;  variable_name{(array_element)} ; variable_value
	
	where the delimiter is a semicolon and elements of multi-dimensional
	Fortran arrays are written with curved brackets (). The array is then
	stored as individual variable with the same name and the array index
	as a suffix (e.g. domain(1:3) is stored as domain1, domain2 and domain3).

"""
class HeaderData:

	def __init__(self,fobj):
		for line in fobj:
			varname=line.split(';')[1].strip().replace('(','').replace(')','')
			varval =line.split(';')[2].strip()
			vars(self)[varname] = varval

class MDHeaderData(HeaderData):

    def __init__(self, fdir):
        if (fdir[-1] != '/'): fdir += '/'
        fobj = open(fdir+'simulation_header','r')
        HeaderData.__init__(self,fobj)

class Serial_CFD_HeaderData(HeaderData):

    def __init__(self, fdir):
        if (fdir[-1] != '/'): fdir += '/'
        fobj = open(fdir+'continuum_header','r')
        HeaderData.__init__(self,fobj)

class FEA_HeaderData(HeaderData):

    def __init__(self, fdir):
        if (fdir[-1] != '/'): fdir += '/'
        fobj = open(fdir+'continuum_header','r')
        HeaderData.__init__(self,fobj)

class openfoam_HeaderData:

    def __init__(self, fdir, readfields=False):

        if (fdir[-1] != '/'): fdir += '/'
        self.fdir = fdir
        headerfiles = self.get_header_files()
        
        if readfields:
            fieldfiles = self.get_field_files()
            readfiles = headerfiles + fieldfiles
        else:
            readfiles = headerfiles

        headerDict = {}
        for filename in readfiles:
            if os.path.isfile(filename):
                with open(filename) as f:
                    lines = self.lines_generator_strip(f)
                    header = self.header_parser(lines)
                headerDict[filename.split("/")[-1]] = header
        self.headerDict = headerDict

    def get_header_files(self):
        #["blockMeshDict", "transportProperties", "controlDict", 
        #  "environmentalProperties", "decomposeParDict"]
        paths = [self.fdir + f for f in ['constant', 'system']]
        filenames = []
        for path in paths:
            files = glob.glob(path + "/*")
            for filename in files:
                filenames.append(filename)

        filenames.append(self.fdir + "constant/polyMesh/blockMeshDict")

        return filenames

    def get_field_files(self):

        path = self.fdir + "0/"
        files = glob.glob(path + "/*")
        filenames = []
        for filename in files:
            try:
                with open(filename) as f:
                    for line in f:
                        if "class" in line:
                            fname = filename.split("/")[-1]
                            if "volScalarField" in line:
                                filenames.append(filename)
                            elif "volVectorField":
                                filenames.append(filename)
                            elif "volSymmTensorField":
                                filenames.append(filename)
                            else:
                                continue
            except IOError:
                pass

        return filenames

    def lines_generator(self, lines):
        for line in lines:
            if not line:
                continue
            yield line

    def lines_generator_strip(self, lines):
        for line in lines:
            line = line.strip()
            if not line:
                continue
            yield line

    def stringtolist(self, s):
        v = s.replace("(","").replace(")","").split()
        r = []
        for i in v:
            try:
                r.append(int(i))
            except ValueError:
                try:
                    r.append(float(i))
                except ValueError:
                    r.append(i)
        return r

    def header_parser(self, lines):

        """
            Recursive header parser which
            builds up a dictonary of input files
        """
        ft = True
        Out = {}
        prevline = ""
        for line in lines:

            #Skip comments
            if line[0:2] == "/*":
                break_next = False
                for line in lines:
                    if break_next:
                        break
                    if '\*' in line:
                        break_next=True
            if "//" in line:
                continue

            #Split line into list
            split = line.split() 

            #One elemnt means we will go down to another level of nesting
            if len(split) == 1:
                if (line == '{' or line == '('):
                    try:
                        Out[prevline] = self.header_parser(lines)
                    except TypeError:
                        continue
                elif line == ');':
                    return Out
                elif line == '}':
                    return Out
                else:
                    #This skip here avoids field contents
                    try:
                        float(line)
                        return Out
                    except ValueError:
                        Out[line] = None

            #If ends with a semi-colon then we define a value
            elif len(split) == 2:
                if line[-1] == ";":
                    key, value = split
                    Out[key] = value.strip(';')
                else:
                    print(("Error, two values not a statement", line))
            #Otherwise we have to parse as needed
            elif len(split) > 2:
                key = split[0]
                if ("[" in line):
                    indx = line.find("]")
                    afterunits = line[indx+1:].replace(";","")
                    Out[key] = self.stringtolist(afterunits)
                elif ("(" in key):
                    if ft:
                        ft = False
                        Out = []
                    Out.append(self.stringtolist(line))
                else:
                    #As we have a key, we assume multiple brackets on line
                    indx = line.find(key)
                    remainingline = line[indx+len(key):]
                    rsplit = re.findall("\((.*?)\)", remainingline)
                    #rsplit = remainingline.replace("(",")").split(")")[:-1]
                    vals = []
                    for s in rsplit:
                        vals.append(self.stringtolist(s))
                    Out[key] = vals

            if line[-1] == ");":
                return Out

            if line[-1] == "}":
                return Out

            prevline = line

        return Out


#if __name__ == "__main__":
#    fdir = "/home/es205/codes/cpl_granlammmps/OpenFOAM-3.0.1_LAMMPS-dev/OpenFOAM-3.0.1_coupled/runs/Couette_Gran/openfoam"
#    filename = fdir+"/constant/polyMesh/blockMeshDict"
#    #filename = fdir+"/system/decomposeParDict"

#    with open(filename) as fobj:
#        lines = lines_generator(fobj)
#        header = header_parser(lines)

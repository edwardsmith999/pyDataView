#! /usr/bin/env python
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

# pyDataView
Data Viewer GUI written in python, wxpython and matplotlib.

The intention is to provide a lightweight interface for quick insight into available data.
This can be explored both as a lineplot and contour over the range of existing records and bins.
For more detailed analysis, a figure can be saved, the data output as a csv file or a sample python script generated.

# Quickstart

The data view works with the concept of fields of three dimensional data with an arbitary 4th dimension.
This reads some types of field data written in binary format by MPI, fortran code, OpenFOAM, Channelflow and LAMMPS.
Simple useage involves pointing at directory 

    pyDataView -d ./path/to/dir
    
or simply `pyDataView` and choosing the directory.
Any files which can be converted to fields are displayed on the left hand side.

![alt tag](https://raw.githubusercontent.com/edwardsmith999/pyDataView/master/pyDataView_screenshot.png)

If the datatype is already supported, there is nothing further to do.
In order to add new datatypes, the user must create a raw data reader as follows,

```python

    from rawdata import RawData

    class SomeNewReader(RawData):
    
        def __init__(self,fdir,fname,dtype,nperbin):
            if (fdir[-1] != '/'): fdir += '/' 
            self.fdir = fdir
            self.fname = fname
            self.dtype = dtype
            self.nperbin = nperbin
            self.filepath = self.fdir + self.fname + '/'
            self.header = self.read_header(fdir)
            self.grid = self.get_gridtopology()
            self.maxrec = self.get_maxrec()

        def read(self, startrec, endrec):

            # Read a 5D array with nx, ny, nz, nperbin, nrecs
            # where nrecs=endrec-startrec+1 and nperbin is 1 for scalar field
            # and 3 for vector field, etc
            
            return bindata
    
 ```
 
A new field datatype must then be added to read and uses these raw inputs. 
Any new fields can then be added to postproc.py which is instantiated by allpostproc.py allowing pyDataView to find and display the new field format. The process is more complex and further funtionality such as slicing requires binlimits to be specified. There are many examples in the postproclib file which can be used as a template.

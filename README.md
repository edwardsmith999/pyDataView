# pyDataView
Data Viewer GUI written in python, wxpython and matplotlib

The data view works with the concept of fields of three dimensional data with an arbitary 4th dimension.
This reads some types of field data written in binary format by MPI, fortran code, OpenFOAM, Channelflow and LAMMPS.
Simple useage involves pointing at directory 

    pyDataView -d ./path/to/dir
    
or simply `pyDataView` and choosing the directory.
Any files which can be converted to fields are displayed on the left hand side.



![alt tag](https://raw.githubusercontent.com/edwardsmith999/pyDataView/master/pyDataView_screenshot.png)

#Write colormap as file with name specified by colormap

import matplotlib.cm as cm
import numpy as np

class WriteColorMap():
       
    def __init__(self,cmap,N):
 
        self.N = N
        cmapobj =  cm.get_cmap(cmap, N) 
        self.colormap = cmapobj(np.arange(N))
        self.outfile = 'cmap.dat'

    def __str__(self):
        string = ''
        for i in self.colormap:
            for j in range(3):
                string += str(i[j]) + '    '
            string+= '\n'
        return string

    def write(self,fdir='./'):

        f = open(fdir + self.outfile,'w')
        f.write(self.__str__())
        f.close()


if __name__ == "__main__":

    cmap_writer = WriteColorMap('RdYlBu_r',1024)
    cmap_writer.write()

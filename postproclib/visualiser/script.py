
import matplotlib.pyplot as plt
import numpy as np
import sys

sys.path.append(resultdirectory)
import postproclib as ppl

#Get Post Proc Object
PPObj = ppl.MD_PostProc(utlisdirectory)

#Get plotting object
plotObj = PPObj.plotlist[plottype]

#Get profile
x, y = plotObj.profile(axis=0, 
                       startrec=10, 
                       endrec=0)

#Plot only normal component
plt.plot(x,y[0])
plt.show()
                    
        
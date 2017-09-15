import wx
import numpy as np
import matplotlib
import os
#matplotlib.use('WXAgg')
import matplotlib.backends.backend_wxagg as wxaggb
import matplotlib.backends.backend_wx as wxb
import matplotlib.pyplot as plt

class PyplotPanel(wx.Panel):

    def __init__(self, parent,**kwargs):
        wx.Panel.__init__(self,parent,**kwargs)
        self.parent = parent
        self.figure = matplotlib.figure.Figure()
        self.canvas = wxaggb.FigureCanvasWxAgg(self, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.Bind(wx.EVT_SIZE, self.sizeHandler)

        # canvas is your canvas, and root is your parent (Frame, TopLevel, Tk instance etc.)
        #self.zoomhandle = wxaggb.NavigationToolbar2WxAgg(self.canvas)

        #self.toolbar = wxb.NavigationToolbar2Wx(self.canvas) 
        #self.toolbar.Realize()
        #self.toolbar.update()

        self.cmap = matplotlib.cm.RdYlBu_r

    def sizeHandler(self, event):
        self.canvas.SetSize(self.GetSize())

    def redraw_plot(self, ax, data, xlabel=None, ylabel=None):
        self.figure.clf(keep_observers=True)
        self.ax = self.figure.add_subplot(111)
        self.lines = self.ax.plot(ax, data, 'r-o', linewidth=2)
        self.ax.set_xlim(ax.min(), ax.max())
        if (xlabel): self.ax.set_xlabel(xlabel)
        if (ylabel): self.ax.set_ylabel(ylabel)
        self.canvas.draw()

    def redraw_plot_many(self, axs, datas, styles=None, xlabel=None, ylabel=None):
        self.figure.clf(keep_observers=True)
        self.ax = self.figure.add_subplot(111)

        if (styles == None):
            styles = [{}]*len(axs)

        self.lines = [] 
        for ax,data,style in zip(axs,datas,styles):
            line = self.ax.plot(ax, data, **style)
            self.lines.append(line)

        # Maximum and minimum grid values
        maxval = np.max([np.max(ax) for ax in axs])
        minval = np.min([np.min(ax) for ax in axs])
        self.ax.set_xlim(minval,maxval)

        if (xlabel): self.ax.set_xlabel(xlabel)
        if (ylabel): self.ax.set_ylabel(ylabel)
        self.canvas.draw()
   
    def update_plot_many(self, axs, datas):
        for line, ax, data in zip(self.lines, axs, datas):
            plt.setp(line, xdata=ax, ydata=data)
        self.canvas.draw() 
    
    def update_plot(self, ax, data):
        plt.setp(self.lines, xdata=ax, ydata=data)
        self.canvas.draw()

    def set_plot_limits(self,lims):
        self.ax.set_ylim(lims[0], lims[1])
        self.canvas.draw()

    def redraw_contour(self, ax1, ax2, data, xlabel=None, ylabel=None):
        self.figure.clf(keep_observers=True)
        self.ax = self.figure.add_subplot(111)
        self.colormesh = self.ax.pcolormesh(ax1, ax2, data[:,1:], 
                                            cmap=self.cmap)
        self.cbar = self.figure.colorbar(self.colormesh)
        self.ax.set_xlim(ax1.min(), ax1.max())
        self.ax.set_ylim(ax2.min(), ax2.max())
        if (xlabel): self.ax.set_xlabel(xlabel)
        if (ylabel): self.ax.set_ylabel(ylabel)
        self.canvas.draw()

    def update_contour(self, data):
        self.colormesh.set_array(data[:,1:].ravel())
        self.canvas.draw()

    def set_contour_limits(self, lims):
        self.colormesh.set_clim(vmin=lims[0], vmax=lims[1])
        self.canvas.draw()

    def savefigure(self, fpath):
        fs = matplotlib.rcParams.get('font.size')
        matplotlib.rcParams.update({'font.size': 22})
        self.figure.savefig(str(fpath),dpi=300, transparent=True, 
                            bbox_inches='tight', pad_inches=0.1)
        matplotlib.rcParams.update({'font.size': fs})
        self.canvas.draw()

    def writedatacsv(self, fpath):
        ax = self.figure.get_axes()[0]
        print(ax)
        xy = ax.get_lines()[0].get_xydata()
        np.savetxt(fpath, xy, delimiter=",")

    def writescript(self, fpath):
        #print(self.parent.bin,self.parent.rec, self.parent.recwidth, self.parent.binwidth,  self.parent.component,  self.parent.normal,  self.parent.fieldname, self.parent.plottype)

        ppdir = os.path.realpath(__file__)
        inx = ppdir.find('/postproclib')
        ppdir = ppdir[:inx]
        script = self.minimalscript(plottype=self.parent.plottype,
                                    fdir=self.parent.fdir,
                                    ppdir=ppdir, 
                                    fieldname = self.parent.fieldname, 
                                    startrec=self.parent.rec, 
                                    endrec = self.parent.rec+self.parent.recwidth, 
                                    comp = self.parent.component, 
                                    norm = self.parent.normal,
                                    bins = self.parent.bin,
                                    binwidth = self.parent.binwidth)

        with open(fpath,'w+') as f:
            f.write(script)

    def minimalscript(self, plottype, fdir, ppdir, fieldname, 
                      startrec, endrec, comp, norm, bins, binwidth):

        script=r"""
import matplotlib.pyplot as plt
import numpy as np
import sys

ppdir = '{0}'
sys.path.append(ppdir)
import postproclib as ppl

normal ={3}
component={6}
startrec={4}
endrec={5}

#Get Post Proc Object
fdir = '{1}'
PPObj = ppl.MD_PostProc(fdir)
print(PPObj)

#Get plotting object
plotObj = PPObj.plotlist['{2}']
""".format(ppdir, fdir, fieldname, str(comp), str(startrec), str(endrec), str(norm))

        if plottype == "Profile":
            script += r"""
#Get profile
x, y = plotObj.profile(axis=normal, 
           startrec=startrec, 
           endrec=endrec)

#Plot only normal component
fig, ax = plt.subplots(1,1)
ax.plot(x,y[:,component])
plt.show()
"""

        elif plottype == "Contour":
            script += r"""
#Get Contour
naxes = [0,1,2]
naxes.remove(normal)
bins = {0}
binwidth = {1}
binlimits = [None]*3
binlimits[normal] = (bins-binwidth, 
                     bins+binwidth+1) #Python +1 slicing

ax1, ax2, data = plotObj.contour(axes=naxes, 
                                 startrec=startrec,
                                 endrec=endrec,
                                 binlimits=binlimits,
                                 missingrec='returnzeros')

fig, ax = plt.subplots(1,1)
cmap = plt.cm.RdYlBu_r
colormesh = ax.pcolormesh(ax1, ax2, data[:,:,component], 
                                    cmap=cmap)
plt.colorbar(colormesh)
plt.axis('tight')
plt.show()
""".format(str(bins), str(binwidth))
                   
        return script 
        


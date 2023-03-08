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
        try:
            self.canvas = wxaggb.FigureCanvas(self, -1, self.figure)
        except AttributeError:
            self.canvas = wxaggb.FigureCanvasWxAgg(self, -1, self.figure)

            
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.add_toolbar()
        #If we add this, the chart toolbar does not work
        #self.Bind(wx.EVT_SIZE, self.sizeHandler)

        self.cmap = matplotlib.cm.RdYlBu_r

    def add_toolbar(self):

        #Set up Matplotlib Toolbar
        self.chart_toolbar = wxb.NavigationToolbar2Wx(self.canvas)
        tw, th = self.chart_toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        self.chart_toolbar.SetSize(wx.Size(fw, th))
        self.chart_toolbar.Realize()

        self.sizer.Add(self.chart_toolbar, 1, 
                       wx.ALIGN_CENTER | wx.TOP| wx.SYSTEM_MENU | wx.CLOSE_BOX)
        self.sizer.Add(self.canvas, 20, wx.LEFT | wx.BOTTOM | wx.GROW)

        self.SetSizer(self.sizer)
        self.chart_toolbar.update()
        self.canvas.Update()
        self.canvas.Refresh()
        self.Update()

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

        from .minimalscript import minimalscript

        extension = fpath.split(".")[-1]
        if (extension == "py"):
            scripttype = "python"
        elif (extension == "m"):
            scripttype = "matlab"
        else:
            raise ValueError("Script extension shoule be *.py or *.m") 

        script = minimalscript(scripttype=scripttype,
                               plottype=self.parent.plottype,
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

        return

        # script = self.minimalscript(plottype=self.parent.plottype,
                                    # fdir=self.parent.fdir,
                                    # ppdir=ppdir, 
                                    # fieldname = self.parent.fieldname, 
                                    # startrec=self.parent.rec, 
                                    # endrec = self.parent.rec+self.parent.recwidth, 
                                    # comp = self.parent.component, 
                                    # norm = self.parent.normal,
                                    # bins = self.parent.bin,
                                    # binwidth = self.parent.binwidth)

        #with open(fpath,'w+') as f:
        #    f.write(script)

    # def minimalscript(self, plottype, fdir, ppdir, fieldname, 
                      # startrec, endrec, comp, norm, bins, binwidth):

        # script=r"""
# import matplotlib.pyplot as plt
# import numpy as np
# import sys

# ppdir = '{0}'
# sys.path.append(ppdir)
# import postproclib as ppl

# normal ={6}
# component={3}
# startrec={4}
# endrec={5}

# #Get Post Proc Object
# fdir = '{1}'
# PPObj = ppl.All_PostProc(fdir)
# print(PPObj)

# #Get plotting object
# plotObj = PPObj.plotlist['{2}']
# """.format(ppdir, fdir, fieldname, str(comp), str(startrec), str(endrec), str(norm))

        # if plottype == "Profile":
            # script += r"""
# #Get profile
# x, y = plotObj.profile(axis=normal, 
           # startrec=startrec, 
           # endrec=endrec)

# #Plot only normal component
# fig, ax = plt.subplots(1,1)
# ax.plot(x,y[:,component])
# plt.show()
# """

        # elif plottype == "Contour":
            # script += r"""
# #Get Contour
# naxes = [0,1,2]
# naxes.remove(normal)
# bins = {0}
# binwidth = {1}
# binlimits = [None]*3
# binlimits[normal] = (bins-binwidth, 
                     # bins+binwidth+1) #Python +1 slicing

# ax1, ax2, data = plotObj.contour(axes=naxes, 
                                 # startrec=startrec,
                                 # endrec=endrec,
                                 # binlimits=binlimits,
                                 # missingrec='returnzeros')

# fig, ax = plt.subplots(1,1)
# cmap = plt.cm.RdYlBu_r
# colormesh = ax.pcolormesh(ax1, ax2, data[:,:,component], 
                                    # cmap=cmap)
# plt.colorbar(colormesh)
# plt.axis('tight')
# plt.show()
# """.format(str(bins), str(binwidth))
                   
        # return script 
        

try:
    from vispy import visuals, scene
    from postproclib.mdmols import VMDReader

    class VispyPanel(wx.Panel):
        def __init__(self, parent, catch_noresults=True):
            super(VispyPanel, self).__init__(parent)
            self.parent = parent
            self.fdir = parent.fdir
            self.plotexists = False
            self.alpha = 0.5
            self.cmap = matplotlib.cm.RdYlBu_r
            self.canvas = scene.SceneCanvas(app="wx", keys='interactive', size=(800,500), 
                                            dpi=200, bgcolor='w', parent=self)
            box = wx.BoxSizer(wx.VERTICAL)
            box.Add(self.canvas.native, 1, wx.EXPAND | wx.ALL)
            self.SetAutoLayout(True)
            self.SetSizer(box)

        def CreatePlot(self, data, cdata, sizes, connect=None, griddata=False):

            # build visuals
            Mols3D = scene.visuals.create_visual_node(visuals.LinePlotVisual)

            # Add a ViewBox to let the user zoom/rotate
            view = self.canvas.central_widget.add_view()
            view.camera = 'turntable'
            view.camera.azimuth = 360.
            view.camera.elevation = 90.
            view.camera.fov = 0.

            # Scatter
            self.p1 = Mols3D(parent=view.scene)
            self.p1.set_gl_state('translucent', blend=True, depth_test=True)
            if data.shape[0] > 100000:
                self.p1.set_data(data, face_color=cdata, edge_width=0., edge_color=None, 
                                 marker_size=sizes/10., width=2, connect=connect)
            else:
                self.p1.set_data(data, face_color=cdata, edge_color=[0.,0.,0.,self.alpha], 
                                 marker_size=sizes, color=cdata ,width=5, connect=connect)

            #Add a GRID
            if isinstance(griddata, np.ndarray):
                self.p2 = Mols3D(parent=view.scene, marker_size=0.)
                self.p2.set_gl_state('translucent', blend=True, depth_test=True)
                self.p2.set_data(griddata)

            view.camera.set_range()
            self.canvas.show()
            self.plotexists = True

        def set_data(self, data, cdata, sizes, connect=None, griddata=False):

            if data.shape[0] > 100000:
                self.p1.set_data(data, face_color=cdata, edge_width=0., edge_color=None, 
                                 marker_size=sizes/10., width=2, connect=connect)
            else:
                self.p1.set_data(data, face_color=cdata, edge_color=[0.,0.,0.,self.alpha],
                                 marker_size=sizes, color=cdata, width=5, connect=connect)

            #Add a GRID
            if isinstance(griddata, np.ndarray):
                self.p2.set_data(griddata, marker_size=0.)

            self.canvas.update()

        def get_vispy_sizes(self, vmdr, scalefact=5):
            moltypes = vmdr.read_moltype() 
            #Using actual scales based on sigma
#            typeDict = {b"Ar":1.0, b"S":1.2,
#                        b"W":1.0, b"CM":1.0, 
#                        b"EO":1.0, b"T":4.5012/2.9016, 
#                        b"EM":4.022/2.9016, b"OA":3.69/2.9016, 
#                        b"W1":1.0, 
#                        b"M":4.1840/2.9016}
            #Making chains much bigger
            typeDict = {b"Ar":1.0, b"S":1.2,
                        b"W":1.0,  b"W1":1.0,
                        b"CM":3.0, b"EO":3.0, 
                        b"T":3.0,  b"EM":3.0, 
                        b"OA":3.0, b"M":3.0}

            sizes= np.ones(vmdr.n)
            molno = 0; 
            for moltype in moltypes:
                try:
                    sizes[molno] = typeDict[moltype]
                except KeyError:
                    pass
                if (molno == vmdr.n-1):
                    break
                molno += 1

            return sizes*scalefact

        def get_vispy_colours(self, vmdr, component):

            c = vmdr.labels[component]
            colours = np.ones([vmdr.n, 4])
            if (c is "White"):
                pass
            elif (c is "Red"):
                colours[:,1] = 0.2
                colours[:,2] = 0.2
                colours[:,3] = 0.5
            elif (c is "moltype"):
                moltypes = vmdr.read_moltype() 
                typeDict = {b"Ar":[1., 0., 0.], b"S":[1.,1.,1.],
                            b"W":[0.8, 0.8, 1.0], b"CM":[0., 0., 1.], 
                            b"EO":[0., 1., 1.], b"T":[0.0, 0.0, 1.0], 
                            b"EM":[1., 0.75, 0.75], b"OA":[1.0, 0.0, 0.0], 
                            b"W1":[0.8, 0.8, 1.0], 
                            b"M":[0.0, 1.0, 1.0]}
                molno = 0
                for moltype in moltypes:
                    #Convert tag name to colour
                    try:
                        colours[molno,:3] = typeDict[moltype]
#                        if moltype == b"W1":
#                            colours[molno,3] = 0.1
#                        else:
                        colours[molno,3] = self.alpha
                    except KeyError:
                        colours[molno,:3] = self.cmap(float(hash(moltype) % 256) / 256)[:3]
                        colours[molno,3] = self.alpha
                    except IndexError:
                        print(vmdr.n, l)
                    if (molno == vmdr.n-1):
                        break
                    molno += 1

            elif (c is "tag"):

                #Load tag data (assumes same ordering)
                #tagDict = {"free": 0, "fixed": 1, "fixed_slide": 2, "teth": 3, "thermo": 4, 
                #            "teth_thermo": 5, "teth_slide": 6, "teth_thermo_slide": 7}   
                #D = vmdr.read_moldata()
                #D["tag"]
                tags = vmdr.read_tags()
                colours[:,:] = self.cmap(tags/tags.max())

            elif (c in ["v1", "v2", "v3",
                        "globnum", 
                        "potdata1", "potdata2", "potdata3", "potdata4", 
                        "rtrue1", "rtrue2", "rtrue3",
                        "rtether1", "rtether2", "rtether3"]):
                D = vmdr.read_moldata()
                try:
                    if "1" in c or "2" in c or "3" in  c:
                        cb = c[:-1]
                        indx = int(c[-1])-1
                        if cb in D:
                            output = D[cb][:,indx]
                    else:
                        if c in D:
                            output = D[c]

                    colours[:,:] = self.cmap(output/output.max())

                #Return plain case if key not found
                except KeyError:
                    pass
                except UnboundLocalError:
                    pass

            return colours



except ImportError:

    class DummyVispyScene():
        def set_data(self, a, face_color=None):
            pass

    class DummyVispyCanvas():
        def update(self):
            dlg = wx.MessageDialog(parent=None, message="3D not available, install Vispy")
            dlg.ShowModal()
            dlg.Destroy()

    class VispyPanel(wx.Panel):
        def __init__(self, parent):
            super(VispyPanel, self).__init__(parent)
            self.parent = parent
            self.fdir = parent.fdir
            self.pos = np.zeros([1,3,1000])
            self.colours= np.zeros([1,4])
            self.p1 = DummyVispyScene()
            self.canvas = DummyVispyCanvas()
    pass

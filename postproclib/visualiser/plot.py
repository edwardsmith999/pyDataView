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
    from vispy.color import Colormap
    from scipy.io import FortranFile


    class VMDReader:

        def __init__(self, fdir):

            self.fdir = fdir
            self.n = self.read_header()
            self.fname = self.check_files()
            #self.pos = self.read_pos(0, self.steps)
            #self.colours = self.read_colours()

        def read_header(self, headername="/simulation_header"):

            #Load number of molecules data
            fname = self.fdir + headername
            with open(fname,"r") as f:
                for l in f:
                    if "globalnp" in l:
                        n = int(l.split(";")[2])
                        break

            return n

        def check_files(self, dsize=4, ftmp="vmd_temp.dcd", fout="vmd_out.dcd"):

            #Check which MD files are available
            ftmp = self.fdir + "/" + ftmp#"/vmd_temp.dcd"
            fout = self.fdir + "/" + fout#"/vmd_out.dcd"
            #If both, check if temp is newer
            self.use_temp=False
            if (os.path.exists(ftmp) and os.path.exists(fout)):
                if (os.path.getmtime(ftmp) > os.path.getmtime(fout)):
                    self.use_temp=True
            elif (os.path.exists(ftmp)):
                self.use_temp=True

            #Get size of file
            if (self.use_temp):
                filesize = os.path.getsize(ftmp)
                fname = ftmp
                self.mol_data = True
            elif (os.path.exists(fout)):
                filesize = os.path.getsize(fout)
                fname = fout
                self.mol_data = True
            else:
                self.mol_data = False
                self.steps = 0
                return None

             #4 byte single records
            self.steps = int(np.floor(filesize/(3.*self.n*dsize)))

            return fname

        def read_pos(self, start, end):

            if start != 0:
                print("WARNING - NON ZERO START IN READ POS NOT FULLY TESTED")

            steps = end-start
            if (self.mol_data):
                pos = np.zeros([self.n, 3, steps])
            else:
                print("NO DATA FOUND")
                return np.zeros([self.n,3, 1])

            #Tries to load record rec from vmd_temp.dcd or vmd_out.dcd
            #Numpy fromfile does not work on final dcd as insists on using Fortran 
            #unformatted which is an archaic binary format incompatible
            #with stream, etc. Need to keep like this so VMD still works
            #Load data
            read_success = False
            if (self.use_temp):
                offset = 3 * start * self.n
                print("Loading MD data from " + self.fname, " at offset ", offset)
                data = np.fromfile(self.fname, dtype=np.single, offset=offset)

                cntrec = 0
                for rec in range(start, end):
                    si = 3*self.n*(rec-start)
                    ei = 3*self.n*(rec-start+1)
                    print("Loading record ", rec)
                    for ixyz in range(3):
                        pos[:,ixyz,cntrec] = data[si+self.n*ixyz:si+self.n*(ixyz+1)]
                    cntrec += 1
                read_success = True

            elif (os.path.exists(self.fname)):
                print("Loading MD data from " + self.fname)
                with FortranFile(self.fname, 'r') as f:
                    h1 = f.read_record('i4')
                    h2 = f.read_record('i4')
                    Nb = f.read_record('i4')
                    if (Nb[0] != self.n):
                        raise IOError(self.fname + " is not in expected format")

                    #No Seek offered so read and discard up to start
#                    if (start != 0):
#                        for rec in range(start):
#                            pos[:,0,0] = f.read_record('f4')
#                            pos[:,1,0] = f.read_record('f4')
#                            pos[:,2,0] = f.read_record('f4')

                    #Then read data
                    cntrec = 0; datacorrupt = False
                    for rec in range(start, end):
                        for ixyz in range(3):
                            #Corrupted data beyond a point causes TypeError
                            #so best to exit
                            try:
                                data = f.read_record('f4')
                                #Check n to handle case where 
                                #extra record between timesteps
                                if data.size == self.n:
                                    pos[:,ixyz,cntrec] = data
                                else:
                                    print(rec, "Extra record of size = ", data.size, " with N mols = ", self.n)
                                    pos[:,ixyz,cntrec] = f.read_record('f4')
                            except TypeError as e:
                                print("Corruped data at record=", rec, " in " 
                                      + self.fname, " Error is ", e)
                                datacorrupt = True
                        if datacorrupt:
                            break
                        cntrec += 1

                read_success = True

            if (not read_success):
                raise IOError("Failed to read data from" + self.fname)

            return pos



        def read_colours(self, fname="vmd_out.psf"):
                       
            #Load tag data (assumes same ordering)
            #tagDict = {"free": 0, "fixed": 1, "fixed_slide": 2, "teth": 3, "thermo": 4, 
            #            "teth_thermo": 5, "teth_slide": 6, "teth_thermo_slide": 7}     
            cm = Colormap(['r', 'g', 'b'])
            colours = np.ones([self.n, 4])
            typeDict = {"Ar":[1., 0., 0., 1.], "S":[1.,1.,1.,1.]}

            fpsf = self.fdir + "/" +  fname
            if (os.path.exists(fpsf)):
                with open(fpsf) as f:
                    rd = True
                    for l in f:
                        if (rd and "!NATOM" in l):
                            N = int(l.replace("!NATOM",""))
                            rd = False
                            continue
                        elif (rd):
                            continue                   
                        try:
                            molno = int(l.split()[0])-1
                        except IndexError:
                            print("Line not molecules in ", fname, " skipping")
                            continue    
          
                        tag = l.split()[1]
                        #print(molno, tag, N, float(hash(tag) % 256) / 256, cm[float(hash(tag) % 256) / 256].RGBA[0])
                        #Convert tag name to colour
                        try:
                            colours[molno,:] = typeDict[tag]
                        except KeyError:
                            colours[molno,0:3] = cm[float(hash(tag) % 256) / 256].rgb[0]
                        except IndexError:
                            print(self.n, N, l)
                        if (molno == N-1):
                            break

            return colours

    #def get_vmd_data(fdir):



                #maxheadersize =100 #260

#                with open(fout, 'rb') as f:
#                    #print(f.read(headersize))
#                    #f.seek(headersize,os.SEEK_SET)
#                    for i in range(maxheadersize):
#                        Nb = f.read(4)
#                        print(i, Nb, int.from_bytes(Nb, byteorder="little"))
#                        if (int.from_bytes(Nb, byteorder="little") == self.n):
#                            break
#                    self.data = np.fromfile(f, dtype=np.single)


        #return n, steps, pos, colours


    class VispyPanel(wx.Panel):
        def __init__(self, parent, catch_noresults=True):
            super(VispyPanel, self).__init__(parent)
            self.parent = parent
            self.fdir = parent.fdir

            #Load data from VMD object
            self.vmdr = VMDReader(self.fdir)
            self.n = self.vmdr.n
            self.steps = self.vmdr.steps
            self.pos = self.vmdr.read_pos(0, self.steps)
            self.colours = self.vmdr.read_colours()    

            box = wx.BoxSizer(wx.VERTICAL)
            self.canvas = scene.SceneCanvas(app="wx", keys='interactive', size=(800,500), 
                                            dpi=200, bgcolor='w', parent=self)
            box.Add(self.canvas.native, 1, wx.EXPAND | wx.ALL)
            self.SetAutoLayout(True)
            self.SetSizer(box)

            # # build your visuals, that's all
            Scatter3D = scene.visuals.create_visual_node(visuals.MarkersVisual)
            # #Plot3D = scene.visuals.create_visual_node(visuals.LinePlotVisual)

            # Add a ViewBox to let the user zoom/rotate
            view = self.canvas.central_widget.add_view()
            view.camera = 'turntable'
            view.camera.azimuth = 360.
            view.camera.elevation = 90.

            # plot ! note the parent parameter
            #self.p1 = Plot3D(parent=view.scene)
            self.p1 = Scatter3D(parent=view.scene)
            self.p1.set_gl_state('translucent', blend=True, depth_test=True)
            self.p1.set_data(self.pos[:,:,0], face_color=self.colours)#, edge_width=0.5, size=10)#, symbol='o',
                        #edge_width=0.5)#, edge_color='blue')
            view.camera.set_range()
            self.canvas.show()

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

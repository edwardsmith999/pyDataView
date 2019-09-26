# -*- encoding: utf-8 -*-
import wx
from .plot import PyplotPanel
from .choosefield import FieldChooserPanel
from .sliders import RecordSliderPanel

from postproclib.pplexceptions import DataNotAvailable
from postproclib.allpostproc import All_PostProc  
from misclib import unicodetolatex, round_to_n

def showMessageDlg(msg, title='Information', style=wx.OK|wx.ICON_INFORMATION):
    """"""
    dlg = wx.MessageDialog(parent=None, message=msg, 
                           caption=title, style=style)
    dlg.ShowModal()
    dlg.Destroy()


class VisualiserPanel(wx.Panel):
 
    def __init__(self,parent,fdir,**kwargs):

        wx.Panel.__init__(self,parent,**kwargs)

        if (fdir[-1] != '/'): fdir+='/'
        self.fdir = fdir
        self.PP = All_PostProc(self.fdir)

        # Loop through all field classes and try to initialise at least one.
        # As fundametal classes typically return zeros on missing results 
        # while DataNotAvailable error is returned for some complex classes
        for item in list(self.PP.plotlist.items()):
            try:
                #Skip example case as we end up with wrong binlimits
                if ("example" in str(item)):
                    continue
                self.initialise_visuals(item)
                #If successful, use the current object
                # if not then keep trying
                break
            except DataNotAvailable as ValueError:
                pass

    def initialise_visuals(self,item):
        print(('Trying to initialise visuals with ', item))
        self.fieldname, self.field = item
        self.pyplotp = PyplotPanel(self)
        self.choosep = FieldChooserPanel(self)
        self.slidersp = RecordSliderPanel(self)
    
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.choosep, 0, wx.EXPAND | wx.ALL)
        hbox.Add(self.pyplotp, 1, wx.EXPAND | wx.ALL)
        vbox.Add(hbox, 1, wx.EXPAND | wx.ALL)
        vbox.Add(self.slidersp, 0, wx.EXPAND | wx.ALL)
        self.SetSizer(vbox)

        self.set_bindings()
        self.set_defaults()


    def set_defaults(self):

        self.autoscale = False
        self.update_components()
        self.update_normals()
        self.component = 0
        self.normal = 0
        self.plottype = "Profile"

        self.maxbin = len(self.field.grid[self.normal])-1
        self.maxrec = self.field.Raw.maxrec
        self.bin = int(float(self.maxbin)/2.)
        self.rec = int(float(self.maxrec)/2.)
        self.recwidth = 0
        self.binwidth = 0

        self.slidersp.recslider.SetMax(self.maxrec)
        self.slidersp.binslider.SetMax(self.maxbin)
        self.slidersp.binslider.SetValue(self.bin)
        self.slidersp.recslider.SetValue(self.rec)

        self.redraw = self.redraw_plot
        self.update = self.update_plot
        self.set_limits = self.set_plot_limits
        self.toggle_binslider("Off")
        self.redraw()

        #Attempt to create a custom event to set initial value
        #import wx.lib.newevent
        #SomeNewEvent, EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent()
        #evt = SomeNewEvent(GetString=lambda : unicode(self.fieldname))
        #self.handle_fieldtype(evt)

        #Set radio box to initial value
        for i, k in enumerate(sorted(self.PP.plotlist.keys())):
            if k == self.fieldname:    
                self.choosep.fieldtype_p.fieldradiobox.SetSelection(i)
                break

    def set_bindings(self):

        self.Bind(wx.EVT_RADIOBOX, self.handle_plottype, 
                  self.choosep.plottype_p.fieldradiobox)
        self.Bind(wx.EVT_RADIOBOX, self.handle_fieldtype, 
                  self.choosep.fieldtype_p.fieldradiobox)
        self.Bind(wx.EVT_COMBOBOX, self.handle_component, 
                  self.choosep.component_p.componentcombobox)
        self.Bind(wx.EVT_COMBOBOX, self.handle_normal, 
                  self.choosep.component_p.normalcombobox)
        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.handle_recslider, 
                  self.slidersp.recslider.slider)
        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.handle_binslider, 
                  self.slidersp.binslider.slider)
        self.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.handle_recslider, 
                  self.slidersp.recslider.slider)
        self.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.handle_binslider, 
                  self.slidersp.binslider.slider)
        self.Bind(wx.EVT_TEXT_ENTER, self.handle_rectxt,
                  self.slidersp.recslider.slidertext)
        self.Bind(wx.EVT_TEXT_ENTER, self.handle_bintxt,
                  self.slidersp.binslider.slidertext)

        self.Bind(wx.EVT_SPINCTRL, self.handle_recspin,
                  self.slidersp.recslider.spin)
        self.Bind(wx.EVT_SPINCTRL, self.handle_binspin,
                  self.slidersp.binslider.spin)

        self.Bind(wx.EVT_CHECKBOX, self.handle_autoscale, 
                  self.choosep.autoscale_b) 
        self.Bind(wx.EVT_TEXT_ENTER, self.handle_minscale, 
                  self.choosep.minpspin) 
        self.Bind(wx.EVT_TEXT_ENTER, self.handle_maxscale, 
                  self.choosep.maxpspin) 

        self.choosep.save_b.Bind(wx.EVT_BUTTON, 
                                 lambda event: self.save_dialogue(event, 'fig.png'))
        self.choosep.save_d.Bind(wx.EVT_BUTTON, 
                                 lambda event: self.save_dialogue(event, 'data.csv'))
        self.choosep.save_s.Bind(wx.EVT_BUTTON, 
                                 lambda event: self.save_dialogue(event, 'script.py'))

    def save_dialogue(self, event, defaultFile):
        dlg = wx.FileDialog(self, defaultDir='./', defaultFile=defaultFile,
                            style=wx.FD_SAVE) 
        if (dlg.ShowModal() == wx.ID_OK):
            fpath = dlg.GetPath()
        dlg.Destroy()

        #Check if defined, if cancel pressed then return
        try:
            fpath
        except NameError:
            return

        if defaultFile == 'fig.png':
            try:
                print(('Saving figure as ' + fpath))
                self.pyplotp.savefigure(fpath)
                print('Saved.')
            except ValueError:
                raise
        elif defaultFile == 'data.csv':
            print(('Writing data as ' + fpath))
            self.pyplotp.writedatacsv(fpath)
            print('Finished.')
        elif defaultFile == 'script.py':
            self.pyplotp.writescript(fpath)

        #Output error as dialogue
        #import sys
        #exc_info = sys.exc_info()
        #print(exc_info, dir(exc_info), type(exc_info))
        #showMessageDlg(exc_info[1])


    def handle_plottype(self, event):
        plottype = event.GetString()
        self.plottype = plottype
        if plottype == 'Profile':
            self.redraw = self.redraw_plot
            self.update = self.update_plot
            self.set_limits = self.set_plot_limits
            self.toggle_binslider("Off")
            self.toggle_button("On")
        elif plottype == 'Contour':
            self.redraw = self.redraw_contour
            self.update = self.update_contour
            self.set_limits = self.set_contour_limits
            self.toggle_binslider("On")
            self.toggle_button("Off")
        elif plottype == 'CPL':
            self.redraw = self.redraw_cpl_plot
            self.update = self.update_cpl_plot
            self.toggle_binslider("Off")
            self.toggle_button("Off")
        #else: 
            #try:
            #    from mayavi import mlab
            #except ImportError:
            #    self.showMessageDlg("3D plotting requires mayavi to be installed",
            #                        "Information", wx.OK|wx.ICON_INFORMATION)
        else:
            quit("Error in plotype specified")

        self.redraw()

    def handle_fieldtype(self, event):
        ftype = unicodetolatex(event.GetString())
        if (self.field == self.PP.plotlist[ftype]):
            pass
        else:
            self.field = self.PP.plotlist[ftype]
            self.fieldname = ftype
        self.update_components()
        self.update_normals(self.normal)

        self.maxbin = len(self.field.grid[self.normal]) - 1
        self.maxrec = self.field.Raw.maxrec
        self.slidersp.recslider.slider.SetMax(self.maxrec)
        self.slidersp.binslider.slider.SetMax(self.maxbin)
        if (self.rec > self.maxrec):
            self.SetRecord(self.maxrec)
        if (self.bin > self.maxbin):
            self.SetBin(self.maxbin)

        self.redraw()

    def update_components(self):
        self.choosep.component_p.componentcombobox.Clear()
        try:
            self.choosep.component_p.componentcombobox.AppendItems(self.field.labels)
        except AttributeError:
            self.choosep.component_p.componentcombobox.AppendItems(
                [str(x) for x in range(self.field.nperbin)])

        try:
            #Set component to zero if existing one is too large
            #print("Check", len(self.field.labels), self.component, self.prev_component)
            if (len(self.field.labels) < self.component+1):
                self.prev_component = self.component
                #print("Saving previous component", self.component)
                self.component = 0
            elif (len(self.field.labels) > self.prev_component and
                self.prev_component != self.component):
                #print("loading previous component", self.prev_component)
                self.component = self.prev_component

        except AttributeError:
            #Define component to 0 if doesn't exist
            self.prev_component = 0
            self.component = 0
            #print("Reset to zero")
        self.choosep.component_p.componentcombobox.SetSelection(self.component)

    def update_normals(self,normal=0):
        self.choosep.component_p.normalcombobox.Clear()
        try:
            self.choosep.component_p.normalcombobox.AppendItems(self.field.axislabels)
        except AttributeError:
            self.choosep.component_p.normalcombobox.AppendItems(['0','1','2'])
        self.normal = normal
        self.choosep.component_p.normalcombobox.SetSelection(self.normal)

    def handle_component(self, event):
        self.component = event.GetInt()
        self.prev_component = self.component
        #print("Handle")
        self.redraw()

    def handle_normal(self, event):
        self.normal = event.GetInt()
        self.maxbin = len(self.field.grid[self.normal]) - 1
        self.slidersp.binslider.SetMax(self.maxbin) 
        if (self.bin > self.maxbin):
            self.SetBin(self.maxbin)
        self.redraw()

    def handle_autoscale(self,event):
        self.autoscale = event.GetInt()
        self.redraw()

    def handle_minscale(self, event):
        self.minp = float(event.GetString())
        self.maxp = float(self.choosep.maxpspin.GetValue())
        self.choosep.minpspin.SetValue(event.GetString())
        self.set_limits([self.minp,self.maxp])

    def handle_maxscale(self, event):
        self.minp = float(self.choosep.minpspin.GetValue())
        self.maxp = float(event.GetString())
        self.choosep.maxpspin.SetValue(event.GetString())
        self.set_limits([self.minp,self.maxp])

    def handle_recslider(self, event):
        self.SetRecord(event.GetInt())

    def handle_rectxt(self, event):
        rec = int(event.GetString())
        if (rec > self.maxrec):
            self.SetRecord(self.maxrec)
        else:
            self.SetRecord(rec)

    def handle_recspin(self, event):
        width = event.GetInt()
        self.SetRecordWidth(width)

    def handle_binslider(self, event):
        self.SetBin(event.GetInt()) 

    def handle_bintxt(self, event):
        bin = int(event.GetString())
        if (bin > self.maxbin):
            self.SetBin(self.maxbin)
        else:
            self.SetBin(bin)

    def handle_binspin(self, event):
        width = event.GetInt()
        self.SetBinWidth(width)

    def SetRecord(self, rec):
        self.rec = rec
        if (self.rec + self.recwidth > self.maxrec):
            self.rec = self.maxrec-self.recwidth
        elif (self.rec - self.recwidth < 0):
            self.rec = self.recwidth
        self.slidersp.recslider.SetValue(self.rec)
        if self.autoscale:
            self.redraw()
        else:
            self.update()

    def SetRecordWidth(self, width):
        self.recwidth = width
        if (self.recwidth > self.maxrec/2):
            self.recwidth = self.maxrec/2
            self.SetRecord(self.maxrec/2)
        self.SetRecord(self.rec)

    def SetBin(self, bin):
        self.bin = bin
        if (self.bin + self.binwidth > self.maxbin):
            self.bin = self.maxbin - self.binwidth
        elif (self.bin - self.binwidth < 0):
            self.bin = self.binwidth
        self.slidersp.binslider.SetValue(self.bin)
        if self.autoscale:
            self.redraw()
        else:
            self.update()

    def SetBinWidth(self, width):
        self.binwidth = width
        if (self.binwidth > self.maxbin/2):
            self.binwidth = self.maxbin/2
            self.SetBin(self.maxbin/2)
        self.SetBin(self.bin)

    # Below this point are the data updating/plotting routines

    def get_contour_data(self):
        naxes = [0,1,2]
        naxes.remove(self.normal)
        binlimits = [None]*3
        binlimits[self.normal] = (self.bin-self.binwidth, 
                                  self.bin+self.binwidth+1)#Python +1 slicing
        ax1, ax2, data = self.field.contour(axes=naxes, 
                                            startrec=self.rec-self.recwidth,
                                            endrec=self.rec+self.recwidth,
                                            binlimits=binlimits,
                                            missingrec='returnzeros')
        return ax1, ax2, data[:,:,self.component], naxes

    def get_plot_data(self):
        ax, data = self.field.profile(self.normal, 
                                      startrec=self.rec-self.recwidth, 
                                      endrec=self.rec+self.recwidth, 
                                      missingrec='returnzeros')
        return ax, data[:,self.component]

    def get_cpl_plot_data(self):
        (md_ax, md_data, cfd_ax, cfd_data, md_ax_cnst, md_data_cnst, 
         cfd_ax_bc, cfd_data_bc) = self.field.profile_both_cnstinfo(self.normal, 
                                      startrec=self.rec-self.recwidth, 
                                      endrec=self.rec+self.recwidth, 
                                      missingrec='returnzeros')
        axs = [md_ax, cfd_ax, md_ax_cnst, cfd_ax_bc]
        datas = [md_data[:,self.component], cfd_data[:,self.component],
                 md_data_cnst[:,self.component], cfd_data_bc[:,self.component]]
        return axs, datas

    def redraw_plot(self):
        ax, data = self.get_plot_data()
        xlabel = self.field.axislabels[self.normal] 
        ylabel = self.fieldname + "_" + self.field.labels[self.component] 
        self.pyplotp.redraw_plot(ax, data, xlabel, ylabel)
        
        # Set min/max text values
        self.minp, self.maxp = self.pyplotp.ax.get_ylim()
        self.choosep.minpspin.SetValue(str(round_to_n(self.minp,3)))
        self.choosep.maxpspin.SetValue(str(round_to_n(self.maxp,3)))
        #self.post_string_event(wx.EVT_TEXT_ENTER,self.round_to_n(self.minp,6),self.choosep.minpspin)
        #self.post_string_event(wx.EVT_TEXT_ENTER,self.round_to_n(self.maxp,6),self.choosep.maxpspin)
        self.Refresh()

    def update_plot(self):
        ax, data = self.get_plot_data()
        self.pyplotp.update_plot(ax, data)
        self.Refresh()

    def set_plot_limits(self, lims):
        self.pyplotp.set_plot_limits(lims)

    def redraw_cpl_plot(self):
        axs, datas = self.get_cpl_plot_data()
        xlabel = self.field.axislabels[self.normal] 
        ylabel = self.fieldname + "_" + self.field.labels[self.component] 
        styles = [{'marker':'o','mec':'none', 'ms':5.0, 'color':'b', 
                   'label':'MD'},#,'linestyle':'none'},
                  {'marker':'x','color':'g', 'mew':2.0, 'ms':5.0, 
                   'label':'CFD'},
                  {'marker':'o','mec':'none', 'ms':5.0, 'color':'r', 
                   'alpha':0.6, 'label':'MD const'},#,'linestyle':'none'},
                  {'marker':'o','linestyle':'none','mec':'g','mfc':'none',
                   'ms':10.0, 'mew':2.0, 'label':'CFD const'}]
        self.pyplotp.redraw_plot_many(axs, datas, styles, xlabel, ylabel)
        self.Refresh()

    def update_cpl_plot(self):
        axs, datas = self.get_cpl_plot_data()
        self.pyplotp.update_plot_many(axs, datas)
        self.Refresh()

    def redraw_contour(self):
        ax1, ax2, data, naxes = self.get_contour_data()
        xlabel = naxes[0]
        ylabel = naxes[1]
        self.pyplotp.redraw_contour(ax1, ax2, data, xlabel, ylabel)
        # Set min/max contour values
        self.minp,self.maxp = self.pyplotp.colormesh.get_clim()
        self.choosep.minpspin.SetValue(str(round_to_n(self.minp,3)))
        self.choosep.maxpspin.SetValue(str(round_to_n(self.maxp,3)))
        #self.post_string_event(wx.EVT_TEXT_ENTER,self.round_to_n(self.minp,6),self.choosep.minpspin)
        #self.post_string_event(wx.EVT_TEXT_ENTER,self.round_to_n(self.maxp,6),self.choosep.maxpspin)
        self.Refresh()

    def update_contour(self):
        ax1, ax2, data, naxes = self.get_contour_data()
        self.pyplotp.update_contour(data)
        self.Refresh()

    def set_contour_limits(self, lims):
        self.pyplotp.set_contour_limits(lims)

    def toggle_binslider(self,switchon):
        slider = self.slidersp.binslider
        if (switchon == "On"):
            slider.Enable(True)
        elif(switchon == "Off"):
            slider.SetValue(0)
            slider.Enable(False)
            slider.SetTransparent(10)
        else:
            quit("Error - toggle_position_slider must be str On of Off")

    def toggle_button(self, switchon):
        button = self.choosep.save_d
        if (switchon == "On"):
            button.Enable(True)
        elif(switchon == "Off"):
            button.Enable(False)
            button.SetTransparent(10)
        else:
            quit("Error - button must be str On of Off")

    def post_string_event(self, eventtype, eventval, panel):
        """
            Triggers an event 
        """
        event = wx.PyCommandEvent(eventtype.typeId, panel.GetId())
        event.SetString(str(eventval))
        wx.PostEvent(self.GetEventHandler(),event)


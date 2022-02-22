import wx
import wx.lib.scrolledpanel as scrolled

from misclib import latextounicode

class PlotTypePanel(wx.Panel):

    def __init__(self,parent,**kwargs):
        wx.Panel.__init__(self,parent,**kwargs)
        choices = ['Profile','Contour','Molecules']
        self.radiobox = wx.RadioBox(self,label='Plot Type',    
                                    style=wx.RA_SPECIFY_COLS,
                                    choices=choices)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.radiobox, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(vbox)

class FieldTypePanel(scrolled.ScrolledPanel):

    def __init__(self,parent,**kwargs):
        scrolled.ScrolledPanel.__init__(self, parent,**kwargs)

        choices = latextounicode(sorted(parent.parent.PP.plotlist.keys()))
        self.fieldradiobox = wx.RadioBox(self,label='Field',    
                                    style=wx.RA_SPECIFY_ROWS,
                                    choices=choices)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.fieldradiobox, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(vbox)
        self.SetAutoLayout(1)
        self.SetupScrolling(scroll_x=False, scrollToTop=False)

        #Fix to prevent jump to top when select
        self.Bind(wx.EVT_CHILD_FOCUS, self.on_focus)

    def on_focus(self,event):
        pass

class MolTypePanel(scrolled.ScrolledPanel):

    def __init__(self,parent,**kwargs):
        scrolled.ScrolledPanel.__init__(self, parent,**kwargs)

        #This will be moved to a top level MD data collector
        #import glob
        #choices = "final_state" + glob.glob("*.dcd") + glob.glob("*.xyz")
        #choices = ["final_state", "all_clusters.xyz", "vmd_out.dcd", "vmd_temp.dcd"]
        choices = sorted(parent.parent.MM.plotlist.keys())
        self.molradiobox = wx.RadioBox(self,label='Molecule Files',    
                                    style=wx.RA_SPECIFY_ROWS,
                                    choices=choices)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.molradiobox, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(vbox)
        self.SetAutoLayout(1)
        self.SetupScrolling(scroll_x=False, scrollToTop=False)

        #Fix to prevent jump to top when select
        self.Bind(wx.EVT_CHILD_FOCUS, self.on_focus)

    def on_focus(self,event):
        pass


class SaveFigurePanel(wx.Panel):

    def __init__(self,parent,**kwargs):
        wx.Panel.__init__(self,parent,**kwargs)
        self.savebutton = wx.Button(self,-1,"Save Fig")

class SaveDataPanel(wx.Panel):

    def __init__(self,parent,**kwargs):
        wx.Panel.__init__(self,parent,**kwargs)
        self.savebutton = wx.Button(self,-1,"Save Data")

class SaveScriptPanel(wx.Panel):

    def __init__(self,parent,**kwargs):
        wx.Panel.__init__(self,parent,**kwargs)
        self.savebutton = wx.Button(self,-1,"Save Script")


class FieldComponentPanel(wx.Panel):
    
    def __init__(self,parent,**kwargs):
        wx.Panel.__init__(self,parent,**kwargs)

        self.componenttitle = wx.StaticText(self,-1,label='Component',size=(100,-1))
        self.componentcombobox = wx.ComboBox(self, size=(10,-1), value='0')

        choices = ['0','1','2']
        self.normaltitle = wx.StaticText(self,-1,label='Normal', size=(100,-1))
        self.normalcombobox = wx.ComboBox(self, choices=choices, size=(10,-1), 
                                          value='0')

        grid = wx.GridBagSizer(hgap=3)
        grid.Add(self.componenttitle,    (0,0), flag=wx.EXPAND)
        grid.Add(self.componentcombobox, (1,0), flag=wx.EXPAND)
        grid.Add(self.normaltitle,       (0,1), flag=wx.EXPAND)
        grid.Add(self.normalcombobox,    (1,1), flag=wx.EXPAND)
        grid.AddGrowableCol(0)
        grid.AddGrowableCol(1)
        self.SetSizer(grid)


class FieldChooserPanel(wx.Panel):
    
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.parent = parent 
        # Plot type chooser box
        self.plottype_p = PlotTypePanel(self)    
        # Field type chooser box
        self.fieldtype_p = FieldTypePanel(self, size = (-1, 340))
        self.moltype_p = MolTypePanel(self, size = (-1, 340))
        self.moltype_p.Hide()
        # Component chooser combo box
        self.component_p = FieldComponentPanel(self)
        # Autoscale button
        self.autoscale_b = wx.CheckBox(self,-1,label='Autoscale')
        # Min and max values for autoscale
        self.minpspin = wx.TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(70,-1))
        self.maxpspin = wx.TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(70,-1))
        # Save buttons (figure, data, script)
        self.save_b = SaveFigurePanel(self)
        self.save_d = SaveDataPanel(self)
        self.save_s = SaveScriptPanel(self)

        # Sizer
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.plottype_p, 0,wx.EXPAND, 0)
        vbox.Add(self.fieldtype_p,0,wx.EXPAND, 0)
        vbox.Add(self.moltype_p,0,wx.EXPAND, 0)
        vbox.Add(self.component_p,0,wx.EXPAND, 0)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(hbox,0,wx.EXPAND, 0)
        hbox.Add(self.autoscale_b,0,wx.EXPAND, 0)
        hbox.Add(self.minpspin,0,wx.EXPAND, 0)
        hbox.Add(self.maxpspin,0,wx.EXPAND, 0)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(hbox,0,wx.EXPAND, 0)

        #label = wx.StaticText(self, 0, 'Save', (20, 20))
        #hbox.Add(label,           0,wx.EXPAND, 0)
        hbox.Add(self.save_b,     0,wx.EXPAND, 0)
        hbox.Add(self.save_d,     0,wx.EXPAND, 0)
        hbox.Add(self.save_s,     0,wx.EXPAND, 0)
        self.SetSizer(vbox) 

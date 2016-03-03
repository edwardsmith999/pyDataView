import wx
import os

class DirectoryChooserPanel(wx.Panel):
    
    def __init__(self,parent,fdir,**kwargs):

        wx.Panel.__init__(self,parent,**kwargs) 

        self.fdir = fdir
        statictxt = wx.StaticText(self,-1,label='File directory: ')
        self.textctrl = wx.TextCtrl(self,-1,self.fdir,style=wx.TE_PROCESS_ENTER)
        self.changebutton = wx.Button(self,-1,"...")

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(statictxt,0,wx.ALIGN_CENTER_VERTICAL| wx.LEFT,5)
        hbox.Add(self.textctrl,1,wx.EXPAND,0)
        hbox.Add(self.changebutton,0,wx.EXPAND)
        self.SetSizer(hbox)

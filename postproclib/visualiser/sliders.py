import wx
import numpy as np

class SliderPlusWidth(wx.Panel):
    
    def __init__(self,parent,slidername,**kwargs):

        wx.Panel.__init__(self,parent,**kwargs)
        sliderlabel = wx.StaticText(self,-1,label=slidername+':',size=(50,-1))
        self.slidertext = wx.TextCtrl(self,-1,style=wx.TE_PROCESS_ENTER,
                                      size=(50,-1))
        self.slider = JumpSlider(self)
        #self.slider = wx.Slider(self)
        spintext = wx.StaticText(self,-1,label=u"\u00B1",size=(10,-1))
        self.spin = wx.SpinCtrl(self,value='0',initial=0,size=(50,-1))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(sliderlabel,0,wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        hbox.Add(self.slidertext,0,wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        hbox.Add(self.slider,1,wx.EXPAND,0)
        hbox.Add(spintext,0,wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        hbox.Add(self.spin,0,wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox,1,wx.EXPAND,0)
        self.SetSizer(vbox) 
        self.SetValue(0)

    def SetValue(self,pos):
        self.slidertext.SetValue(str(pos))
        self.slider.SetValue(pos)
   
    def GetValue(self):
        return self.slider.GetValue() 

    def SetMax(self,maximum):
        self.slider.SetMax(maximum)
        self.spin.SetRange(0,maximum/2)

class RecordSliderPanel(wx.Panel):

    def __init__(self,parent,**kwargs):

        wx.Panel.__init__(self,parent,**kwargs)

        self.binslider = SliderPlusWidth(self, 'Bin')
        self.recslider = SliderPlusWidth(self, 'Rec')

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.binslider,1,wx.EXPAND,0)
        vbox.Add(self.recslider,1,wx.EXPAND,0)
        self.SetSizer(vbox)

class JumpSlider(wx.Slider):
    """
        Slider which jumps to location of click
        Mouse click is bound to slider so
        location is set by clicking somewhere. 
    """
    def __init__(self, parent, gap=12, *args, **kwargs):
        wx.Slider.__init__(self, parent, *args, **kwargs)
        self.gap = gap
        self.parent = self.GetParent() 
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)

    def linapp(self, x1, x2, y1, y2, x):
        return (float(x - x1) / (x2 - x1)) * (y2 - y1) + y1

    def post_slide_event(self,eventval):
        """
            Updated positions triggers an
            event to let the parent know scroll 
            position has been changed 
        """
        event = wx.PyCommandEvent(wx.EVT_COMMAND_SCROLL_CHANGED.typeId, self.GetId())
        event.SetInt(eventval)
        wx.PostEvent(self.GetEventHandler(),event)

    def OnClick(self, e):
        click_min = self.gap
        click_max = self.GetSize()[0] - self.gap
        click_position = e.GetX()
        result_min = self.GetMin()
        result_max = self.GetMax()
        if click_position > click_min and click_position < click_max:
            result = self.linapp(click_min, click_max, 
                                 result_min, result_max, 
                                 click_position)
        elif click_position <= click_min:
            result = result_min
        else:
            result = result_max
        #Round to nearest integer using numpy 
        result = int(np.round(result))
        self.parent.SetValue(result)
        self.post_slide_event(result)
        e.Skip()


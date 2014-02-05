#!/usr/bin/env python
# coding=utf-8
'''
Created on 4 Feb 2014

@author: Jamie Bull
'''

from math import floor
import wmi
import winsound
import wx
#from lifesaver.balloon_task_bar import BalloonTaskBarIcon
from balloon_task_bar import BalloonTaskBarIcon

import icons

class BatteryMonitor:
    
    def __init__(self):
        self.c = wmi.WMI()
        self.t = wmi.WMI(moniker = "//./root/wmi")
        self.unplug_alert_enabled = True
        self.PLUGIN_LEVEL = 0.4
        self.UNPLUG_LEVEL = 0.8
        
    @property
    def icon(self):
        charge = self.percentage_charge_remaining * 100
        charge = int(floor(charge/20)*20) # round down to nearest multiple of 20
        if self.plugged_in:
            return icons.icons["%s%03d" % ("battery_charging_", charge)]
        else:
            return icons.icons["%s%03d" % ("battery_discharging_", charge)]
                    
    @property
    def plugged_in(self):
        batts = self.t.ExecQuery('Select * from BatteryStatus where Voltage > 0')
        for _i, b in enumerate(batts):
            if b.PowerOnline:
                return True
    
    @property
    def fully_charged(self):
        return self.percentage_charge_remaining >= 1.0    
    
    @property
    def design_capacity(self):
        capacity = 0
        batts = self.c.CIM_Battery(Caption = 'Portable Battery')
        for _i, b in enumerate(batts):
            capacity += (b.DesignCapacity or 0)
        return capacity 

    @property
    def full_charge_capacity(self):
        capacity = 0
        batts = self.t.ExecQuery('Select * from BatteryFullChargedCapacity')
        for _i, b in enumerate(batts):
            capacity += (b.FullChargedCapacity or 0)
        return capacity 

    @property
    def remaining_capacity(self):
        capacity = 0
        batts = self.t.ExecQuery('Select * from BatteryStatus where Voltage > 0')
        for _i, b in enumerate(batts):
            capacity += (b.RemainingCapacity or 0)            
        return capacity 

    @property
    def percentage_charge_remaining(self):        
        charge = float(self.remaining_capacity) / float(self.full_charge_capacity)
        return charge
        
    def charge_to_full(self, e):
        print "charging to full"
        self.unplug_alert_enabled = False
    
    def should_unplug(self):
        return (self.percentage_charge_remaining > self.UNPLUG_LEVEL and
                self.plugged_in and
                self.unplug_alert_enabled)
        
    def should_plug_in(self):
        return (self.percentage_charge_remaining < self.PLUGIN_LEVEL and
                not self.plugged_in)
        
ID_FULL_CHARGE = wx.NewId()

class BatteryTaskBarIcon(BalloonTaskBarIcon):
    
    def __init__(self,
                 tray_object,
                 tooltip,
                 ):
        wx.TaskBarIcon.__init__(self)
        
        self.tray_object = tray_object
        self.icon = self.tray_object.icon.GetIcon()
        self.tooltip = tooltip
        self.SetIcon(self.icon, self.tooltip)
        self.CreateMenu()
        
        self.Update()
        
    def Update(self):
        self.RefreshIcon()
        self.CheckBalloons()
        self.CheckForFullCharge()
        wx.CallLater(10000, self.Update)
    
    def CheckForFullCharge(self):
        if self.tray_object.fully_charged:
            self.ShowBalloon("Fully charged",
                             "Your battery is now charged to 100%.")
    
    def CheckBalloons(self):
        charge = self.tray_object.percentage_charge_remaining
        if self.tray_object.should_unplug():
            self.ShowBalloon("Unplug charger",
                             "Battery is charged to %i%%. Unplug your charger now to maintain battery life." % (charge * 100))
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        if self.tray_object.should_plug_in():
            self.ShowBalloon("Plug in charger",
                             "Battery is charged to %i%%. Plug in your charger now to maintain battery life." % (charge * 100))
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    
    def RefreshIcon(self):
        self.icon = self.tray_object.icon.GetIcon()
#        self.icon.LoadFile(self.tray_object.icon, type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon, self.tooltip)        
        
    def CreateMenu(self):

        self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.OnPopup)
        
        self.menu = wx.Menu()
        
        self.menu.Append(ID_FULL_CHARGE, '&Charge to full', 'Fully charge without showing alerts')
        self.menu.Append(wx.ID_EXIT, '&Quit', 'Quit application')

        self.Bind(wx.EVT_MENU, self.tray_object.charge_to_full, id=ID_FULL_CHARGE)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=wx.ID_EXIT)
        

    def OnQuit(self, e):
        print "Quitting"
        self.Destroy()
        
    def OnPopup(self, event):
        self.PopupMenu(self.menu)


def main():
    bm = BatteryMonitor()
    tooltip = "Battery life-preserver - beta"
    
    app = wx.App(False)
    BatteryTaskBarIcon(bm, tooltip)
    
    app.MainLoop()

if __name__ == '__main__':
    main()
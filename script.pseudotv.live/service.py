import os
import xbmc, xbmcgui, xbmcaddon

from time import sleep

timer_amounts = {}
timer_amounts['0'] = 0            
timer_amounts['1'] = 5           
timer_amounts['2'] = 10            
timer_amounts['3'] = 15
timer_amounts['4'] = 20

ADDON_ID = 'script.pseudotv.live'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
IDLE_TIME = int(timer_amounts[REAL_SETTINGS.getSetting('timer_amount')])
Msg = REAL_SETTINGS.getSetting('notify')
Enabled = REAL_SETTINGS.getSetting('Auto_Start')

# start service
def Notify():
    if (Msg == 'true'):
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
        xbmc.log("AUTOSTART PTVL: Notifications Enabled...")
    else:
        xbmc.log("AUTOSTART PTVL: Notifications Disabled...")

def autostart():
    Notify()
    sleep(IDLE_TIME)
    xbmc.executebuiltin("XBMC.RunScript(special://home/addons/script.pseudotv.live-master/default.py)")
    xbmc.executebuiltin("XBMC.RunScript(special://home/addons/script.pseudotv.live/default.py)")
    xbmc.log("AUTOSTART PTVL: Service Started...")

if (Enabled == 'true'):
    autostart()
    
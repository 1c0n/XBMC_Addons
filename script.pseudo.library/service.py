#   Copyright (C) 2013 Lunatixz
#
#
# This file is part of PseudoLibrary.
#
# PseudoLibrary is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoLibrary is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoLibrary.  If not, see <http://www.gnu.org/licenses/>.


import os, datetime, _strptime, shutil
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from library import *
from time import sleep
from datetime import date
from datetime import timedelta

SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
THUMB = REAL_SETTINGS.getAddonInfo('icon')
library = library()


def CHKSettings():
    print 'CHKSettings'
    #create missing settings2.xml
    config = xbmc.translatePath(SETTINGS_LOC)
    Settings2 = config + '/settings2.xml'
    if not xbmcvfs.exists(Settings2):
        try:
            f = open(Settings2, 'w')
            f.write("Genre|Type|Source/Path|Exclusion|Limit|1|Name\n")
            f.close
        except:
            pass

            
def AutomaticUpdate():
    print 'AutomaticUpdate'
    Delay_INT = [0,5,10,15,20]
    Update_Delay = Delay_INT[int(REAL_SETTINGS.getSetting('Automatic_Update_Delay'))]
    sleep(Update_Delay)
    
    while not xbmc.abortRequested:

        if REAL_SETTINGS.getSetting('Automatic_Update') == 'true':
            now = datetime.datetime.today()
            Refresh_INT = [2,4,6,12,24,48,72]
            Update_Refresh = Refresh_INT[int(REAL_SETTINGS.getSetting('Automatic_Update_Time'))]

            # try:
            Update_Timer_LastRun = REAL_SETTINGS.getSetting('Update_Timer_NextRun')
            Update_Timer_LastRun = Update_Timer_LastRun.split('.')[0]
            Update_Timer_LastRun = datetime.datetime.strptime(Update_Timer_LastRun, '%Y-%m-%d %H:%M:%S')
            # except:
                # Update_Timer_LastRun = now
                # pass
                
            if now >= Update_Timer_LastRun:
                Update = True
                if REAL_SETTINGS.getSetting('Automatic_Update_Run') == 'false':
                    if xbmc.Player().isPlaying():
                        Update = False

                if Update == True:
                    if REAL_SETTINGS.getSetting('SanityCheck') == 'false':
                        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoLibrary", "Background Service Starting", 4000, THUMB) )

                        # Clear Folder
                        if REAL_SETTINGS.getSetting("Automatic_Clear_Folder") == "true":
                            REAL_SETTINGS.setSetting("Clear_Folder","true")
                        
                        library.readSettings(SETTINGS_LOC, True)
                        Update_Timer_NextRun = (Update_Timer_LastRun + datetime.timedelta(hours=Update_Refresh))
                        print 'Update_Timer_LastRun', now
                        print 'Update_Timer_NextRun', Update_Timer_NextRun
                        REAL_SETTINGS.setSetting("Update_Timer_NextRun",str(Update_Timer_NextRun))
                        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoLibrary", "Background Service Complete", 4000, THUMB) )

        xbmc.sleep(4000)
        
REAL_SETTINGS.setSetting("SanityCheck","false")  
CHKSettings()
AutomaticUpdate()
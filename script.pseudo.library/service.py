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


import os, shutil, datetime, random
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from library import *

SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
THUMB = REAL_SETTINGS.getAddonInfo('icon')
library = library()

def CHKSettings():
    print 'CHKSettings'
    config = xbmc.translatePath(SETTINGS_LOC)
    Settings2 = config + '/settings2.xml'
    if not xbmcvfs.exists(Settings2):
        #create missing settings2.xml
        try:
            f = open(Settings2, 'w')
            f.write("Genre|Type|Source/Path|Exclusion|Limit|1|Name\n")
            f.write("Add your custom configuration below, leave first two lines untouched")
            f.close
        except:
            pass

            
def Update_Timer():
    print 'Update_Timer'
    if REAL_SETTINGS.getSetting('Automatic_Update') == 'true':
    
        while not xbmc.abortRequested:
            Update = True
            Refresh_INT = [120,240,360,720,1440,2880,4320]
            Update_Refresh = Refresh_INT[int(REAL_SETTINGS.getSetting('Automatic_Update_Time'))]
            now  = datetime.datetime.today()
            # try:
            Update_Timer_LastRun = REAL_SETTINGS.getSetting('Update_Timer_NextRun')
            Update_Timer_LastRun = Update_Timer_LastRun.split('.')[0]
            Update_Timer_LastRun = datetime.datetime.strptime(Update_Timer_LastRun, '%Y-%m-%d %H:%M:%S')
            Update_Timer_NextRun = (Update_Timer_LastRun + datetime.timedelta(minutes=Update_Refresh))
            # except:
                # Update_Timer_NextRun = now
                # REAL_SETTINGS.setSetting("Update_Timer_NextRun",str(Update_Timer_NextRun))
                # pass
                
            if now >= Update_Timer_NextRun:
                if REAL_SETTINGS.getSetting('Automatic_Update_Run') == 'false':
                    if xbmc.Player().isPlaying():
                        Update = False

                if Update == True:
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoLibrary", "Background Service Started", 4000, THUMB) )
                    library.readSettings(SETTINGS_LOC, True)
                    REAL_SETTINGS.setSetting("Update_Timer_NextRun",str(Update_Timer_NextRun))
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoLibrary", "Background Service Complete", 4000, THUMB) )

            xbmc.sleep(4000)
            
CHKSettings()
Update_Timer()
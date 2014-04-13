#   Copyright (C) 2013 Lunatixz
#
#
# This file is part of PseudoTV.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

def main():
    pass

if __name__ == '__main__':
    main()
 
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys
import urllib

from resources.lib.Globals import *

xbmc.log('script.pseudotv.live-donordownload: Donor Download Started')
xbmc.log('script.pseudotv.live-donordownload: Donor Enabled? = ' + str(REAL_SETTINGS.getSetting("Donor_Enabled"))) 


UserPass = REAL_SETTINGS.getSetting('Donor_UP')
BaseURL = ('http://'+UserPass+'@ptvl.comeze.com/PTVL/')

DonorURLPath = (BaseURL + 'Donor.py')
DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))

xbmc.log('script.pseudotv.live-donordownload: DonorPath = ' + str(DonorPath))
xbmc.log('script.pseudotv.live-donordownload: DL_DonorPath = ' + str(DL_DonorPath)) 
DonorDownload = False
Installed = False
Error = False

# Find Donor.pyo, Activate/Update
if xbmcvfs.exists(DonorPath):
    if dlg.yesno("PseudoTV Live", "Update Donor Features?"):
        try:
            os.remove(xbmc.translatePath(DonorPath))
            DonorDownload = True  
            xbmc.log('script.pseudotv.live-donordownload: Removed DonorPath')  
        except Exception,e:
            xbmc.log(str(e))
            Error = True
            xbmc.log('script.pseudotv.live-donordownload: Removed DonorPath Failed!' + str(e))    
            pass  
elif xbmcvfs.exists(DL_DonorPath):
    if dlg.yesno("PseudoTV Live", "Update Donor Features?"):
        try: 
            os.remove(xbmc.translatePath(DL_DonorPath))
            DonorDownload = True   
            xbmc.log('script.pseudotv.live-donordownload: Removed DL_DonorPath')  
        except Exception,e:
            xbmc.log(str(e))
            Error = True
            xbmc.log('script.pseudotv.live-donordownload: Removed DL_DonorPath Failed!' + str(e))  
            pass  
else:
    DonorDownload = True  
    xbmc.log('script.pseudotv.live-donordownload: Installing Donor Features')   
        
if DonorDownload:
    # Download Donor.py
    try:
        urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
        xbmc.log('script.pseudotv.live-donordownload: Downloading DL_DonorPath')   
        REAL_SETTINGS.setSetting('Donor_Update', "false")
        if xbmcvfs.exists(DL_DonorPath):
            Installed = True
        else:
            Error = True
            Installed = False
    except Exception,e:
        xbmc.log(str(e))
        xbmc.log('script.pseudotv.live-donordownload: Downloading DL_DonorPath Failed!' + str(e))  
        Error = True
        pass

if Error:
    MSG = "Donor Features Activated\Update Failed!\nTry Again Later..."

if Installed:
    MSG = "Donor Features Activated\Updated"
else:
    MSG = "Donor Features Not Updated..."
    
xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
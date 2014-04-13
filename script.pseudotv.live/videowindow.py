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


def replaceAll(file,searchExp,replaceExp):
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)
        

def main():
    pass

if __name__ == '__main__':
    main()
    
import os, sys, re, fileinput
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
from resources.lib.Globals import *
from resources.lib.FileAccess import *


SkinMasterPath = os.path.join(ADDON_PATH, 'resources', 'skins') + '/'

# Find PseudoTV Skin Path
PseudoSkin = (os.path.join(SkinMasterPath, Skin_Select, '720p')) + '/'

if xbmcvfs.exists(PseudoSkin):
    PseudoSkinfle = xbmc.translatePath(os.path.join(SkinMasterPath, Skin_Select, '720p', 'script.pseudotv.live.EPG.xml'))
else:
    PseudoSkinfle = xbmc.translatePath(os.path.join(SkinMasterPath, Skin_Select, '1080i', 'script.pseudotv.live.EPG.xml'))


xbmc.log('script.pseudotv.live-VideoWindow: Patcher Started')
xbmc.log('script.pseudotv.live-VideoWindow: ADDON_PATH = ' + ADDON_PATH)
xbmc.log('script.pseudotv.live-VideoWindow: PseudoSkinfle = ' + PseudoSkinfle)
xbmc.log('script.pseudotv.live-VideoWindow: SkinPath = ' + skinPath)
    

a = '<!-- PATCH START -->'
b = '<!-- PATCH START --> <!--'
c = '<!-- PATCH END -->'
d = '--> <!-- PATCH END -->'

Install = False
Installed = False
Uninstall = False

Patch = False
Patched = False
UnPatch = False

SeekPatch = False
SeekPatched = True

Error = False
MSG = ''

Path = (os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', '720p'))
fle = 'Custom_PTVL_9506.xml'
fle1 = 'dialogseekbar.xml'
VWPath = (os.path.join(skinPath, fle))
DSPath = xbmc.translatePath(os.path.join(skinPath, fle1))
flePath = (os.path.join(Path, fle)) 

# Delete Old VideoWindow Patch
if xbmcvfs.exists(VWPath):
    if dlg.yesno("PseudoTV Live", "VideoWindow Patch Found!\nRemove Patch?"):
        try:
            xbmcvfs.delete(VWPath)
            Uninstall = True
            xbmc.log('script.pseudotv.live-VideoWindow: Uninstall')
        except Exception,e:
            xbmc.log('script.pseudotv.live-VideoWindow: Delete Patch Failed' + str(e))
            Error = True
            pass
            
        try:
            f = FileAccess.open(PseudoSkinfle, "r")
            linesLST = f.readlines()            
            f.close()
            
            for i in range(len(set(linesLST))):
                lines = linesLST[i]
                if a in lines:
                    replaceAll(PseudoSkinfle,a,b)
                if c in lines:
                    replaceAll(PseudoSkinfle,c,d)
            UnPatch = True
            xbmc.log('script.pseudotv.live-VideoWindow: UnPatch')
        except Exception,e:
            xbmc.log('script.pseudotv.live-VideoWindow: Remove Patch Failed' + str(e))
            Error = True
            pass
    else:
        if dlg.yesno("PseudoTV Live", "VideoWindow Patch Found!\n Reapply Patch?"):
            Patch = True
else:
    Install = True
  

  
# Copy VideoWindow Patch  
if Install:
    try:
        xbmcvfs.copy(flePath, VWPath)
        if xbmcvfs.exists(VWPath):
            Installed = True
            Patch = True
            xbmc.log('script.pseudotv.live-VideoWindow: Installed')
    except Exception,e:
        xbmc.log('script.pseudotv.live-VideoWindow: Intall Failed' + str(e))
        Error = True
        pass
    
if Patch:
    try:
        f = FileAccess.open(PseudoSkinfle, "r")
        linesLST = f.readlines()            
        f.close()
        
        for i in range(len(set(linesLST))):
            lines = linesLST[i]
            if b in lines:
                replaceAll(PseudoSkinfle,b,a)
            if d in lines:
                replaceAll(PseudoSkinfle,d,c)            
        xbmc.log('script.pseudotv.live-VideoWindow: script.pseudotv.live.EPG.xml Patched')
        Patched = True
        SeekPatch = True
    except Exception,e:
        xbmc.log('script.pseudotv.live-VideoWindow: script.pseudotv.live.EPG.xml Patch Failed' + str(e))
        Error = True
        pass
    
# if SeekPatch:
    # # try:
    # y = '<visible>'
    # z = ('<visible>!Window.IsActive(script.pseudotv.live.TVOverlay.xml) + ')
    # replaceAll(DSPath,y,z)
    # xbmc.log('script.pseudotv.live-VideoWindow: DialogSeekBar Patched')
    # SeekPatched = True
    # # except Exception,e:
        # # xbmc.log('script.pseudotv.live-VideoWindow: DialogSeekBar Patched')
        # # Error = True
        # # pass
        
        
        
if (Installed and Patched and SeekPatched) or (Patched and SeekPatched):
    MSG = "VideoWindow Patched!\nXBMC Restart Required"

if Uninstall or UnPatch:
    MSG = "VideoWindow Patch Removed!\nXBMC Restart Required"

if Error:
    MSG = "VideoWindow Patch Error!"
    
xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
#   Copyright (C) 2011 Jason Anderson
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

import os, sys, re, shutil
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from resources.lib.Globals import *
from resources.lib.FileAccess import *

# Script constants
__scriptname__ = "PseudoTV Live"
__author__     = "Lunatixz, Jason102 & Angrycamel"
__url__        = "https://github.com/Lunatixz/script.pseudotv.live"
__settings__   = xbmcaddon.Addon(id='script.pseudotv.live')
__cwd__        = __settings__.getAddonInfo('path')

# Adapting a solution from ronie (http://forum.xbmc.org/showthread.php?t=97353)
if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
    xbmcgui.Window(10000).setProperty("PseudoTVRunning", "True")
    shouldrestart = False

    if shouldrestart == False:

        # Clear BCT Folder
        if REAL_SETTINGS.getSetting("ClearBCT") == "true":
            if FileAccess.exists(BCT_LOC):
                try:
                    shutil.rmtree(BCT_LOC)
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "BCT Cache Cleared", 1000, thumb) )
                    REAL_SETTINGS.setSetting('ClearBCT', "false")
                    xbmc.log('script.pseudotv.live-default: BCT Folder Purged!')
                except Exception,e:
                    REAL_SETTINGS.setSetting('ClearBCT', "false")
                    xbmc.log('script.pseudotv.live-default: BCT Folder Purge Failed!' + str(e))  
                    pass
            else:
                REAL_SETTINGS.setSetting('ClearBCT', "false")
                xbmc.log('script.pseudotv.live-default: BCT Folder Not Found!')
        
        # Clear Live Artwork Folder
        if REAL_SETTINGS.getSetting("ClearLiveArt") == "true":
            if FileAccess.exists(ART_LOC):
                try:
                    shutil.rmtree(ART_LOC)
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "LiveTV Artwork Cache Cleared", 1000, thumb) )
                    REAL_SETTINGS.setSetting('ClearLiveArt', "false")
                    xbmc.log('script.pseudotv.live-default: ArtCache Folder Purged!')
                except Exception,e:
                    REAL_SETTINGS.setSetting('ClearLiveArt', "false")
                    xbmc.log('script.pseudotv.live-default: ArtCache Folder Purge Failed!')
                    pass
            else:
                REAL_SETTINGS.setSetting('ClearLiveArt', "false")
                xbmc.log('script.pseudotv.live-default: ArtCache Folder Not Found!')
        
        # Launch PTVL
        xbmc.executebuiltin('RunScript("' + __cwd__ + '/pseudotv.py' + '")')
else:
    xbmc.log('script.pseudotv.live - Already running, exiting', xbmc.LOGERROR)

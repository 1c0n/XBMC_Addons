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


import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import httplib, urllib, urllib2, feedparser, socket, json
import subprocess, os, sys, re
import time, datetime, threading, _strptime

from library import *
from xml.etree import ElementTree as ET
from xml.dom.minidom import parse, parseString


__scriptname__ = "PseudoLibrary"
__author__     = "Lunatixz"
__url__        = "https://github.com/Lunatixz/XBMC_Addons/script.pseudo.library"
__settings__   = xbmcaddon.Addon(id='script.pseudo.library')
__cwd__        = __settings__.getAddonInfo('path')
 
dlg = xbmcgui.Dialog()
library = library()

if dlg.yesno("PseudoLibrary", "Generate Strm's ?"):
    SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
    CONFIG_LOC = (os.path.join(SETTINGS_LOC, 'settings2.xml')) + '/'
    library.readSettings(SETTINGS_LOC, False)
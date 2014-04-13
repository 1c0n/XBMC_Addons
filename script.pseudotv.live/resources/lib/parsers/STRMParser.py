#   Copyright (C) 2014 Lunatixz
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

import xbmc
import os, struct
import traceback

from resources.lib.Globals import *
from resources.lib.FileAccess import FileAccess
from xml.dom.minidom import parse, parseString


class STRMParser:
    def log(self, msg, level = xbmc.LOGDEBUG):
        xbmc.log('script.pseudotv-STRMParser: ' + ascii(msg), level)


    def determineLength(self, filename):
        self.log("determineLength " + filename)
        fleName, fleExt = os.path.splitext(filename)
        fleName += '.nfo'
        runtime = 0
        durationinseconds = 0
        
        if FileAccess.exists(fleName):
            try:
                file = FileAccess.open(fleName, "r")
                dom = parse(file)
                xmlruntime = dom.getElementsByTagName('runtime')[0].toxml()
                xmldurationinseconds = dom.getElementsByTagName('durationinseconds')[0].toxml()
                runtime = xmlruntime.replace('<runtime>','').replace('</runtime>','')    
                runtime = int(runtime)
                durationinseconds = xmlruntime.replace('<durationinseconds>','').replace('</durationinseconds>','')    
                durationinseconds = int(durationinseconds)
            except:
                self.log("Unable to open file, defaulting to 3600")
                self.log(traceback.format_exc(), xbmc.LOGERROR)
                dur = 3600
                return dur

        if runtime == 0:
            if durationinseconds != 0:
                dur = durationinseconds
            else:
                self.log('Unable to find runtime and durationinseconds info, defaulting to 3600')
                dur = 3600
        else:
            dur = runtime * 60

        self.log("Duration is " + str(dur))
        return dur

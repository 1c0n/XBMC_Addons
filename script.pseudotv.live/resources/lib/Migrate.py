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

import subprocess, os, re, sys, time
import xbmcaddon, xbmc, xbmcgui, xbmcvfs
import Settings, Globals, ChannelList
import urllib, urllib2, httplib

from xml.etree import ElementTree as ET
from FileAccess import FileLock, FileAccess


class Migrate:

    def log(self, msg, level = xbmc.LOGDEBUG):
        Globals.log('Migrate: ' + msg, level)

    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if Globals.REAL_SETTINGS.getSetting('enable_Debug') == "true":
            Globals.log('Migrate: ' + msg, level)
            
    def migrate(self):
        self.log("migrate")
        settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))    
        chanlist = ChannelList.ChannelList()
        chanlist.background = True
        chanlist.forceReset = True
        chanlist.createlist = True
        
        # If Autotune is enabled direct to autotuning
        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":
            self.log("autoTune, migrate")
            if self.autoTune():
                return True
        else:
            if FileAccess.exists(settingsFile):
                return False
            else:
                currentpreset = 0

            for i in range(Globals.TOTAL_FILL_CHANNELS):
                chantype = 9999

                try:
                    chantype = int(Globals.ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type"))
                except Exception,e:
                    pass

                if chantype == 9999:
                    self.log("addPreset")
                    self.addPreset(i + 1, currentpreset)
                    currentpreset += 1
                    
        return True

    
    def addPreset(self, channel, presetnum): # Initial settings2.xml preset on first run when empty...
    # Youtube
        BBCWW = ['BBCWW']
        Trailers = ['Trailers']
    # RSS
        HDNAT = ['HDNAT']
        TEKZA = ['TEKZA']
        
        if presetnum < len(BBCWW):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "10")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "BBCWorldwide")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "BBC World News")
        elif presetnum - len(BBCWW) < len(Trailers):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "10")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "movieclips")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")          
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "Movie Trailers")
        elif presetnum - len(BBCWW) - len(Trailers) < len(HDNAT):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "11")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "http://revision3.com/hdnation/feed/Quicktime-High-Definition")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")     
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "HD Nation")
        elif presetnum - len(BBCWW) - len(Trailers) - len(HDNAT) < len(TEKZA):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "11")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "http://revision3.com/tekzilla/feed/quicktime-high-definition")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "Tekzilla")
            
              
    def autoTune(self):
        self.log('autoTune, Init')
        curtime = time.time()
        chanlist = ChannelList.ChannelList()
        chanlist.background = True
        chanlist.makenewlists = True
        channelNum = 0
        updateDialogProgress = 0
        
        self.updateDialog = xbmcgui.DialogProgress()
        self.updateDialog.create("PseudoTV Live", "Auto Tune")
        
        # LiveTV - PVR
        self.updateDialogProgress = 5
        if Globals.REAL_SETTINGS.getSetting("autoFindLivePVR") == "true":
            self.log("autoTune, Adding Live PVR Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live PVR Channels","")
            CHnum = 0
            RCHnum = 0
            CHid = 0
            CHlst = ''
            CHname = ''
            CHzapit = ''
            
            if channelNum == 0:
                channelNum = 1
            try:
                json_query = '{"jsonrpc":"2.0","method":"PVR.GetChannels","params":{"channelgroupid":2}, "id":1}'
                json_folder_detail = chanlist.sendJSON_NEW(json_query)
                file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                self.logDebug('autoFindLivePVR, file_detail = ' + str(file_detail))
                self.xmlTvFile = xbmc.translatePath(os.path.join(Globals.REAL_SETTINGS.getSetting('xmltvLOC'), 'xmltv.xml'))

                f = FileAccess.open(self.xmlTvFile, "rb")
                tree = ET.parse(f)
                root = tree.getroot()
                f.close()

                file_detail = str(file_detail)
                CHnameLST = re.findall('"label" *: *(.*?),', file_detail)
                CHidLST = re.findall('"channelid" *: *(.*?),', file_detail)
                self.logDebug('autoFindLivePVR, CHnameLST = ' + str(CHnameLST))
                self.logDebug('autoFindLivePVR, CHidLST = ' + str(CHidLST))
                    
                for CHnum in range(len(file_detail)):
                    CHname = CHnameLST[CHnum]
                    CHname = str(CHname)
                    CHname = CHname.split('"', 1)[-1]
                    CHname = CHname.split('"')[0]
                    CHlst = (CHname + ',' + CHidLST[CHnum])
                    inSet = False
                    self.logDebug('autoFindLivePVR, CHlst.1 = ' + str(CHlst))
                    # search xmltv for channel name, then find its id
                    for elem in root.getiterator():
                        if elem.tag == ("channel"):
                            name = elem.findall('display-name')
                            for i in name:
                                RCHnum = (CHnum + 1)
                                if CHname == i.text:
                                    CHzapit = elem.attrib
                                    CHzapit = str(CHzapit)
                                    CHzapit = CHzapit.split(": '", 1)[-1]
                                    CHzapit = CHzapit.split("'")[0]
                                    CHlst = (CHlst + ',' + str(CHzapit))
                                    self.logDebug('autoFindLivePVR, CHlst.2 = ' + str(CHlst))
                                    inSet = True
                    
                    self.log('autoFindLivePVR, inSet = ' + str(inSet) + ' , ' +  str(CHlst))
                    if inSet == True:
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "pvr://channels/tv/All TV channels/" + str(CHnum) + ".pvr")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "xmltv")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        channelNum = channelNum + 1
                    
                    if inSet == False:
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "pvr://channels/tv/All TV channels/" + str(CHnum) + ".pvr")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "XMLTV DATA NOT FOUND")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        channelNum = channelNum + 1  
            
            except Exception,e:
                self.log(str(e))
                pass
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        # LiveTV - HDhomerun
        self.updateDialogProgress = 10
        if Globals.REAL_SETTINGS.getSetting("autoFindLiveHD") == "true" and (Globals.REAL_SETTINGS.getSetting('xmltvLOC') != '' or Globals.REAL_SETTINGS.getSetting('EPGDB') == "true"):
            self.log("autoTune, Adding Live HDhomerun Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live HDhomerun Channels","")
            CHnum = 0
            RCHnum = 0
            CHid = 0
            CHlst = ''
            CHname = ''
            CHzapit = ''
            LocalLST = []
            LocalFle = ''
            
            if channelNum == 0:
                channelNum = 1
                
            try:
                HDstrmPath = Globals.REAL_SETTINGS.getSetting('autoFindLiveHDPath')
                self.logDebug('autoFindLiveHD, HDstrmPath = ' + str(HDstrmPath))   
                self.xmlTvFile = xbmc.translatePath(os.path.join(Globals.REAL_SETTINGS.getSetting('xmltvLOC'), 'xmltv.xml'))
                self.logDebug('autoFindLiveHD, self.xmlTvFile = ' + str(self.xmlTvFile))   
            
                f = FileAccess.open(self.xmlTvFile, "rb")
                tree = ET.parse(f)
                root = tree.getroot()
                f.close()

                LocalFLE = ''
                LocalLST = str(xbmcvfs.listdir(HDstrmPath)[1]).replace("[","").replace("]","").replace("'","")
                LocalLST = LocalLST.split(", ")
                
                for n in range(len(LocalLST)):
                    if '.strm' in (LocalLST[n]):
                        inSet = False
                        LocalFLE = (LocalLST[n])
                        filename = (HDstrmPath + LocalFLE)
                        CHname = os.path.splitext(LocalFLE)[0]
                        for elem in root.getiterator():
                            if elem.tag == ("channel"):
                                name = elem.findall('display-name')

                                for i in name:
                                    CHlst = ''
                                    RCHnum = (CHnum + 1)
                                    if CHname == i.text:
                                        inSet = True
                                        CHzapit = elem.attrib
                                        CHzapit = str(CHzapit)
                                        CHzapit = CHzapit.split(": '", 1)[-1]
                                        CHzapit = CHzapit.split("'")[0]
                                        CHlst = (CHlst + ',' + str(CHzapit))

                        self.log('autoFindLiveHD, inSet = ' + str(inSet) + ' , ' +  str(CHlst))
                        if inSet == True:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", filename)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "xmltv")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            channelNum = channelNum + 1
                        
                        if inSet == False:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", filename)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "XMLTV DATA NOT FOUND")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            channelNum = channelNum + 1  
            except Exception,e:
                pass
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        # LiveTV - USTVnow
        self.updateDialogProgress = 15
        if Globals.REAL_SETTINGS.getSetting("autoFindUSTVNOW") == "true":
            self.log("autoTune, Adding USTVnow Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding USTVnow Channels","")
            id = 'plugin.video.ustvnow'
            CHnum = 0
            RCHnum = 0
            CHlst = ''
            CHid = 0
            CHname = ''
            CHzapit = ''
            LocalLST = []
            LocalFle = ''   
            f = ''
            
            if channelNum == 0:
                channelNum = 1
            
            try:
                xbmcaddon.Addon(id)
                installed = True
            except Exception,e:
                self.log(str(e))
                installed = False
                
            if installed:
                try:
                    json_query = '{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"plugin://plugin.video.ustvnow/live?mode=live"},"id":1}'
                    json_folder_detail = chanlist.sendJSON_NEW(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                     
                    url = 'https://docs.google.com/uc?export=download&id=0BzyNK_dHGPHkQno2aVV2THlKLUE'
                    url_bak = 'https://dl.dropboxusercontent.com/s/3pp8j7962l1t4z1/ustvnow.xml'
                    
                    try: 
                        f = urllib2.urlopen(url)
                        self.log("ustvnow, INFO: URL Connected...")
                    except urllib2.URLError as e:
                        f = urllib2.urlopen(url_bak)
                        self.log("ustvnow, INFO: URL_BAK Connected...")
                    except urllib2.URLError as e:
                        pass

                    tree = ET.parse(f)
                    root = tree.getroot()
                    f.close()
                  
                    for f in file_detail:                    
                        inSet = False
                        file = re.search('"file" *: *"(.*?)"', f)
                        label = re.search('"label" *: *"(.*?)"', f)
                        if file and label:
                            file = file.group(1)
                            label = label.group(1)
                            CHname = str(label.split(' -')[0])
                            
                            for elem in root.getiterator():
                                if elem.tag == ("channel"):
                                    name = elem.findall('display-name')

                                    for i in name:
                                        RCHnum = (CHnum + 1)
                                        if CHname == i.text:
                                            inSet = True
                                            CHzapit = elem.attrib
                                            CHzapit = str(CHzapit)
                                            CHzapit = CHzapit.split(": '", 1)[-1]
                                            CHzapit = CHzapit.split("'")[0]
                                            
                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.ustvnow/?name="+CHname+"&mode=play")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "ustvnow")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USTVnow')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                channelNum = channelNum + 1
                            
                            if inSet == False:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.ustvnow/?name="+CHname+"&mode=play")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "XMLTV DATA NOT FOUND")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USTVnow')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                channelNum = channelNum + 1  
                except:
                    pass
            
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
            
        # Custom Channels
        self.updateDialogProgress = 20
        if Globals.REAL_SETTINGS.getSetting("autoFindCustom") == "true" :
            self.log("autoTune, Adding Custom Channel")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Custom Channel","")
            i = 1
            for i in range(500):
                if os.path.exists(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Video Playlist Channel")
                    channelNum = channelNum + 1
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/video/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp')),"")
                elif os.path.exists(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Mixed Playlist Channel")
                    channelNum = channelNum + 1
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/mixed/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp')),"")
                elif os.path.exists(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Music Playlist Channel")
                    channelNum = channelNum + 1
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/music/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp')),"")
        
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        #TV - Networks/Genres
        self.updateDialogProgress = 20
        self.log("autoTune, autoFindNetworks " + str(Globals.REAL_SETTINGS.getSetting("autoFindNetworks")))
        self.log("autoTune, autoFindTVGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindTVGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true"):
            self.log("autoTune, Searching for TV Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for TV Channels","")
            chanlist.fillTVInfo()

        # need to add check for auto find network channels
        self.updateDialogProgress = 21
        if Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true":
            self.log("autoTune, Adding TV Networks")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Networks","")
            i = 1
            for i in range(len(chanlist.networkList)):
                channelNum = channelNum + 1
                # channelNum = self.initialAddChannels(chanlist.networkList, 1, channelNum)
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1",Globals.uni(chanlist.networkList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Network",Globals.uni(chanlist.networkList[i]))
        
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        self.updateDialogProgress = 22
        if Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true":
            self.log("autoTune, Adding TV Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres","")
            channelNum = channelNum - 1
            # channelNum = self.initialAddChannels(chanlist.showGenreList, 3, channelNum)
            for i in range(len(chanlist.showGenreList)):
                channelNum = channelNum + 1
                # add network presets
                if chanlist.showGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "3")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.showGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres",Globals.uni(chanlist.showGenreList[i]) + " TV")
            
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        self.updateDialogProgress = 23
        self.log("autoTune, autoFindStudios " + str(Globals.REAL_SETTINGS.getSetting("autoFindStudios")))
        self.log("autoTune, autoFindMovieGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true"):
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Movie Channels","")
            chanlist.fillMovieInfo()

        self.updateDialogProgress = 24
        if Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true":
            self.log("autoTune, Adding Movie Studios")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios","")
            i = 1
            for i in range(len(chanlist.studioList)):
                channelNum = channelNum + 1
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.studioList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.studioList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios",Globals.uni(chanlist.studioList[i]))

            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        self.updateDialogProgress = 25
        if Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true":
            self.log("autoTune, Adding Movie Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","")
            channelNum = channelNum - 1
            # channelNum = self.initialAddChannels(chanlist.movieGenreList, 4, channelNum)
            for i in range(len(chanlist.movieGenreList)):
                channelNum = channelNum + 1
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.movieGenreList))
                # add network presets
                if chanlist.movieGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "4")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.movieGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","Found " + Globals.uni(chanlist.movieGenreList[i]) + " Movies")
            
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        self.updateDialogProgress = 26
        self.log("autoTune, autoFindMixGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMixGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Mixed Channels","")
            chanlist.fillMixedGenreInfo()
        
        self.updateDialogProgress = 27
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.log("autoTune, Adding Mixed Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres","")
            channelNum = channelNum - 1
            for i in range(len(chanlist.mixedGenreList)):
                channelNum = channelNum + 1
                # add network presets
                if chanlist.mixedGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "5")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.mixedGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres",Globals.uni(chanlist.mixedGenreList[i]) + " Mix")

            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        self.updateDialogProgress = 28
        self.log("autoTune, autoFindMusicGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Music Channels","")
            chanlist.fillMusicInfo()

        self.updateDialogProgress = 29
        #Music Genre
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.log("autoTune, Adding Music Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres","")
            i = 1
            for i in range(len(chanlist.musicGenreList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "12")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.musicGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres",Globals.uni(chanlist.musicGenreList[i]) + " Music")
        
            channelNum = channelNum
            self.logDebug('channelNum = ' + str(channelNum))
        
        #Music Videos - Last.fm user
        self.updateDialogProgress = 30
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFM") == "true":
            self.log("autoTune, Adding Last.FM Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Last.FM Music Videos","")
            
            if channelNum == 0:
                channelNum = 1
            
            user = Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFMuser")
            lastapi = "http://api.tv.timbormans.com/user/" + user + "/topartists.xml"
            for i in range(1):
                # add Last.fm user presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "13")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", lastapi)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Last.FM")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
       
            channelNum = channelNum + 1
            self.logDebug('channelNum = ' + str(channelNum))
        
        #Music Videos - Youtube
        self.updateDialogProgress = 35
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosYoutube") == "true":
            self.log("autoTune, Adding Youtube Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Youtube Music Videos","")
            
            if channelNum == 0:
                channelNum = 1
            
            for i in range(1):
                # add HungaryRChart presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "HungaryRChart")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "HRChart")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                # add BillbostdHot100 presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "BillbostdHot100")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "BillbostdHot100")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                # add TheTesteeTop50Charts presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "TheTesteeTop50Charts")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "TheTesteeTop50Charts")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_changed", "true")
        
            channelNum = channelNum + 3
            self.logDebug('channelNum = ' + str(channelNum))
        
        #Music Videos - VevoTV
        self.updateDialogProgress = 40
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosVevoTV") == "true":
            self.log("autoTune, Adding VevoTV Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding VevoTV Music Videos","")
            
            if channelNum == 0:
                channelNum = 1

            for i in range(1):
                # add VevoTV presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.vevo_tv/?url=TIVEVSTRUS00&mode=playOfficial")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "VEVO TV (US: Hits)")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "VevoTV - Hits")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "9")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "plugin://plugin.video.vevo_tv/?url=TIVEVSTRUS01&mode=playOfficial")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "VEVO TV (US: Flow)")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "VevoTV - Flow")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")

            channelNum = channelNum + 2
            self.logDebug('channelNum = ' + str(channelNum))
        
        #Music Videos - Local
        self.updateDialogProgress = 45
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLocal") != "":
            self.log("autoTune, Adding Local Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Local Music Videos","")
            
            if channelNum == 0:
                channelNum = 1
            
            LocalVideo = str(Globals.REAL_SETTINGS.getSetting('autoFindMusicVideosLocal'))
            for i in range(1):
                # add Local presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +LocalVideo+ "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "Music Videos")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")        

            channelNum = channelNum + 1
            self.logDebug('channelNum = ' + str(channelNum))
        
        
        #InternetTV - Bringthepopcorn
        self.updateDialogProgress = 60
        if Globals.REAL_SETTINGS.getSetting("autoFindPopcorn") == "true":
            self.log("autoTune, Adding Bring The Popcorn Movies")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Bring The Popcorn Movies","")
            
            if channelNum == 0:
                channelNum = 1
                        
            # AT_PopCat = ['action','adventure','animation','british','comedy','crime','disaster','documentary','drama','eastern','erotic','family','fan+film','fantasy','film+noir','foreign','history','holiday','horror','indie','kids','music','musical','mystery','neo-noir','road+movie','romance','science+fiction','short','sport','sports+film','suspense','thriller','tv+movie','war','western']
            # ATPopCat = AT_PopCat[int(Globals.REAL_SETTINGS.getSetting('autoFindPopcornGenre'))]
               
            # AT_PopYear = ['2010-Now','2000-2010','1990-2000','1980-1990','1970-1980','1960-1970','1950-1960','1940-1950','1930-1940','1920-1930','1910-1920']
            # ATPopYear = AT_PopYear[int(Globals.REAL_SETTINGS.getSetting('autoFindPopcornYear'))]
            
            # AT_PopRes = ['480','720','1080']
            # ATPopRes = AT_PopRes[int(Globals.REAL_SETTINGS.getSetting('autoFindPopcornResoultion'))]    
              
            # if Globals.REAL_SETTINGS.getSetting('autoFindPopcornPop') == "true":
                # ATPopCat = 'pop|' + ATPopCat
            
            for i in range(1):
                # add Bringthepopcorn user presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "14")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "popcorn")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", 'autotune')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", '')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", '')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "BringThePopcorn")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
       
            channelNum = channelNum + 1
            self.logDebug('channelNum = ' + str(channelNum))
        

        #InternetTV - Strms
        self.updateDialogProgress = 50
        if Globals.REAL_SETTINGS.getSetting("autoFindInternetStrms") == "true":
            self.log("autoTune, Adding InternetTV Strms")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV Strms","")
            
            if channelNum == 0:
                channelNum = 1

            for i in range(1):
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "BBCWorldwide")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "BBC World News")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "11")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "http://revision3.com/hdnation/feed/Quicktime-High-Definition")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "HD Nation")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")

            channelNum = channelNum + 2
            self.logDebug('channelNum = ' + str(channelNum))
            
            # if Globals.REAL_SETTINGS.getSetting("Donor_Enabled") == "true" and Donor_Enabled == True:      
                # self.updateDialogProgress = 50
                # self.updateDialog = xbmcgui.DialogProgress()
                # self.updateDialog.create("PseudoTV Live", "Auto Tune")
                # UserPass = Globals.REAL_SETTINGS.getSetting('Donor_UP')
                # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV...","")
                # GenericPath = (xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'cache', 'strms', 'Generic')) + '/')
        
                # if os.path.exists(GenericPath):
                    # id = 'plugin.video.tgun'
                    # try:
                        # xbmcaddon.Addon(id)
                        # installed = True
                    # except Exception,e:
                        # installed = False

                    # if installed == True:
                        # self.log("autoTune, Adding InternetTV TGUN")
                        # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV from TGUN","")
                        # InternetTgunTVMovies = (GenericPath + 'TGUN.-.TVMovies/')
                        # InternetTgunClassicTV = (GenericPath + 'TGUN.-.ClassicTV/')
                        # for i in range(1):
                            # # add TGUN
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +InternetTgunTVMovies+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "TGUN - TV/Movies")  
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +InternetTgunClassicTV+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "TGUN - ClassicTV")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")

                    # channelNum = channelNum + 2
                    # self.logDebug('channelNum = ' + str(channelNum))   

                    # id = 'plugin.video.jtv.archives'            
                    # try:
                        # xbmcaddon.Addon(id)
                        # installed = True
                    # except Exception:
                        # installed = False

                    # if installed == True:
                        # self.log("autoTune, Adding InternetTV JTV")
                        # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV from JTV","")
                        # InternetJTVDocumentary = (GenericPath + 'JTV.-.Documentary/')
                        # InternetJTVMovies = (GenericPath + 'JTV.-.Movies/')
                        # InternetJTVSeries = (GenericPath + 'JTV.-.Series/')
                        # for i in range(1):
                            # # add JTV
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +InternetJTVDocumentary+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "JTV - Documentary")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +InternetJTVMovies+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "JTV - Movies")  
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "" +InternetJTVSeries+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "JTV - Series")  
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_changed", "true")

                    # channelNum = channelNum + 3
                    # self.logDebug('channelNum = ' + str(channelNum))

                    # id = 'plugin://plugin.video.F.T.V'            
                    # try:
                        # xbmcaddon.Addon(id)
                        # installed = True
                    # except Exception:
                        # installed = False

                    # if installed == True:
                        # self.log("autoTune, Adding InternetTV FTV")
                        # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV from FTV","")
                        # InternetFTVMovies = (GenericPath + 'FilmOn.-.Movies/')
                        # InternetFTVMusic = (GenericPath + 'FilmOn.-.Music/')
                        # for i in range(1):
                            # # add FTV
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +InternetFTVMovies+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "FTV - Movies")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +InternetFTVMusic+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "FTV - Music")  
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")

                    # channelNum = channelNum + 2
                    # self.logDebug('channelNum = ' + str(channelNum))

                    # id = 'plugin://plugin.video.foodnetwork'            
                    # try:
                        # xbmcaddon.Addon(id)
                        # installed = True
                    # except Exception:
                        # installed = False

                    # if installed == True:
                        # self.log("autoTune, Adding InternetTV FoodNetwork")
                        # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV from FoodNetwork","")
                        # InternetFoodNetwork = (GenericPath + 'Generic/Food.Network/')
                        # for i in range(1):
                            # # add FoodNetwork
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +InternetFoodNetwork+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Food Network")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")

                    # channelNum = channelNum + 1
                    # self.logDebug('channelNum = ' + str(channelNum))

                    # id = 'plugin://plugin.video.supercartoons'            
                    # try:
                        # xbmcaddon.Addon(id)
                        # installed = True
                    # except Exception:
                        # installed = False

                    # if installed == True:
                        # self.log("autoTune, Adding InternetTV Supercartoons")
                        # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV from Supercartoons","")
                        # InternetSupercartoons = (GenericPath + 'SuperCartoons/')
                        # for i in range(1):
                            # # add Supercartoons
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +InternetSupercartoons+ "")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Super Cartoons")
                            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")

                    # channelNum = channelNum + 1
                    # self.logDebug('channelNum = ' + str(channelNum))
            
           
        Globals.ADDON_SETTINGS.writeSettings()

        #set max channels
        # chanlist.setMaxChannels()
        
        self.updateDialogProgress = 100
        # reset auto tune settings        
        Globals.REAL_SETTINGS.setSetting('Autotune', "false")
        Globals.REAL_SETTINGS.setSetting('Warning1', "false")
        Globals.REAL_SETTINGS.setSetting('autoFindLivePVR', "false")
        Globals.REAL_SETTINGS.setSetting('autoFindLiveHD', "false")
        Globals.REAL_SETTINGS.setSetting('autoFindUSTVNOW', "false")        
        Globals.REAL_SETTINGS.setSetting("autoFindCustom","false")
        Globals.REAL_SETTINGS.setSetting("autoFindNetworks","false")
        Globals.REAL_SETTINGS.setSetting("autoFindStudios","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMovieGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMixGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVShows","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosYoutube","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosVevoTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLastFM","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLocal","")
        Globals.REAL_SETTINGS.setSetting("autoFindInternetStrms","false")
        Globals.REAL_SETTINGS.setSetting("autoFindInternetStrms","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPopcorn","false")
        Globals.REAL_SETTINGS.setSetting("ForceChannelReset","true")

        Globals.ADDON_SETTINGS.setSetting('LastExitTime', str(int(curtime)))
        self.updateDialog.close()

        
def initialAddChannels(self, thelist, chantype, currentchan):
    if len(thelist) > 0:
        counted = 0
        lastitem = 0
        curchancount = 1
        lowerlimit = 1
        lowlimitcnt = 0

        for item in thelist:
            if item[1] > lowerlimit:
                if item[1] != lastitem:
                    if curchancount + counted <= 10 or counted == 0:
                        counted += curchancount
                        curchancount = 1
                        lastitem = item[1]
                    else:
                        break
                else:
                    curchancount += 1

                lowlimitcnt += 1

                if lowlimitcnt == 3:
                    lowlimitcnt = 0
                    lowerlimit += 1
            else:
                break

        if counted > 0:
            for item in thelist:
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_type", str(chantype))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_1", item[0])
                counted -= 1
                currentchan += 1

                if counted == 0:
                    break

    return currentchan

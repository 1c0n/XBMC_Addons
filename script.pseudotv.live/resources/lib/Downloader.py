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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random, traceback
import urllib, urllib2
import fanarttv

from Globals import *
from FileAccess import FileLock, FileAccess
from xml.etree import ElementTree as ET
from tvdb import *
from tmdb import *

class Downloader:

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Downloader: ' + msg, level)

    
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if REAL_SETTINGS.getSetting('enable_Debug') == "true":
            log('Downloader: ' + msg, level)
    

    def DownloadArt(self, type, id, typeEXT, mediapathSeason, mediapathSeries):
        self.log('LiveTVArtDownloader')           
        tvdbAPI = TVDB(TVDB_API_KEY)
        tmdbAPI = TMDB(TMDB_API_KEY)     

        LiveArtwork = False
        FanTVDownload = False
        FanMovieDownload = False
                
        if not FileAccess.exists(ART_LOC):
            os.makedirs(ART_LOC)
            
        # LiveArtwork split flename
        try:
            typeEXT = typeEXT.split('-')[1]
            LiveArtwork = True
        except Exception,e:
            pass

        ArtType = typeEXT.split('.')[0]
        self.log('type = ' + type)
        self.log('typeEXT = ' + typeEXT)
        self.log('ArtType = ' + ArtType) 

        if type == 'tvshow':
            if LiveArtwork:
                TVFileSys = ART_LOC
                TVFileFle = id + '-' + typeEXT
                TVFilePath = ascii(os.path.join(TVFileSys, TVFileFle))
            elif REAL_SETTINGS.getSetting("TVFileSys") == "0":
                TVFileSys = mediapathSeries
                TVFilePath = ascii(os.path.join(TVFileSys, typeEXT))
            elif REAL_SETTINGS.getSetting("TVFileSys") == "1":
                TVFileSys = mediapathSeason
                TVFilePath = ascii(os.path.join(TVFileSys, typeEXT))
            else:                
                TVFileSys = ART_LOC
                TVFileFle = id + '-' + typeEXT
                TVFilePath = ascii(os.path.join(TVFileSys, TVFileFle))
            self.log('TVFilePath = ' + TVFilePath)  

            tvdb = ['banner', 'fanart', 'folder', 'poster']
            
            if ArtType in tvdb:
                ArtType = ArtType.replace('banner', 'graphical').replace('folder', 'poster')
                tvdb = str(tvdbAPI.getBannerByID(id, ArtType))
                self.log('tvdb = ' + tvdb)  
                try:
                    tvdbPath = tvdb.split(', ')[0].replace("[('", "").replace("'", "")
                    self.log('tvdbPath = ' + tvdbPath)  
                    resource = urllib.urlopen(tvdbPath)
                    output = FileAccess.open(TVFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    # urllib.urlretrieve(tvdbPath, TVFilePath)
                    return TVFilePath
                except Exception,e:
                    FanTVDownload = True
                    self.log('tvdbAPI Failed!') 
                    pass
            else:
                FanTVDownload = True

            if FanTVDownload:
                ArtType = ArtType.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'tvfanart')
                fanartTV = fanarttv.FTV_TVProvider()
                fan = fanartTV.get_image_list(id)
                try:
                    data = str(fan).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    fanPath = str([s for s in data if ArtType in s]).split("', 'art_type: ")[0]
                    self.log('fanPath = ' + fanPath) 
                    match = re.search("url *: *(.*?),", fanPath)
                    fanPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    self.log('fanPath = ' + fanPath)                     
                    resource = urllib.urlopen(fanPath)
                    output = FileAccess.open(TVFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    # urllib.urlretrieve(fanPath, TVFilePath)
                    return TVFilePath
                except Exception,e:
                    self.log('FanTVDownload Failed!') 
                    pass

        elif type == 'movie':
            if LiveArtwork:
                MovieFileSys = ART_LOC
                MovieFileFle = id + '-' + typeEXT
                MovieFilePath = ascii(os.path.join(MovieFileSys, MovieFileFle))
            elif REAL_SETTINGS.getSetting("MovieFileSys") == "0":
                MovieFileSys = mediapathSeason
                MovieFilePath = ascii(os.path.join(MovieFileSys, typeEXT))
            else:
                MovieFileSys = ART_LOC
                MovieFileFle = id + '-' + typeEXT
                MovieFilePath = ascii(os.path.join(MovieFileSys, MovieFileFle))

            self.log('MovieFilePath = ' + MovieFilePath) 

            tmdb = ['fanart', 'folder', 'poster']
            
            if ArtType in tmdb:
                ArtType = ArtType.replace('folder', 'poster')
                tmdb = tmdbAPI.get_image_list(id)
                self.log('tmdb = ' + str(tmdb))
                try:
                    data = str(tmdb).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    tmdbPath = str([s for s in data if ArtType in s]).split("', 'width: ")[0]
                    self.log('tmdbPath = ' + tmdbPath) 
                    match = re.search('url *: *(.*?),', tmdbPath)
                    tmdbPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    self.log('tmdbPath = ' + tmdbPath) 
                    resource = urllib.urlopen(tmdbPath)
                    output = FileAccess.open(MovieFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    # urllib.urlretrieve(tmdbPath, MovieFilePath)
                    return MovieFilePath
                except Exception,e:
                    FanMovieDownload = True
                    self.log('tmdbAPI Failed!') 
                    pass
            else:
                FanMovieDownload = True

            if FanMovieDownload:
                ArtType = ArtType.replace('folder', 'poster').replace('fanart', 'moviefanart')
                fanartTV = fanarttv.FTV_MovieProvider()
                fan = fanartTV.get_image_list(id)
                self.log('fan = ' + str(fan))
                try:
                    data = str(fan).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    fanPath = str([s for s in data if ArtType in s]).split("', 'art_type: ")[0]
                    self.log('fanPath = ' + fanPath) 
                    match = re.search("url *: *(.*?),", fanPath)
                    fanPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    self.log('fanPath = ' + fanPath)
                    resource = urllib.urlopen(fanPath)
                    output = FileAccess.open(MovieFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    # urllib.urlretrieve(fanPath, MovieFilePath)
                    return MovieFilePath
                except Exception,e:
                    self.log('FanMovieDownload Failed!') 
                    pass
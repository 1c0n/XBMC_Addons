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

from xml.etree import ElementTree as ET
from xml.dom.minidom import parse, parseString

try:
    from metahandler import metahandlers
except Exception,e:  
    self.log("script.pseudotv.live-ChannelList: metahandler Import Failed" + str(e))    
    pass
      
# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

# Plugin Info
ADDON_ID = 'script.pseudo.library'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_ID = REAL_SETTINGS.getAddonInfo('id')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
xbmc.log(ADDON_ID +' '+ ADDON_NAME +' '+ ADDON_PATH +' '+ ADDON_VERSION)

# Globals
SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
THUMB = REAL_SETTINGS.getAddonInfo('icon')
cache = StorageServer.StorageServer("plugin://script.pseudo.library/" + "cache",1)

class library:

    def __init__(self):
        self.settingChannel = '0'
        self.httpJSON = True
        self.discoveredWebServer = False
        self.background = True
        
  
    def readSettings(self, config, background):
        print 'readSettings'
        MSG = ''
        config = xbmc.translatePath(config)
        Settings2 = config + '/settings2.xml'
        self.background = background
        
        if self.background == False:
            self.updateDialog = xbmcgui.DialogProgress()
            self.updateDialogProgress = 0
            self.updateDialog.create("PseudoLibrary", "Building Strms")
            self.updateDialog.update(0, "Building Strms")
        
        #parse internal list
        if not xbmcvfs.exists(Settings2):
            #create settings2.xml
            try:
                f = open(Settings2, 'w')
                f.write("Genre|Type|Source|Exclusion|Limit|NA|Name\n")
                f.close
            except:
                MSG = "No Configuration File Found!, Check settings2.xml"
                pass
        else:
            #read from list
            # try:
            f = open(Settings2, 'r')
            Settings = f.readlines()
            f.close
            
            for i in range(len(Settings)):
                lineLST = Settings[i]
                line = lineLST.split("|")
                StrmType = line[0]
                Name = str(line[6]).replace('\n','')
                
                if self.background == False:
                    self.updateDialog.update(self.updateDialogProgress, "Building Strms", "Parsing Internal List", "adding " + str(Name))
            # except:
                # MSG = "No Configurations Found!, Check settings2.xml"
                # pass

        if MSG:
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoLibrary", MSG, 4000, THUMB) )
            
        print Settings
            
        if REAL_SETTINGS.getSetting('CN_Enable') == 'true': 
            #parse external list
            genre_filter = []
            url = 'https://pseudotv-live-community.googlecode.com/svn/addons.xml'
            url1 = 'https://pseudotv-live-community.googlecode.com/svn/playon.xml'
            
            if REAL_SETTINGS.getSetting("CN_TV") == "true":
                genre_filter.append('TV') 
            if REAL_SETTINGS.getSetting("CN_Movies") == "true":
                genre_filter.append('Movies') 
            if REAL_SETTINGS.getSetting("CN_Episodes") == "true":
                genre_filter.append('Episodes') 
            if REAL_SETTINGS.getSetting("CN_Sports") == "true":
                genre_filter.append('Sports') 
            if REAL_SETTINGS.getSetting("CN_News") == "true":
                genre_filter.append('News') 
            if REAL_SETTINGS.getSetting("CN_Kids") == "true":
                genre_filter.append('Kids') 
            if REAL_SETTINGS.getSetting("CN_Music") == "true":
                genre_filter.append('Music') 
            if REAL_SETTINGS.getSetting("CN_Other") == "true":
                genre_filter.append('Other') 
                    
            data = self.OpenURL(url)
            data1 = self.OpenURL(url1)
            data = data + data1
            data = data[2:] #remove first two unwanted lines
            data = ([x for x in data if x != '']) #remove empty lines    
                
            # try:
            for i in range(len(data)):
                lineLST = data[i]
                line = lineLST.split("|")
                StrmType = line[0]
                Name = line[5]
                
                #append wanted items by genre
                if StrmType in genre_filter:
                    Settings.append(lineLST)
                
                    if self.background == False:
                        self.updateDialog.update(self.updateDialogProgress, "Building Strms", "Parsing External List", "adding " + str(Name))
            # except:
                # pass
                
        print Settings

        # try:
        for n in range(len(Settings)):
            line = ((Settings[n]).replace('\n','').replace('""',"")).split('|')
            StrmType = line[0]
            BuildType = line[1]
            setting1 = line[2]
            setting2 = line[3]
            setting3 = line[4]
            setting4 = line[5]
            FolderName = line[6]
            
            if BuildType.lower() == 'plugin' or BuildType == '15':
                self.BuildPluginFileList(StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName)
            elif BuildType.lower() == 'playon' or BuildType == '16':
                self.BuildPlayonFileList(StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName)
            elif BuildType.lower() == 'upnp':
                print StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName
            elif BuildType.lower() == 'youtube':
                print StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName
        # except:
            # pass

            
    def BuildPluginFileList(self, StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName):
        print "BuildPluginFileList"
        print StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName
        showList = []
        DetailLST = []
        DetailLST_CHK = []
        self.dircount = 0
        self.filecount = 0
        limit = int(setting3)
        Pluginvalid = self.plugin_ok(setting1)
        
        if Pluginvalid != False:
            try:
                Directs = (setting1.split('/')) # split folders
                Directs = ([x for x in Directs if x != '']) # remove empty elements
                plugins = Directs[1] # element 1 in split is plugin name
                Directs = Directs[2:] # slice two unwanted elements. ie (plugin:, plugin name)
                plugin = 'plugin://' + plugins
                PluginName = plugins.replace('plugin.video.','').replace('plugin.program.','').replace('/','')
            except:
                Directs = []
                pass

            try:
                excludeLST = setting2.split(',')
                excludeLST = ([x.lower() for x in excludeLST if x != '']) # remove empty elements
            except:
                excludeLST = []
                pass
                
            #filter out unwanted folders
            excludeLST += ['back','previous','home','create new super folder','explore favourites','explore  favourites','explore xbmc favourites','explore kodi favourites','isearch','search','clips','seasons','trailers']
            
            if self.background == False:
                self.updateDialog.update(self.updateDialogProgress, "Building Strms", "Parsing " + BuildType + ": " + (PluginName), 'searching for ' + FolderName)

            Match = True
            while Match:

                DetailLST = self.PluginInfo(plugin)

                #Plugin listitems return parent list during error, catch repeat list and end loops.
                if DetailLST_CHK == DetailLST:
                    break
                else:
                    DetailLST_CHK = DetailLST

                #end while when no more directories to walk
                if len(Directs) <= 1:
                    Match = False
                    
                try:
                    for i in range(len(DetailLST)):
                    
                        if self.background == False:
                            self.updateDialog.update(self.updateDialogProgress, "Building Strms", "Parsing " + BuildType + ": " + (PluginName), 'found ' + str(Directs[0]))

                        Detail = (DetailLST[i]).split(',')
                        filetype = Detail[0]
                        title = Detail[1]
                        genre = Detail[2]
                        dur = Detail[3]
                        description = Detail[4]
                        file = Detail[5]
                        
                        if title.lower() not in excludeLST and title != '':
                            if filetype == 'directory':
                                if Directs[0].lower() == title.lower():
                                    print 'directory match'
                                    DirName = Directs[0]
                                    Directs.pop(0) #remove old directory, search next element
                                    plugin = file
                                    break
                                    
                except:
                    pass
                    
            if FolderName != '':
                DirName = FolderName
            
            #all directories found, walk final folder
            if len(Directs) == 0:              
                showList = self.PluginWalk(plugin, excludeLST, limit, StrmType, BuildType, 'video')
            
            print showList, StrmType, BuildType, PluginName, DirName
            self.WriteSTRM(showList, StrmType, BuildType, PluginName, DirName)

        
    def BuildPlayonFileList(self, StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName):
        print ("BuildPlayonFileList")
        print StrmType, BuildType, setting1, setting2, setting3, setting4, FolderName
        showList = []
        DetailLST = []
        DetailLST_CHK = []
        self.dircount = 0
        self.filecount = 0
        limit = int(setting3)
        upnpID = self.playon_player()

        if upnpID != False:

            try:
                Directs = (setting1.split('/')) # split folders
                Directs = ([x for x in Directs if x != '']) # remove empty elements
                PluginName = Directs[0]
            except:
                Directs = []
                PluginName = setting1
                pass

            try:
                excludeLST = setting2.split(',')
                excludeLST = ([x.lower() for x in excludeLST if x != '']) # remove empty elements
            except:
                excludeLST = []
                pass
                
            #filter out unwanted folders
            excludeLST += ['back','previous','home','create new super folder','explore favourites','explore  favourites','explore xbmc favourites','explore kodi favourites','isearch','search','clips','seasons','trailers']
                    
            if self.background == False:
                self.updateDialog.update(self.updateDialogProgress, "Building Strms", "Parsing " + BuildType + ": " + (PluginName), 'searching for ' + FolderName)
                
            Match = True
            while Match:

                DetailLST = self.PluginInfo(upnpID)

                #Plugin listitems return parent list during error, catch repeat list and end loops.
                if DetailLST_CHK == DetailLST:
                    break
                else:
                    DetailLST_CHK = DetailLST

                #end while when no more directories to walk
                if len(Directs) <= 1:
                    Match = False
                
                try:
                    for i in range(len(DetailLST)):
                        Detail = (DetailLST[i]).split(',')
                        filetype = Detail[0]
                        title = Detail[1]
                        genre = Detail[2]
                        dur = Detail[3]
                        description = Detail[4]
                        file = Detail[5]

                        if title.lower() not in excludeLST and title != '':
                            if filetype == 'directory':
                                if Directs[0].lower() == title.lower():
                                    print 'directory match'
                                    DirName = Directs[0]
                                    Directs.pop(0) #remove old directory, search next element
                                    upnpID = file
                                    break
                except Exception,e:
                    pass    
                    
            if FolderName != '':
                DirName = FolderName
            
            #all directories found, walk final folder
            if len(Directs) == 0:
                showList = self.PluginWalk(upnpID, excludeLST, limit, StrmType, BuildType, 'video')
            
            print showList, StrmType, BuildType, PluginName, DirName
            self.WriteSTRM(showList, StrmType, BuildType, PluginName, DirName)
        

    def WriteSTRM(self, fileList, StrmType, BuildType, PluginName, DirName):
        print 'WriteSTRM'
        print fileList, StrmType, BuildType, PluginName, DirName
        STRM_LOC = REAL_SETTINGS.getSetting('STRM_LOC')
        
        if REAL_SETTINGS.getSetting('Write_NFOS') == 'true': 
            WriteNFO = True
        else:
            WriteNFO = False

        for i in range(len(fileList)):
            tmpstrLST = (fileList[i]).split('\n')[0]
            file = (fileList[i]).split('\n')[1]
            tmpstr = tmpstrLST.split('//')
            
            dur = tmpstr[0].split(',')[0]
            title = tmpstr[0].split(',')[1]
            eptitle = tmpstr[1]
            description = tmpstr[2]
            genre = tmpstr[3]
            GenreLiveID = tmpstr[5]
            liveID = self.unpackLiveID(GenreLiveID)
            print liveID
            
            if StrmType.lower() == 'tvshow' or StrmType.lower() == 'tvshows' or StrmType.lower() == 'episodes':
                StrmType = 'TVShows'
                FleName = (title + ' - ' + eptitle + '.strm').replace(":"," - ")
                FleName = "".join(i for i in FleName if i not in "\/:*?<>|")

                Folder = os.path.join(STRM_LOC,StrmType)
                FleFolder = os.path.join(Folder,DirName)
                Fle = FleFolder + '/' + FleName
                
            elif StrmType.lower() == 'movie' or StrmType.lower() == 'movies':
                StrmType = 'Movies'
                FleName = (title + '.strm').replace(":",",")
                FleName = "".join(i for i in FleName if i not in "\/:*?<>|")

                Folder = os.path.join(STRM_LOC,StrmType)
                FleFolder = os.path.join(Folder,title.replace(":"," - ").replace("*","").replace("|",''))
                Fle = FleFolder + '/' + FleName
                
            else:
                StrmType = 'Generic'
                FleName = (title + ' - ' + eptitle + '.strm').replace(":",",")
                FleName = "".join(i for i in FleName if i not in "\/:*?<>|")

                Folder = os.path.join(STRM_LOC,StrmType)
                FleFolder = os.path.join(Folder,PluginName,DirName)
                Fle = FleFolder + '/' + FleName
                
            
            type = liveID[0]
            
            try:
                id = liveID[1]
            except:
                id = ['tvshow','0','0','False','1','NR','']
                pass
            
            try:
                rating = liveID[5]
            except:
                rating = 'NA'
                pass

            if not xbmcvfs.exists(FleFolder):
                xbmcvfs.delete(FleFolder)
                xbmcvfs.mkdirs(FleFolder)

            if xbmcvfs.exists(Fle):
                try:
                    xbmcvfs.delete(Fle)
                except:
                    pass
            try:
                f = open(Fle, "w")
                f.write("%s\n" % file)
                f.close
            except:
                pass
                
            print Fle, file

    #return plugin query, not tmpstr
    def PluginQuery(self, path): 
        self.log("PluginQuery") 
        FleType = 'video'
        json_query = self.uni('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "properties":["title","year","mpaa","imdbnumber","description","season","episode","playcount","genre","duration","runtime","showtitle","album","artist","plot","plotoutline","tagline"]}, "id": 1}' % (self.escapeDirJSON(path), FleType))
        json_folder_detail = self.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        return file_detail
    
    
    #Parse Plugin, return essential information. Not tmpstr
    def PluginInfo(self, path):
        print 'PluginInfo'
        json_query = self.uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","properties":["genre","runtime","description"]},"id":1}' % ( (path),))
        json_folder_detail = self.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        Detail = ''
        DetailLST = []
        PluginName = os.path.split(path)[0]

        #run through each result in json return
        for f in (file_detail):
            filetype = re.search('"filetype" *: *"(.*?)"', f)
            label = re.search('"label" *: *"(.*?)"', f)
            genre = re.search('"genre" *: *"(.*?)"', f)
            runtime = re.search('"runtime" *: *([0-9]*?),', f)
            description = re.search('"description" *: *"(.*?)"', f)
            file = re.search('"file" *: *"(.*?)"', f)

            #if core values have info, proceed
            if filetype and file and label:
                filetype = filetype.group(1)
                title = (label.group(1)).replace(',',' ')
                file = file.group(1)

                try:
                    genre = genre.group(1)
                except:
                    genre = 'Unknown'
                    pass

                if genre == '':
                    genre = 'Unknown'

                try:
                    runtime = runtime.group(1)
                except:
                    runtime = 0
                    pass

                if runtime == 0 or runtime == '':
                    runtime = 1800

                try:
                    description = (description.group(1)).replace(',',' ')
                except:
                    description = PluginName
                    pass

                if description == '':
                    description = PluginName

                if title != '':
                    Detail = ((filetype + ',' + title + ',' + genre + ',' + str(runtime) + ',' + description + ',' + file)).replace(',,',',')
                    DetailLST.append(Detail)

        return DetailLST
    
 
    #recursively walk through plugin directories, return tmpstr of all files found.
    def PluginWalk(self, path, excludeLST, limit, StrmType, BuildType, FleType='video'):
        print "PluginWalk"
        print path, excludeLST, limit, StrmType, BuildType, FleType
        dirlimit = limit * 2
        tmpstr = ''
        LiveID = 'tvshow|0|0|False|1|NR|'
        fileList = []
        dirs = []
        Managed = False
        PluginPath = str(os.path.split(path)[0])
        PluginName = PluginPath.replace('plugin://plugin.video.','').replace('plugin://plugin.program.','')
        youtube_plugin = self.youtube_player()
        
        json_query = self.uni('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "properties":["title","year","mpaa","imdbnumber","description","season","episode","playcount","genre","duration","runtime","showtitle","album","artist","plot","plotoutline","tagline"]}, "id": 1}' % ((path), FleType))
        json_folder_detail = self.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        print file_detail
        # try:       
        if BuildType != '':    
            xName = BuildType
            PlugCHK = BuildType
        elif BuildType.lower() == 'playon':
            xName = (path.split('/')[3]).split('-')[0]
            PlugCHK = BuildType
        else:
            xName = PluginName
            PlugCHK = PluginPath.replace('plugin://','')
                
        #run through each result in json return
        for f in (file_detail):

            istvshow = False
            durations = re.search('"duration" *: *([0-9]*?),', f)
            runtimes = re.search('"runtime" *: *([0-9]*?),', f)
            filetypes = re.search('"filetype" *: *"(.*?)"', f)
            labels = re.search('"label" *: *"(.*?)"', f)
            files = re.search('"file" *: *"(.*?)"', f)
            
            #if core variables have info proceed
            if filetypes and labels and files:
                filetype = filetypes.group(1)
                file = files.group(1)
                label = labels.group(1)
                
                print label
                if label.lower() not in excludeLST and label != '':
                    if filetype == 'directory':
                        #try to speed up parsing by not over searching directories when media limit is low
                        if self.filecount < limit and self.dircount < dirlimit:
                        
                            #if no return (bad file), try unquote
                            if not self.PluginInfo(file):
                                print 'unquote'
                                file = unquote(file).replace('",return)','')
                                #remove unwanted reference to super.favorites plugin
                                try:
                                    file = (file.split('ActivateWindow(10025,"')[1])
                                except:
                                    pass

                            dirs.append(file)
                            self.dircount += 1
                        
                    elif filetype == 'file':
                    
                        #Remove PlayMedia to keep link from launching
                        try:
                            file = ((file.split('PlayMedia%28%22'))[1]).replace('%22%29','')
                        except:
                            try:
                                file = ((file.split('PlayMedia("'))[1]).replace('")','')
                            except:
                                pass

                        if file.startswith('plugin%3A%2F%2F'):
                            print 'unquote'
                            file = unquote(file).replace('",return)','')

                        # If music duration returned, else 0
                        try:
                            dur = int(durations.group(1))
                        except Exception,e:
                            dur = 0

                        if dur == 0:
                            try:
                                dur = int(runtimes.group(1))
                            except Exception,e:
                                dur = 3600
                            
                            if not runtimes or dur == 0 or dur == '0':
                                dur = 3600
                        
                        #correct playon default duration
                        if dur == 18000:
                            dur = 3600
                            
                        self.log("buildFileList.dur = " + str(dur))

                        if dur > 0:
                            self.filecount += 1
                            seasonval = -1
                            epval = -1
                            
                            tmpstr = str(dur) + ','
                            labels = re.search('"label" *: *"(.*?)"', f)
                            titles = re.search('"title" *: *"(.*?)"', f)
                            showtitles = re.search('"showtitle" *: *"(.*?)"', f)
                            plots = re.search('"plot" *: *"(.*?)",', f)
                            plotoutlines = re.search('"plotoutline" *: *"(.*?)",', f)
                            years = re.search('"year" *: *([0-9]*?) *(.*?)', f)
                            genres = re.search('"genre" *: *\[(.*?)\]', f)
                            playcounts = re.search('"playcount" *: *([0-9]*?),', f)
                            imdbnumbers = re.search('"imdbnumber" *: *"(.*?)"', f)
                            ratings = re.search('"mpaa" *: *"(.*?)"', f)
                            descriptions = re.search('"description" *: *"(.*?)"', f)
                            episodes = re.search('"episode" *: *(.*?),', f)

                            if (episodes != None and episodes.group(1) != '-1') and showtitles != None and len(showtitles.group(1)) > 0:
                                type = 'tvshow'
                                dbids = re.search('"tvshowid" *: *([0-9]*?),', f)   
                                FolderName = showtitles.group(1) 
                            else:
                                type = 'movie'
                                dbids = re.search('"movieid" *: *([0-9]*?),', f)
                                FolderName = label
                            
                            if self.background == False:
                                if self.filecount == 1:
                                
                                    self.updateDialog.update(self.updateDialogProgress, "Building Strms", "Parsing " + BuildType + ": " + (FolderName), "added " + str(self.filecount) + " entry")
                                else:
                                    self.updateDialog.update(self.updateDialogProgress, "Building Strms", "Parsing " + BuildType + ": " + (FolderName), "added " + str(self.filecount) + " entries")
                    
                            if years == None or len(years.group(1)) == 0:
                                try:
                                    year = int(((showtitles.group(1)).split(' ('))[1].replace(')',''))
                                except Exception,e:
                                    try:
                                        year = int(((labels.group(1)).split(' ('))[1].replace(')',''))
                                    except:
                                        year = 0
                                        pass
                            else:
                                year = 0
                            
                            if genres != None and len(genres.group(1)) > 0:
                                genre = ((genres.group(1).split(',')[0]).replace('"',''))
                            else:
                                genre = 'Unknown'
                            
                            if playcounts != None and len(playcounts.group(1)) > 0:
                                playcount = playcounts.group(1)
                            else:
                                playcount = 1
                            
                            if ratings != None and len(ratings.group(1)) > 0:
                                rating = self.cleanRating(ratings.group(1))
                                if type == 'movie':
                                    rating = rating[0:5]
                                    try:
                                        rating = rating.split(' ')[0]
                                    except:
                                        pass
                            else:
                                rating = 'NR'
                            
                            if imdbnumbers != None and len(imdbnumbers.group(1)) > 0:
                                imdbnumber = imdbnumbers.group(1)
                            else:
                                imdbnumber = 0
                                
                            if dbids != None and len(dbids.group(1)) > 0:
                                dbid = dbids.group(1)
                            else:
                                dbid = 0

                            if plots != None and len(plots.group(1)) > 0:
                                theplot = (plots.group(1)).replace('\\','').replace('\n','')
                            elif descriptions != None and len(descriptions.group(1)) > 0:
                                theplot = (descriptions.group(1)).replace('\\','').replace('\n','')
                            else:
                                theplot = (titles.group(1)).replace('\\','').replace('\n','')
                            
                            try:
                                theplot = (self.trim(theplot, 350, '...'))
                            except Exception,e:
                                self.log("Plot Trim failed" + str(e))
                                theplot = (theplot[:350])
                                
                            #remove // because interferes with playlist split.
                            theplot = theplot.replace('//', ' ')

                            # This is a TV show
                            if (episodes != None and episodes.group(1) != '-1') and showtitles != None and len(showtitles.group(1)) > 0:
                                seasons = re.search('"season" *: *(.*?),', f)
                                episodes = re.search('"episode" *: *(.*?),', f)
                                swtitle = (labels.group(1)).replace('\\','')
                                
                                try:
                                    seasonval = int(seasons.group(1)) 
                                    epval = int(episodes.group(1))
                                except:
                                    seasonval = -1
                                    epval = -1
                                    pass
                                    
                                if seasonval != -1 and epval != -1:
                                    try:
                                        eptitles = swtitle.split(' - ')[1]
                                    except:
                                        try:
                                            eptitles = swtitle.split(' . ')[1]
                                        except:
                                            eptitles = swtitle
                                            pass
                                    print 'ttest', swtitle, seasonval, epval, eptitles
                                else:
                                    #no season, episode meta. try to extract from swtitle
                                    try:
                                        #S01E01 - eptitle or s01e01 - eptitle
                                        SEinfo = (swtitle.split(' - ')[0]).replace('S','s').replace('E','e')
                                        seasonval = SEinfo.split('e')[0].replace('s','')
                                        epval = SEinfo.split('e')[1]
                                        eptitles = (swtitle.split('- ', 1)[1])
                                    except:
                                        try:
                                            #2x01 - eptitle or #2X01 - eptitle
                                            SEinfo = (swtitle.split(' -')[0]).replace('X','x')
                                            seasonval = SEinfo.split('x')[0]
                                            epval = SEinfo.split('x')[1]
                                            eptitles = (swtitle.split('- ', 1)[1])
                                        except:
                                            try:
                                                #2x01 . eptitle or #2X01 . eptitle
                                                SEinfo = (swtitle.split(' . ',1)[0]).replace('X','x')
                                                seasonval = SEinfo.split('x')[0]
                                                epval = SEinfo.split('x')[1]
                                                eptitles = (swtitle.split(' . ', 1)[1])                                               
                                            except: 
                                                eptitles = swtitle
                                                seasonval = -1
                                                epval = -1
                                                pass
                                                
                                print 'tttest', seasonval, epval, eptitles
                                
                                if seasonval > 0 and epval > 0:
                                    swtitle = (('0' if seasonval < 10 else '') + str(seasonval) + 'x' + ('0' if epval < 10 else '') + str(epval) + ' - ' + (eptitles)).replace('  ',' ')
                                else:
                                    swtitle = swtitle.replace(' . ',' - ')
                                    
                                print 'ttttest', swtitle
                                    
                                showtitle = (showtitles.group(1)).replace(' [HD]', '').replace('(Sub) ','').replace('(Dub) ','').replace('[B]','').replace('[/B]','')
                                    
                                # if PlugCHK in DYNAMIC_PLUGIN_TV:
                                    # print 'DYNAMIC_PLUGIN_TV'
         
                                    # if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true': 
                                        # print 'EnhancedGuideData' 

                                        # if imdbnumber == 0:
                                            # imdbnumber = self.getTVDBID(showtitle, year)
                                                
                                        # if genre == 'Unknown':
                                            # genre = (self.getGenre(type, showtitle, year))
                                            
                                        # if rating == 'NR':
                                            # rating = (self.getRating(type, showtitle, year, imdbnumber))
                                            # rating = self.cleanRating(rating)
                                            
                                    # # if imdbnumber != 0:
                                        # # Managed = self.sbManaged(imdbnumber)
                            
                                    # GenreLiveID = [genre, type, imdbnumber, dbid, Managed, 1, rating]
                                    # genre, LiveID = self.packGenreLiveID(GenreLiveID)
                                
                                tmpstr += showtitle + "//" + swtitle + "//" + theplot + "//" + genre + "////" + LiveID
                                istvshow = True

                            else:
                                                                
                                if labels:
                                    label = (labels.group(1)).replace(' [HD]','').replace('(Sub) ','').replace('(Dub) ','').replace('[B]','').replace('[/B]','').replace('//','')
                                
                                if titles:
                                    title = (titles.group(1)).replace(' [HD]','').replace('(Sub) ','').replace('(Dub) ','').replace('[B]','').replace('[/B]','').replace('//','')
                                   
                                tmpstr += (label).replace('\\','').replace('//','') + "//"
                                    
                                album = re.search('"album" *: *"(.*?)"', f)

                                # This is a movie
                                if not album or len(album.group(1)) == 0:
                                    taglines = re.search('"tagline" *: *"(.*?)"', f)
                                    
                                    if taglines != None and len(taglines.group(1)) > 0:
                                        tmpstr += ((taglines.group(1)).replace('\\','').replace('//',''))
                                    else:
                                        tmpstr += 'PluginTV'

                                    # if PlugCHK in DYNAMIC_PLUGIN_MOVIE:
                                        # print 'DYNAMIC_PLUGIN_MOVIE'

                                        # if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true': 
                                            # print 'EnhancedGuideData'    
                                            
                                            # try:
                                                # showtitle = label.split(' (')[0]
                                                # year = (label.split(' (')[1]).replace(')','')
                                            # except:
                                                # showtitle = label
                                                # year = ''
                                                # pass
                                                
                                            # try:
                                                # showtitle = showtitle.split('. ')[1]
                                            # except:
                                                # pass
                                
                                            # if imdbnumber == 0:
                                                # imdbnumber = self.getIMDBIDmovie(showtitle, year)

                                            # if genre == 'Unknown':
                                                # genre = (self.getGenre(type, showtitle, year))

                                            # if rating == 'NR':
                                                # rating = (self.getRating(type, showtitle, year, imdbnumber))
                                                # rating = self.cleanRating(rating)
                                        
                                        # # if imdbnumber != 0:
                                            # # Managed = self.cpManaged(showtitle, imdbnumber)
                                            
                                        # GenreLiveID = [genre, type, imdbnumber, dbid, Managed, 1, rating]
                                        # genre, LiveID = self.packGenreLiveID(GenreLiveID)
                                                    
                                    tmpstr += "//" + theplot + "//" + genre + "////" + (LiveID)
                                
                                else: #Music
                                    LiveID = 'music|0|0|False|1|NR|'
                                    artist = re.search('"artist" *: *"(.*?)"', f)
                                    tmpstr += album.group(1) + "//" + artist.group(1) + "//" + 'Music' + "////" + LiveID
                            
                            #file = file.replace('plugin://plugin.video.youtube/?action=play_video&videoid=', youtube_plugin)
                            tmpstr = tmpstr
                            tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                            tmpstr = tmpstr + '\n' + file.replace("\\\\", "\\")
                            fileList.append(tmpstr)
                                
            if self.filecount >= limit:
                break
        
        for item in dirs: 
        
            if self.filecount >= limit:
                break
                
            #recursively scan all subfolders  
            fileList += self.PluginWalk(item, excludeLST, limit, StrmType, BuildType, FleType)           

        # except:
            # pass
        
        if self.filecount == 0:
            self.log(json_folder_detail)

        self.log("buildFileList return")
        print fileList

        return fileList


    def log(msg, level =xbmc.LOGDEBUG):
        try:
           xbmc.log(ADDON_ID + '-' + ascii(msg), level)
        except Exception,e:
            pass

            
    def uni(self, string, encoding = 'utf-8'):
        if isinstance(string, basestring):
            if not isinstance(string, unicode):
                string = unicode(string, encoding, errors='ignore')
        return string

        
    def utf(self, string):
        if isinstance(string, basestring):
            if isinstance(string, unicode):
               string = string.encode( 'utf-8', 'ignore' )
        return string


    def ascii(self, string):
        if isinstance(string, basestring):
            if isinstance(string, unicode):
               string = string.encode('ascii', 'ignore')
        return string
    
    
    def packGenreLiveID(self, GenreLiveID):
        self.log("packGenreLiveID")
        genre = GenreLiveID[0]
        GenreLiveID.pop(0)
        LiveID = (str(GenreLiveID)).replace("u'",'').replace(',','|').replace('[','').replace(']','').replace("'",'').replace(" ",'') + '|'
        return genre, LiveID
        
        
    def unpackLiveID(self, LiveID):
        self.log("unpackLiveID")
        LiveID = LiveID.split('|')
        return LiveID

        
    def escapeDirJSON(self, dir_name):
        mydir = uni(dir_name)

        if (mydir.find(":")):
            mydir = mydir.replace("\\", "\\\\")
        return mydir

          
    def trim(self, content, limit, suffix):
        if len(content) <= limit:
            return content
        else:
            return content[:limit].rsplit(' ', 1)[0]+suffix
           
           
    def splitall(self, path):
        self.log("splitall")
        allparts = []
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path: # sentinel for relative paths
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts
    
    
    def determineWebServer(self):
        if self.discoveredWebServer:
            return

        self.discoveredWebServer = True
        self.webPort = 8080
        self.webUsername = ''
        self.webPassword = ''
        fle = xbmc.translatePath("special://profile/guisettings.xml")

        try:
            xml = FileAccess.open(fle, "r")
        except Exception,e:
            self.log("determineWebServer Unable to open the settings file")
            self.httpJSON = False
            return

        try:
            dom = parse(xml)
        except Exception,e:
            self.log('determineWebServer Unable to parse settings file')
            self.httpJSON = False
            return

        xml.close()
                
        try:
            plname = dom.getElementsByTagName('webserver')
            self.httpJSON = (plname[0].childNodes[0].nodeValue.lower() == 'true')
            self.log('determineWebServer is ' + str(self.httpJSON))

            if self.httpJSON == True:
                plname = dom.getElementsByTagName('webserverport')
                self.webPort = int(plname[0].childNodes[0].nodeValue)
                self.log('determineWebServer port ' + str(self.webPort))
                plname = dom.getElementsByTagName('webserverusername')
                self.webUsername = plname[0].childNodes[0].nodeValue
                self.log('determineWebServer username ' + self.webUsername)
                plname = dom.getElementsByTagName('webserverpassword')
                self.webPassword = plname[0].childNodes[0].nodeValue
                self.log('determineWebServer password is ' + self.webPassword)
        except Exception,e:
            return


    # Code for sending JSON through http adapted from code by sffjunkie (forum.xbmc.org/showthread.php?t=92196)
    def sendJSON(self, command):
        self.log('sendJSON')
        data = ''
        usedhttp = False

        self.determineWebServer()
        self.log('sendJSON command: ' + command)

        # If there have been problems using the server, just skip the attempt and use executejsonrpc
        if self.httpJSON == True:
            try:
                payload = command.encode('utf-8')
            except Exception,e:
                self.log(str(e))
                return data

            headers = {'Content-Type': 'application/json-rpc; charset=utf-8'}

            if self.webUsername != '':
                userpass = base64.encodestring('%s:%s' % (self.webUsername, self.webPassword))[:-1]
                headers['Authorization'] = 'Basic %s' % userpass

            try:
                conn = httplib.HTTPConnection('127.0.0.1', self.webPort)
                conn.request('POST', '/jsonrpc', payload, headers)
                response = conn.getresponse()

                if response.status == 200:
                    data = uni(response.read())
                    usedhttp = True

                conn.close()
            except Exception,e:
                self.log("Exception when getting JSON data")

        if usedhttp == False:
            self.httpJSON = False
            
            try:
                data = xbmc.executeJSONRPC(self.uni(command))
            except UnicodeEncodeError:
                data = xbmc.executeJSONRPC(ascii(command))

        return self.uni(data)

        
    def plugin_ok(self, plugin):
        self.log("plugin_ok")
        self.PluginFound = False
        self.Pluginvalid = False
        
        addon = os.path.split(plugin)[0]
        addon = (plugin.split('/?')[0]).replace("plugin://","")
        addon = self.splitall(addon)[0]
        self.log("plugin id = " + addon)
        
        try:
            addon_ok = xbmcaddon.Addon(id=addon)
            if addon_ok:
               self.PluginFound = True
        except:
            self.PluginFound = False 
        
        self.log("PluginFound = " + str(self.PluginFound))
        
        return self.PluginFound
                
                
    def youtube_duration(self, YTID):
        self.log("youtube_duration")
        url = 'https://gdata.youtube.com/feeds/api/videos/{0}?v=2'.format(YTID)
        s = urlopen(url).read()
        d = parseString(s)
        e = d.getElementsByTagName('yt:duration')[0]
        a = e.attributes['seconds']
        v = int(a.value)
        return v
        
        
    def youtube_player(self):
        self.log("youtube_player")
        Plugin_1 = self.plugin_ok('plugin.video.bromix.youtube')
        Plugin_2 = self.plugin_ok('plugin.video.youtube')
        
        if Plugin_1 == True:
            path = 'plugin://plugin.video.bromix.youtube/?action=play&id='
        elif Plugin_2 == True:
            path = 'plugin://plugin.video.youtube/?action=play_video&videoid='
        else:
            path = False
            
        return path
            
            
    def playon_player(self):
        print ("playon_player")
        PlayonPath = False
        json_query = ('{"jsonrpc": "2.0", "method": "Files.GetSources", "params": {"media":"video"}, "id": 2}')
        json_folder_detail = self.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in file_detail:
            labels = re.search('"label" *: *"(.*?)"', f)
            files = re.search('"file" *: *"(.*?)"', f)
            try:
                label = (labels.group(1)).lower()
                upnp = (files.group(1))
                if label == 'playon':
                    PlayonPath = upnp
                    break
            except:
                pass

        return PlayonPath

        
    def getGenre(self, type, title, year):
        self.log("getGenre")
        genre = 'Unknown'
        
        try:
            self.log("metahander")
            self.metaget = metahandlers.MetaData(preparezip=False)
            genre = str(self.metaget.get_meta(type, title)['genre'])
            try:
                genre = str(genre.split(',')[0])
            except Exception as e:
                pass
            try:
                genre = str(genre.split(' / ')[0])
            except Exception as e:
                pass
        except Exception,e:
            pass

        if not genre or genre == 'Unknown':

            if type == 'tvshow':
                try:
                    self.log("tvdb_api")
                    genre = str((self.t[title]['genre']))
                    try:
                        genre = str((genre.split('|'))[1])
                    except:
                        pass
                except Exception,e:
                    pass
            else:
                self.log("tmdb")
                movieInfo = str(self.tmdbAPI.getMovie(title, year))
                try:
                    genre = str(movieInfo['genres'][0])
                    genre = str(genre.split("u'")[3]).replace("'}",'')
                except Exception,e:
                    pass

        if not genre or genre == 'None' or genre == 'Empty':
            genre = 'Unknown'
            
        return genre.replace('NA','Unknown')
        
    
    def cleanRating(self, rating):
        self.log("cleanRating")
        rating = rating.replace('Rated ','').replace('US:','').replace('UK:','').replace('Unrated','NR').replace('NotRated','NR').replace('N/A','NR').replace('NA','NR').replace('Approved','NR')
        return rating
    

    def getRating(self, type, title, year, imdbid):
        self.log("getRating")
        rating = 'NR'

        try:
            self.log("metahander")     
            self.metaget = metahandlers.MetaData(preparezip=False)
            rating = self.metaget.get_meta(type, title)['mpaa']
        except Exception,e:
            pass
            
        rating = rating.replace('Unrated','NR').replace('NotRated','NR').replace('N/A','NR').replace('Approved','NR')
        if not rating or rating == 'NR':
        
            if type == 'tvshow':
                try:
                    self.log("tvdb_api")
                    rating = str(self.t[title]['contentrating'])
                    try:
                        rating = rating.replace('|','')
                    except:
                        pass
                except Exception,e:
                    pass
            else:
                if imdbid or imdbid != 0:
                    try:
                        self.log("tmdb")
                        rating = str(self.tmdbAPI.getMPAA(imdbid))
                    except Exception,e:
                        pass

        rating = rating.replace('Unrated','NR').replace('NotRated','NR').replace('N/A','NR').replace('Approved','NR')
        if not rating or rating == 'None' or rating == 'Empty':
            rating = 'NR'
            
        return (self.cleanRating(rating)).replace('M','R')


    def getTVDBID(self, title, year):
        print 'getTVDBID'
        tvdbid = 0
        imdbid = 0
 
        try:
            self.log("metahander")
            self.metaget = metahandlers.MetaData(preparezip=False)
            tvdbid = self.metaget.get_meta('tvshow', title)['tvdb_id']
        except Exception,e:
            pass

        if not tvdbid or tvdbid == 0:
            try:
                self.log("tvdb_api")
                tvdbid = int(self.t[title]['id'])
            except Exception,e:
                pass

        if not tvdbid or tvdbid == 0:
            try:
                imdbid = self.getIMDBIDtv(title)
                if imdbid or imdbid != 0:
                    tvdbid = int(self.getTVDBIDbyIMDB(imdbid))
                if not tvdbid:
                    tvdbid = 0
            except Exception,e:
                pass

        if not tvdbid or tvdbid == 'None' or tvdbid == 'Empty':
            tvdbid = 0

        return tvdbid


    def getIMDBIDtv(self, title):
        print 'getIMDBIDtv'
        imdbid = 0

        try:
            self.log("metahander")
            self.metaget = metahandlers.MetaData(preparezip=False)
            imdbid = self.metaget.get_meta('tvshow', title)['imdb_id']
        except Exception,e:
            pass

        if not imdbid or imdbid == 0:
            try:
                self.log("tvdb_api")
                imdbid = self.t[title]['imdb_id']
                if not imdbid:
                    imdbid = 0
            except Exception,e:
                pass

        if not imdbid or imdbid == 'None' or imdbid == 'Empty':
            imdbid = 0

        return imdbid


    def getTVDBIDbyIMDB(self, imdbid):
        print 'getTVDBIDbyIMDB'
        tvdbid = 0

        try:
            tvdbid = self.tvdbAPI.getIdByIMDB(imdbid)
        except Exception,e:
            pass

        if not tvdbid or tvdbid == 'None' or tvdbid == 'Empty':
            tvdbid = 0
            
        return tvdbid


    def getIMDBIDmovie(self, showtitle, year):
        print 'getIMDBIDmovie'
        imdbid = 0
        try:
            self.log("metahander")
            self.metaget = metahandlers.MetaData(preparezip=False)
            imdbid = (self.metaget.get_meta('movie', showtitle)['imdb_id'])
        except Exception,e:
            pass

        if not imdbid or imdbid == 0:
            try:
                self.log("tmdb")
                movieInfo = (self.tmdbAPI.getMovie(showtitle, year))
                imdbid = (movieInfo['imdb_id'])
                if not imdbid:
                    imdbid = 0
            except Exception,e:
                pass
                
        if not imdbid or imdbid == 'None' or imdbid == 'Empty':
            imdbid = 0
            
        return imdbid
        
    
    def getTVDBIDbyZap2it(self, dd_progid):
        print 'getTVDBIDbyZap2it'
        tvdbid = 0
        
        try:
            tvdbid = self.tvdbAPI.getIdByZap2it(dd_progid)
            if not tvdbid:
                tvdbid = 0
        except Exception,e:
            pass
        
        if not tvdbid or tvdbid == 'None' or tvdbid == 'Empty':
            tvdbid = 0
            
        return tvdbid
        
        
    def getTVINFObySubtitle(self, title, subtitle):
        print 'getTVINFObySubtitle'
        episode = ''
        episodeName = ''
        seasonNumber = 0
        episodeNumber = 0
        
        try:
            episode = self.t[title].search(subtitle, key = 'episodename')
            # Output example: [<Episode 01x01 - My First Day>]
            episode = str(episode[0])
            episode = episode.split('x')
            seasonNumber = int(episode[0].split('Episode ')[1])
            episodeNumber = int(episode[1].split(' -')[0])
            episodeName = str(episode[1]).split('- ')[1].replace('>','')
        except Exception,e:
            pass

        return episodeName, seasonNumber, episodeNumber

        
    def getTVINFObySE(self, title, seasonNumber, episodeNumber):
        print 'getTVINFObySE'
        episode = ''
        episodeName = ''
        episodeDesc = ''
        episodeGenre = 'Unknown'
        
        try:
            episode = self.t[title][seasonNumber][episodeNumber]
            episodeName = str(episode['episodename'])
            episodeDesc = str(episode['overview'])
            episodeGenre = str(self.t[title]['genre'])
            # Output ex. Comedy|Talk Show|
            episodeGenre = str(episodeGenre)
            try:
                episodeGenre = str(episodeGenre.split('|')[1])
            except:
                pass
        except Exception,e:
            pass
        
        if episodeName != '' or episodeName != None:
            if not episodeDesc:
                episodeDesc = episodeName

        return episodeName, episodeDesc, episodeGenre
        
        
    def getMovieINFObyTitle(self, title, year):
        print 'getMovieINFObyTitle'
        imdbid = 0
        plot = ''
        tagline = ''
        genre = 'Unknown'
        
        try:
            movieInfo = self.tmdbAPI.getMovie((title), year)
            imdbid = movieInfo['imdb_id']
            try:
                plot = str(movieInfo['overview'])
            except:
                pass
            try:
                tagline = str(movieInfo['tagline'])
            except:
                pass
            try:
                genre = str(movieInfo['genres'][0])
                genre = str((genre.split("u'")[3])).replace("'}",'')
            except:
                pass
                
            if not imdbid or imdbid == 'None' or imdbid == 'Empty':
                imdbid = 0
                
        except Exception,e:
            pass

        return imdbid, plot, tagline, genre


    def OpenURL(self, url):
        print ("OpenURL")
        try:
            f = urllib2.urlopen(url)
            data = f.readlines()
            f.close()
            return data
        except urllib2.URLError as e:
            return
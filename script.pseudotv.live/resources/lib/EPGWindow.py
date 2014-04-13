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

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import subprocess, os
import time, threading
import datetime, traceback
import sys, re
import urllib
import urllib2

from Playlist import Playlist
from Globals import *
from Channel import Channel
from ChannelList import ChannelList
from FileAccess import FileLock, FileAccess
from xml.etree import ElementTree as ET
from Downloader import *

class EPGWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.focusRow = 0
        self.focusIndex = 0
        self.focusTime = 0
        self.focusEndTime = 0
        self.shownTime = 0
        self.centerChannel = 0
        self.rowCount = 6
        self.channelButtons = [None] * self.rowCount
        self.buttonCache = []
        self.buttonCount = 0
        self.actionSemaphore = threading.BoundedSemaphore()
        self.lastActionTime = time.time()
        self.channelLogos = ''
        self.textcolor = "FFFFFFFF"
        self.focusedcolor = "FF7d7d7d"
        self.clockMode = 0
        self.textfont  = "font14"
        self.startup = time.time()
        self.showingInfo = False
        self.infoOffset = 0
        self.infoOffsetV = 0
        self.log('Using EPG Coloring = ' + str(REAL_SETTINGS.getSetting('EPGcolor_enabled')))
        self.textureButtonFocus = MEDIA_LOC + BUTTON_FOCUS
        self.textureButtonNoFocus = MEDIA_LOC + BUTTON_NO_FOCUS


        for i in range(self.rowCount):
            self.channelButtons[i] = []

        self.clockMode = ADDON_SETTINGS.getSetting("ClockMode")
        self.toRemove = []


    def onFocus(self, controlid):
        pass


    # set the time labels
    def setTimeLabels(self, thetime):
        self.log('setTimeLabels')
        now = datetime.datetime.fromtimestamp(thetime)
        self.getControl(104).setLabel(now.strftime('%A, %b %d'))
        delta = datetime.timedelta(minutes=30)

        for i in range(3):
            if self.clockMode == "0":
                self.getControl(101 + i).setLabel(now.strftime("%I:%M%p").lower())
            else:
                self.getControl(101 + i).setLabel(now.strftime("%H:%M"))

            now = now + delta

        self.log('setTimeLabels return')
        self.log('thetime ' + str(now))


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('EPGWindow: ' + msg, level)

    
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if REAL_SETTINGS.getSetting('enable_Debug') == "true":
            log('EPGWindow: ' + msg, level)
                
    
    def onInit(self):
        self.log('onInit')
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
        
        #Set timebar path, else use alt. path
        self.currentTimeBar = xbmcgui.ControlImage(timex, timey, timew, timeh, MEDIA_LOC + TIME_BAR)  
        self.addControl(self.currentTimeBar)
        
        ### Skin labels, Set textcolor, focusedcolor and font. Rowcount todo ###
        try:
            textcolor = int(self.getControl(100).getLabel(), 16)            

            if textcolor > 0:
                self.textcolor = hex(textcolor)[2:]
                self.logDebug("onInit.Self.textcolor = " + str(self.textcolor))
        except:
            pass
        
        try:
            focusedcolor = int(self.getControl(99).getLabel(), 16)

            if focusedcolor > 0:
                self.focusedcolor = hex(focusedcolor)[2:]
                self.logDebug("onInit.Self.focusedcolor = " + str(self.focusedcolor))
        except:
            pass
        
        try:    
            self.textfont = self.getControl(105).getLabel()
            self.logDebug("onInit.Self.textfont = " + str(self.textfont))

        except:
            pass
        
        # try: 
            # self.rowCount = self.getControl(106).getLabel()
            # self.logDebug("onInit, Self.rowCount = " + str(self.rowCount))       
        # except:
            # pass

        ##################################################################
        
        try:
            if self.setChannelButtons(time.time(), self.MyOverlayWindow.currentChannel) == False:
                self.log('Unable to add channel buttons')
                return

            curtime = time.time()
            self.focusIndex = -1
            basex, basey = self.getControl(113).getPosition()
            baseh = self.getControl(113).getHeight()
            basew = self.getControl(113).getWidth()

            # set the button that corresponds to the currently playing show
            for i in range(len(self.channelButtons[2])):
                left, top = self.channelButtons[2][i].getPosition()
                width = self.channelButtons[2][i].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))

                if curtime >= starttime and curtime <= endtime:
                    self.focusIndex = i
                    self.setFocus(self.channelButtons[2][i])
                    self.focusTime = int(time.time())
                    self.focusEndTime = endtime
                    break

            # If nothing was highlighted, just select the first button
            if self.focusIndex == -1:
                self.focusIndex = 0
                self.setFocus(self.channelButtons[2][0])
                left, top = self.channelButtons[2][0].getPosition()
                width = self.channelButtons[2][0].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))
                self.focusTime = int(starttime + 30)
                self.focusEndTime = endtime
            self.focusRow = 2
            self.setShowInfo()
        except:
            self.log("Unknown EPG Initialization Exception", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)
            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)

            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return

        self.log('onInit return')


    # setup all channel buttons for a given time
    def setChannelButtons(self, starttime, curchannel, singlerow = -1):
        self.log('setChannelButtons ' + str(starttime) + ', ' + str(curchannel))
        self.centerChannel = self.MyOverlayWindow.fixChannel(curchannel)
        # This is done twice to guarantee we go back 2 channels.  If the previous 2 channels
        # aren't valid, then doing a fix on curchannel - 2 may result in going back only
        # a single valid channel.
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        starttime = self.roundToHalfHour(int(starttime))
        self.setTimeLabels(starttime)
        self.shownTime = starttime
        basex, basey = self.getControl(111).getPosition()
        basew = self.getControl(111).getWidth()
        tmpx, tmpy =  self.getControl(110 + self.rowCount).getPosition()
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
        basecur = curchannel
        self.toRemove.append(self.currentTimeBar)
        myadds = []

        for i in range(self.rowCount):
            if singlerow == -1 or singlerow == i:
                self.setButtons(starttime, basecur, i)
                myadds.extend(self.channelButtons[i])
                
            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        basecur = curchannel

        for i in range(self.rowCount):
            self.getControl(301 + i).setLabel(self.MyOverlayWindow.channels[basecur - 1].name)
            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        for i in range(self.rowCount): 
            try:
                self.getControl(311 + i).setLabel(str(curchannel))
            except:
                pass

            try:        
                if REAL_SETTINGS.getSetting("ColorEPG") == "true":
                    self.getControl(321 + i).setImage(self.channelLogos + self.MyOverlayWindow.channels[curchannel - 1].name + '_c.png')
                else:
                    self.getControl(321 + i).setImage(self.channelLogos + self.MyOverlayWindow.channels[curchannel - 1].name + '.png')
            except:
                pass

            curchannel = self.MyOverlayWindow.fixChannel(curchannel + 1)

        if time.time() >= starttime and time.time() < starttime + 5400:
            dif = int((starttime + 5400 - time.time()))
            self.currentTimeBar.setPosition(int((basex + basew - 2) - (dif * (basew / 5400.0))), timey)
        else:
            if time.time() < starttime:
                self.currentTimeBar.setPosition(basex + 2, timey)
            else:
                 self.currentTimeBar.setPosition(basex + basew - 2 - timew, timey)

        myadds.append(self.currentTimeBar)

        try:
            self.removeControls(self.toRemove)
        except:
            for cntrl in self.toRemove:
                try:
                    self.removeControl(cntrl)
                except:
                    pass
        try:
            self.addControls(myadds)
            self.toRemove = []
            self.log('setChannelButtons return')
        except:
            xbmc.log('self.addControls(myadds) in use')
            pass


    # round the given time down to the nearest half hour
    def roundToHalfHour(self, thetime):
        n = datetime.datetime.fromtimestamp(thetime)
        delta = datetime.timedelta(minutes=30)

        if n.minute > 29:
            n = n.replace(minute=30, second=0, microsecond=0)
        else:
            n = n.replace(minute=0, second=0, microsecond=0)

        return time.mktime(n.timetuple())


    # create the buttons for the specified channel in the given row
    def setButtons(self, starttime, curchannel, row):
        self.log('setButtons ' + str(starttime) + ", " + str(curchannel) + ", " + str(row))

        try:
            curchannel = self.MyOverlayWindow.fixChannel(curchannel)
            basex, basey = self.getControl(111 + row).getPosition()
            baseh = self.getControl(111 + row).getHeight()
            basew = self.getControl(111 + row).getWidth()

            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(curchannel) + '_type'))
            self.lastExitTime = (ADDON_SETTINGS.getSetting("LastExitTime"))
            if xbmc.Player().isPlaying() == False:
                self.log('No video is playing, not adding buttons')
                self.closeEPG()
                return False

            # Backup all of the buttons to an array
            self.toRemove.extend(self.channelButtons[row])
            del self.channelButtons[row][:]

            # if the channel is paused, then only 1 button needed

            nowDate = datetime.datetime.now()
            self.logDebug("setbuttonnowtime " + str(nowDate))
            if self.MyOverlayWindow.channels[curchannel - 1].isPaused:
                self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle() + " (paused)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, textColor=self.textcolor, focusedColor=self.focusedcolor))
            else:
                # Find the show that was running at the given time
                # Use the current time and show offset to calculate it
                # At timedif time, channelShowPosition was playing at channelTimes
                # The only way this isn't true is if the current channel is curchannel since
                # it could have been fast forwarded or rewinded (rewound)?
                if curchannel == self.MyOverlayWindow.currentChannel: #currentchannel epg
                    
                    #Live TV pull date from the playlist entry
                    if chtype == 8:
                       playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                       #episodetitle is actually the start time of each show that the playlist gets from channellist.py
                       tmpDate = self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)
                       self.logDebug("setButtons.setbuttonnowtime2 " + str(tmpDate))
                       t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                       epochBeginDate = time.mktime(t)
                       #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                       #videotime = (nowDate - beginDate).seconds
                       videotime = time.time() - epochBeginDate
                       reftime = time.time()
                    else:
                       playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                       videotime = xbmc.Player().getTime()
                       reftime = time.time()
                   
                else:
                    #Live TV pull date from the playlist entry
                    if chtype == 8:
                       playlistpos = self.MyOverlayWindow.channels[curchannel - 1].playlistPosition
                       #playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                       #episodetitle is actually the start time of each show that the playlist gets from channellist.py
                       tmpDate = self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)
                       self.logDebug("setButtons.setbuttonnowtime2 " + str(tmpDate))
                       t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                       epochBeginDate = time.mktime(t)
                       #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                       #videotime = (nowDate - beginDate).seconds
                       #loop to ensure we get the current show in the playlist
                       while epochBeginDate + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) <  time.time():
                            epochBeginDate += self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                            playlistpos = self.MyOverlayWindow.channels[curchannel - 1].fixPlaylistIndex(playlistpos + 1)
                       videotime = time.time() - epochBeginDate
                       reftime = time.time()
                       
                    else:
                       playlistpos = self.MyOverlayWindow.channels[curchannel - 1].playlistPosition #everyotherchannel epg
                       videotime = self.MyOverlayWindow.channels[curchannel - 1].showTimeOffset
                       reftime = self.MyOverlayWindow.channels[curchannel - 1].lastAccessTime

                    self.log('videotime  & reftime  + starttime + channel === ' + str(videotime) + ', ' + str(reftime) + ', ' + str(starttime) + ', ' + str(curchannel))

                # normalize reftime to the beginning of the video
                reftime -= videotime

                while reftime > starttime:
                    playlistpos -= 1
                    # No need to check bounds on the playlistpos, the duration function makes sure it is correct
                    reftime -= self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)

                while reftime + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < starttime:
                    reftime += self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                    playlistpos += 1

                # create a button for each show that runs in the next hour and a half
                endtime = starttime + 5400
                totaltime = 0
                totalloops = 0

                while reftime < endtime and totalloops < 1000:
                    xpos = int(basex + (totaltime * (basew / 5400.0)))
                    tmpdur = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                    shouldskip = False

                    # this should only happen the first time through this loop
                    # it shows the small portion of the show before the current one
                    if reftime < starttime:
                        tmpdur -= starttime - reftime
                        reftime = starttime

                        if tmpdur < 60 * 3:
                            shouldskip = True

                    # Don't show very short videos
                    if self.MyOverlayWindow.hideShortItems and shouldskip == False and chtype <= 7:
                        if self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < self.MyOverlayWindow.shortItemLength:
                            shouldskip = True
                            tmpdur = 0
                        else:
                            nextlen = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos + 1)
                            prevlen = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos - 1)

                            if nextlen < 60:
                                tmpdur += nextlen / 2

                            if prevlen < 60:
                                tmpdur += prevlen / 2

                    width = int((basew / 5400.0) * tmpdur)

                    if width < 30 and shouldskip == False:
                        width = 30
                        tmpdur = int(30.0 / (basew / 5400.0))

                    if width + xpos > basex + basew:
                        width = basex + basew - xpos

                    if shouldskip == False and width >= 30:
                        mylabel = self.MyOverlayWindow.channels[curchannel - 1].getItemTitle(playlistpos)
                        mygenre = self.MyOverlayWindow.channels[curchannel - 1].getItemgenre(playlistpos)
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(curchannel) + '_type'))
                                
                        if REAL_SETTINGS.getSetting('EPGcolor_enabled') == '1':
                            if FileAccess.exists(EPGGENRE_LOC + mygenre + '.png'):
                                self.textureButtonNoFocusGenre = (EPGGENRE_LOC + mygenre + '.png')
                            else:
                                self.textureButtonNoFocusGenre = (EPGGENRE_LOC + 'Unknown' + '.png')    
                            self.channelButtons[row].append(xbmcgui.ControlButton(xpos, basey, width, baseh, mylabel, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocusGenre, alignment=4, font=self.textfont, textColor=self.textcolor, focusedColor=self.focusedcolor))
                        
                        elif REAL_SETTINGS.getSetting('EPGcolor_enabled') == '2':
                            if FileAccess.exists(EPGGENRE_LOC + str(chtype) + '.png'):
                                self.textureButtonNoFocusChtype = (EPGGENRE_LOC + str(chtype) + '.png')
                            else:
                                self.textureButtonNoFocusGenre = (EPGGENRE_LOC + 'Unknown' + '.png') 
                            self.channelButtons[row].append(xbmcgui.ControlButton(xpos, basey, width, baseh, mylabel, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocusChtype, alignment=4, font=self.textfont, textColor=self.textcolor, focusedColor=self.focusedcolor))
                        
                        else:            
                            self.channelButtons[row].append(xbmcgui.ControlButton(xpos, basey, width, baseh, mylabel, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, font=self.textfont, textColor=self.textcolor, focusedColor=self.focusedcolor))

                    totaltime += tmpdur
                    reftime += tmpdur
                    playlistpos += 1
                    totalloops += 1

                if totalloops >= 1000:
                    self.log("Broken big loop, too many loops, reftime is " + str(reftime) + ", endtime is " + str(endtime))

                # If there were no buttons added, show some default button
                if len(self.channelButtons[row]) == 0:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].name, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, textColor=self.textcolor, focusedColor=self.focusedcolor))
        except:
            self.log("Exception in setButtons", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

        self.log('setButtons return')
        return True


    def onAction(self, act):
        self.log('onAction ' + str(act.getId()))

        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        action = act.getId()

        try:
            if action in ACTION_PREVIOUS_MENU:
                self.closeEPG()           
                if self.showingInfo:
                    self.infoOffset = 0
                    self.infoOffsetV = 0
            
            elif action == ACTION_MOVE_DOWN: 
                self.GoDown()           
                if self.showingInfo:
                    self.infoOffsetV -= 1
            
            elif action == ACTION_MOVE_UP:
                self.GoUp()           
                if self.showingInfo:
                    self.infoOffsetV += 1
            
            elif action == ACTION_MOVE_LEFT:
                self.GoLeft()           
                if self.showingInfo:
                    self.infoOffset -= 1
            
            elif action == ACTION_MOVE_RIGHT:
                self.GoRight()           
                if self.showingInfo:
                    self.infoOffset += 1
            
            elif action == ACTION_STOP:
                self.closeEPG()           
                if self.showingInfo:
                    self.infoOffset = 0
                    self.infoOffsetV = 0
            
            elif action == ACTION_SELECT_ITEM:
                lastaction = time.time() - self.lastActionTime           
                if self.showingInfo:
                    self.infoOffset = 0
                    self.infoOffsetV = 0

                if lastaction >= 2:
                    self.selectShow()
                    self.closeEPG()
                    self.lastActionTime = time.time()
            
            elif action == ACTION_MOVE_DOWN: 
                self.GoDown()           
                if self.showingInfo:
                    self.infoOffsetV -= 1
            
            elif action == ACTION_PAGEDOWN: 
                self.GoPgDown()           
            
            elif action == ACTION_MOVE_UP:
                self.GoUp()           
                if self.showingInfo:
                    self.infoOffsetV += 1
            elif action == ACTION_PAGEUP:
                self.GoPgUp()

        except:
            self.log("Unknown EPG Exception", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)

            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return

        self.actionSemaphore.release()
        self.log('onAction return')


    def closeEPG(self):
        self.log('closeEPG')

        try:
            self.removeControl(self.currentTimeBar)
            self.MyOverlayWindow.startSleepTimer()
        except:
            pass

        self.close()


    def onControl(self, control):
        self.log('onControl')


    # Run when a show is selected, so close the epg and run the show
    def onClick(self, controlid):
        self.log('onClick')

        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        lastaction = time.time() - self.lastActionTime

        if lastaction >= 2:
            try:
                selectedbutton = self.getControl(controlid)
            except:
                self.actionSemaphore.release()
                self.log('onClick unknown controlid ' + str(controlid))
                return

            for i in range(self.rowCount):
                for x in range(len(self.channelButtons[i])):
                    mycontrol = 0
                    mycontrol = self.channelButtons[i][x]

                    if selectedbutton == mycontrol:
                        self.focusRow = i
                        self.focusIndex = x
                        self.selectShow()
                        self.closeEPG()
                        self.lastActionTime = time.time()
                        self.actionSemaphore.release()
                        self.log('onClick found button return')
                        return

            self.lastActionTime = time.time()
            self.closeEPG()

        self.actionSemaphore.release()
        self.log('onClick return')
    
    
    def GoPgDown(self):
        self.log('GoPgDown')
        newchannel = self.centerChannel
        for x in range(0, 6):
            newchannel = self.MyOverlayWindow.fixChannel(newchannel + 1)
        self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(newchannel))
        self.setProperButton(0)
        self.log('GoPgDown return')

    
    def GoPgUp(self):
        self.log('GoPgUp')
        newchannel = self.centerChannel
        for x in range(0, 6):
            newchannel = self.MyOverlayWindow.fixChannel(newchannel - 1, False)
        self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(newchannel))
        self.setProperButton(0)
        self.log('GoPgUp return')

        
    def GoDown(self):
        self.log('goDown')

        # change controls to display the proper junks
        if self.focusRow == self.rowCount - 1:
            self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(self.centerChannel + 1))
            self.focusRow = self.rowCount - 2

        self.setProperButton(self.focusRow + 1)
        self.log('goDown return')


    def GoUp(self):
        self.log('goUp')

        # same as godown
        # change controls to display the proper junks
        if self.focusRow == 0:
            self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(self.centerChannel - 1, False))
            self.focusRow = 1

        self.setProperButton(self.focusRow - 1)
        self.log('goUp return')


    def GoLeft(self):
        self.log('goLeft')
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        basew = self.getControl(111 + self.focusRow).getWidth()

        # change controls to display the proper junks
        if self.focusIndex == 0:
            left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            self.setChannelButtons(self.shownTime - 1800, self.centerChannel)
            curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

            if(curbutidx - 1) >= 0:
                self.focusIndex = curbutidx - 1
            else:
                self.focusIndex = 0
        else:
            self.focusIndex -= 1

        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
        self.setShowInfo()
        self.focusEndTime = endtime
        self.focusTime = starttime + 30
        self.log('goLeft return')


    def GoRight(self):
        self.log('goRight')
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        basew = self.getControl(111 + self.focusRow).getWidth()

        # change controls to display the proper junks
        if self.focusIndex == len(self.channelButtons[self.focusRow]) - 1:
            left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            self.setChannelButtons(self.shownTime + 1800, self.centerChannel)
            curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

            if(curbutidx + 1) < len(self.channelButtons[self.focusRow]):
                self.focusIndex = curbutidx + 1
            else:
                self.focusIndex = len(self.channelButtons[self.focusRow]) - 1
        else:
            self.focusIndex += 1

        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
        self.setShowInfo()
        self.focusEndTime = endtime
        self.focusTime = starttime + 30
        self.log('goRight return')


    def findButtonAtTime(self, row, selectedtime):
        self.log('findButtonAtTime ' + str(row))
        basex, basey = self.getControl(111 + row).getPosition()
        baseh = self.getControl(111 + row).getHeight()
        basew = self.getControl(111 + row).getWidth()

        for i in range(len(self.channelButtons[row])):
            left, top = self.channelButtons[row][i].getPosition()
            width = self.channelButtons[row][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if selectedtime >= starttime and selectedtime <= endtime:
                return i

        return -1


    # based on the current focus row and index, find the appropriate button in
    # the new row to set focus to
    def setProperButton(self, newrow, resetfocustime = False):
        self.log('setProperButton ' + str(newrow))
        self.focusRow = newrow
        basex, basey = self.getControl(111 + newrow).getPosition()
        baseh = self.getControl(111 + newrow).getHeight()
        basew = self.getControl(111 + newrow).getWidth()

        for i in range(len(self.channelButtons[newrow])):
            left, top = self.channelButtons[newrow][i].getPosition()
            width = self.channelButtons[newrow][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if self.focusTime >= starttime and self.focusTime <= endtime:
                self.focusIndex = i
                self.setFocus(self.channelButtons[newrow][i])
                self.setShowInfo()
                self.focusEndTime = endtime

                if resetfocustime:
                    self.focusTime = starttime + 30

                self.log('setProperButton found button return')
                return

        self.focusIndex = 0
        self.setFocus(self.channelButtons[newrow][0])
        left, top = self.channelButtons[newrow][0].getPosition()
        width = self.channelButtons[newrow][0].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.focusEndTime = endtime

        if resetfocustime:
            self.focusTime = starttime + 30

        self.setShowInfo()
        self.log('setProperButton return')

        
    def setShowInfo(self):
        self.log('setShowInfo')
        self.showingInfo = True
        ART_CACHE = False
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        baseh = self.getControl(111 + self.focusRow).getHeight()
        basew = self.getControl(111 + self.focusRow).getWidth()
        # use the selected time to set the video
        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex + (width / 2)
        starttime = self.shownTime + (left / (basew / 5400.0))
        chnoffset = self.focusRow - 2
        newchan = self.centerChannel
        self.Downloader = Downloader()   
        id = ''
        EnhancedLiveTV = True
        
        while chnoffset != 0:
            if chnoffset > 0:
                newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                chnoffset -= 1
            else:
                newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                chnoffset += 1

        plpos = self.determinePlaylistPosAtTime(starttime, newchan)

        if plpos == -1:
            self.log('Unable to find the proper playlist to set from EPG')
            return

        
        #Check if VideoWindow Patch found, change label.
        if FileAccess.exists(os.path.join(skinPath, 'Custom_PTVL_9506.xml')):
            try:
                self.getControl(523).setLabel('NOW WATCHING:')
                Patched = True
            except:
                pass
        else:
            Patched = False

            
        #Change Label when Dynamic artwork enabled
        if REAL_SETTINGS.getSetting("art.enable") == "true":        
            
            if self.infoOffset > 0:
                self.getControl(522).setLabel('COMING UP:')
            elif self.infoOffset < 0:
                self.getControl(522).setLabel('ALREADY SEEN:')          
            elif self.infoOffset == 0 and self.infoOffsetV == 0:
                self.getControl(522).setLabel('NOW WATCHING:')       
            elif self.infoOffsetV < 0 and self.infoOffset == 0:
                self.getControl(522).setLabel('ON NOW:')            
            elif self.infoOffset == 0 and self.infoOffsetV == 0:
                self.getControl(522).setLabel('NOW WATCHING:')            
        else:
            self.getControl(522).setLabel('NOW WATCHING:')       
        
        type = ''
        tvdbid = 0
        imdbid = 0
        dbid = 0

        mediapath = uni(self.MyOverlayWindow.channels[newchan - 1].getItemFilename(plpos))        
        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(newchan) + '_type'))
        setting3 = ADDON_SETTINGS.getSetting('Channel_' + str(newchan) + '_3')
        
        if setting3 == 'ustvnow':
            EnhancedLiveTV = False
        
        genre = uni(self.MyOverlayWindow.channels[newchan - 1].getItemgenre(plpos))
        title = uni(self.MyOverlayWindow.channels[newchan - 1].getItemTitle(plpos))
        LiveID = uni(self.MyOverlayWindow.channels[newchan - 1].getItemLiveID(plpos))
        
        try:
            type1 = str(self.getControl(507).getLabel())
            self.log('setShowInfo.type1 = ' + str(type1))  
        except:
            pass
        
        try:
            type2 = str(self.getControl(509).getLabel())
            self.log('setShowInfo.type2 = ' + str(type2))  
        except:
            pass
        
        jpg = ['banner', 'fanart', 'folder', 'landscape', 'poster']
        png = ['character', 'clearart', 'logo', 'disc']
        
        if type1 in jpg:
            type1EXT = (type1 + '.jpg')
        else:
            type1EXT = (type1 + '.png')
        self.logDebug('setShowInfo.type1.ext = ' + str(type1EXT))  
        
        if type2 in jpg:
            type2EXT = (type2 + '.jpg')
        else:
            type2EXT = (type2 + '.png')
        self.logDebug('setShowInfo.type2.ext = ' + str(type2EXT))   
        
        #rename art types for script.artwork.downloader
        arttype1 = type1.replace("folder", "poster").replace("character", "characterart").replace("logo", "clearlogo").replace("disc", "discart")
        arttype2 = type2.replace("folder", "poster").replace("character", "characterart").replace("logo", "clearlogo").replace("disc", "discart")
        
        if not 'LiveID' in LiveID:
            try:
                LiveLST = LiveID.split("|", 4)
                imdbid = LiveLST[0]
                imdbid = imdbid.split('imdb_', 1)[-1]
                tvdbid = LiveLST[1]
                tvdbid = tvdbid.split('tvdb_', 1)[-1]
                SBCP = LiveLST[2]
                
                if 'dbid_' in LiveLST[3]:
                    dbidTYPE = LiveLST[3]
                    dbidTYPE = dbidTYPE.split('dbid_', 1)[-1]
                    dbid = dbidTYPE.split(',')[0]
                    type = dbidTYPE.split(',', 1)[-1]

                    if type == 'tvshow':
                        id = tvdbid
                    elif type == 'movie':
                        id = imdbid
                    
                    if REAL_SETTINGS.getSetting("TVFileSys") == "2" and type == 'tvshow':
                        ART_CACHE = True
                    elif REAL_SETTINGS.getSetting("MovieFileSys") == "1" and type == 'movie':
                        ART_CACHE = True

                else:
                    UnairedTYPE = LiveLST[3]
                    UnairedTYPE = UnairedTYPE.split('dbid_', 1)[-1]
                    Unaired = UnairedTYPE.split(',')[0]
                    type = UnairedTYPE.split(',', 1)[-1]
            except:
                self.log('setShowInfo.LiveLST Failed')
                pass     
            
            try:
                #Try, and pass if label isn't found (Backward compatibility with PTV Skins)
                #Sickbeard/Couchpotato
                if SBCP == 'SB':
                    self.getControl(511).setImage(DEFAULT_IMAGES_LOC + 'SB.png')
                elif SBCP == 'CP':
                    self.getControl(511).setImage(DEFAULT_IMAGES_LOC + 'CP.png')
                else:
                    self.getControl(511).setImage(DEFAULT_IMAGES_LOC + 'NA.png')
            except:
                self.getControl(511).setImage(DEFAULT_IMAGES_LOC + 'NA.png')
                pass     

            try:
                #Try, and pass if label isn't found (Backward compatibility with PTV Skins)             
                #Unaired/aired
                if Unaired == 'NEW':
                    self.getControl(512).setImage(MEDIA_LOC + 'NEW.png')
                elif Unaired == 'OLD':
                    self.getControl(512).setImage(MEDIA_LOC + 'OLD.png')                  
                else:
                    self.getControl(512).setImage(MEDIA_LOC + 'NA.png')
            except:
                self.getControl(512).setImage(MEDIA_LOC + 'NA.png')
                pass     

        if REAL_SETTINGS.getSetting("art.enable") == "true":
            self.log('setShowInfo.Dynamic artwork enabled')
        
            # Local Chtypes
            if chtype <= 7:
                mediapathSeason, filename = os.path.split(mediapath)
                mediapathSeries = os.path.dirname(mediapathSeason)
                
                if ART_CACHE:
                    fle1 = id + '-' + type1EXT
                    fle1Path = os.path.join(ART_LOC, fle1)
                    try:
                        if FileAccess.exists(fle1Path):
                            self.getControl(508).setImage(fle1Path)
                        else:
                            self.getControl(508).setImage(MEDIA_LOC + type1 + '.png')

                            if REAL_SETTINGS.getSetting("EnableDown") == "1" and chtype != 7:
                                link = self.Downloader.DownloadArt(type, id, fle1, ART_LOC, ART_LOC)
                                self.getControl(508).setImage(link)
                    except:
                        pass
                        
                else:                    
                    #artwork type1 (508)
                    mediapathSeries1 = ascii(os.path.join(mediapathSeries, type1EXT))
                    mediapathSeason1 = ascii(os.path.join(mediapathSeason, type1EXT))

                    try:
                        if FileAccess.exists(mediapathSeries1):
                            self.getControl(508).setImage(mediapathSeries1)

                        elif FileAccess.exists(mediapathSeason1):
                            self.getControl(508).setImage(mediapathSeason1)

                        else:
                            self.getControl(508).setImage(MEDIA_LOC + type1 + '.png')

                            if REAL_SETTINGS.getSetting("EnableDown") == "2" and chtype != 7:
                                xbmc.executebuiltin('XBMC.runscript(script.artwork.downloader, silent=true, mediatype='+type+', dbid='+dbid+', '+arttype1+')')
                                
                            elif REAL_SETTINGS.getSetting("EnableDown") == "1" and chtype != 7:
                                link = self.Downloader.DownloadArt(type, id, type1EXT, mediapathSeason, mediapathSeries)                        
                                self.getControl(508).setImage(link)
                    except:
                        pass
                   
                if ART_CACHE:
                    fle2 = id + '-' + type2EXT
                    fle2Path = os.path.join(ART_LOC, fle2)
                    
                    try:
                        if FileAccess.exists(fle2Path):
                            self.getControl(510).setImage(fle2Path)
                        else:
                            self.getControl(510).setImage(MEDIA_LOC + type2 + '.png')
                            
                            if REAL_SETTINGS.getSetting("EnableDown") == "1" and chtype != 7:
                                link = self.Downloader.DownloadArt(type, id, fle2, ART_LOC, ART_LOC)
                                self.getControl(510).setImage(link)
                    except:
                        pass
                                
                else:
                    #artwork type2 (510)
                    mediapathSeries2 = ascii(os.path.join(mediapathSeries, type2EXT))
                    mediapathSeason2 = ascii(os.path.join(mediapathSeason, type2EXT))
                    
                    try:
                        if FileAccess.exists(mediapathSeries2):
                            self.getControl(510).setImage(mediapathSeries2)
                        elif FileAccess.exists(mediapathSeason2):
                            self.getControl(510).setImage(mediapathSeason2)
                        else:
                            self.getControl(510).setImage(MEDIA_LOC + type2 + '.png')

                            if REAL_SETTINGS.getSetting("EnableDown") == "2" and chtype != 7:
                                xbmc.executebuiltin('XBMC.runscript(script.artwork.downloader, silent=true, mediatype='+type+', dbid='+dbid+', '+arttype2+')')
                                
                            elif REAL_SETTINGS.getSetting("EnableDown") == "1" and chtype != 7:
                                link = self.Downloader.DownloadArt(type, id, type2EXT, mediapathSeason, mediapathSeries)
                                self.getControl(510).setImage(link)
                    except:
                        pass
      
                        
            #LiveTV Chtypes
            elif chtype == 8:
                if REAL_SETTINGS.getSetting('EnhancedLiveTV') == 'true' and REAL_SETTINGS.getSetting('Live.art.enable') == 'true' and EnhancedLiveTV == True:
                    self.log('LiveTV Art Enabled')
                    
                    if type == 'tvshow':
                        id = tvdbid
                        fle1 = tvdbid + '-' + type1EXT
                        fle2 = tvdbid + '-' + type2EXT
                    elif type == 'movie':
                        id = imdbid
                        fle1 = imdbid + '-' + type1EXT
                        fle2 = imdbid + '-' + type2EXT
                    
                    flename1 = (ART_LOC + fle1)
                    flename2 = (ART_LOC + fle2)
                    
                    try:
                        if FileAccess.exists(flename1):
                            self.getControl(508).setImage(flename1)
                        else: 
                            self.getControl(508).setImage(MEDIA_LOC + type1 + '.png')  
                            link = self.Downloader.DownloadArt(type, id, fle1, ART_LOC, ART_LOC)
                            self.getControl(508).setImage(link)
                    except:
                        pass
                    
                    try:
                        if FileAccess.exists(flename2):
                            self.getControl(510).setImage(flename2)
                        else:   
                            self.getControl(510).setImage(MEDIA_LOC + type2 + '.png')  
                            link = self.Downloader.DownloadArt(type, id, fle2, ART_LOC, ART_LOC)
                            self.getControl(510).setImage(link)
                    except:
                        pass         
                
                else:#fallback all artwork because live art disabled
                    self.getControl(508).setImage(MEDIA_LOC + type1 + '.png')
                    self.getControl(510).setImage(MEDIA_LOC + type2 + '.png')
                    
            elif chtype == 9:
                self.getControl(508).setImage(MEDIA_LOC + 'EPG.Internet.508.png')
                self.getControl(510).setImage(MEDIA_LOC + 'EPG.Internet.510.png')
            
            elif chtype == 10:
                self.getControl(508).setImage(MEDIA_LOC + 'EPG.Youtube.508.png')
                self.getControl(510).setImage(MEDIA_LOC + 'EPG.Youtube.510.png')
            
            elif chtype == 11:
                self.getControl(508).setImage(MEDIA_LOC + 'EPG.RSS.508.png')
                self.getControl(510).setImage(MEDIA_LOC + 'EPG.RSS.510.png')
            
            elif chtype == 13:
                self.getControl(508).setImage(MEDIA_LOC + 'EPG.LastFM.508.png')
                self.getControl(510).setImage(MEDIA_LOC + 'EPG.LastFM.510.png')  
            
            elif chtype == 14:
                self.getControl(508).setImage(MEDIA_LOC + 'EPG.Extras.508.png')
                self.getControl(510).setImage(MEDIA_LOC + 'EPG.Extras.510.png')  

        ItemTitle = (self.MyOverlayWindow.channels[newchan - 1].getItemTitle(plpos)).replace("*NEW*", "")
        self.getControl(500).setLabel(ItemTitle)
        self.getControl(501).setLabel(self.MyOverlayWindow.channels[newchan - 1].getItemEpisodeTitle(plpos))
        self.getControl(502).setLabel(self.MyOverlayWindow.channels[newchan - 1].getItemDescription(plpos))
        
        if REAL_SETTINGS.getSetting("ColorEPG") == "true":
            self.getControl(503).setImage(self.channelLogos + ascii(self.MyOverlayWindow.channels[newchan - 1].name) + '_c.png')
        else:
            self.getControl(503).setImage(self.channelLogos + ascii(self.MyOverlayWindow.channels[newchan - 1].name) + '.png')
        self.log('setShowInfo return')

    # using the currently selected button, play the proper shows
    def selectShow(self):
        self.log('selectShow')
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        baseh = self.getControl(111 + self.focusRow).getHeight()
        basew = self.getControl(111 + self.focusRow).getWidth()
        # use the selected time to set the video
        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex + (width / 2)
        starttime = self.shownTime + (left / (basew / 5400.0))
        chnoffset = self.focusRow - 2
        newchan = self.centerChannel

        nowDate = datetime.datetime.now()
        
        while chnoffset != 0:
            if chnoffset > 0:
                newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                chnoffset -= 1
            else:
                newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                chnoffset += 1

        plpos = self.determinePlaylistPosAtTime(starttime, newchan)

        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(newchan) + '_type'))
        
        if plpos == -1:
            self.log('Unable to find the proper playlist to set from EPG', xbmc.LOGERROR)
            return
       
        timedif = (time.time() - self.MyOverlayWindow.channels[newchan - 1].lastAccessTime)
        
        pos = self.MyOverlayWindow.channels[newchan - 1].playlistPosition
        
        showoffset = self.MyOverlayWindow.channels[newchan - 1].showTimeOffset

        
        #code added for "LiveTV" types
        #Get the Start time of the show from "episodeitemtitle"
        #we just passed this from channellist.py ; just a fill in to get value
        #Start at the beginning of the playlist get the first epoch date
        #position pos of the playlist convert the string add until we get to the current item in the playlist

        if chtype == 8:
            tmpDate = self.MyOverlayWindow.channels[newchan - 1].getItemtimestamp(pos)
            self.log("selectshow tmpdate " + str(tmpDate))
            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
            epochBeginDate = time.mktime(t)
            #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
            #loop till we get to the current show  
            while epochBeginDate + self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos) <  time.time():
                epochBeginDate += self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos)
                pos = self.MyOverlayWindow.channels[newchan - 1].fixPlaylistIndex(pos + 1)
                self.log('live tv while loop')

        # adjust the show and time offsets to properly position inside the playlist
        else:
            while showoffset + timedif > self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos):
                self.log('duration ' + str(self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos)))
                timedif -= self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos) - showoffset
                pos = self.MyOverlayWindow.channels[newchan - 1].fixPlaylistIndex(pos + 1)
                showoffset = 0

            self.log('pos + plpos ' + str(pos) +', ' + str(plpos))
        
        if self.MyOverlayWindow.currentChannel == newchan:
            if plpos == xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition():
                self.log('selectShow return current show')
                return

            if chtype == 8:
                self.log('selectShow return current LiveTV channel')
                return
        
        if pos != plpos:
            if chtype == 8:
                self.log('selectShow return different LiveTV channel')
                return
            else:
                self.MyOverlayWindow.channels[newchan - 1].setShowPosition(plpos)
                self.MyOverlayWindow.channels[newchan - 1].setShowTime(0)
                self.MyOverlayWindow.channels[newchan - 1].setAccessTime(time.time())

        self.MyOverlayWindow.newChannel = newchan
        self.log('selectShow return')
        


    def determinePlaylistPosAtTime(self, starttime, channel):
        self.log('determinePlaylistPosAtTime ' + str(starttime) + ', ' + str(channel))
        channel = self.MyOverlayWindow.fixChannel(channel)

        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
        self.lastExitTime = ADDON_SETTINGS.getSetting("LastExitTime")
        nowDate = datetime.datetime.now()
        # if the channel is paused, then it's just the current item
        if self.MyOverlayWindow.channels[channel - 1].isPaused:
            self.log('determinePlaylistPosAtTime paused return')
            return self.MyOverlayWindow.channels[channel - 1].playlistPosition
        else:
            # Find the show that was running at the given time
            # Use the current time and show offset to calculate it
            # At timedif time, channelShowPosition was playing at channelTimes
            # The only way this isn't true is if the current channel is curchannel since
            # it could have been fast forwarded or rewinded (rewound)?
            if channel == self.MyOverlayWindow.currentChannel: #currentchannel epg
                    #Live TV pull date from the playlist entry
                    if chtype == 8:
                       playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                       tmpDate = self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)
                       self.log("setbuttonnowtime2 " + str(tmpDate))
                       t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                       epochBeginDate = time.mktime(t)
                       videotime = time.time() - epochBeginDate
                       reftime = time.time()
                    else:
                        playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                        videotime = xbmc.Player().getTime()
                        reftime = time.time()
                   
            else:
                    #Live TV pull date from the playlist entry
                    if chtype == 8:
                       playlistpos = self.MyOverlayWindow.channels[channel - 1].playlistPosition
                       tmpDate = self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)
                       self.log("setbuttonnowtime2 " + str(tmpDate))
                       t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                       epochBeginDate = time.mktime(t)
                       while epochBeginDate + self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos) <  time.time():
                            epochBeginDate += self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)
                            playlistpos = self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos + 1)
                       
                       videotime = time.time() - epochBeginDate
                       self.log('videotime ' + str(videotime))
                       reftime = time.time()
                      
                    else:
                       playlistpos = self.MyOverlayWindow.channels[channel - 1].playlistPosition 
                       videotime = self.MyOverlayWindow.channels[channel - 1].showTimeOffset
                       reftime = self.MyOverlayWindow.channels[channel - 1].lastAccessTime

            # normalize reftime to the beginning of the video
            reftime -= videotime

            while reftime > starttime:
                playlistpos -= 1
                reftime -= self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)

            while reftime + self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos) < starttime:
                reftime += self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)
                playlistpos += 1

            self.log('determinePlaylistPosAtTime return' + str(self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)))
            return self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)


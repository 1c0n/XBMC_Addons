#-------------------------------------------------------------------------------
# Name:        UPNP
# Purpose:
#
# Author:      Kevin
#
# Created:     22/03/2014
# Copyright:   (c) Kevin 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    pass

if __name__ == '__main__':
    main()

import json, requests, os, re, datetime
import socket,select,json,StringIO,copy
import Globals



def SendUPNP(IPP, file, seektime):
    print 'SendUPNP'
    xbmc_host = ''
    xbmc_port = 0

    hours = 0
    minutes = 0
    Mseconds = 0
    seconds = 0
    milliseconds = 0

    print IPP
    print file
    print seektime
    
    xbmc_host = str(IPP.split(":")[0])
    xbmc_port = int(IPP.split(":")[1])
    print xbmc_host
    print xbmc_port
    
    seek = str(datetime.timedelta(seconds=seektime))
    seek = seek.split(":")
    hours = int(seek[0])
    minutes = int(seek[1])
    Mseconds = str(seek[2])
    seconds = int(Mseconds.split(".")[0])
    try:
        milliseconds = int(Mseconds.split(".")[1])
        milliseconds = int(str(milliseconds)[:3])
    except Exception,e:
        pass
    print seek
    print hours
    print minutes
    print seconds
    print milliseconds

    params = ({"jsonrpc": "2.0", "method": "Player.Open", "params": {"item": {"file": file},"options":{"resume":{"hours":hours,"minutes":minutes,"seconds":seconds,"milliseconds":milliseconds}}}})
    print params    
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((xbmc_host, xbmc_port))

    params2 = copy.copy(params)
    params2["jsonrpc"] = "2.0"
    params2["id"] = 1

    s.send(json.dumps(params2))

    s.shutdown(socket.SHUT_RDWR)
    s.close()

#file = 'smb://192.168.0.51/TV/Falling Skies/Season 02/Falling Skies - S02E07 - Molon Labe [HD TV].mkv'
#res = SendUPNP({"jsonrpc": "2.0", "method": "Player.Open", "params": {"item": {"file": file},"options":{"resume":{"hours":hours,"minutes":minutes,"seconds":seconds,"milliseconds":milliseconds}}}})

def StopUPNP(IPP):
    print 'StopUPNP'
    print IPP
    xbmc_host = ''
    xbmc_port = 0

    xbmc_host = str(IPP.split(":")[0])
    xbmc_port = int(IPP.split(":")[1])
    print xbmc_host
    print xbmc_port
    
    params = ({"jsonrpc":"2.0","id":1,"method":"Player.Stop","params":{"playerid":1}})
    print params    
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((xbmc_host, xbmc_port))

    params2 = copy.copy(params)
    params2["jsonrpc"] = "2.0"
    params2["id"] = 1

    s.send(json.dumps(params2))

    s.shutdown(socket.SHUT_RDWR)
    s.close()
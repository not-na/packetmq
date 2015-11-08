#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server.py
#  
#  Copyright 2015 notna <notna@apparat.org>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import time

from twisted.internet import reactor

import packetmq

from common import *

PORT = 8080

def init():
    global reg,ADDR,server
    reg = packetmq.PacketRegistry()
    reg.registerDefaultPackets()
    
    reg.addPacket("chat:msg",ChatMsgPacket(),17)
    reg.addPacket("chat:pubmsg",ChatPubMsgPacket(),18)
    reg.addPacket("chat:sendcmd",ChatSendCmdPacket(),19)
    
    server = Server(reg)
    
    server.listen(PORT)
    
    #reactor.callInThread(_main)
    #reactor.run()
    _main()
    reactor.callInThread(reactor.run)

def _main():
    print("Done!")
    try:
        main()
    except Exception:
        import traceback;traceback.print_exc()
    finally:
        server.stop()


def main():
    print("Server running")
    server.run = True
    while server.run:
        incmd = raw_input("[server]> ")
        server.parseCommand({"msg":incmd,"from":"SERVER","timestamp":time.time()},server)

if __name__ == "__main__":
    init()

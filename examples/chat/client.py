#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client.py
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

from common import Client,ChatMsgPacket,ChatPubMsgPacket,ChatSendCmdPacket

ADDR = ("localhost",8080)

conn = -1

def init():
    global reg,ADDR,client,uname
    reg = packetmq.PacketRegistry(True)
    reg.registerDefaultPackets()
    
    if ADDR == None:
        addr = raw_input("Server: ")
        ADDR = addr.split(":")
        if len(ADDR)!=2:
            raise ValueError("Address needs to be of format host:port")
    
    uname = raw_input("Nickname: ")
    
    print("Connecting...")
    
    client = Client(reg)
    
    client.on_connMade = _doconn
    
    reg.addPacket("chat:msg",ChatMsgPacket(),17)
    reg.addPacket("chat:pubmsg",ChatPubMsgPacket(),18)
    reg.addPacket("chat:sendcmd",ChatSendCmdPacket(),19)
    
    client.connect(ADDR)
    
    reactor.callInThread(_main)
    reactor.run()

def _doconn(ccon):
    global conn
    packetmq.dprint("Conn Made conn=%s"%conn)
    conn = ccon

def _main():
    #super(self,Client).on_connMade(conn)
    while conn == -1:
        time.sleep(0.005)
    while client.peerObj(conn).getState()!="active":
        time.sleep(0.005)
    packetmq.dprint("Conn Made conn=%s"%conn)
    print("Done!")
    try:
        main()
    except Exception:
        import traceback;traceback.print_exc()
    finally:
        client.stop()

def parse_input(msg):
    global uname,run
    if msg == "/exit":
        run = False
        #reactor.stop()
        return
    elif msg.startswith("/nick"):
        try:
            uname = msg.split()[1:]
        except Exception:
            print("Invalid Username!")
            return
    elif msg.startswith("/"):
        client.sendPacket({"msg":msg,"from":uname,"timestamp":time.time()},"chat:sendcmd")
    else:
        client.sendPacket({"msg":msg,"from":uname,"timestamp":time.time()},"chat:pubmsg")
    

def main():
    global run
    run = True
    while run:
        parse_input(raw_input("[%s] "%uname))

if __name__ == "__main__":
    init()

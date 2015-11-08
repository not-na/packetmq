#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  common.py
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

import packetmq

dprint = packetmq.dprint

MSG_FMT = "[{fmttime}] <{from}> {msg}"
TIME_FMT = "%d-%m-%Y %H:%M:%S"

class Server(packetmq.Server):
    def parseCommand(self,packet,fromid):
        if packet["msg"] == "/stop":
            self.run = False
            return
        print("Server-side Commands are currently not supported!")
        self.sendPacket({"msg":"Server-side Commands are currently not supported!","timestamp":time.time(),"from":"Server"},"chat:msg",fromid)

class Client(packetmq.Client):
    pass

class ChatMsgPacket(packetmq.packet.Packet):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(ChatMsgPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        dprint("RECV chat:msg %s"%packet)
        packet["fmttime"] = time.strftime(TIME_FMT,time.localtime(packet["timestamp"]))
        print(MSG_FMT.format(**packet))
        return [packet,fromid,to]

class ChatPubMsgPacket(packetmq.packet.Packet):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(ChatPubMsgPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        dprint("RECV chat:pubmsg %s"%packet)
        mpacket = {}
        mpacket.update(packet)
        mpacket["fmttime"] = time.strftime(TIME_FMT,time.localtime(packet["timestamp"]))
        print(MSG_FMT.format(**mpacket))
        for cid in to.factory.clients:
            dprint("SEND chat:msg %s to %s"%(packet,cid))
            to.sendPacket({"msg":packet["msg"],"timestamp":packet["timestamp"],"from":packet["from"]},"chat:msg",cid)
        return [packet,fromid,to]

class ChatSendCmdPacket(packetmq.packet.Packet):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(ChatSendCmdPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        dprint("RECV chat:sendcmd %s"%packet)
        to.parseCommand(packet,fromid)
        return [packet,fromid,to]

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  packet.py
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
try:
    import umsgpack as msgpack
except ImportError:
    try:
        import msgpack
    except ImportError:
        raise ImportError("No msgpack module was found!!")

PROTOCOL_VERSION = 1

def dprint(msg): # pylint:disable=unused-argument
    pass # Added to stop landscape.io complaining about undefined methods, will be overriden upon import by packetmq.dprint

class BasePacket(object):
    def __init__(self):
        self.bypassStateCheck = False
        self.name = None
        self.numid = None
    def setName(self,name):
        self.name = name
    def setNumid(self,numid):
        self.numid = numid
    def dataEncoded(self,arg,*args,**kwargs):
        if isinstance(arg,str):
            return arg
        self.onEncode(arg,*args,**kwargs)
        return msgpack.dumps(arg)
    def dataDecoded(self,arg,*args,**kwargs):
        if isinstance(arg,str):
            return msgpack.loads(arg)
        self.onDecode(arg,*args,**kwargs)
        return arg
    
    def recv(self,data,fromid,to,*args,**kwargs):
        """Called by the Server/Client to process the packet."""
        return self.onReceive(data,fromid,to,*args,**kwargs)
    def send(self,data,to,fromobj,*args,**kwargs):
        """Called by the Server/Client for final modifications before encoding."""
        dprint("1/2 Callbacks called")
        return self.onSend(data,to,fromobj,*args,**kwargs)
    
    # Callbacks
    def onEncode(self,data,to=-1): # pylint:disable=unused-argument
        """Callback to be overriden by subclasses.
        
        Called before every encoding.
        
        :param obj data: Non-Encoded payload"""
        return data
    def onSend(self,data,to,fromobj,*args,**kwargs): # pylint:disable=unused-argument
        """Callback to be overriden by subclasses.
        
        Called before every send.
        
        :param obj data: Non-Encoded payload"""
        dprint("2/2 Callbacks called")
        dprint("Packet sent:")
        dprint("data  : %s"%data)
        dprint("to    : %s"%to)
        dprint("from  : %s"%fromobj)
        #print("*args : %s"%args)
        dprint("kwargs: %s"%kwargs)
        return [data,to,fromobj]
    def onDecode(self,data,fromid=-1): # pylint:disable=unused-argument
        """Callback to be overriden by subclasses.
        
        Called before every decoding."""
        return data
    def onReceive(self,packet,fromid,to,*args,**kwargs): # pylint:disable=unused-argument
        """Callback to be overriden by subclasses.
        
        Called on every received packet of this type.
        
        :param obj packet: decoded packet
        :param int fromid: fileno of the socket from which the packet was received."""
        dprint("Packet received:")
        dprint("packet: %s"%packet)
        dprint("fromid: %s"%fromid)
        dprint("to    : %s"%to)
        #print("*args : %s"%args)
        dprint("kwargs: %s"%kwargs)
        return [packet,fromid,to]

class Packet(BasePacket):
    pass

class EchoPacket(Packet):
    def __init__(self,retType):
        super(EchoPacket,self).__init__()
        self.retType = retType
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(EchoPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        print("Received EchoPacket: %s"%packet)
        to.sendPacket(packet,self.retType,fromid)
        return [packet,fromid,to]

class PrintPacket(Packet):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(PrintPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        print("Received packet from client #%s: %s"%(to.peerFileno(fromid),packet))
        return [packet,fromid,to] 

class InternalPacket(Packet):
    def __init__(self):
        super(InternalPacket,self).__init__()
        self.bypassStateCheck = True

class HandshakeInitPacket(InternalPacket):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(HandshakeInitPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        if to.peerObj(fromid).getState() != "connMade":
            print("Connection already made, ignoring")
            return [packet,fromid,to]
        elif packet["version"]!=PROTOCOL_VERSION:
            print("Version mismatch, aborting")
            to.softquit(fromid,"reason.versionmismatch")
        else:
            dprint("Establishing connection (1/3)")
            to.peerObj(fromid).setState("idcheck")
            data = {"adapt":to.registry.adaptivePacketIds,"idmap":dict(to.registry.reg_name_int)}
            to.sendPacket(data,"packetmq:handshake_pubids",fromid)
        return [packet,fromid,to]

class HandshakePubidsPacket(InternalPacket):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(HandshakePubidsPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        if to.peerObj(fromid).getState() != "idcheck":
            return [packet,fromid,to]
        elif packet["adapt"]==to.registry.adaptivePacketIds:
            dprint("softquit with sameadaptivepolicy: fromid=%s to=%s"%(fromid,to))
            to.softquit(fromid,"reason.sameadaptivepolicy")
        elif packet["adapt"] and not to.registry.adaptivePacketIds:
            # Ids have already been sent, no further action is required.
            to.sendPacket(None,"packetmq:handshake_finish",fromid) # finish handshake
            return [packet,fromid,to]
        elif not packet["adapt"] and to.registry.adaptivePacketIds:
            # Ids have been received, insert them into the registry
            if list(to.registry.reg_name_int)!=list(packet["idmap"]):
                to.softquit(fromid,"reason.nonequalpackets")
            to.registry.reg_name_int.update(packet["idmap"])
            to.sendPacket(None,"packetmq:handshake_finish",fromid)
        else:
            to.softquit(fromid,"reason.unknown")
        return [packet,fromid,to]

class HandshakeFinishPacket(InternalPacket):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(HandshakeFinishPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        to.peerObj(fromid).setState("active")
        to.on_connMade(fromid)
        return [packet,fromid,to]
    def onSend(self,data,to,fromobj,*args,**kwargs):
        super(HandshakeFinishPacket,self).onSend(data,to,fromobj,*args,**kwargs)
        to.setState("active")
        #fromobj.on_connMade(to)
        return [data,to,fromobj]

class SoftquitPacket(InternalPacket):
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(SoftquitPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        to.peerObj(fromid).transport.loseConnection()
        dprint("Softquit: %s"%packet["reason"])
        return [packet,fromid,to]

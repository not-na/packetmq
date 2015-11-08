#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- test-case-name: packetmq.test -*-
#
#  __init__.py
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
    from twisted.internet.endpoints import TCP4ServerEndpoint
    from twisted.internet import reactor
except ImportError:
    pass

import threading
import struct

import bidict

import packetprotocol
import packet


PROTOCOL_VERSION = 1
packet.PROTOCOL_VERSION = PROTOCOL_VERSION

DPRINT = False
packet.DPRINT = DPRINT
packetprotocol.DPRINT = DPRINT

def dprint(msg):
    if DPRINT:
        print(msg)
packet.dprint = dprint
packetprotocol.dprint = dprint

TYPE_FMT = "!H" # struct used for encoding the packet type
#TYPE_FMT = "!L" # Uncomment for more packet ids, do not forget to also change MAX_PACKET_ID to 2**32
TYPE_LEN = 2 # Length of the type prefix in bytes

MIN_PACKET_ID = 16 # minimum packet id, used during packet registration; should be smaller than MAX_PACKET_ID but bigger than 0
MAX_PACKET_ID = 2**16 # maximum packet id, used during packet registration; correlates to TYPE_FMT

class PacketRegistry(object):
    def __init__(self,adaptPacketIds=False):
        self.reg_name_int = bidict.bidict()
        self.reg_name_obj = bidict.bidict()
        self.packetId = self.packetInt
        self.adaptivePacketIds = adaptPacketIds
    def addPacket(self,name,obj,numid=None,bypass_assert=False):
        assert MIN_PACKET_ID<=numid<=MAX_PACKET_ID or bypass_assert
        self.reg_name_int[name]=numid
        self.reg_name_obj[name]=obj
    def delPacket(self,arg):
        del self.reg_name_int[self.packetName(arg)]
        del self.reg_name_obj[self.packetName(arg)]
    def packetStr(self,arg):
        if isinstance(arg,str):
            return arg
        elif isinstance(arg,int):
            return self.reg_name_int[:arg]
        elif isinstance(arg,packet.BasePacket):
            return self.reg_name_obj[:arg]
        else:
            raise TypeError("Invalid type %s"%type(arg))
    packetName = packetStr
    def packetInt(self,arg):
        if isinstance(arg,int):
            return arg
        elif isinstance(arg,str):
            return self.reg_name_int[arg]
        elif isinstance(arg,packet.BasePacket):
            return self.reg_name_int[self.reg_name_obj[:arg]]
        else:
            raise TypeError("Invalid type %s"%type(arg))
    def packetObj(self,arg):
        if isinstance(arg,packet.BasePacket):
            return arg
        elif isinstance(arg,int):
            return self.reg_name_obj[self.reg_name_int[:arg]]
        elif isinstance(arg,str):
            return self.reg_name_obj[arg]
        else:
            raise TypeError("Invalid type %s"%type(arg))
    def registerDefaultPackets(self):
        self.addPacket("packetmq:handshake_init",packet.HandshakeInitPacket(),0,True)
        self.addPacket("packetmq:softquit",packet.SoftquitPacket(),1,True)
        self.addPacket("packetmq:handshake_pubids",packet.HandshakePubidsPacket(),2,True)
        self.addPacket("packetmq:handshake_finish",packet.HandshakeFinishPacket(),3,True)

class Peer(object):
    def __init__(self,registry,proto=packetprotocol.PacketProtocol,factory=packetprotocol.PacketFactory):
        self.registry = registry
        self.factory = factory(self,proto)
        self.skip_handshake = False
    def peerFileno(self,arg):
        if isinstance(arg,int):
            return arg
        elif isinstance(arg,packetprotocol.PacketProtocol) or isinstance(arg,Peer):
            return self.factory.clients[:arg]
        else:
            raise TypeError("Invalid type %s"%type(arg))
    def peerObj(self,arg):
        if isinstance(arg,packetprotocol.PacketProtocol) or isinstance(arg,Peer):
            return arg
        elif isinstance(arg,int):
            return self.factory.clients[arg]
        else:
            raise TypeError("Invalid type %s"%type(arg))
    def initConnection(self,conn):
        if self.skip_handshake:
            self.peerObj(conn).setState("active")
            return
        data = {"version":PROTOCOL_VERSION}
        self.sendPacket(data,"packetmq:handshake_init",conn)
    def lostConnection(self,conn,reason=None):
        pass
    def sendPacket(self,data,dtype,to):
        dprint("SEND START")
        to = self.peerObj(to)
        ptint = self.registry.packetInt(dtype)
        pobj = self.registry.packetObj(dtype)
        #import pdb;pdb.set_trace()
        dprint("Calling send callbacks...")
        data,to,fromid = pobj.send(data,to,self)
        dprint("dtype: %s"%dtype)
        dprint("Encoding packet...")
        data = pobj.dataEncoded(data,to=to)
        dprint("Packing packet...")
        raw = struct.pack(TYPE_FMT,ptint)+data
        dprint("Start sending...")
        self.sendEncoded(raw,to)
        dprint("SEND END")
    def sendEncoded(self,raw,to):
        dprint("Sending encoded...")
        self.peerObj(to).sendEncoded(raw)
    def recvPacket(self,data,dtype,fromid):
        #dprint("recvPacket(%s,%s,%s)"%(data,dtype,fromid))
        dprint("recvPacket dtype=%s fromid=%s"%(self.registry.packetStr(dtype),self.peerFileno(fromid)))
        pobj = self.registry.packetObj(dtype)
        if self.peerObj(fromid).getState()=="active" or pobj.bypassStateCheck:
            pobj.recv(data,fromid,self)
        else:
            dprint("Invalid state %s for recv"%self.peerObj(fromid))
    def recvEncoded(self,data,fromid):
        ptraw = data[:TYPE_LEN]
        dprint("RECV encodedpacket:")
        dprint("fromid: %s"%fromid)
        ptint = struct.unpack(TYPE_FMT,ptraw)[0]
        dprint("dtype: %s"%self.registry.packetStr(ptint))
        pobj = self.registry.packetObj(ptint)
        data = data[TYPE_LEN:]
        data = pobj.dataDecoded(data,fromid=fromid)
        dprint("data: %s"%data)
        self.recvPacket(data,pobj,fromid)
    def runAsync(self):
        self.thread = threading.Thread(name="Network thread",target=self.run)
        self.thread.daemon = True
        self.thread.run()
    def run(self):
        reactor.run()
    def stop(self):
        reactor.stop()
    def softquit(self,peer,reason="reason.unknown"):
        peerobj = self.peerObj(peer)
        peerobj.setState("softquitted")
        self.sendPacket({"reason":reason},"packetmq:softquit",peer)
    def on_connMade(self,conn):
        dprint("Connection Made peer=%s"%self.peerFileno(conn))
    def __del__(self):
        self.stop()

class Server(Peer):
    def __init__(self,registry,proto=packetprotocol.PacketProtocol,factory=packetprotocol.PacketFactory):
        super(Server,self).__init__(registry,proto,factory)
    def listen(self,port):
        #self.endpoint = TCP4ServerEndpoint(reactor, port)
        #self.endpoint.listen(self.factory)
        reactor.listenTCP(port,self.factory)
        #reactor.listenTCP(port,self.factory) # call listenTCP two times to also listen IPv6 addresses
    def runAsync(self):
        self.thread = threading.Thread(name="Server thread",target=self.run)
        self.thread.daemon = True
        self.thread.run()

class MemoryServer(Server):
    def __init__(self,registry,proto=packetprotocol.MemoryPacketProtocol,factory=packetprotocol.MemoryPacketFactory):
        super(MemoryServer,self).__init__(registry,proto,factory)
        self.skip_handshake = True
        self.state = "connMade"
    def setState(self,state):
        self.state = state
    def getState(self):
        return self.state
    def listen(self,port):
        pass
    def connectClient(self,client):
        self.factory.addClient(client)
        client.factory.addClient(self)
        self.initConnection(client)
    def disconnectClient(self,client):
        self.factory.delClient(self.peerObj(client))
    def sendPacket(self,data,dtype,to):
        self.peerObj(to).recvPacket(data,dtype,to)
    def sendEncoded(self,raw,to):
        self.peerObj(to).recvEncoded(data,dtype,to)

class Client(Peer):
    def __init__(self,registry,proto=packetprotocol.PacketProtocol,factory=packetprotocol.ClientPacketFactory):
        super(Client,self).__init__(registry,proto,factory)
        self.default_peer = None
    def initConnection(self,conn):
        super(Client,self).initConnection(conn)
        if self.default_peer == None or self.default_peer not in self.factory.clients:
            self.default_peer = conn
    def lostConnection(self,conn,reason=None):
        super(Client,self).lostConnection(conn,reason)
        self.default_peer = None
    def connect(self,address):
        reactor.connectTCP(address[0],address[1],self.factory)
    def runAsync(self):
        self.thread = threading.Thread(name="Client thread",target=self.run)
        self.thread.daemon = True
        self.thread.run()
    def sendPacket(self,data,dtype,to=None):
        if to == None:
            to = self.default_peer
        super(Client,self).sendPacket(data,dtype,to)
    def sendEncoded(self,raw,to=None):
        if to == None:
            to = self.default_peer
        super(Client,self).sendEncoded(raw,to)
    def recvPacket(self,data,dtype,fromid=None):
        if fromid == None:
            fromid = self.default_peer
        super(Client,self).recvPacket(data,dtype,fromid)
    def recvEncoded(self,data,fromid=None):
        if fromid == None:
            fromid = self.default_peer
        super(Client,self).recvEncoded(data,fromid)

class MemoryClient(Client):
    def __init__(self,registry,proto=packetprotocol.MemoryPacketProtocol,factory=packetprotocol.MemoryClientPacketFactory):
        super(MemoryClient,self).__init__(registry,proto,factory)
        self.skip_handshake = True
        self.state = "connMade"
    def setState(self,state):
        self.state = state
    def getState(self):
        return self.state
    def connect(self,server):
        if self.default_peer == None:
            self.default_peer = server
        server.connectClient(self)
        self.initConnection(server)
    def disconnect(self,server=None):
        if server == None:
            server = self.default_peer
        server.disconnectClient(self)
    def sendPacket(self,data,dtype,to=None):
        if to == None:
            to = self.default_peer
        pobj = self.registry.packetObj(dtype)
        dprint("Calling send callbacks...")
        data,to,fromid = pobj.send(data,to,self)
        dprint("dtype: %s"%dtype)
        self.peerObj(to).recvPacket(data,dtype,self)
    def sendEncoded(self,raw,to=None):
        if to == None:
            to = self.default_peer
        self.peerObj(to).recvEncoded(raw,to)

"""class MemoryServer(BaseServer):
    def __init__(self,registry):
        super(MemoryServer,self).__init__(registry)
        self.fromid = "server"
        self.clients = {}
        self.skip_handshake = True
    def peerFileno(self,arg):
        return arg
    def peerObj(self,arg):
        return arg
    def sendPacket(self,data,dtype,to):
        if to not in self.clients:
            raise RuntimeError("No such client")
        self.clients[to].recvPacket(data,dtype,self.fromid)
    def connectClient(self,client,toid):
        self.clients[toid]=client
    def disconnectClient(self,toid):
        del self.clients[toid]
"""

"""
class BaseClient(object):
    def __init__(self,registry):
        self.registry = registry
        self.skip_handshake = False
    def peerFileno(self,arg):
        return arg
    def peerObj(self,arg):
        return arg
    def sendPacket(self,data,dtype,to):
        self.on_sendPacket(data,dtype,to)
        ptint = self.registry.packetInt(dtype)
        pobj = self.registry.packetObj(dtype)
        data,to = pobj.send(data,to)
        data = pobj.dataEncoded(data,to=to)
        raw = struct.pack(TYPE_FMT,ptint)+data
        self.sendEncoded(raw,to)
    def on_sendPacket(self,data,dtype,to):
        pass
    def sendEncoded(self,raw,to):
        self.on_sendEncoded(raw,to)
        self.peerObj(to).sendString(raw)
    def on_sendEncoded(self,raw,to):
        pass
    def recvPacket(self,data,dtype,fromid):
        self.on_recvPacket(data,dtype,fromid)
        pobj = self.registry.packetObj(dtype)
        pobj.recv(data,fromid)
    def on_recvPacket(self,data,dtype,fromid):
        pass
    def recvEncoded(self,data,fromid):
        self.on_recvEncoded(data,fromid)
        ptraw = data[:TYPE_LEN]
        ptint = struct.unpack(TYPE_FMT,ptraw)
        pobj = self.registry.packetObj(ptint)
        data = data[TYPE_LEN:]
        data = pobj.dataDecoded(data,fromid=fromid)
        self.recvPacket(data,pobj,fromid)
    def on_recvEncoded(self,data,fromid):
        pass
    def runAsync(self):
        pass
    def run(self):
        pass
    def stop(self):
        pass
    def softquit(self,peer,reason="reason.unknown"):
        peerobj = self.peerObj(peer)
        peerobj.setState("softquitted")
        self.sendPacket({"reason":reason},"packetmq:softquit",peer)
"""

"""
class Client(BaseClient):
    def __init__(self,registry):
        super(Client,self).__init__(registry)
        self.factory = packetprotocol.PacketFactory()
        self.skip_handshake = False
    def peerFileno(self):
        if isinstance(arg,int):
            return arg
        elif isinstance(arg,packetprotocol.PacketProtocol):
            return self.factory.clients.index(arg)
        else:
            raise TypeError("Invalid type")
    def peerObj(self,arg):
        if isinstance(arg,packetprotocol.PacketProtocol):
            return arg
        elif isinstance(arg,int):
            return self.factory.clients[arg]
        else:
            raise TypeError("Invalid type")
    def initConnection(self,conn):
        if self.skip_handshake:
            return
        data = {"version":PROTOCOL_VERSION}
        self.sendPacket(data,"packetmq:handshake_init",conn)
    def connect(self,address):
        self.endpoint = TCP4ClientEndpoint(reactor,address)
        self.endpoint.listen(self.factory)
    def runAsync(self):
        self.thread = threading.Thread(name="Client thread",target=reactor.run)
        self.thread.daemon = True
        self.thread.run()
    def run(self):
        reactor.run()
    def stop(self):
        reactor.stop()
"""

"""class MemoryClient(BaseClient):
    def __init__(self,registry):
        super(MemoryClient,self).__init__(registry)
        self.server = None
        self.skip_handshake = True
    def connectServer(self,server,toid=0):
        self.server = server
        self.toid = toid
        server.connectClient(self,toid)
    def disonnectServer(self):
        self.server.disconnectClient(self.toid)
    def sendPacket(self,data,dtype,to):
        self.server.recvPacket(data,dtype,"client")
"""

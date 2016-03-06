#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  packetprotocol.py
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

# pylint: disable=W0613

import threading

import bidict

from zope.interface import implementer

from twisted.internet.protocol import Factory, ClientFactory, Protocol
from twisted.internet.address import IAddress
from twisted.protocols.basic import Int32StringReceiver

def dprint(msg): # pylint:disable=unused-argument
    pass # Added to stop landscape.io complaining about undefined methods, will be overriden upon import by packetmq.dprint


class PacketProtocol(Int32StringReceiver):
    def __init__(self,parent,addr):
        #super(PacketProtocol,self).__init__()
        self.parent = parent
        self.state = "connMade"
        self.addr = addr
    def connectionMade(self):
        dprint("Connection Made...")
        self.parent.initConnection(self)
        self.parent.factory.addClient(self)
    def connectionLost(self,reason=None): # pylint:disable=unused-argument
        self.setState("disonnected")
        self.parent.lostConnection(self,reason)
        self.parent.factory.delClient(self)
    def stringReceived(self,string):
        dprint("RECV START")
        dprint("Received String...")
        self.parent.recvEncoded(string,self.parent.peerFileno(self))
        dprint("RECV END")
    def sendEncoded(self,data):
        dprint("Sending Encoded over Protocol...")
        self.sendString(bytes(data))
        dprint("Sent Encoded over Protocol")
    def setState(self,state):
        self.state = state
    def getState(self):
        return self.state

class PacketFactory(Factory):
    def __init__(self,parent,proto):
        #super(PacketFactory,self).__init__()
        self.parent = parent
        self.proto = proto
        self.clients = bidict.bidict()
        self.sesscounter = 0
        self.cllock = threading.Lock()
    def startedConnecting(self,arg):
        pass
    def buildProtocol(self,addr): # pylint:disable=unused-argument
        return self.proto(self.parent,addr)
    def addClient(self,client):
        self.cllock.acquire()
        dprint("sesscounter: %s;client: %s"%(self.sesscounter,client))
        self.clients[self.sesscounter]=client
        self.sesscounter+=1
        self.cllock.release()
    def delClient(self,client):
        self.cllock.acquire()
        if client in self.clients.values():
            del self.clients.inv[client]
        self.cllock.release()

class ClientPacketFactory(ClientFactory):
    def __init__(self,parent,proto):
        #super(ClientPacketFactory,self).__init__()
        self.parent = parent
        self.proto = proto
        self.clients = bidict.bidict()
        self.sesscounter = 0
        self.cllock = threading.Lock()
    def startedConnecting(self,arg):
        pass
    def buildProtocol(self,addr): # pylint:disable=unused-argument
        return self.proto(self.parent,addr)
    def addClient(self,client):
        self.cllock.acquire()
        self.clients[self.sesscounter]=client
        self.sesscounter+=1
        self.cllock.release()
    def delClient(self,client):
        self.cllock.acquire()
        if client in self.clients.values():
            del self.clients.inv[client]
        self.cllock.release()

# Memory Protocols

@implementer(IAddress)
class MemoryAddress(object):
    def __init__(self):
        self.host = "memory:0"

class MemoryPacketProtocol(Protocol):
    def __init__(self,parent,addr):
        #super(MemoryPacketProtocol,self).__init__()
        self.parent = parent
        self.state = "connMade"
        self.addr = addr
    def connectionMade(self):
        self.parent.initConnection(self)
        self.parent.factory.addClient(self)
    def connectionLost(self,reason=None): # pylint:disable=unused-argument
        self.parent.factory.delClient(self)
    def sendEncoded(self,data):
        self.parent.recvEncoded(data)
    def setState(self,state):
        self.state = state
    def getState(self):
        return self.state

class MemoryPacketFactory(Factory):
    def __init__(self,parent,proto):
        #super(MemoryPacketFactory,self).__init__()
        self.parent = parent
        self.proto = proto
        self.clients = bidict.bidict()
        self.sesscounter = 0
        self.cllock = threading.Lock()
    def buildProtocol(self,addr): # pylint:disable=unused-argument
        return self.proto(self.parent,addr)
    def addClient(self,client):
        self.cllock.acquire()
        self.clients[self.sesscounter]=client
        self.sesscounter+=1
        self.cllock.release()
    def delClient(self,client):
        self.cllock.acquire()
        if client in self.clients.values():
            del self.clients.inv[client]
        self.cllock.release()

class MemoryClientPacketFactory(ClientFactory):
    def __init__(self,parent,proto):
        #super(MemoryPacketFactory,self).__init__()
        self.parent = parent
        self.proto = proto
        self.clients = bidict.bidict()
        self.sesscounter = 0
        self.cllock = threading.Lock()
    def buildProtocol(self,addr): # pylint:disable=unused-argument
        return self.proto(self.parent,addr)
    def addClient(self,client):
        self.cllock.acquire()
        self.clients[self.sesscounter]=client
        self.sesscounter+=1
        self.cllock.release()
    def delClient(self,client):
        self.cllock.acquire()
        if client in self.clients.values():
            del self.clients.inv[client]
        self.cllock.release()

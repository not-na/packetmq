#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import time

import packetmq
import packetmq.packet

import bidict

from twisted.trial import unittest
from twisted.test import proto_helpers

class TestPacket(packetmq.packet.Packet):
    def __init__(self):
        super(TestPacket,self).__init__()
        self.recved = []
    def onReceive(self,packet,fromid,to,*args,**kwargs):
        super(TestPacket,self).onReceive(packet,fromid,to,*args,**kwargs)
        self.recved.append([packet,to.peerFileno(fromid)])
        return [packet,fromid,to]

class PacketRegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.reg = packetmq.PacketRegistry()
    
    def test_regdicts(self):
        self.assertEqual(self.reg.reg_name_int,bidict.bidict())
        self.assertEqual(self.reg.reg_name_obj,bidict.bidict())
    
    def test_registerDefaultPackets(self):
        self.reg.registerDefaultPackets()
        
        self.assertEqual(self.reg.packetInt("packetmq:handshake_init"),0)
        self.assertEqual(self.reg.packetName("packetmq:handshake_init"),"packetmq:handshake_init")
        
        self.assertEqual(self.reg.packetInt("packetmq:softquit"),1)
        self.assertEqual(self.reg.packetName("packetmq:softquit"),"packetmq:softquit")
        
        self.assertEqual(self.reg.packetInt("packetmq:handshake_pubids"),2)
        self.assertEqual(self.reg.packetName("packetmq:handshake_pubids"),"packetmq:handshake_pubids")
        
        self.assertEqual(self.reg.packetInt("packetmq:handshake_finish"),3)
        self.assertEqual(self.reg.packetName("packetmq:handshake_finish"),"packetmq:handshake_finish")
    
    def test_packetTypeConversion(self):
        self.reg.registerDefaultPackets()
        
        self.assertRaises(TypeError,self.reg.packetStr,{})
        self.assertRaises(TypeError,self.reg.packetInt,{})
        self.assertRaises(TypeError,self.reg.packetObj,{})
    
    def test_addPacket(self):
        self.reg.registerDefaultPackets()
        
        obj = TestPacket()
        self.reg.addPacket("packetmq:test",obj,17)
        
        self.assertEqual(self.reg.packetInt("packetmq:test"),17)
        self.assertEqual(self.reg.packetStr("packetmq:test"),"packetmq:test")
        self.assertEqual(self.reg.packetObj("packetmq:test"),obj)
        
        self.assertEqual(self.reg.packetInt(17),17)
        self.assertEqual(self.reg.packetStr(17),"packetmq:test")
        self.assertEqual(self.reg.packetObj(17),obj)
        
        self.assertEqual(self.reg.packetInt(obj),17)
        self.assertEqual(self.reg.packetStr(obj),"packetmq:test")
        self.assertEqual(self.reg.packetObj(obj),obj)
    
    def test_delPacket(self):
        self.reg.registerDefaultPackets()
        
        obj = TestPacket()
        self.reg.addPacket("packetmq:test",obj,17)
        
        self.assertEqual(self.reg.packetInt("packetmq:test"),17)
        self.assertEqual(self.reg.packetStr("packetmq:test"),"packetmq:test")
        self.assertEqual(self.reg.packetObj("packetmq:test"),obj)
        
        self.reg.delPacket("packetmq:test")
        
        self.assertRaises(KeyError,self.reg.packetInt,"packetmq:test")
        #self.assertRaises(KeyError,self.reg.packetStr,"packetmq:test")
        self.assertRaises(KeyError,self.reg.packetObj,"packetmq:test")
        
        #self.assertRaises(KeyError,self.reg.packetInt,17)
        self.assertRaises(KeyError,self.reg.packetStr,17)
        self.assertRaises(KeyError,self.reg.packetObj,17)
        
        self.assertRaises(KeyError,self.reg.packetInt,obj)
        self.assertRaises(KeyError,self.reg.packetStr,obj)
        #self.assertRaises(KeyError,self.reg.packetObj,obj)

class TCPServerTestCase(unittest.TestCase):
    def setUp(self):
        self.reg = packetmq.PacketRegistry()
        self.reg.registerDefaultPackets()
        
        self.testpacket = TestPacket()
        self.reg.addPacket("packetmq:test",self.testpacket,17)
        
        self.server = packetmq.Server(self.reg)
        
        self.proto = self.server.factory.buildProtocol(('127.0.0.1', 0))
        self.tr = proto_helpers.StringTransport()
        
        self.client = packetmq.Client(self.reg)
        self.client.factory.clients[0]=self.proto
        
        self.proto.makeConnection(self.tr)
        self.proto.transport = self.tr
        self.proto.sendString = self.proto.stringReceived
        
        time.sleep(0.5)
    
    def test_connStateServer(self):
        self.assertEqual(self.server.peerObj(0).getState(),"active")
    
    def test_connStateClient(self):
        self.assertEqual(self.client.peerObj(0).getState(),"active")
    
    def test_packetSend2Server(self):
        self.client.sendPacket({"foo":"bar"},"packetmq:test",0)
        
        self.assertListEqual(self.testpacket.recved,[[{"foo":"bar"},0]])
    
    def test_packetSend2Client(self):
        self.server.sendPacket({"foo":"bar"},"packetmq:test",0)
        
        self.assertListEqual(self.testpacket.recved,[[{"foo":"bar"},0]])
    

class MemServerTestCase(unittest.TestCase):
    def setUp(self):
        self.reg = packetmq.PacketRegistry()
        self.reg.registerDefaultPackets()
        
        self.server = packetmq.MemoryServer(self.reg)
        
        self.client = packetmq.MemoryClient(self.reg)
        self.client.connect(self.server)
        
        self.testpacket = TestPacket()
        self.reg.addPacket("packetmq:test",self.testpacket,17)
    
    def test_connState(self):
        self.assertEqual(self.client.peerObj(0).getState(),"active")
        self.assertEqual(self.server.peerObj(0).getState(),"active")
    
    def test_packetSend2Server(self):
        self.client.sendPacket({"foo":"bar"},"packetmq:test")
        
        self.assertListEqual(self.testpacket.recved,[[{"foo":"bar"},0]])
    
    def test_packetSend2Client(self):
        self.server.sendPacket({"foo":"bar"},"packetmq:test",0)
        
        self.assertListEqual(self.testpacket.recved,[[{"foo":"bar"},0]])
    
    def test_disconnect(self):
        self.client.disconnect()
        
        self.assertRaises(KeyError,self.client.sendPacket,{"foo":"bar"},"packetmq:test")
        
        self.assertRaises(KeyError,self.server.sendPacket,{"foo":"bar"},"packetmq:test",0)

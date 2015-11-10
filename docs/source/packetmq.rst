
`packetmq` - Packet based networking
====================================

.. py:module:: packetmq
   :synopsis: Packet based networking

Packet Registry
---------------

.. py:class:: PacketRegistry([adaptPacketIds)]:
   
   Packet Registry used by both server and client.
   
   `adaptPacketIds` defines whether to adapt or enforce packet IDs when connecting, usually you set this to `False` on servers or to `True` on clients.
   
   .. py:method:: addPacket(name,obj,numid[,bypass_assert)]:
      
      Registers packet Object `obj` using name `name` and numerical id `numid`\ .
      
      `name` should be of format `"<application>:<packet>"` and should only contain standard ascii chars. `name` must also be unique.
      
      `obj` is an instance if :py:class:`packetmq.packet.Packet` or subclass. You may in theory use the same instance for multiple packets, even though not very usefull.
      
      `numid` is an int within :py:data:`MIN_PACKET_ID` and :py:data:`MAX_PACKET_ID`\ , inclusive. This int represents the packet type on the wire.
      
      `bypass_assert` may be used by internal packets that need to bypass the numerical id limitations.
    
   .. py:method:: delPacket(arg):
      
      Removes packet `arg` from the registry.
      
      `arg` can be any packet type, see :ref:`autotypes`\ .
   
   .. py:method:: packetStr(arg):
                  packetInt(arg):
                  packetObj(arg):
      
      :ref:`autotypes` conversion methods for packet objects.
      
      These methods allow conversion between :py:class:`packetmq.packet.Packet`\ , Numerical IDs and names.
   
   .. py:method:: registerDefaultPackets():
      
      Registers all default packets needed by the handshake and other default functionality.

Peer Base Class
---------------

.. py:class:: Peer(registry[,proto[,factory)]]:
   
   Base Class for peers in communication.
   
   `registry` must be an instance of :py:class:`PacketRegistry` or subclass.
   
   `proto` and `factory` are used for creating new connections. You normally do not need to change these.
   
   .. py:method:: peerFileno(arg):
                  peerObj(arg):
      
      :ref:`autotypes` conversion methods for protocol/connection objects.
      
      These methods allow conversion between either :py:class:`packetmq.packetprotocol.PacketProtocol` for TCP connections or :py:class:`packetmq.Peer` for memory connections and Connection IDs.
   
   .. py:method:: initConnection(conn):
      
      Initializes connection `conn`\ , e.g. sends the handshake.
      
      This method is called automatically by :py:meth:`PacketProtocol.connectionMade() <packetmq.packetprotocol.PacketProtocol.connectionMade>` and thus should not be called.
   
   .. py:method:: lostConnection(conn[reason)]:
      
      Callback called when the connection with `conn` is lost.
      
      `reason` is either a dotted string describing the reason or a reason given by twisted.
      If a dotted string is passed, usually a softquit has occured and when a reason by twisted is passed, then the connection was aborted.
      
      This callback is the last chance to send another packet to the peer, however responses may not arrive.
   
   .. py:method:: sendPacket(data,dtype,to):
      
      Sends a packet of type `dtype` to peer `to` with payload `data`\ .
      
      `dtype` can be any packet type, see :ref:`autotypes`\ .
      
      `to` can be any peer type, see :ref:`autotypes`\ .
      
      `data` can be of any type, by default only msgpack-compatible objects are accepted. Accepted values can be changed by the packet.
      
      This methods encodes and frames the data and sends it with :py:meth:`sendEncoded()`\ .
   
   .. py:method:: sendEncoded(raw,to):
      
      Sends the raw data `raw` to peer `to`\ .
      
      `raw` can be any string, including special characters.
      
      `to` can be any peer type, see :ref:`autotypes`\ .
      
      Data is sent either through TCP or memory.
   
   .. py:method:: recvPacket(data,dtype,fromid):
      
      Called to process packets.
      
      `data` is the decoded data, e.g. most often dicts or lists.
      
      `dtype` can be any packet type, see :ref:`autotypes`\ .
      
      `fromid` can be any peer type, see :ref:`autotypes`\ .
      
      This method will be called automatically by :py:meth:`recvEncoded`\ .
      
   .. py:method:: recvEncoded(data,fromid):
      
      Called by twisted's reactor methods upon receiving full packets.
      
      `data` is the encoded data, e.g. most often msgpack encoded data.
      
      `fromid` can be any peer type, see :ref:`autotypes`\ .
      
      This method is called automatically and thus should not be called manually.
   
   .. py:method:: run():
      
      Starts the reactor in the same thread. The reactor processes all incoming and outcoming network traffic.
      
      This call blocks until :py:meth:`Peer.stop()` is called.
   
   .. py:method:: runAsync():
      
      Calls :py:meth:`Peer.run()` in another thread.
      
      This call does not block, but you will still need to call :py:meth:`Peer.stop()`\ , else your program will continue running infinitely.
   
   .. py:method:: stop():
      
      Stops the reactor and all traffic processing without closing the connections.
      
      This is also called when the peer gets deleted.
   
   .. py:method:: softquit(peer[,reason)]:
      
      Soft-closes the connection to peer `peer`\ , optionally with the reason `reason`\ .
      
      This will also trigger :py:meth:`Peer.lostConnection()`\ .
   
   .. py:method:: on_connMade(conn):
      
      Callback called when connection `conn` is made.
      
      `conn` can be any peer type, see :ref:`autotypes`\ . 

.. _autotypes:

Auto-Types
----------

Auto-types are a mechanic supported by several classes in packetmq.

Auto-Types allows you to convert easily between different representations of an object.
Conversion is done via a set of methods, internally using bidicts.
The conversion methods are usually named after a scheme, e.g. `<object><type to convert to>()`\ .

Example::
   
   >>> registry.packetObj(obj)
   obj
   >>> registry.packetObj(name)
   obj
   >>> registry.packetObj(numid)
   obj
   >>> registry.packetStr(obj)
   name
   >>> registry.packetStr(name)
   name
   >>> registry.packetStr(numid)
   name
   >>> registry.packetInt(obj)
   numid
   >>> registry.packetInt(name)
   numid
   >>> registry.packetInt(numid)
   numid

This is a simplified example based on :py:class:`PacketRegistry`\ .

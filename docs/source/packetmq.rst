
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
      
      If the main loop is started using this method, spawning subprocesses via twisted will not work, because their termination cannot be detected.
   
   .. py:method:: stop():
      
      Stops the reactor and all traffic processing without closing the connections.
      
      This is also called when the peer gets deleted.
   
   .. py:method:: softquit(peer[,reason)]:
      
      Soft-closes the connection to peer `peer`\ , optionally with the reason `reason`\ .
      
      This will also trigger :py:meth:`Peer.lostConnection()`\ .
   
   .. py:method:: on_connMade(conn):
      
      Callback called when connection `conn` is made.
      
      `conn` can be any peer type, see :ref:`autotypes`\ . 

TCP Servers and Clients
-----------------------

.. py:class:: Server(registry[,proto[,factory]]):
   
   TCP Server class powered by twisted. This class is a subclass of :py:class:`Peer`\ .
   
   `registry` must be an instance of :py:class:`PacketRegistry` or subclass.
   
   `proto` and `factory` are used for creating new connections. You normally do not need to change these.
   
   .. py:method:: listen(port):
      
      Listen to TCP port `port`\ .
      
      You can call this method multiple times to listen to multiple ports.

.. py:class:: Client(registry[,proto[,factory)]:
   
   TCP Client class powered by twisted. This class is a subclass of :py:class:`Peer`\ .
   
   `registry` must be an instance of :py:class:`PacketRegistry` or subclass.
   
   `proto` and `factory` are used for creating new connections. You normally do not need to change these.
   
   
   Most methods that require a peer will default to the first connected server.
   This applies to following methods:
   
   * :py:meth:`sendPacket() <packetmq.Peer.sendPacket>`
   * :py:meth:`sendEncoded() <packetmq.Peer.sendEncoded>`
   * :py:meth:`recvPacket() <packetmq.Peer.recvPacket>`
   * :py:meth:`recvEncoded() <packetmq.Peer.recvEncoded>`
   
   .. py:method:: connect(address):
      
      Connects to TCP address tuple `address`\ .
      
      `address` is a tuple of `(host,port)`\ .

Memory Servers and Clients
--------------------------

All memory servers and clients also have :py:meth:`setState() <packetmq.packetprotocol.PacketProtocol.setState>` and :py:meth:`getState() <packetmq.packetprotocol.PacketProtocol.getState>` state methods, for compatibility with :py:class:`PacketProtocol <packetmq.packetprotocol.PacketProtocol>`\ .

.. py:class:: MemoryServer(registry[,proto[,factory]]):
   
   Memory Server class for in-process data transmission. This class is a subclass of :py:class:`Peer`\ .
   
   `registry` must be an instance of :py:class:`PacketRegistry` or subclass.
   
   `proto` is not used since all connections are in-memory.
   
   `factory` is used for storing active connections.
   
   .. py:method:: connectClient(client):
      
      Connects client `client` to the server.
      
      This method should not be used manually, use :py:meth:`MemoryClient.connect()` instead.
   
   .. py:method:: disconnectClient(client):
      
      Disconnects client `client` from the server.
      
      This method should not be used manually, use :py:meth:`MemoryClient.disconnect()` instead.

.. py:class:: MemoryClient(registry[,proto[,factory]]):
   
   Memory Client class for in-process data transmission. This class is a subclass of :py:class:`Peer`\ .
   
   `registry` must be an instance of :py:class:`PacketRegistry` or subclass.
   
   `proto` is not used since all connections are in-memory.
   
   `factory` is used for storing active connections.
   
   .. py:method:: connect(server):
      
      Connects the client with the server `server`\ .
   
   .. py:method:: disconnect([server]):
      
      Terminates the connection to server `server` and calls all appropriate callbacks.
   

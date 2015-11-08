
`packetmq` - Packet based networking
====================================

.. py:module:: packetmq
   :synopsis: Packet based networking

Packet Registry
---------------

.. py:class:: PacketRegistry([adaptPacketIds)]
   
   Packet Registry used by both server and client.
   
   `adaptPacketIds` defines whether to adapt or enforce packet IDs when connecting, usually you set this to `False` on servers or to `True` on clients.
   
   .. py:method:: 

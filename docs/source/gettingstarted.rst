
Getting Started
===============

This is a simple guide to the most important features of packetmq.

Installation
------------

Installation with pip::
   
   $ pip install packetmq

Installation with easy_install::
   
   $ easy_install packetmq

You can also download and manually install packetmq `here <https://pypi.python.org/pypi/packetmq>`_\ .

If installing manually, do not forget to also install twisted, u-msgpack-python and bidict.

The Packet Registry
-------------------

The :py:class:`~packetmq.PacketRegistry` is used to store packet objects, name and numid.

First, we need to import packetmq::
   
   >>> import packetmq

Then, we can create the :py:class:`~packetmq.PacketRegistry` instance::
   
   >>> reg = packetmq.PacketRegistry()
   >>> reg.registerDefaultPackets() # Initializes all standard packets required for normal operation

We can then access the default packets using the so called :ref:`autotypes` that convert between different representations of a packet smartly::
   
   >>> reg.packetInt("packetmq:handshake_init") # packetInt converts all representations to a numid
   0
   >>> reg.packetStr(0) # packetStr converts all representations to the packets name
   "packetmq:handshake_init"
   >>> reg.packetObj("packetmq:handshake_init") # packetObj converts all representations to the packet object
   <packetmq.packet.HandshakeInitPacket object at 0x.........>
   >>> reg.packetInt(0) # if the type is already correct, conversion is skipped
   0

To add new packets, we just call :py:meth:`packetmq.PacketRegistry.addPacket()` with the name, object and numid::
   
   >>> mypacket = packetmq.packet.PrintPacket()
   >>> reg.addPacket("myapplication:mypacket",mypacket,17) # the number needs to be above 16 and below 65536, else registration will fail.
   >>> reg.packetObj("myapplication:mypacket")
   <packetme.packet.EchoPacket object at 0x........>
   >>> reg.packetInt(mypacket)
   17

You can also create new packets by subclassing :py:class:´packetmq.packet.Packet`\ .

Sending Data to Peers
---------------------

Now, that we know how to use the PacketRegistry, we can move on to sending actual data to the server or client.
For now, we will setup a simple echo system::
   
   >>> mypacket = packetmq.packet.EchoPacket(retType="myapplication:myprintpacket") # EchoPacket simply resends the packet verbatim with the type changed
   >>> myprintpacket = packetmq.packet.PrintPacket() # PrintPacket prints out the packet
   >>> reg.addPacket("myapplication:mypacket",mypacket,17)
   >>> reg.addPacket("myapplication:myprintpacket",myprintpacket,18)

Then, we create the server in one session::
   
   [server]>>> server = packetmq.Server(reg)
   [server]>>> server.listen(12345)
   [server]>>> server.runAsync()

For TCP clients, the client should not run in the same process, just use a new shell and do all the above steps for packet registration, but set the argument adaptPacketIds to True in the PacketRegistry::
   
   [client]>>> client = packetmq.Client(reg)
   [client]>>> client.connect(("localhost",12345)) # change the address to the server's IP address, if not on the same machine
   [client]>>> client.runAsync()

Now, both peers are connected and you can start transmitting data using :py:meth:`sendPacket() <packetmq.Peer.sendPacket>`\ ::
   
   [client]>>> client.sendPacket({"foo":"bar",123:None,0.001:True,"mylist":["abc","def"]},"myapplication:mypacket")
   [client]>>> {"foo":"bar",123:None,0.001:True,"mylist":["abc","def"]} # Note that this output will be received AFTER the function completed and thus the prompt will already appear
   [server]Received EchoPacket: {"foo":"bar",123:None,0.001:True,"mylist":["abc","def"]} # Printed on the server

You could also send packets from the server to the client or maybe you want to communicate between threads, then you can use :py:class:`packetmq.MemoryServer` and :py:class:`packetmq.MemoryClient`

Creating new packet types
-------------------------

Coming soon, for now look at the sources on github if you want information about creating new packet types.

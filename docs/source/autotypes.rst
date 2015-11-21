.. _autotypes:

Auto-Types
==========

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


####################################################
# DVrouter.py
# Name: Junyong Zhao
# PennKey: junyong
#####################################################

import sys
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads


class DVrouter(Router):
    def __init__(self, addr, heartbeatTime):
        Router.__init__(self, addr)
        self.infty = 16
        self.timestamp = 0
        self.hbtime = heartbeatTime
        self.addr = addr
        self.rtable = {}
        self.nport = {}
        self.nadd = {}

    def handlePacket(self, port, packet):
        if packet.isTraceroute():
            if packet.dstAddr in self.rtable:
                if self.rtable[packet.dstAddr]["cost"] < self.infty and self.rtable[packet.dstAddr]["eport"] != None:
                    self.send(self.rtable[packet.dstAddr]["eport"], packet)

        elif packet.isRouting():
            content = loads(packet.getContent())
            for add in content.keys():
                if content[add]["cost"] == self.infty and content[add]["nhop"] == packet.srcAddr:
                    self.rtable[add]["cost"] = self.infty
                    self.rtable[add]["nhop"] = None
                    self.rtable[add]["eport"] = None
                if add not in self.rtable:
                    # we've never seen this before
                    cost = content[add]["cost"] + \
                        self.nadd[packet.srcAddr]["cost"]
                    nhop = packet.srcAddr
                    eport = self.rtable[packet.srcAddr]["eport"]
                    if cost >= self.infty:
                        cost = self.infty
                        nhop = None
                        eport = None
                    self.rtable[add] = {
                        "cost": cost,
                        "nhop": nhop,
                        "eport": eport
                    }
                else:
                    # if this is a better route
                    if content[add]["cost"] + self.nadd[packet.srcAddr]["cost"] < self.rtable[add]["cost"]:
                        self.rtable[add]["cost"] = content[add]["cost"] + \
                            self.nadd[packet.srcAddr]["cost"]
                        self.rtable[add]["nhop"] = packet.srcAddr
                        self.rtable[add]["eport"] = self.rtable[packet.srcAddr]["eport"]
                    # if there's a break in the packet
                    elif content[add]["cost"] == self.infty and self.rtable[add]["nhop"] == packet.srcAddr:
                        self.rtable[add]["cost"] = self.infty
                        self.rtable[add]["nhop"] = None
                        self.rtable[add]["eport"] = None

    def handleNewLink(self, port, endpoint, cost):
        self.nport[port] = endpoint
        self.nadd[endpoint] = {
            "eport": port,
            "cost": cost
        }
        if endpoint not in self.rtable or cost < self.rtable[endpoint]["cost"]:
            self.rtable[endpoint] = {
                "cost": cost,
                "nhop": endpoint,
                "eport": port
            }
        for entry in self.rtable:
            packet = Packet(Packet.ROUTING, self.addr, entry)
            packet.content = dumps(self.rtable)
            self.send(self.rtable[entry]["eport"], packet)

    def handleRemoveLink(self, port):
        nadd = self.nport[port]
        del self.nport[port]
        del self.nadd[nadd]
        for entry in self.rtable:
            if self.rtable[entry]["eport"] == port:
                self.rtable[entry] = {
                    "cost": self.infty,
                    "nhop": None,
                    "eport": None
                }
        for entry in self.rtable:
            packet = Packet(Packet.ROUTING, self.addr, entry)
            packet.content = dumps(self.rtable)
            self.send(self.rtable[entry]["eport"], packet)

    def handleTime(self, timeMillisecs):
        if timeMillisecs - self.timestamp >= self.hbtime:
            for entry in self.rtable:
                packet = Packet(Packet.ROUTING, self.addr, entry)
                packet.content = dumps(self.rtable)
                self.send(self.rtable[entry]["eport"], packet)
            self.timestamp = timeMillisecs

    def debugString(self):
        return ""

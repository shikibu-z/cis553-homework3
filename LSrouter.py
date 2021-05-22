####################################################
# LSrouter.py
# Name: Junyong Zhao
# PennKey: junyong
#####################################################

import sys
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads


class LSrouter(Router):
    def __init__(self, addr, heartbeatTime):
        Router.__init__(self, addr)
        self.seq_num = 0
        self.timestamp = 0
        self.hbtime = heartbeatTime
        self.tent = {}  # tentative list
        self.conf = {   # confirmed list
            addr: {
                "cost": 0,
                "nhop": None,
                "nupdate": True
            }
        }
        self.neighb = {}  # for storing neighbour
        self.rpacket = {
            addr: {
                "seq_num": self.seq_num,
                "neighb": self.neighb
            }
        }

    def handlePacket(self, port, packet):
        # simply send packet if it is a traceroute
        if packet.isTraceroute():
            eport = None
            if packet.dstAddr in self.conf:
                nhop = self.conf[packet.dstAddr]["nhop"]
                if nhop == None:
                    eport = None
                else:
                    if nhop in self.neighb:
                        eport = self.neighb[nhop]["eport"]
                    else:
                        eport = None
            if eport != None:
                self.send(eport, packet)

        # updating by LS, if it is routing
        elif packet.isRouting():
            content = loads(packet.getContent())
            if packet.srcAddr not in self.rpacket or self.rpacket[packet.srcAddr]["seq_num"] < content["seq_num"]:
                self.tent = {}
                self.conf = {}
                self.conf[self.addr] = {
                    "cost": 0,
                    "nhop": None,
                    "nupdate": True
                }
                self.rpacket[packet.srcAddr] = content
                while 1:
                    for add in self.conf:
                        if self.conf[add]["nupdate"]:
                            if add in self.rpacket:
                                next_add = self.rpacket[add]
                                next_neighb = next_add["neighb"]
                                for nadd in next_neighb:
                                    cost_to_neighb = self.conf[add]["cost"] + \
                                        next_neighb[nadd]["cost"]
                                    # if not on tentative / confirmed, add to tentative list
                                    if nadd not in self.tent and nadd not in self.conf:
                                        if add == self.addr:
                                            self.tent[nadd] = {
                                                "cost": cost_to_neighb,
                                                "nhop": nadd
                                            }
                                        else:
                                            nhop = self.conf[add]["nhop"]
                                            self.tent[nadd] = {
                                                "cost": cost_to_neighb,
                                                "nhop": nhop
                                            }
                                    # in tentative and has lower cost, replace current confirm entry
                                    elif nadd in self.tent and cost_to_neighb < self.tent[nadd]["cost"]:
                                        nhop = self.conf[add]["nhop"]
                                        self.tent[nadd] = {
                                            "cost": cost_to_neighb,
                                            "nhop": nhop
                                        }
                                self.conf[add]["nupdate"] = False
                    if not self.tent:  # break if tentative is empty
                        break
                    else:
                        infty = float("inf")
                        min_cost_add = None
                        for tent_add in self.tent:
                            if self.tent[tent_add]["cost"] < infty:
                                infty = self.tent[tent_add]["cost"]
                                min_cost_add = tent_add
                                self.conf[min_cost_add] = {
                                    "cost": self.tent[min_cost_add]["cost"],
                                    "nhop": self.tent[min_cost_add]["nhop"],
                                    "nupdate": True
                                }
                        del self.tent[min_cost_add]
                # broadcast LSP
                for add in self.neighb:
                    if port != self.neighb[add]["eport"] and packet.srcAddr != add:
                        self.send(self.neighb[add]["eport"], packet)

    def handleNewLink(self, port, endpoint, cost):
        self.rpacket[self.addr]['neighb'] = self.neighb
        self.neighb[endpoint] = {
            "cost": cost,
            "eport": port
        }
        # generate LSP, same below
        content = {
            "nid": self.addr,
            "neighb": self.neighb,
            "seq_num": self.seq_num
        }
        content = dumps(content)
        for add in self.neighb:
            packet = Packet(Packet.ROUTING, self.addr, add, content)
            self.send(self.neighb[add]["eport"], packet)
        self.seq_num += 1

    def handleRemoveLink(self, port):
        for add in self.neighb.keys():
            if self.neighb[add]["eport"] == port:
                del self.rpacket[add]
                del self.neighb[add]
                if self.addr in self.rpacket and self.rpacket[self.addr]['neighb'] != None and add in self.rpacket[self.addr]["neighb"]:
                    del self.rpacket[self.addr]["neighb"][add]
                content = {
                    "nid": self.addr,
                    "neighb": self.neighb,
                    "seq_num": self.seq_num
                }
                content = dumps(content)
                for entry in self.neighb:
                    packet = Packet(Packet.ROUTING, self.addr, entry, content)
                    self.send(self.neighb[entry]["eport"], packet)
                self.seq_num += 1

    def handleTime(self, timeMillisecs):
        if timeMillisecs - self.timestamp >= self.hbtime:
            content = {
                "nid": self.addr,
                "neighb": self.neighb,
                "seq_num": self.seq_num
            }
            content = dumps(content)
            for add in self.neighb:
                packet = Packet(Packet.ROUTING, self.addr, add, content)
                self.send(self.neighb[add]["eport"], packet)
            self.seq_num += 1
            self.timestamp = timeMillisecs

    def debugString(self):
        # this is empty when all tests passed
        return ""

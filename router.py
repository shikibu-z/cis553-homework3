import time
import sys
import thread
import Queue


class Router:
    """
    Router superclass that handles the details of
    packet send/receive and link changes.
    Subclass this class and override the "handle..." methods
    to implement routing algorithm functionality
    """

    def __init__(self, addr, heartbeatTime = None):
        """Initialize Router address and threadsafe queue for link changes"""
        self.addr = addr            # address of router
        self.nextFreePort = 1
        self.portMap = {}           # links indexed by port
        self.linkMap = {}
        self.linkChanges = Queue.Queue()


    def changeLink(self, change):
        """
        Add, remove, or change the cost of a link.
        The change argument is a tuple with first element
        'up', or 'down'
        """
        self.linkChanges.put(change)


    def addLink(self, endpointAddr, link, cost):
        """Add new link to router"""
        if link in self.portMap:
            port = self.removeLink(link)
        else:
            port = self.nextFreePort
            self.nextFreePort += 1
        
        self.portMap[link] = port
        self.linkMap[port] = link
        self.handleNewLink(port, endpointAddr, cost)


    def removeLink(self, link):
        """Remove link from router"""
        port = self.portMap[link]
        del self.portMap[link]
        del self.linkMap[port]
        self.handleRemoveLink(port)

        return port


    def runRouter(self):
        """Main loop of router"""
        while True:
            time.sleep(0.1)
            timeMillisecs = int(round(time.time() * 1000))
            try:
                change = self.linkChanges.get_nowait()
                if change[0] == "up":
                    self.addLink(*change[1:])
                elif change[0] == "down":
                    self.removeLink(*change[1:])
            except Queue.Empty:
                pass
            for link, port in self.portMap.items():
                packet = link.recv(self.addr)
                if packet:
                    self.handlePacket(port, packet)
            self.handleTime(timeMillisecs)


    def send(self, port, packet):
        """Send a packet out given port"""
        try:
            self.linkMap[port].send(packet, self.addr)
        except KeyError:
            pass

    """
    TODO: These are the functions you should override in your implementations
    """


    def handlePacket(self, port, packet):
        """process incoming packet"""
        # default implementation sends packet back out the port it arrived
        self.send(port, packet)


    def handleNewLink(self, port, endpoint, cost):
        """handle new link"""
        pass


    def handleRemoveLink(self, port):
        """handle removed link"""
        pass


    def handleTime(self, timeMillisecs):
        """handle current time"""
        pass


    def debugString(self):
        """generate a string for debugging in network visualizer"""
        return "Mirror router: address {}".format(self.addr)

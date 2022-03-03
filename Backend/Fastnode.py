from p2pnetwork.node import Node
import sys
import time
import socket

class FASTnode (Node):              

    # Python class constructor
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(FASTnode, self).__init__(host, port, id, callback, max_connections)
        self.connections = []
        self.received_nodes = ""
        print(str(port) + " Started")

    # all the methods below are called when things happen in the network.
    # implement your network node behavior to create the required functionality.

    def outbound_node_connected(self, node):
        print("outbound_node_connected (" + self.id + "): " + node.id)
        
    def inbound_node_connected(self, node):
        print("inbound_node_connected: (" + self.id + "): " + node.id)

    def inbound_node_disconnected(self, node):
        print("inbound_node_disconnected: (" + self.id + "): " + node.id)

    def outbound_node_disconnected(self, node):
        print("outbound_node_disconnected: (" + self.id + "): " + node.id)

    def node_message(self, node, data):
        print("node_message (" + str(self.id) + ") from " + node.id + ": " + str(data))
        self.received_nodes = data
        
    def node_disconnect_with_outbound_node(self, node):
        print("node wants to disconnect with oher outbound node: (" + self.id + "): " + node.id)
        
    def node_request_to_stop(self):
        print("node is requested to stop (" + self.id + "): ")

    def signature_share_init(self): 
        print( str(self.id) + " Started sharing")
        time.sleep(2)
        totalnodes = self.nodes_inbound + self.nodes_outbound 
        word_to_sign = "Sign"
        msg = ""
        for i in range(len(totalnodes)):    
            print(str(self.id) + " Started Round: " + str(i))
            if i == 0: # Round 0
                msg = word_to_sign + str(self.port)
                for n in totalnodes :
                    print (n)
                    self.send_to_node(n, msg)
                    time.sleep(1)
            else:
                msgList = []
                for i in range(len(totalnodes)):
                    rmsg = self.sock.recvfrom(4096)
                    msgList.append(rmsg)
                result = all(element == msgList[0] for element in msgList)
                if result :
                    print("All msges are equal")
                else:
                    for msg in msgList: 
                        if str(self.port) in msg: # if my signiture is in msg
                            for p in totalnodes :
                                self.send_to_node(p, msg)
                        else: # If my signiture is NOT in msg
                            msg = msg + str(self.port)
                            for p in totalnodes :
                                self.send_to_node(p, msg)

    def run(self):
        self.connect_with_node("127.0.0.1",8001)

        msg = self.host + " " + str(self.port)

        self.send_to_nodes(msg)

        time.sleep(1)

        splitString = self.received_nodes.strip("[]")

        splitString.split(",")

        print(splitString[0])

        # self.print_connections()

        

        
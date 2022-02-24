from p2pnetwork.node import Node
import sys
import time
import socket



class MyOwnPeer2PeerNode (Node):

    # Python class constructor
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(MyOwnPeer2PeerNode, self).__init__(host, port, id, callback, max_connections)
        print("MyPeer2PeerNode: Started")

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
        print("node_message (" + str(self.port) + ") from " + node.id + ": " + str(data))
        
    def node_disconnect_with_outbound_node(self, node):
        print("node wants to disconnect with oher outbound node: (" + self.id + "): " + node.id)
        
    def node_request_to_stop(self):
        print("node is requested to stop (" + self.id + "): ")

    def signature_share_init(self): 
        print( str(self.port) + " Started sharing")
        totalnodes = self.nodes_inbound + self.nodes_outbound 
        word_to_sign = "Sign"
        msg = ""
        print(str(len(totalnodes)) + " Nodes known by " + str(self.port))
        for i in range(len(totalnodes)):    
            print("Round: " + str(i))
            if i == 0: # Round 0
                msg = word_to_sign + str(self.port)
                for n in self.nodes_outbound :
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

node_1 = MyOwnPeer2PeerNode("127.0.0.1", 8001, 1)
node_2 = MyOwnPeer2PeerNode("127.0.0.1", 8005, 2)
node_3 = MyOwnPeer2PeerNode("127.0.0.1", 8003, 3)

nodelist = [node_1,node_2,node_3]

for n in nodelist:
    n.start()

node_1.connect_with_node(node_2.host,node_2.port)
node_1.connect_with_node(node_3.host,node_3.port)
time.sleep(1)


node_1.signature_share_init()   

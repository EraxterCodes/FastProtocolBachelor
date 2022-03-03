from p2pnetwork.node import Node
import sys
import time



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
        print("node_message (" + self.id + ") from " + node.id + ": " + str(data))
        
    def node_disconnect_with_outbound_node(self, node):
        print("node wants to disconnect with oher outbound node: (" + self.id + "): " + node.id)
        
    def node_request_to_stop(self):
        print("node is requested to stop (" + self.id + "): ")


node_1 = MyOwnPeer2PeerNode("127.0.0.1", 8001,3)

time.sleep(1)

node_1.start()
time.sleep(1)   
node_1.connect_with_node('127.0.0.1', 8002)
node_1.send_to_nodes("Hi im node 1 nice to meet you all!")




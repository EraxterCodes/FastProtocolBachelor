from re import S
from p2pnetwork.node import Node
import sys
import time
import socket


class BroadcastNode (Node):              
    # Python class constructor
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(BroadcastNode, self).__init__(host, port, id, callback, max_connections)
        self.connections = []

    def outbound_node_connected(self, connected_node):
        print("outbound_node_connected: " + connected_node.id)
        
    def inbound_node_connected(self, connected_node):
        print("inbound_node_connected: " + connected_node.id)

    def inbound_node_disconnected(self, connected_node):
        print("inbound_node_disconnected: " + connected_node.id)

    def outbound_node_disconnected(self, connected_node):
        print("outbound_node_disconnected: " + connected_node.id)

    def node_message(self, connected_node, data):
        print("node_message from " + connected_node.id + ": " + str(data))
        
    def node_disconnect_with_outbound_node(self, connected_node):
        print("node wants to disconnect with oher outbound node: " + connected_node.id)
        
    def node_request_to_stop(self):
        print("node is requested to stop!")
    

    def run(self):
        while not self.terminate_flag.is_set():
            connection, client_address = self.sock.accept()

            # Basic information exchange (not secure) of the id's of the nodes!
            connected_node_id = connection.recv(4096).decode('utf-8')
            connection.send(self.id.encode('utf-8'))

            connected_node_msg = connection.recv(4096).decode('utf-8')
            print(connected_node_msg)

            thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
            thread_client.start()

            self.nodes_inbound.append(thread_client)
            self.inbound_node_connected(thread_client)

            self.connections.append(connected_node_msg)

            if len(self.connections) == 3:
                break

        self.send_to_nodes(str(self.connections))
    
        print("Broadcast Finished")

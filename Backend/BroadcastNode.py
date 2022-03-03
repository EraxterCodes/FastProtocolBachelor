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
    def run(self):
        while not self.terminate_flag.is_set():
            connection, client_address = self.sock.accept()
            self.connections.append(connection)
            # Basic information exchange (not secure) of the id's of the nodes!
            connected_node_id = connection.recv(4096).decode('utf-8') # When a node is connected, it sends it id!
            connection.send(self.id.encode('utf-8')) # Send my id to the connected node!

            thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
            thread_client.start()

            self.nodes_inbound.append(thread_client)
            self.inbound_node_connected(thread_client)
            if len(self.connections) == 2:
                print("INbound less than 2")
                break
            else:
                print("Length not 2 :" + str(len(self.connections)))
            self.send_to_nodes(self.connections)
            print("Broadcast Finished")



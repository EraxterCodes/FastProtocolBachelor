from p2pnetwork.node import Node
from Backend.Nodes.FastNodeConnection import FastNodeConnection
import socket

class FastNode (Node):
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(FastNode, self).__init__(host, port, id, callback, max_connections)
        self.received_nodes = ""

    def init_server(self):
        print("Initialisation of the Node on port: " + str(self.port) + " on node (" + self.id + ")")
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(20.0)
        self.sock.listen(1)

    def create_new_connection(self, connection, id, host, port):
        return FastNodeConnection(self, connection, id, host, port)

    def outbound_node_connected(self, connected_node):
        print("outbound_node_connected: " + connected_node.id)
        
    def inbound_node_connected(self, connected_node):
        print("inbound_node_connected: " + connected_node.id)

    def inbound_node_disconnected(self, connected_node):
        print("inbound_node_disconnected: " + connected_node.id)

    def outbound_node_disconnected(self, connected_node):
        print("outbound_node_disconnected: " + connected_node.id)

    def node_message(self, connected_node, data):
        self.received_nodes = data #Modified this to send all nodes to broadcastnode
        print("node_message from " + connected_node.id + ": " + str(data))
        
    def node_disconnect_with_outbound_node(self, connected_node):
        print("node wants to disconnect with oher outbound node: " + connected_node.id)
        
    def node_request_to_stop(self):
        print("node is requested to stop!")

    def start_thread_connection(self, connection, connected_node_id, client_address):
        thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
        thread_client.start()

        self.nodes_inbound.append(thread_client)
        self.inbound_node_connected(thread_client)

    def exchange_id(self, connection):
        connected_node_id = connection.recv(4096).decode('utf-8')
        connection.send(self.id.encode('utf-8'))

        return connected_node_id
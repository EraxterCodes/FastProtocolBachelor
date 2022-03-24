from modules.p2pnetwork.node import Node
from Infrastructure.Nodes.FastNodeConnection import FastNodeConnection
import time
import socket

class FastNode (Node):
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(FastNode, self).__init__(host, port, id, callback, max_connections)
        self.clients = []
        self.messages = []
        
        self.coding_type = 'utf-8'
        
        self.broadcast_host = "127.0.0.1"
        self.broadcast_port = 8001

    def init_server(self):
        print("Initialisation of the Node on port: " + str(self.port) + " on node (" + self.id + ")")
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(None)
        self.sock.listen()

    def accept_connections(self):
        while not self.terminate_flag.is_set():  # Check whether the thread needs to be closed
            try:
                self.debug_print("Node: Wait for incoming connection")
                connection, client_address = self.sock.accept()

                self.debug_print("Total inbound connections:" + str(len(self.nodes_inbound)))
                # When the maximum connections is reached, it disconnects the connection 
                if self.max_connections == 0 or len(self.nodes_inbound) < self.max_connections:
                    
                    # Basic information exchange (not secure) of the id's of the nodes!
                    connected_node_id = connection.recv(4096).decode('utf-8') # When a node is connected, it sends it id!
                    connection.send(self.id.encode('utf-8')) # Send my id to the connected node!

                    thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
                    thread_client.start()

                    self.nodes_inbound.append(thread_client)
                    self.inbound_node_connected(thread_client)
                    
                else:
                    self.debug_print("New connection is closed. You have reached the maximum connection limit!")
                    connection.close()
            
            except socket.timeout:
                self.debug_print('Node: Connection timeout!')

            except Exception as e:
                raise e

            self.reconnect_nodes()

            time.sleep(0.01)

        print("Node stopping...")
        for t in self.nodes_inbound:
            t.stop()

        for t in self.nodes_outbound:
            t.stop()

        time.sleep(1)

        for t in self.nodes_inbound:
            t.join()

        for t in self.nodes_outbound:
            t.join()

        self.sock.settimeout(None)   
        self.sock.close()
        print("Node stopped")

    def connect_with_node(self, host, port, reconnect=False):
        if host == self.host and port == self.port:
            # print("connect_with_node: Cannot connect with yourself!!")
            return False

        for node in self.nodes_outbound:
            if node.host == host and node.port == port:
                # print("connect_with_node: Already connected with this node (" + node.id + ").")
                return True

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.debug_print("connecting to %s port %s" % (host, port))
            print(f"{self.id} connected to {str(host)} {str(port)}")
            sock.connect((host, port))
            
            sock.send(self.id.encode('utf-8')) # Send my id to the connected node!
            connected_node_id = sock.recv(4096).decode('utf-8') # When a node is connected, it sends it id!

            for node in self.nodes_inbound:
                if node.host == host and node.id == connected_node_id:
                    # print("connect_with_node: This node (" + node.id + ") is already connected with us.")
                    return True

            thread_client = self.create_new_connection(sock, connected_node_id, host, port)
            thread_client.start()
                        
            self.nodes_outbound.append(thread_client)
            self.outbound_node_connected(thread_client)

            # If reconnection to this host is required, it will be added to the list!
            if reconnect:
                self.debug_print("connect_with_node: Reconnection check is enabled on node " + host + ":" + str(port))
                self.reconnect_to_nodes.append({
                    "host": host, "port": port, "tries": 0
                })

        except Exception as e:
            self.debug_print("TcpServer.connect_with_node: Could not connect with node. (" + str(e) + ")")


    def create_new_connection(self, connection, id, host, port):
        return FastNodeConnection(self, connection, id, host, port)

    def outbound_node_connected(self, connected_node):
        pass
        # print("outbound_node_connected: " + connected_node.id)
        
    def inbound_node_connected(self, connected_node):
        pass
        # print("inbound_node_connected: " + connected_node.id)

    def inbound_node_disconnected(self, connected_node):
        pass
        # print("inbound_node_disconnected: " + connected_node.id)

    def outbound_node_disconnected(self, connected_node):
        pass
        # print("outbound_node_disconnected: " + connected_node.id)

    def node_message(self, connected_node, data):
        print(str(self.id) + " node_message from " + connected_node.id + ": " + str(data))
        
    def node_disconnect_with_outbound_node(self, connected_node):
        pass
        # print("node wants to disconnect with oher outbound node: " + connected_node.id)
        
    def node_request_to_stop(self):
        pass
        # print("node is requested to stop!")

        

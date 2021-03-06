import hashlib
import random
from p2pnetwork.node import Node
from Infrastructure.Nodes.FastNodeConnection import FastNodeConnection
from src.PedersenCommitment.Pedersen import Pedersen
import time
import socket


class FastNode (Node):
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(FastNode, self).__init__(
            host, port, id, callback, max_connections)
        self.clients = []
        self.messages = []

        self.pd = Pedersen()

        self.coding_type = 'utf-8'

    def init_server(self):
        print("Initialisation of the Node on port: " +
              str(self.port) + " on node (" + self.id + ")")
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(20)
        self.sock.listen()

    def accept_connections(self):
        while not self.terminate_flag.is_set():  # Check whether the thread needs to be closed
            try:
                self.debug_print("Node: Wait for incoming connection")
                connection, client_address = self.sock.accept()

                self.debug_print("Total inbound connections:" +
                                 str(len(self.nodes_inbound)))
                # When the maximum connections is reached, it disconnects the connection
                if self.max_connections == 0 or len(self.nodes_inbound) < self.max_connections:

                    # Basic information exchange (not secure) of the id's of the nodes!
                    connected_node_id = connection.recv(65534).decode(
                        'utf-8')  # When a node is connecte, it sends it id!
                    # Send my id to the connected node!
                    connection.send(self.id.encode('utf-8'))

                    thread_client = self.create_new_connection(
                        connection, connected_node_id, client_address[0], client_address[1])
                    thread_client.start()

                    self.nodes_inbound.append(thread_client)
                    self.inbound_node_connected(thread_client)

                else:
                    self.debug_print(
                        "New connection is closed. You have reached the maximum connection limit!")
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
            return False

        for node in self.nodes_outbound:
            if node.host == host and node.port == port:
                return True

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.debug_print("connecting to %s port %s" % (host, port))
            print(f"{self.id} connected to {str(host)} {str(port)}")
            sock.connect((host, port))

            # Send my id to the connected node!
            sock.send(self.id.encode('utf-8'))
            # When a node is connected, it sends it id!
            connected_node_id = sock.recv(65534).decode('utf-8')

            for node in self.nodes_inbound:
                if node.host == host and node.id == connected_node_id:
                    return True

            thread_client = self.create_new_connection(
                sock, connected_node_id, host, port)
            thread_client.start()

            self.nodes_outbound.append(thread_client)
            self.outbound_node_connected(thread_client)

            # If reconnection to this host is required, it will be added to the list!
            if reconnect:
                self.debug_print(
                    "connect_with_node: Reconnection check is enabled on node " + host + ":" + str(port))
                self.reconnect_to_nodes.append({
                    "host": host, "port": port, "tries": 0
                })

        except Exception as e:
            self.debug_print(
                "TcpServer.connect_with_node: Could not connect with node. (" + str(e) + ")")

    def create_new_connection(self, connection, id, host, port):
        return FastNodeConnection(self, connection, id, host, port)

    def send_to_node(self, n: FastNodeConnection, data) -> None:
        """ Send the data to the node n if it exists."""
        self.message_count_send += 1
        if n in self.all_nodes:
            n.send(data)
        else:
            self.debug_print("Node send_to_node: Could not send the data, node is not found!")

    def send_to_nodes(self, data, exclude: list[FastNodeConnection] = []) -> None:
        """ Send a message to all the nodes that are connected with this node. data is a python variable which is
            converted to JSON that is send over to the other node. exclude list gives all the nodes to which this
            data should not be sent."""
        nodes = filter(lambda node: node not in exclude, self.all_nodes)
        for n in nodes:
            self.send_to_node(n, data)

    
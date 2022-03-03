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

    def connect_with_node(self, host, port, reconnect=False):
        """ Make a connection with another node that is running on host with port. When the connection is made, 
            an event is triggered outbound_node_connected. When the connection is made with the node, it exchanges
            the id's of the node. First we send our id and then we receive the id of the node we are connected to.
            When the connection is made the method outbound_node_connected is invoked. If reconnect is True, the
            node will try to reconnect to the code whenever the node connection was closed."""

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
            sock.connect((host, port))

            sock.send(self.id.encode('utf-8')) 
            connected_node_id = sock.recv(4096).decode('utf-8') 

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
                        if str(self.port) in msg:
                            for p in totalnodes :
                                self.send_to_node(p, msg)
                        else: 
                            msg = msg + str(self.port)
                            for p in totalnodes :
                                self.send_to_node(p, msg)

    def connect_to_fastnode(self, nodes):
        for i in range(len(nodes)):
            client_address_info = nodes[i].split(" ")

            self.connect_with_node(client_address_info[0], int(client_address_info[1]))
            if not i == len(nodes) - 1:
                connection, client_address = self.sock.accept()

                connected_node_id = connection.recv(4096).decode('utf-8')
                connection.send(self.id.encode('utf-8'))

                thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
                thread_client.start()

                self.nodes_inbound.append(thread_client)
                self.inbound_node_connected(thread_client)
    
    def get_trimmed_node_info(self):
        splitArray = self.received_nodes.strip("[]").split(",")
        trimmmedArray = []

        for i in splitArray:
            trimmmedArray.append(i.strip()[1:-5])

        return trimmmedArray

    def run(self):
        self.connect_with_node("127.0.0.1",8001)

        msg = self.host + " " + str(self.port)
        self.send_to_nodes(msg)

        time.sleep(1)

        trimmed = self.get_trimmed_node_info()

        self.connect_to_fastnode(trimmed)

        print("Finished Round 0 for " + str(self.port))
    

        
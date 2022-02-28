from p2pnetwork.node import Node
import sys
import time
import socket

class FASTnode (Node):              

    # Python class constructor
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(FASTnode, self).__init__(host, port, id, callback, max_connections)
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
    def run(self):
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
                self.signature_share_init()
            
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

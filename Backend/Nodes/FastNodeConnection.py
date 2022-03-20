from p2pnetwork.nodeconnection import NodeConnection
import time
import socket
import json

class FastNodeConnection(NodeConnection):
    def __init__(self, main_node, sock, id, host, port):
        super(FastNodeConnection, self).__init__(main_node, sock, id, host, port)
        self.sock.settimeout(None)
        self.message = ""

    def send(self, data, encoding_type='utf-8'):
        """Send the data to the connected node. The data can be pure text (str), dict object (send as json) and bytes object.
           When sending bytes object, it will be using standard socket communication. A end of transmission character 0x04 
           utf-8/ascii will be used to decode the packets ate the other node. When the socket is corrupted the node connection
           is closed."""
        if isinstance(data, str):
            try:
                self.sock.send( data.encode(encoding_type))

            except Exception as e: # Fixed issue #19: When sending is corrupted, close the connection
                self.main_node.debug_print("nodeconnection send: Error sending data to node: " + str(e))
                self.stop() # Stopping node due to failure

        elif isinstance(data, dict):
            try:
                json_data = json.dumps(data)
                json_data = json_data.encode(encoding_type)
                self.sock.sendall(json_data)
                
            except TypeError as type_error:
                self.main_node.debug_print('This dict is invalid')
                self.main_node.debug_print(type_error)

            except Exception as e: # Fixed issue #19: When sending is corrupted, close the connection
                self.main_node.debug_print("nodeconnection send: Error sending data to node: " + str(e))
                self.stop() # Stopping node due to failure

        elif isinstance(data, bytes):
            bin_data = data
            self.sock.sendall(bin_data)

        else:
            self.main_node.debug_print('datatype used is not valid plese use str, dict (will be send as json) or bytes')

    def reset_node_message(self):
        self.message = ""

    def get_node_message(self):
        return self.message

    def run(self):
        """The main loop of the thread to handle the connection with the node. Within the
           main loop the thread waits to receive data from the node. If data is received 
           the method node_message will be invoked of the main node to be processed."""          
        buffer = b'' # Hold the stream that comes in!

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while not self.terminate_flag.is_set():
            chunk = b''
            try:
                chunk = self.sock.recv(4096) 
                # self.main_node.node_message( self, chunk.decode('utf-8'))
                self.message = chunk.decode('utf-8')

            except socket.timeout:
                self.main_node.debug_print("NodeConnection: timeout")

            except Exception as e:
                self.terminate_flag.set() # Exception occurred terminating the connection
                self.main_node.debug_print('Unexpected error')
                self.main_node.debug_print(e)

            time.sleep(2)

        # IDEA: Invoke (event) a method in main_node so the user is able to send a bye message to the node before it is closed?
        self.sock.settimeout(None)
        self.sock.close()
        self.main_node.node_disconnected( self ) # Fixed issue #19: Send to main_node when a node is disconnected. We do not know whether it is inbounc or outbound.
        self.main_node.debug_print("NodeConnection: Stopped")


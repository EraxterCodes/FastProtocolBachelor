from p2pnetwork.nodeconnection import NodeConnection
import time
import socket
import json


class FastNodeConnection(NodeConnection):
    def __init__(self, main_node, sock, id, host, port):
        super(FastNodeConnection, self).__init__(
            main_node, sock, id, host, port)
        self.sock.settimeout(None)

        self.coding_type = 'utf-8'

        self.message = ""

    def send(self, data):
        if isinstance(data, str):
            try:
                self.sock.sendall(data.encode(
                    self.coding_type))  # Changed this

            except Exception as e:
                self.main_node.debug_print(
                    "nodeconnection send: Error sending data to node: " + str(e))
                self.stop()

        elif isinstance(data, dict):
            try:
                json_data = json.dumps(data)
                json_data = json_data.encode(self.coding_type)
                self.sock.sendall(json_data)

            except TypeError as type_error:
                self.main_node.debug_print('This dict is invalid')
                self.main_node.debug_print(type_error)

            except Exception as e:  # Fixed issue #19: When sending is corrupted, close the connection
                self.main_node.debug_print(
                    "nodeconnection send: Error sending data to node: " + str(e))
                self.stop()  # Stopping node due to failure

        elif isinstance(data, bytes):
            bin_data = data
            self.sock.sendall(bin_data)

        else:
            self.main_node.debug_print(
                'datatype used is not valid plese use str, dict (will be send as json) or bytes')

    def reset_node_message(self):
        self.message = ""

    def get_node_message(self):
        return self.message

    def run(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while not self.terminate_flag.is_set():
            try:
                chunk = self.sock.recv(16384).decode(self.coding_type)

                # Has a lot of print statements for debugging
                if chunk != "":
                    # self.main_node.node_message( self, chunk)
                    self.message = chunk

                # Doesn't have a lot of print statements
                # self.message = chunk

            except socket.timeout:
                self.main_node.debug_print("NodeConnection: timeout")

            except Exception as e:
                self.terminate_flag.set()  # Exception occurred terminating the connection
                self.main_node.debug_print('Unexpected error')
                self.main_node.debug_print(e)

            time.sleep(0.01)

        self.sock.settimeout(None)
        self.sock.close()
        self.main_node.node_disconnected(self)
        self.main_node.debug_print("NodeConnection: Stopped")

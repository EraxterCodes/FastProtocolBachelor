from p2pnetwork.node import Node
import time

class EchoServer(Node):
    def __init__(self, connection):
        super(Node)
        self.connection = connection
        self.list = []

    #TODO Only append msg if msg isn't empty
    def run(self):
        while True:
            msg = self.connection.recv(4096).decode('utf-8')
            self.send_to_nodes(msg)

            if msg not in self.list:
                self.list.append(msg)
   


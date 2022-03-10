from p2pnetwork.node import Node
import time

class ClientMessageQueue(Node):
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(Node, self).__init__(host, port, id, callback, max_connections)
        self.connection = connection
        self.message_queue = []

    #TODO Only append msg if msg isn't empty
    def run(self):

        while True:
            msg = self.connection.recv(4096).decode('utf-8')
            # send to client
            if "send" in msg: 
                self.send_to_node(connection, self.message_queue[0])
                message_queue.pop()

            message_queue.append(msg)
            
   


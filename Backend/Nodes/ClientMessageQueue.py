from Backend.Nodes.FastNode import FastNode
import time

class ClientMessageQueue(FastNode):
    def __init__(self, host, port, node_count, id=None, callback=None, max_connections=0):
        super(ClientMessageQueue, self).__init__(host, port, id, callback, max_connections)
        self.message_queue = []
        self.connection = None
        self.node_count = node_count
        self.connection_count = 0

    #TODO Only append msg if msg isn't empty
    def run(self):
        while not self.terminate_flag.is_set():
            self.connection, client_address = self.sock.accept()
            self.connection_count += 1

            connected_node_id = self.exchange_id(self.connection)

            self.start_thread_connection(self.connection, connected_node_id, client_address)
            if self.connection_count == self.node_count:
                break
            
        
        while True:
            print(str(self.connection_count) + " i was a MQ")
            msg = self.connection.recv(4096).decode('utf-8')
            # send to client
            if "send" in msg: 
                self.send_to_node(self.connection, self.message_queue[0])
                self.message_queue.pop()

            if "send" not in msg and msg != "" :
                self.message_queue.append(msg)
            
   


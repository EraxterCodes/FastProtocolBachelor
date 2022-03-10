from Backend.Nodes.FastNode import FastNode
from Backend.Nodes.ClientMessageQueue import ClientMessageQueue
import time
import ecdsa

class ClientNode (FastNode): 
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(host, port, id, callback, max_connections)
        self.connectionList = []
        self.received_nodes = ""
        self.mq_connection = None
        
        self.secret_key = ecdsa.SigningKey.generate()
        self.public_key = self.secret_key.verifying_key
        
        self.public_keys_set = {}

    def get_msg_q_connection(self):
        for i in self.nodes_outbound:
            if str(self.msg_q.port) in str(i):
                return i
        return None


    def signature_share_init(self): 
        print(str(self.port) + " Started sharing")
        time.sleep(0.1)
        totalnodes = self.nodes_inbound + self.nodes_outbound

        msg_q = self.get_msg_q_connection()
        
        excluded_nodes = [msg_q, self.nodes_outbound[0]]
        
        for i in range(len(totalnodes)):    
            print(self.id + " Started Round: " + str(i))
            if i == 0: # Round 0
                msg = "Message :-) " #+ self.secret_key.sign(b"Message :-)")
                self.send_to_nodes(msg,exclude=excluded_nodes)
                # print(self.id + "Has sent to following connections:" + str(self.nodes_outbound))
            elif i == 1:
                print("Try not to cry :')")
                # for j in range(len(totalnodes) - 2): #Minus by 2, to remove broadcast node and own msg_q
                    # self.send_to_node(msg_q, "getmessage")
                    # msg = self.sock.recv(4096).decode('utf-8')
                    # self.public_keys_set.append(msg.split[1])

                # print("This was received : " + msg)


    def connect_to_msg_q(self, nodes):
        for i in range(len(nodes)):
            client_address_info = nodes[i].split(" ")

            self.connect_with_node(client_address_info[0], int(client_address_info[1]) + 100)
    
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

        time.sleep(0.5)

        trimmed = self.get_trimmed_node_info()
        
        print(trimmed) 
        
        
        self.msg_q = ClientMessageQueue(self.host, self.port + 100, len(trimmed),self.id + "q")
        self.msg_q.start()
        self.connect_with_node(self.host,self.port + 100)
        self.connect_to_msg_q(trimmed)
        self.signature_share_init()

        
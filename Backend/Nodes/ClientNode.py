from Backend.Nodes.FastNode import FastNode
import time
import ecdsa
import ClientMessageQueue

class ClientNode (FastNode): 
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(host, port, id, callback, max_connections)
        self.connectionList = []
        self.received_nodes = ""
        
        self.secret_key = ecdsa.SigningKey.generate()
        self.public_key = self.secret_key.verifying_key
        self.msg_q = ClientMessageQueue(self)
        self.connect_with_node(msg_q)

    def signature_share_init(self): 
        print(str(self.port) + " Started sharing")
        time.sleep(0.1)
        totalnodes = self.nodes_inbound + self.nodes_outbound 
        word_to_sign = "Sign"

        msg = "Hello"
        for i in range(len(totalnodes)):    
            print(self.id + " Started Round: " + str(i))
            if i == 0: # Round 0
                signed_msg = self.secret_key.sign(b"Sign")
                msg += word_to_sign + " " + str(signed_msg) + " Public key: " + str(self.public_key.to_string())
                self.send_to_nodes(msg)
            else:
                time.sleep(0.1)
                for connection in self.connectionList: 
                    rmsg = connection.recv(4096).decode('utf-8')
                    print("This is the msg " + rmsg)

                # result = all(element == msgList[0] for element in msgList)
                # if result :
                # #     print("All msges are equal")
                # else:
                #     for msg in msgList: 
                #         if str(self.port) in msg:
                #             for p in totalnodes :
                #                 self.send_to_node(p, msg)
                #         else: 
                #             msg = msg + str(self.port)
                #             for p in totalnodes :
                #                 self.send_to_node(p, msg)

    def connect_to_fastnode(self, nodes):
        for i in range(len(nodes)):
            client_address_info = nodes[i].split(" ")

            self.connect_with_node(client_address_info[0], int(client_address_info[1]))
            if not i == len(nodes) - 1:
                connection, client_address = self.sock.accept()
                self.connectionList.append(connection)

                connected_node_id = self.exchange_id(connection)
                self.start_thread_connection(connection, connected_node_id, client_address)
    
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
        self.connect_to_fastnode(trimmed)

        print("Finished Round 0 for " + self.id)

        self.signature_share_init()

        
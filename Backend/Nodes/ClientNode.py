from Backend.Nodes.FastNode import FastNode
import time

class ClientNode (FastNode):              
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
        self.print_connections()

        time.sleep(1)

        self.signature_share_init()
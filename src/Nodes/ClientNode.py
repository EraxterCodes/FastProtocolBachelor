from pydoc import cli
from Infrastructure.Nodes.FastNode import FastNode
from Infrastructure.PedersenCommit.Pedersen import Pedersen

import threading
import time
from ecdsa import SigningKey, SECP256k1 #Bitcoin curve
import random 

class ClientNode (FastNode): 
    def __init__(self, host, port, bid, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(host, port, id, callback, max_connections)
        
        self.debugPrint = False
        self.easy_signatures = True
        self.bid = bid
        
        self.sk = SigningKey.generate()
        self.vk = self.sk.verifying_key
        
        self.pd = Pedersen(10)
        self.bit_commitments = []

            
    def get_trimmed_info(self, node_info=str):
        try:
            info_array = []
            
            remove_braces = node_info.strip("[]")
            temp_info = remove_braces.split(" ")
            for info in temp_info:
                remove_commas = info.strip(',')
                remove_ticks = remove_commas.strip("'")
                host, port = remove_ticks.split(":")
                
                converted_port = int(port)
                
                info_tuple = (host, converted_port)
                info_array.append(info_tuple)
                
            return info_array  
        except:
            print(f"{self.id} has crashed when splitting node_info")
            self.sock.close()     
    
    def bid_decomposition(self):
        bits = [int(digit) for digit in bin(self.bid)[2:]]
        
        numtoprepend = 32  - len(bits)        
        for i in range(numtoprepend):
            bits.insert(0, 0)
        
        for bit in bits:
            self.bit_commitments.append(self.pd.p.commit(self.pd.param, bit))
        
        if self.debugPrint:
            print(f"Bit commits for {self.id}: {str(self.bit_commitments)}")
            
        # for i in range(len(self.bit_commitments)):
        #     print(f"{str(self.bit_commitments[i][0])} open val {self.pd.v.openBool(self.pd.param, self.bit_commitments[i][0], bits[i], self.bit_commitments[i][1])}")
    
    def connect_to_clients(self, node_info):
        try:
            host = node_info[0]
            port = int(node_info[1])
            
            if not(host == self.host and port == self.port): 
                self.clients.append((host, port))     
                self.connect_with_node(host, port)   
        except:
            print(f"{self.id} has crashed when connecting to clients")
            self.sock.close()             
                
    def connect_to_nodes(self):
        try:
            self.connect_with_node(self.broadcast_host, self.broadcast_port)
            
            node_info = f"{self.host}:{str(self.port)}"
            self.send_to_nodes(node_info)

            while self.all_nodes[0].get_node_message() == "":
                time.sleep(0.1)
            
            node_info = self.all_nodes[0].get_node_message()
            self.all_nodes[0].reset_node_message()
                    
            trimmed_info = self.get_trimmed_info(node_info)
            
            self.disconnect_with_node(self.all_nodes[0])
            self.nodes_outbound.remove(self.all_nodes[0])
               
            time.sleep(0.1)
                    
            for node in trimmed_info:
                self.connect_to_clients(node)
                time.sleep(0.1)
        except:
            print(f"{self.id} has crashed when connecting to all nodes")
            self.sock.close()
            
    def get_conflicting_messages(self):
        pass
         
    def get_all_messages(self, num_messages):
        while len(self.messages) != num_messages:
            for node in self.all_nodes:
                msg = node.get_node_message()
                
                if msg != "":
                    self.messages.append(msg)
                    node.reset_node_message()
                time.sleep(0.1)
           
    # TODO - This is always happy case with honest parties. 
    # TODO - When do we stop signing?!     
    def signature_share_init(self):
        print(f"{self.id} started sharing {len(self.clients)}")
        
        for i in range(len(self.clients)+1):
            print(f"{self.id} started round {i}")
            if i == 0:
                msg_to_sign = f"init"
                if self.easy_signatures:
                    msg = f"{msg_to_sign} s{self.id}-{msg_to_sign}" 
                else:
                    signed_msg = self.sk.sign(b"{msg_to_sign}")
                    msg = f"{msg_to_sign} {signed_msg}" 
                self.send_to_nodes(msg) 
                time.sleep(0.1)
                          
            else:
                time.sleep(0.1)
                
                client_len = len(self.clients) * i                 
                self.get_all_messages(client_len)
                
                # print(f"Messages received for {self.id} in round {i-1}: {str(self.messages)}")        
                                                    
                signed_messages = []
                                
                for message in self.messages:
                    msg_to_sign = f"{message}"

                    if self.easy_signatures:
                        msg = f"{message} s-{msg_to_sign}"
                    else:
                        signed_msg = self.sk.sign(b"{msg_to_sign}")
                        msg = f"{msg_to_sign} {signed_msg}"
                    
                    signed_messages.append(msg)
                
                if self.debugPrint:
                    print(f"Messages for {self.id}: {str(self.messages)}")
                
                removed_braces = str(signed_messages)[2:-2]
                self.send_to_nodes(removed_braces)
                time.sleep(0.1)
           
        time.sleep(0.1)
        
        client_len = len(self.clients) * (len(self.clients) + 1)                            
        self.get_all_messages(client_len)        
        
        if self.debugPrint:
            print(f"Messages for {self.id}: {str(self.messages)}")
            sorted_1 = str(self.messages[-1])
            sorted_2 = str(self.messages[-2])
            
            # print(f"Diffences for {self.id}")
            # print(str(sorted(sorted_1)) + " DIFFERENCE " + str(sorted(sorted_2)))
            
            # print(sorted(sorted_1) == sorted(sorted_2))
            
        print(f"{self.id} finished signature sharing")

    def setup(self):
        # change (secret)
        change = 0.1  
        # fee: work
        work = 0.1
        # build secret deposit 
        param = [self.bid, change, work, self.id]
        g = None # receive from smart contract, everyone gets same g + h
        h = None # receive from smart contract, everyone gets same g + h 

        # (a) send to smart contract (BroadcastNode)
        self.send_to_node(self.broadcast_node, "msg")
        # (b) compute bit commitments
        # (c) build UTXO for confidential transaction - skippable
        # (d) compute r_out, we think it's for range proof - skippable
        # (e) 
        
        
        pass 
        
        
    def run(self):
        accept_connections_thread = threading.Thread(target=self.accept_connections)
        accept_connections_thread.start()
        
        self.connect_to_nodes()
        
        self.signature_share_init()            
        
        self.bid_decomposition()
        
        # print(f"Nodes for {self.id}: {str(self.all_nodes)}")
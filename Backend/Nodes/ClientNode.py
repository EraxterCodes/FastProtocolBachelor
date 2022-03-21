from Backend.Nodes.FastNode import FastNode
import threading
import time
import ecdsa

class ClientNode (FastNode): 
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(host, port, id, callback, max_connections)
        
        self.sk = ecdsa.SigningKey.generate()
        self.vk = self.sk.verifying_key
    
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
            
    def signature_share_init(self):
        print(f"{self.id} started sharing")
        
        for i in range(len(self.clients)+1):
            print(f"{self.id} started round {i}")
            if i == 0:
                signed_msg = self.sk.sign(b"init")
                msg = f"init {signed_msg}" 
                self.send_to_nodes(msg) 
                time.sleep(0.1)
                          
            elif i == 1:
                while len(self.messages) != len(self.clients):
                    for node in self.all_nodes:
                        msg = node.get_node_message()
                        
                        if msg != "":
                            self.messages.append(msg)
                            node.reset_node_message()
                        time.sleep(0.1)
                        
                print(f"Messages for {self.id}: {str(self.messages)}")
                
                signed_messages = []
                                
                for msg in self.messages:
                    signed_msg = f"s{self.id} {msg}"
                    signed_messages.append(signed_msg)
                
                
                self.send_to_nodes(str(signed_messages))
                    
                
                
            
            # sending_msg = b"Round {i}"
            # signature = self.sk.sign(sending_msg)
            # converted_sig = f"{signature}"
            
            # self.send_to_nodes(f"Round {i} from {self.id}")    
            
            # #Should wait until all have received
            # client_len = len(self.clients) * (i+1)
            # while len(self.messages) != client_len:
            #     for i in self.all_nodes:
            #         msg = i.get_node_message()
                    
            #         if(msg != ""):
            #             self.messages.append(msg)
            #             i.reset_node_message()
            #     time.sleep(0.05)
            
            # print(f"Messages for {self.id}: {self.messages}")
        
    def run(self):
        accept_connections_thread = threading.Thread(target=self.accept_connections)
        accept_connections_thread.start()
        
        self.connect_to_nodes()
        
        self.signature_share_init()            
                
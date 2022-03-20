import threading
from Backend.Nodes.FastNode import FastNode
import time

class ClientNode (FastNode): 
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(host, port, id, callback, max_connections)
    
    def get_trimmed_info(self, node_info=str):
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
    
    def connect_to_clients(self, node_info):
        host = node_info[0]
        port = int(node_info[1])
        
        if not(host == self.host and port == self.port): 
            self.clients.append((host, port))     
            self.connect_with_node(host, port)            
                
    def connect_to_nodes(self):
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
                
        for node in trimmed_info:
            self.connect_to_clients(node)
            time.sleep(0.1)
            
    def signature_share_init(self):
        print(f"{self.id} started sharing")
        
        for i in range(len(self.clients)):
            if i == 0:
                print(f"{self.id} started round 0")
                
                self.send_to_nodes(f"Hello from {self.id}")    
                    
                time.sleep(1)
                
                for i in self.all_nodes:
                    if(i.get_node_message() != ""):
                        print(i.get_node_message())
                        i.reset_node_message()
                    
                  
        
    def run(self):
        accept_connections_thread = threading.Thread(target=self.accept_connections)
        accept_connections_thread.start()
        
        self.connect_to_nodes()
        
        self.signature_share_init()            
        
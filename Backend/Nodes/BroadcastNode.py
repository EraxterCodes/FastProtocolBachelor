import time
from Backend.Nodes.FastNode import FastNode

class BroadcastNode (FastNode): 
    def __init__(self, host, port, id=None, callback=None, max_connections=0):
        super(BroadcastNode, self).__init__(host, port, id, callback, max_connections)

    def accept_connections(self):
        while not self.terminate_flag.is_set():
            connection, client_address = self.sock.accept()
            print(f"Broadcast connected with {str(client_address)}")
            
            connected_node_id = connection.recv(4096).decode(self.coding_type)
            connection.send(self.id.encode(self.coding_type))

            node_info = connection.recv(4096).decode(self.coding_type)

            thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
            thread_client.start()

            self.nodes_inbound.append(thread_client)
            self.inbound_node_connected(thread_client)
            
            self.clients.append(node_info)

            if len(self.clients) == 3:
                break
            
        self.send_to_nodes(str(self.clients))
        self.terminate_flag.set()
        print("Broadcast Finished")

    def run(self):
        self.accept_connections()

        

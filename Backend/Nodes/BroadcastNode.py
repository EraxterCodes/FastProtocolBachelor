from Backend.Nodes.FastNode import FastNode

class BroadcastNode (FastNode):              
    def run(self):
        while not self.terminate_flag.is_set():
            connection, client_address = self.sock.accept()

            connected_node_id = connection.recv(4096).decode('utf-8')
            connection.send(self.id.encode('utf-8'))

            connected_node_msg = connection.recv(4096).decode('utf-8')
            print(connected_node_msg)

            thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
            thread_client.start()

            self.nodes_inbound.append(thread_client)
            self.inbound_node_connected(thread_client)

            self.connections.append(connected_node_msg)

            if len(self.connections) == 3:
                break

        self.send_to_nodes(str(self.connections))
    
        print("Broadcast Finished")

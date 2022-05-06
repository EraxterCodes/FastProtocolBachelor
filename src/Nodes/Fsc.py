import json
import threading
import time
from Infrastructure.Nodes.FastNode import FastNode
from src.PedersenCommitment.Pedersen import Pedersen
from src.utils.node import *


class Fsc (FastNode):
    def __init__(self, host, port, id=None, nodes=int, callback=None, max_connections=0):
        super(Fsc, self).__init__(
            host, port, id, callback, max_connections)
        self.nodes = nodes
        self.received_bids = []
        self.bid_commitments = []

    def receive_bids(self, client):
        bids = get_message(client)

        index = bids["index"]
        self.received_bids[index] = bids

        bid_commitment = get_message(client)
        c_to_bid = Point(bid_commitment["commitment_to_bid"]["x"],
                         bid_commitment["commitment_to_bid"]["y"], self.pd.cp)
        index = bid_commitment["client_index"]
        self.bid_commitments[index].append(c_to_bid)

        opening = get_message(client)
        self.verify_winning_bid(opening)

    def verify_winning_bid(self, opening):
        # Verify winning bid
        index = opening["p_w"]
        c_to_bid = self.bid_commitments[index]

        print(
            f"verify winning bid = {self.pd.open(self.pd.param[1], self.pd.param[2], opening['b_w'], c_to_bid[0], opening['r_bw'])} : {index}")

        quit()

    def send_params(self, client):
        while(self.nodes > len(self.received_bids)):
            time.sleep(0.1)

        sid = client.id  # Not true, since we use self.index
        p = self.pd.param[0]
        g = self.pd.param[1]
        h = self.pd.param[2]

        pk_c_array = []  # We currently dont implement comittee
        composed_msg = {
            "sid": sid,
            "g": {
                "x": g.x,
                "y": g.y,
            },
            "h": {
                "x": h.x,
                "y": h.y,
            },
            "p": p,
            "pk_c_array": str(pk_c_array)
        }

        self.send_to_node(client, (composed_msg))

    def accept_connections(self):
        while not self.terminate_flag.is_set():
            connection, client_address = self.sock.accept()
            print(f"Broadcast connected with {str(client_address)}")

            connected_node_id = connection.recv(16384).decode(self.coding_type)
            connection.send(self.id.encode(self.coding_type))

            node_info = connection.recv(16384).decode(self.coding_type)

            thread_client = self.create_new_connection(
                connection, connected_node_id, client_address[0], client_address[1])
            thread_client.start()

            # For receiving bids
            receive_bids_thread = threading.Thread(
                target=self.receive_bids, args=(thread_client, ))
            receive_bids_thread.start()

            # For returning params
            param_thread = threading.Thread(
                target=self.send_params, args=(thread_client, ))
            param_thread.start()

            self.nodes_inbound.append(thread_client)
            self.inbound_node_connected(thread_client)

            self.clients.append(node_info)

            if len(self.clients) == self.nodes:
                break

        converted_clients = []

        for i in range(len(self.clients)):
            converted_clients.append(
                {"client_index": i, "client_info": json.loads(self.clients[i])})
            self.bid_commitments.append([])
            self.received_bids.append([])

        self.send_to_nodes({"node_info": converted_clients})
        print("Broadcast Finished")

    def run(self):
        accept_connections_thread = threading.Thread(
            target=self.accept_connections())
        accept_connections_thread.start()

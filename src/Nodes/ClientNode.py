import sys
from src.FPA.fpa import fpa
from src.utils.utils import *
from Infrastructure.Nodes.FastNode import FastNode
from src.utils.node import *
import threading
import time


class ClientNode (FastNode):
    def __init__(self, host, port, bid, bc_ip="127.0.0.1", id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(
            host, port, id, callback, max_connections)

        self.index = None  # Is used when doing step 3 of FPA protocol
        self.bc_node = None  # gets set in setup

        self.bid = bid
        self.bid_commitment = None

        self.p = 0
        self.h = Point(0, 0, self.pd.cp, check=False)
        self.g = Point(0, 0, self.pd.cp, check=False)

        self.bit_commitments = []
        self.bits = []

        self.vetos = []

        self.small_xs = []
        self.big_xs = []
        self.big_ys = []
        self.commitments = []

        self.contractparams = None

        self.broadcast_host = bc_ip
        self.broadcast_port = 8001

    def connect_to_clients(self, node_info):
        host = node_info["client_info"]["host"]
        port = node_info["client_info"]["port"]

        if not(host == self.host and port == self.port):
            self.clients.append((host, port))
            self.connect_with_node(host, port)
        else:
            self.index = node_info["client_index"]

    def connect_to_nodes(self):
        self.connect_with_node(self.broadcast_host, self.broadcast_port)

        node_info = {"host": self.host, "port": self.port}
        self.send_to_nodes(node_info)

        node_info_json = get_message(self.all_nodes[0])

        self.bc_node = get_broadcast_node(self.all_nodes)

        for node in node_info_json["node_info"]:
            self.connect_to_clients(node)
            time.sleep(0.01)

    def veto_output(self):
        self.send_to_nodes(({"winner": self.vetos}), exclude=[self.bc_node])

        winner = get_all_messages_arr(self, len(self.clients))

        if self.bits == self.vetos:
            print("You won! Sending win proof to FSC")
            self.send_win_proof()

    def send_win_proof(self):
        # P_w opens the commitment, sends it to the smart contract
        # sends (output, sid, P_w, b_w, r_bw, {sig_sk, (b_w)}
        # Make the smart contract do work | Broadcast node

        Proof_of_winning = {
            "Label": "OUTPUT",
            "sid": self.id,
            "p_w": self.index,
            "b_w": self.bid,
            # Should be computed in step b og stage 1 in setup. Maybe
            "r_bw": self.bid_commit[1],
            "signed_b_w": ""
        }
        self.send_to_node(self.bc_node, Proof_of_winning)

    def run(self):
        accept_connections_thread = threading.Thread(
            target=self.accept_connections)
        accept_connections_thread.start()

        self.connect_to_nodes()

        fpa(self)

        self.veto_output()

        print("finished")
        sys.exit()

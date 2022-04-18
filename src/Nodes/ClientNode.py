from Infrastructure.Nodes.FastNode import FastNode
from src.utils.string import str_to_point, unpack_commitment_and_x
from src.utils.node import reset_all_node_msgs, get_broadcast_node, get_trimmed_info, get_message, get_all_messages, get_all_messages_arr
from ecpy.curves import Point, Curve
from Crypto.Util import number
from ecpy.keys import ECPublicKey, ECPrivateKey
from ecpy.ecdsa import ECDSA

import threading
import time


class ClientNode (FastNode):
    def __init__(self, host, port, bid, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(
            host, port, id, callback, max_connections)

        self.bc_node = None  # gets set in setup

        self.debugPrint = False
        self.easy_signatures = True
        self.bid = bid

        self.bit_commitments = []
        self.bits = []

        self.broadcast_node = None
        self.vetoarray = []

        self.ext_bigxs = []
        self.ext_commitments = []

        self.contractparams = None

        self.utxos = []

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

            trimmed_info = get_trimmed_info(self, node_info)

            self.broadcast_node = self.all_nodes[0]

            # self.disconnect_with_node(self.all_nodes[0])
            # self.nodes_outbound.remove(self.all_nodes[0])

            time.sleep(0.1)

            for node in trimmed_info:
                self.connect_to_clients(node)
                time.sleep(0.1)
        except:
            print(f"{self.id} has crashed when connecting to all nodes")
            self.sock.close()

    def bid_decomposition(self):
        bits = [int(digit) for digit in bin(self.bid)[2:]]

        numtoprepend = 32 - len(bits)
        for i in range(numtoprepend):
            bits.insert(0, 0)

        for bit in bits:
            self.bits.append(bit)
            self.bit_commitments.append(self.pd.commit(bit))

    def setup(self):
        self.bc_node = get_broadcast_node(self.all_nodes)
        # Stage 1
        # change (secret)
        change = 0.1
        # fee: work
        work = 0.1
        # build secret deposit
        bid_param = F"{self.bid};{change};{work}"
        [self.bid, change, work, self.id]

        # (a) send to smart contract (BroadcastNode)
        self.send_to_nodes(bid_param, exclude=[self.clients])
        # (b) compute bit commitments

        self.bid_decomposition()

        # (c) build UTXO for confidential transaction - skippable
        # (d) compute r_out, we think it's for range proof - skippable
        # (e) Uses stuff from C - SKIP
        # (f) Compute shares of g^bi and h^rbi, Use distribution from PVSS protocol with committee - skippable?
        # (g) ?
        # (h) ?
        # (i) ?
        # secret_key =

        self.contractparams = get_message(self.bc_node).split(";")
        p = int(self.contractparams[6])
        g = str_to_point(self.contractparams[4], self.pd.cp)

        # Stage 2: Compute all big X's and send commits along with X to other nodes. Is used for stage three in veto
        commit_x_arr = []
        for i in range(len(self.bit_commitments)):
            x = number.getRandomRange(1, p - 1)

            commit_and_big_x = self.bit_commitments[i][0].__str__(
            ) + "|" + self.pd.cp.mul_point(x, g).__str__()

            commit_and_big_x = commit_and_big_x + ";"
            commit_x_arr.append(commit_and_big_x)

        reset_all_node_msgs(self.all_nodes)

        # maybe also send identification of yourself along ?
        self.send_to_nodes(str(commit_x_arr), exclude=[self.bc_node])
        #print(f"{self.id} has sent {len(commit_x_arr)} commitments and big X's to other nodes of size: {self.utf8len(str(commit_x_arr))} ")

        commit_and_X_array = get_all_messages_arr(self, len(self.clients))
        #print(str(commit_and_X_array) + "          " + self.id +  "   " + str(len(commit_and_X_array)))

        # print(commit_and_X_array)
        unpack_commitment_and_x(self, commit_and_X_array)

        # TODO: Stage 3 of setup we now send the array containing commitments and big X's maybe make a helper method to unravel it again
        big_y_arr = []

        n = len(self.clients) + 1
        j = n-1
        k = 32

        left_side_col = []
        right_side_col = []

        for i in range(k):
            point = Point(0x0, 0x0, self.pd.cp, check=False)

    def veto(self):
        p = int(self.contractparams[6])
        g = str_to_point(self.contractparams[4], self.pd.cp)

        get_all_messages(self, len(self.clients))
        time.sleep(0.1)

        veto = None
        out_of_running = False
        last_v_ir = None

        for j in range(len(self.bit_commitments)):  # Rounds
            print(f"{j} for: {self.id}")
            v_ir_array = []

            if j != 0:
                v_ir_array = get_all_messages_arr(self, len(self.clients))
                v_ir_array.append(last_v_ir)
                print(v_ir_array)

            # compute the random value X and broadcast that to all other nodes
            # get random value from the field.
            # Random elements of Z_p used for commitments

            str_big_x_arr = get_all_messages_arr(self, len(self.clients))

            # if self.hasAnyoneVetoed(v_ir_array) == False:  # before first veto
            #     # Compute V_ir
            #     if (self.bits[j] == 0):
            #         print("bit is 0")
            #         # Case for no veto:
            #         # Y = g^(negative of other x's)
            #         veto = g ** e
            #         last_v_ir = veto
            #         self.send_to_nodes(str(veto), exclude=[self.bc_node])
            #         time.sleep(0.05)
            #     else:
            #         # Case for veto:
            #         print("YO I VETOED G :" + self.id)
            #         r_hat = random.randint(1, p - 1)
            #         veto = g ** r_hat
            #         self.send_to_nodes(str(veto), exclude=[self.bc_node])

            #     # Generate NIZK BV (before veto) for veto decision proof.
            # else:  # after first veto
            #     print("Function returned true")
            #     if self.bits[j] == 0:
            #         veto = g ** e
            #         self.send_to_nodes(str(veto), exclude=[self.bc_node])

            #         # should be out of running if and only if some other party has vetoed
            #     elif out_of_running:
            #         veto = g ** e
            #         self.send_to_nodes(str(veto), exclude=[self.bc_node])
            #     else:
            #         # calc veto
            #         pass

        # send v_ir to all others

    def hasAnyoneVetoed(self, v_ir_array):
        # we must know all others v_ir

        if len(v_ir_array) == 0:  # First round case
            return False

        V = 1
        for v_ir in v_ir_array:
            V = V*(int(v_ir))  # V = product of all v_ir's

        if V == 1:
            return False
        else:
            return True

    def pay_to_public_key(self, utxo_arr, recepient):
        pass

    def run(self):
        accept_connections_thread = threading.Thread(
            target=self.accept_connections)
        accept_connections_thread.start()

        self.connect_to_nodes()

        self.setup()

        self.veto()

        print("finished")

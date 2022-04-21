from Infrastructure.Nodes.FastNode import FastNode
from src.utils.string import *
from src.utils.node import *
from Crypto.Util import number
from ecdsa import SigningKey, VerifyingKey

import threading
import time


class ClientNode (FastNode):
    def __init__(self, host, port, bid, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(
            host, port, id, callback, max_connections)

        self.index = None  # Is used when doing step 3 of FPA protocol
        self.bc_node = None  # gets set in setup

        self.debugPrint = False
        self.bid = bid

        self.sk = SigningKey.generate()
        self.vk = self.sk.verifying_key

        self.bit_commitments = []
        self.bits = []

        self.vetos = []

        self.small_xs = []
        self.big_xs = []
        self.big_ys = []
        self.commitments = []

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
            self.small_xs.append(x)

            commit_and_big_x = self.bit_commitments[i][0].__str__(
            ) + "|" + self.pd.cp.mul_point(x, g).__str__()

            commit_and_big_x = commit_and_big_x + ";"
            commit_x_arr.append(commit_and_big_x)

        reset_all_node_msgs(self.all_nodes)

        commits_w_index = f"{str(self.index)}--{str(commit_x_arr)}"

        # maybe also send identification of yourself along ?
        self.send_to_nodes(
            commits_w_index, exclude=[self.bc_node])
        # print(f"{self.id} has sent {len(commit_x_arr)} commitments and big X's to other nodes of size: {self.utf8len(str(commit_x_arr))} ")

        for i in range(len(self.clients) + 1):
            self.commitments.append([])  # add room for another client
            self.big_xs.append([])  # add room for another client

        unpack_commitment_and_x(self, [commits_w_index])

        # self.big_xs.append(unpack_commitment_and_x(self, str(commit_x_arr)))

        commit_and_X_array = get_all_messages_arr(self, len(self.clients))
        # print(str(commit_and_X_array) + "          " + self.id +  "   " + str(len(commit_and_X_array)))
        unpack_commitment_and_x(self, commit_and_X_array)

        # TODO: Stage 3 of setup we now send the array containing commitments and big X's maybe make a helper method to unravel it again

        for i in range(len(self.big_xs)):
            self.big_ys.append([])
            for j in range(len(self.big_xs[0])):
                left_side = self.pd.param[1]
                right_side = self.pd.param[1]

                for h in range(self.index):  # Left side of equation
                    left_side = self.pd.cp.add_point(
                        left_side, self.big_xs[h][j])

                for h in range(self.index+1, len(self.big_xs)):  # Right side of equation
                    right_side = self.pd.cp.add_point(
                        right_side, self.big_xs[h][j])

                left_side = self.pd.cp.sub_point(
                    left_side, self.pd.param[1])
                right_side = self.pd.cp.sub_point(
                    right_side, self.pd.param[1])

                self.big_ys[i].append(self.pd.cp.sub_point(
                    left_side, right_side))

        # verify c_j for each other party p_j, skipped atm

    def veto(self):
        # Own veto result has to be saved in an array, so we can check for it in after first veto.
        # Create NIZK :)

        p = int(self.contractparams[6])
        g = str_to_point(self.contractparams[4], self.pd.cp)

        bfv = True  # Before First Veto

        previous_vetos = []
        latest_veto_r = None

        for i in range(len(self.bit_commitments)):
            if bfv:  # Before first veto
                if self.bits[i] == 1:
                    r = number.getRandomRange(1, p - 1)
                    v = self.pd.cp.mul_point(r, g)
                    previous_vetos.append(True)
                else:
                    v = self.pd.cp.mul_point(
                        self.small_xs[i], self.big_ys[self.index][i])
                    previous_vetos.append(False)

                self.send_to_nodes(str(v), exclude=[self.bc_node])

                time.sleep(0.1)

                vs = get_all_messages_arr(self, len(self.clients))

                v_arr = []

                v_arr.append(v)
                for j in range(len(self.clients)):
                    v_arr.append(str_to_point(vs[j], self.pd.cp))

                point = g

                for j in range(len(v_arr)):
                    point = self.pd.cp.add_point(point, v_arr[j])

                if point != g:
                    bfv = False
                    latest_veto_r = i
                    self.vetos.append(1)
                else:
                    self.vetos.append(0)

                print(i)

            else:  # After first veto
                # If the bit is 1 and the previous veto was true
                if self.bits[i] == 1 and previous_vetos[latest_veto_r] == True:
                    r = number.getRandomRange(1, p - 1)
                    v = self.pd.cp.mul_point(r, g)
                    previous_vetos.append(True)
                # If the bit is 1 and the previous veto was false
                elif self.bits[i] == 1 and previous_vetos[latest_veto_r] == False:
                    v = self.pd.cp.mul_point(
                        self.small_xs[i], self.big_ys[self.index][i])
                    previous_vetos.append(False)
                else:  # If the bit is 0
                    v = self.pd.cp.mul_point(
                        self.small_xs[i], self.big_ys[self.index][i])
                    previous_vetos.append(False)

                self.send_to_nodes(str(v), exclude=[self.bc_node])

                time.sleep(0.1)

                vs = get_all_messages_arr(self, len(self.clients))

                v_arr = []

                v_arr.append(v)
                for j in range(len(self.clients)):
                    v_arr.append(str_to_point(vs[j], self.pd.cp))

                point = g

                for j in range(len(v_arr)):
                    point = self.pd.cp.add_point(point, v_arr[j])

                if point != g:
                    latest_veto_r = i
                    self.vetos.append(1)
                else:
                    self.vetos.append(0)

                print(i)

            time.sleep(0.1)

    def veto_output(self):
        self.send_to_nodes(str(self.vetos), exclude=[self.bc_node])

        winner = get_all_messages_arr(self, len(self.clients))

        first_win = winner[0]

        for win in winner:
            if win != first_win:
                print("OH NOOO")
                break

        if str(self.bits) == first_win:
            self.send_win_proof()

    def bit_to_int(self, bitlist):
        output = 0
        for bit in bitlist:
            output = (output << 1) | bit
        return output

    def send_win_proof(self):
        # P_w opens the commitment, sends it to the smart contract
        # sends (output, sid, P_w, b_w, r_bw, {sig_sk, (b_w)}
        # Make the smart contract do work | Broadcast node

        output = self.bit_to_int(self.vetos)  # Decimal winning bid
        sid = self.id
        p_w = self.index
        b_w = self.bits
        r_bw = None
        signed_b_w = None

    def run(self):
        accept_connections_thread = threading.Thread(
            target=self.accept_connections)
        accept_connections_thread.start()

        self.connect_to_nodes()

        self.setup()

        self.veto()

        self.veto_output()

        print("finished")

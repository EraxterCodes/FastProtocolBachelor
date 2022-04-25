import json
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

        self.p = 0
        self.h = Point(0, 0, self.pd.cp, check=False)
        self.g = Point(0, 0, self.pd.cp, check=False)

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

            self.bc_node = get_broadcast_node(self.all_nodes)

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
        # Stage 1
        # change (secret)
        change = 0.1
        # fee: work
        work = 0.1
        # build secret deposit
        bid_param = f"{self.bid};{change};{work}"
        [self.bid, change, work, self.id]

        # (a) send to smart contract (BroadcastNode)
        self.send_to_node(self.bc_node, bid_param)
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
        self.p = int(self.contractparams[6])
        self.h = str_to_point(self.contractparams[5], self.pd.cp)
        self.g = str_to_point(self.contractparams[4], self.pd.cp)

        # Stage 2: Compute all big X's and send commits along with X to other nodes. Is used for stage three in veto
        commit_x_arr = []
        for i in range(len(self.bit_commitments)):
            x = number.getRandomRange(1, self.p - 1)
            self.small_xs.append(x)

            commit_and_big_x = self.bit_commitments[i][0].__str__(
            ) + "|" + self.pd.cp.mul_point(x, self.g).__str__()

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
        unpack_commitment_and_x(self, commit_and_X_array)

        # TODO: Stage 3 of setup we now send the array containing commitments and big X's maybe make a helper method to unravel it again
        try:
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
        except:
            print(
                f"Failed when creating Y's for {self.id} - Big X's: {len(self.big_xs)}")
        # verify c_j for each other party p_j, skipped atm

    def generate_bfv_nizk(self, i, c, v, X, Y, r, x, r_hat):
        # Theoretically these could be the same, but we'll run that chance chief
        if i == 1:
            alpha = 2
        else:
            alpha = 1

        v_s = self.sample_from_field_arr(4)

        w_1, w_2 = 0, 0

        if alpha == 1:  # F_1
            w_2 = self.sample_from_field()
        else:  # F_2
            w_1 = self.sample_from_field()

        c_div_g = self.pd.cp.sub_point(c, self.g)

        # c^w_1 * h^v_1
        t_1 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_1, c), self.pd.cp.mul_point(v_s[0], self.h))
        t_1_p = Point(t_1.x % self.p, t_1.y % self.p, self.pd.cp)

        # v^w_1 * Y^v_2
        t_2 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_1, v), self.pd.cp.mul_point(v_s[1], Y))
        t_2_p = Point(t_2.x % self.p, t_2.y % self.p, self.pd.cp)

        # X^_w_1 * g^v_2
        t_3 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_1, X), self.pd.cp.mul_point(v_s[1], self.g))
        t_3_p = Point(t_3.x % self.p, t_3.y % self.p, self.pd.cp)

        # (c/g)^w_2 * h^v_3
        t_4 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_2, c_div_g), self.pd.cp.mul_point(v_s[2], self.h))
        t_4_p = Point(t_4.x % self.p, t_4.y % self.p, self.pd.cp)

        # v^w_2 * g^v_4
        t_5 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_2, v), self.pd.cp.mul_point(v_s[3], self.g))
        t_5_p = Point(t_5.x % self.p, t_5.y % self.p, self.pd.cp)

        h_p = Point(self.h.x % self.p, self.h.y % self.p, self.pd.cp)
        c_p = Point(c.x % self.p, c.y % self.p, self.pd.cp)
        Y_p = Point(Y.x % self.p, Y.y % self.p, self.pd.cp)
        v_p = Point(v.x % self.p, v.y % self.p, self.pd.cp)
        g_p = Point(self.g.x % self.p, self.g.y % self.p, self.pd.cp)
        X_p = Point(X.x % self.p, X.y % self.p, self.pd.cp)
        c_div_g_p = Point(c_div_g.x % self.p, c_div_g.y % self.p, self.pd.cp)

        h_add_arr = [self.h, c, Y, v, self.g,
                     X, c_div_g, t_1, t_2, t_3, t_4, t_5]

        h_p_add_arr = [h_p, c_p, Y_p, v_p, g_p, X_p,
                       c_div_g_p, t_1_p, t_2_p, t_3_p, t_4_p, t_5_p]

        if alpha == 1:  # F_1
            gamma_1 = None  # H - (w_1 + w_2) (mod p)
            gamma_2 = w_2

            x_1, x_2, x_3, x_4 = r, x, 0, 0

            # (v_1 - gamma_1 * x_1) mod p
            r_1 = (v_s[0] - (gamma_1 * x_1)) % self.p

            # (v_2 - gamma_1 * x_2) mod p
            r_2 = (v_s[1] - (gamma_1 * x_2)) % self.p

            # (v_2 - gamma_1 * x_2) mod p
            r_3 = r_2

            # (v_3 - gamma_1 * x_3) mod p
            r_4 = (v_s[2] - (gamma_1 * x_3)) % self.p

            # (v_4 - gamma_1 * x_4) mod p
            r_5 = (v_s[3] - (gamma_1 * x_4)) % self.p

        else:  # F_2
            gamma_1 = w_1
            gamma_2 = None  # H - (w_1 + w_2) (mod p)

            x_1, x_2, x_3, x_4 = 0, 0, r, r_hat

            # (v_1 - gamma_2 * x_1) mod p
            r_1 = (v_s[0] - (gamma_2 * x_1)) % self.p

            # (v_2 - gamma_2 * x_2) mod p
            r_2 = (v_s[1] - (gamma_2 * x_2)) % self.p

            # (v_2 - gamma_2 * x_2) mod p
            r_3 = r_2

            # (v_3 - gamma_2 * x_3) mod p
            r_4 = (v_s[2] - (gamma_2 * x_3)) % self.p

            # (v_4 - gamma_2 * x_4) mod p
            r_5 = (v_s[3] - (gamma_2 * x_4)) % self.p

        return (gamma_1, gamma_2, r_1, r_2, r_3, r_4, r_5)

    def generate_afv_nizk(self, i, d, c, v, X, Y, Xr, Yr):
        if i == 1 and d == 1:
            alpha = 2
        elif i == 1 and d == 0:
            alpha = 3
        else:
            alpha = 1

        v_s = self.sample_from_field_arr(8)

        w_1, w_2, w_3 = 0, 0, 0

        if i == 1 and d == 1:  # F_2
            w_1, w_3 = self.sample_from_field(), self.sample_from_field()
        elif i == i and d == 0:  # F_3
            w_1, w_2 = self.sample_from_field(), self.sample_from_field()
        else:  # F_1
            w_2, w_3 = self.sample_from_field(), self.sample_from_field()

        c_div_g = self.pd.cp.sub_point(c, self.g)

        # c^w_1 * h^v_1
        t_1 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_1, c), self.pd.cp.mul_point(v_s[0], self.h))
        t_1_p = Point(t_1.x % self.p, t_1.y % self.p, self.pd.cp)

        # v^w_1 * Y^v_2
        t_2 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_1, v), self.pd.cp.mul_point(v_s[1], Y))
        t_2_p = Point(t_2.x % self.p, t_2.y % self.p, self.pd.cp)

        # X^_w_1 * g^v_2
        t_3 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_1, X), self.pd.cp.mul_point(v_s[1], self.g))
        t_3_p = Point(t_3.x % self.p, t_3.y % self.p, self.pd.cp)

        # (c/g)^w_2 * h^v_3
        t_4 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_2, c_div_g), self.pd.cp.mul_point(v_s[2], self.h))
        t_4_p = Point(t_4.x % self.p, t_4.y % self.p, self.pd.cp)

        # d^w_2 * g^v_4
        t_5 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_2, d), self.pd.cp.mul_point(v_s[3], self.g))
        t_5_p = Point(t_5.x % self.p, t_5.y % self.p, self.pd.cp)

        # v^w_2 * g^v_5
        t_6 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_2, v), self.pd.cp.mul_point(v_s[4], self.g))
        t_6_p = Point(t_6.x % self.p, t_6.y % self.p, self.pd.cp)

        # (c/g)^w_3 * h^v_6
        t_7 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_3, c_div_g), self.pd.cp.mul_point(v_s[5], self.h))
        t_7_p = Point(t_7.x % self.p, t_7.y % self.p, self.pd.cp)

        # d^w_3 * Yr^v_7
        t_8 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_3, d), self.pd.cp.mul_point(v_s[6], Yr))
        t_8_p = Point(t_8.x % self.p, t_8.y % self.p, self.pd.cp)

        # Xr^w_3 * g^v_7
        t_9 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_3, Xr), self.pd.cp.mul_point(v_s[6], self.g))
        t_9_p = Point(t_9.x % self.p, t_9.y % self.p, self.pd.cp)

        # v^w_3 * Y^v_8
        t_10 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_3, v), self.pd.cp.mul_point(v_s[7], Y))
        t_10_p = Point(t_10.x % self.p, t_10.y % self.p, self.pd.cp)

        # X^w_3 * g^v_8
        t_11 = self.pd.cp.add_point(self.pd.cp.mul_point(
            w_3, X), self.pd.cp.mul_point(v_s[7], self.g))
        t_11_p = Point(t_11.x % self.p, t_11.y % self.p, self.pd.cp)

        h_add_arr = [self.h, c, Y, v, self.g, X, c_div_g, d, Yr, Xr,
                     t_1, t_2, t_3, t_4, t_5, t_6, t_7, t_8, t_9, t_10, t_11]

        if alpha == 1:  # F_1
            gamma_1 = None  # H - (w_1 + w_2 + w_3) (mod p)
            gamma_2 = w_2
            gamma_3 = w_3

            r_1 = None
            r_2 = None
            r_3 = None
            r_4 = None
            r_5 = None
            r_6 = None
            r_7 = None
            r_8 = None
            r_9 = None
            r_10 = None
            r_11 = None
        elif alpha == 2:  # F_2
            gamma_1 = w_1
            gamma_2 = None  # H - (w_1 + w_2 + w_3) (mod p)
            gamma_3 = w_3

            r_1 = None
            r_2 = None
            r_3 = None
            r_4 = None
            r_5 = None
            r_6 = None
            r_7 = None
            r_8 = None
            r_9 = None
            r_10 = None
            r_11 = None
        else:  # F_3
            gamma_1 = w_1
            gamma_2 = w_2
            gamma_3 = None  # H - (w_1 + w_2 + w_3) (mod p)

            r_1 = None
            r_2 = None
            r_3 = None
            r_4 = None
            r_5 = None
            r_6 = None
            r_7 = None
            r_8 = None
            r_9 = None
            r_10 = None
            r_11 = None

        return (gamma_1, gamma_2, gamma_3, r_1, r_2, r_3, r_4, r_5, r_6, r_7, r_8, r_9, r_10, r_11)

    def sample_from_field(self):
        return number.getRandomRange(1, self.p - 1)

    def sample_from_field_arr(self, amount):
        lst = []
        for i in range(amount):
            lst.append(self.sample_from_field())

        return lst

    def veto(self):
        # Create NIZK :)
        bfv = True  # Before First Veto

        previous_vetos = []
        latest_veto_r = None

        print(
            f"{self.id} small_xs: {len(self.small_xs)}, big_ys: {len(self.big_ys[self.index])}")

        for i in range(len(self.bit_commitments)):
            if bfv:  # Before first veto
                r_hat = number.getRandomRange(1, self.p - 1)

                if self.bits[i] == 1:
                    v = self.pd.cp.mul_point(r, self.g)
                    previous_vetos.append(True)
                else:
                    v = self.pd.cp.mul_point(
                        self.small_xs[i], self.big_ys[self.index][i])
                    previous_vetos.append(False)

                bfv_nizk = self.generate_bfv_nizk(
                    self.bits[i], self.bit_commitments[i][0], v, self.big_ys[self.index][i], self.big_xs[self.index][i], self.bit_commitments[i][1], self.small_xs[i], r_hat)

                self.send_to_nodes(str(v), exclude=[self.bc_node])

                time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

                vs = get_all_messages_arr(self, len(self.clients))

                v_arr = []

                v_arr.append(v)
                for j in range(len(self.clients)):
                    v_arr.append(str_to_point(vs[j], self.pd.cp))

                point = self.g

                for j in range(len(v_arr)):
                    point = self.pd.cp.add_point(point, v_arr[j])

                if point != self.g:
                    bfv = False
                    latest_veto_r = i
                    self.vetos.append(1)
                else:
                    self.vetos.append(0)

                print(i)

            else:  # After first veto
                # If the bit is 1 and the previous veto was true
                if self.bits[i] == 1 and previous_vetos[latest_veto_r] == True:
                    r = number.getRandomRange(1, self.p - 1)
                    v = self.pd.cp.mul_point(r, self.g)
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

                afv_nizk = self.generate_afv_nizk(
                    self.bits[i], self.bits[latest_veto_r], self.bit_commitments[i][0], v, self.big_ys[self.index][i], self.big_xs[self.index][i], self.big_ys[self.index][latest_veto_r], self.big_xs[self.index][latest_veto_r])

                self.send_to_nodes(str(v), exclude=[self.bc_node])

                time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

                vs = get_all_messages_arr(self, len(self.clients))

                v_arr = []

                v_arr.append(v)
                for j in range(len(self.clients)):
                    v_arr.append(str_to_point(vs[j], self.pd.cp))

                point = self.g

                for j in range(len(v_arr)):
                    point = self.pd.cp.add_point(point, v_arr[j])

                if point != self.g:
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
            print(f"{self.id} won")
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
        r_bw = None  # Should be computed in step b og stage 1 in setup. Maybe
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

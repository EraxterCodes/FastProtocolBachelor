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

        node_info_json = json.loads(get_message(self.all_nodes[0]))

        self.bc_node = get_broadcast_node(self.all_nodes)

        for node in node_info_json["node_info"]:
            self.connect_to_clients(node)
            time.sleep(0.01)

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

        # (a) send to smart contract (BroadcastNode)
        self.send_to_node(self.bc_node, bid_param)  # Not a dict
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

                    self.big_ys[i].append(self.pd.cp.sub_point(
                        left_side, right_side))
        except:
            print(
                f"Failed when creating Y's for {self.id} - Big X's: {len(self.big_xs)}")
        # verify c_j for each other party p_j, skipped atm

    def generate_bfv_nizk(self, i, c, v, X, Y, r, x, r_hat):
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

        #Dont think we need this.
        #h_p = Point(self.h.x % self.p, self.h.y % self.p, self.pd.cp)
        #c_p = Point(c.x % self.p, c.y % self.p, self.pd.cp)
        #Y_p = Point(Y.x % self.p, Y.y % self.p, self.pd.cp)
        #v_p = Point(v.x % self.p, v.y % self.p, self.pd.cp)
        #g_p = Point(self.g.x % self.p, self.g.y % self.p, self.pd.cp)
        #X_p = Point(X.x % self.p, X.y % self.p, self.pd.cp)
        #c_div_g_p = Point(c_div_g.x % self.p, c_div_g.y % self.p, self.pd.cp)

        h_add_arr = [self.h, c, Y, v, self.g,
                     X, c_div_g, t_1, t_2, t_3, t_4, t_5]

        big_h = self.Calc_h(h_add_arr)
    
        #Calc gamma
        if alpha == 1:  # F_1
            gamma_1 = (big_h - (w_1 + w_2)) % self.p
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
            gamma_2 = (big_h - (w_1 + w_2)) % self.p

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

        return {
            "gamma_1": gamma_1,
            "gamma_2": gamma_2,
            "r_1": r_1,
            "r_2": r_2,
            "r_3": r_3,
            "r_4": r_4,
            "r_5": r_5
        }

    def generate_afv_nizk(self, i, d, c, v, X, Y, Xr, Yr, r, x, r_hat, r_hat_lv, x_lv):
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
             w_2, d), self.pd.cp.mul_point(v_s[3], self.g))  # D is not a point
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

        big_h = self.Calc_h(h_add_arr)

        if alpha == 1:  # F_1
            gamma_1 = (big_h - (w_1 + w_2 + w_3)) % self.p
            gamma_2 = w_2
            gamma_3 = w_3

            x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8 = r, x, 0, 0, 0, 0, 0, 0

            #  v_1 - gamma alpha * x1
            r_1 = (v_s[0] - (gamma_1 * x_1)) % self.p  # Bob is this right?

            # v_2 - gamma alpha * x2
            r_2 = (v_s[1] - (gamma_1 * x_2)) % self.p

            # v_2 - gamma alpha * x2 -> The same as r2?
            r_3 = r_2

            # v_3 - gamma alpha * x3
            r_4 = (v_s[2] - (gamma_1 * x_3)) % self.p

            # v_4 - gamma alpha * x4
            r_5 = (v_s[3] - (gamma_1 * x_4)) % self.p

            # v_5 - gamma alpha * x5
            r_6 = (v_s[4] - (gamma_1 * x_5)) % self.p

            # v_6 - gamma alpha * x6
            r_7 = (v_s[5] - (gamma_1 * x_6)) % self.p

            # v_7 - gamma alpha * x7
            r_8 = (v_s[6] - (gamma_1 * x_7)) % self.p

            # v_7 - gamma alpha * x7 -> Same as r8?
            r_9 = r_8

            # v_8 - gamma alpha * x8
            r_10 = (v_s[7] - (gamma_1 * x_8)) % self.p

            # v_8 - gamma alpha * x8 -> Same as r_10 ?
            r_11 = r_10

        elif alpha == 2:  # F_2
            gamma_1 = w_1
            gamma_2 = (big_h - (w_1 + w_2 + w_3)) % self.p
            gamma_3 = w_3

            x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8 = 0, 0, r, r_hat_lv, r_hat, 0, 0, 0

            #  v_1 - gamma alpha * x1
            r_1 = (v_s[0] - (gamma_2 * x_1)) % self.p  # Bob is this right?

            # v_2 - gamma alpha * x2
            r_2 = (v_s[1] - (gamma_2 * x_2)) % self.p

            # v_2 - gamma alpha * x2 -> The same as r2?
            r_3 = r_2

            # v_3 - gamma alpha * x3
            r_4 = (v_s[2] - (gamma_2 * x_3)) % self.p

            # v_4 - gamma alpha * x4
            r_5 = (v_s[3] - (gamma_2 * x_4)) % self.p

            # v_5 - gamma alpha * x5
            r_6 = (v_s[4] - (gamma_2 * x_5)) % self.p

            # v_6 - gamma alpha * x6
            r_7 = (v_s[5] - (gamma_2 * x_6)) % self.p

            # v_7 - gamma alpha * x7
            r_8 = (v_s[6] - (gamma_2 * x_7)) % self.p

            # v_7 - gamma alpha * x7 -> Same as r8?
            r_9 = r_8

            # v_8 - gamma alpha * x8
            r_10 = (v_s[7] - (gamma_2 * x_8)) % self.p

            # v_8 - gamma alpha * x8 -> Same as r_10 ?
            r_11 = r_10
        else:  # F_3
            gamma_1 = w_1
            gamma_2 = w_2
            gamma_3 = (big_h - (w_1 + w_2 + w_3)) % self.p

            x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8 = 0, 0, 0, 0, 0, r, x_lv, x

            #  v_1 - gamma alpha * x1
            r_1 = (v_s[0] - (gamma_3 * x_1)) % self.p  # Bob is this right?

            # v_2 - gamma alpha * x2
            r_2 = (v_s[1] - (gamma_3 * x_2)) % self.p

            # v_2 - gamma alpha * x2 -> The same as r2?
            r_3 = r_2

            # v_3 - gamma alpha * x3
            r_4 = (v_s[2] - (gamma_3 * x_3)) % self.p

            # v_4 - gamma alpha * x4
            r_5 = (v_s[3] - (gamma_3 * x_4)) % self.p

            # v_5 - gamma alpha * x5
            r_6 = (v_s[4] - (gamma_3 * x_5)) % self.p

            # v_6 - gamma alpha * x6
            r_7 = (v_s[5] - (gamma_3 * x_6)) % self.p

            # v_7 - gamma alpha * x7
            r_8 = (v_s[6] - (gamma_3 * x_7)) % self.p

            # v_7 - gamma alpha * x7 -> Same as r8?
            r_9 = r_8

            # v_8 - gamma alpha * x8
            r_10 = (v_s[7] - (gamma_3 * x_8)) % self.p

            # v_8 - gamma alpha * x8 -> Same as r_10 ?
            r_11 = r_10

        return {
            "gamma_1": gamma_1,
            "gamma_2": gamma_2,
            "gamma_3": gamma_3,
            "r_1": r_1,
            "r_2": r_2,
            "r_3": r_3,
            "r_4": r_4,
            "r_5": r_5,
            "r_6": r_6,
            "r_7": r_7,
            "r_8": r_8,
            "r_9": r_9,
            "r_10": r_10,
            "r_11": r_11
        }

    def sample_from_field(self):
        return number.getRandomRange(1, self.p - 1)

    def sample_from_field_arr(self, amount):
        lst = []
        for i in range(amount):
            lst.append(self.sample_from_field())

        return lst

    def verify_bfv_nizk(self, data, h, c, Y, v, g, X):
        gamma_result = data["gamma_1"] + data["gamma_2"]

        c_div_g = self.pd.cp.sub_point(c, g)

        # c^gamma_1 * h^r_1
        t_1_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_1"], c), self.pd.cp.mul_point(data["r_1"], h))

        # v^gamma_1 * Y^r_2
        t_2_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_1"], v), self.pd.cp.mul_point(data["r_2"], Y))

        # X^gamma_1 * g^r_3
        t_3_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_1"], X), self.pd.cp.mul_point(data["r_3"], g))

        # (c/g)^gamma_2 * h^r_4
        t_4_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_2"], c_div_g), self.pd.cp.mul_point(data["r_4"], h))

        # v^gamma_2 * g^r_5
        t_5_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_2"], v), self.pd.cp.mul_point(data["r_5"], g))

        #Calc H
        

        # Check if gamma = H



    def verify_afv_nizk(self, data, c, Y, v, X, d, Yr, Xr):
        gamma_res = data["gamma_1"] + data["gamma_2"] + data["gamma_3"]

        c_div_g = self.pd.cp.sub_point(c, self.g)

        # c^gamma_1 * h^r_1
        t_1_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_1"], c), self.pd.cp.mul_point(data["r_1"], self.h))

        # v^gamma_1 * Y^r_2
        t_2_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_1"], v), self.pd.cp.mul_point(data["r_2"], Y))

        # X^gamma_1 * g^r_3
        t_3_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_1"], X), self.pd.cp.mul_point(data["r_3"], self.g))

        # (c/g)^gamma_2 * h^r_4
        t_4_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_2"], c_div_g), self.pd.cp.mul_point(data["r_4"], self.h))

        # d^gamma_2 * g^r_5 # d is not a point
        # t_5_prime = self.pd.cp.add_point(self.pd.cp.mul_point(data["gamma_2"], d), self.pd.cp.mul_point(data["r_5"], self.g))

        # v^gamma_2 * g^r_6
        t_6_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_2"], v), self.pd.cp.mul_point(data["r_6"], self.g))

        # (c/g)^gamma_3 * h^r_7
        t_7_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_3"], c_div_g), self.pd.cp.mul_point(data["r_7"], self.h))

        # d^gamma_3 * Yr^r_8 # d is not a point
        # t_8_prime = self.pd.cp.add_point(self.pd.cp.mul_point(data["gamma_3"], d), self.pd.cp.mul_point(data["r_8"], Yr))

        # Xr^gamma_3 * g^r_9
        t_9_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_3"], Xr), self.pd.cp.mul_point(data["r_9"], self.g))

        # v^gamma_3 * Y^r_10
        t_10_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_3"], v), self.pd.cp.mul_point(data["r_10"], Y))

        # X^gamma_3 * g^r_11
        t_11_prime = self.pd.cp.add_point(self.pd.cp.mul_point(
            data["gamma_3"], X), self.pd.cp.mul_point(data["r_11"], self.g))

        # Check if gamma = H

    def Calc_h(self, sumarray):
        result = Point(0,0,self.pd.cp,check=False)
        for x in sumarray :
            result = self.pd.cp.add_point(result,x)
        result_p = Point(result.x % self.p, result.y % self.p, self.pd.cp)
        return result_p

    def veto(self):
        # Create NIZK :)
        bfv = True  # Before First Veto

        previous_vetos = []
        veto_randomness = []
        latest_veto_r = None

        print(
            f"{self.id} small_xs: {len(self.small_xs)}, big_ys: {len(self.big_ys[self.index])}")

        for i in range(len(self.bit_commitments)):
            if bfv:  # Before first veto
                r_hat = number.getRandomRange(1, self.p - 1)
                veto_randomness.append(r_hat)
                if self.bits[i] == 1:
                    v = self.pd.cp.mul_point(r_hat, self.g)
                    previous_vetos.append(True)
                else:
                    v = self.pd.cp.mul_point(
                        self.small_xs[i], self.big_ys[self.index][i])
                    previous_vetos.append(False)

                bfv_nizk = self.generate_bfv_nizk(
                    self.bits[i], self.bit_commitments[i][0], v, self.big_ys[self.index][i], self.big_xs[self.index][i], self.bit_commitments[i][1], self.small_xs[i], r_hat)

                self.send_to_nodes(
                    ({"v_ir": str(v), "BV": bfv_nizk}), exclude=[self.bc_node])

                time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

                vs = get_all_messages_arr(self, len(self.clients))

                v_arr = []
                v_arr.append(v)
                for j in range(len(self.clients)):
                    json_data = json.loads(vs[j])
                    self.verify_bfv_nizk(json_data["BV"], self.h, self.bit_commitments[i][0],
                                         self.big_ys[self.index][i], v, self.g, self.big_xs[self.index][i])
                    v_arr.append(str_to_point(
                        str(json_data["v_ir"]), self.pd.cp))

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
                r_hat = number.getRandomRange(1, self.p - 1)
                veto_randomness.append(r_hat)
                if self.bits[i] == 1 and previous_vetos[latest_veto_r] == True:
                    v = self.pd.cp.mul_point(r_hat, self.g)
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
                    self.bits[i], self.bits[latest_veto_r], self.bit_commitments[i][0], v, self.big_ys[self.index][i], self.big_xs[
                        self.index][i], self.big_ys[self.index][latest_veto_r], self.big_xs[self.index][latest_veto_r],
                    self.bit_commitments[i][1], self.small_xs[i], r_hat, veto_randomness[latest_veto_r], self.small_xs[latest_veto_r])

                self.send_to_nodes(
                    ({"v_ir": str(v), "AV": afv_nizk}), exclude=[self.bc_node])

                time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

                vs = get_all_messages_arr(self, len(self.clients))

                v_arr = []

                v_arr.append(v)
                for j in range(len(self.clients)):
                    json_data = json.loads(vs[j])
                    # self.verify_afv_nizk(json_data["AV"], self.bit_commitments[i][0], self.big_ys[self.index][i], v, self.big_xs[
                    #                      self.index][i], self.bits[latest_veto_r], self.big_ys[latest_veto_r], self.big_xs[latest_veto_r])
                    v_arr.append(str_to_point(json_data["v_ir"], self.pd.cp))

                point = self.g

                for j in range(len(v_arr)):
                    point = self.pd.cp.add_point(point, v_arr[j])

                if point != self.g:  # veto
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

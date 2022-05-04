import json
import sys
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

        node_info_json = get_message(self.all_nodes[0])

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
            commitment = self.pd.commit((self.p, self.g, self.h), bit)
            self.bit_commitments.append(commitment)

    def setup(self):
        # Stage 1
        # change (secret)
        change = 0.1
        # fee: work
        work = 0.1
        # build secret deposit
        bid_param = {
            "bid": self.bid,
            "change": change,
            "work": work
        }

        # (a) send to smart contract (BroadcastNode)
        self.send_to_node(self.bc_node, (bid_param))  # Not a dict

        self.contractparams = get_message(self.bc_node)

        # Receive from smart contract
        self.p = self.contractparams["p"]
        self.h = Point(self.contractparams["h"]["x"],
                       self.contractparams["h"]["y"], self.pd.cp)
        self.g = Point(self.contractparams["g"]["x"],
                       self.contractparams["g"]["y"], self.pd.cp)

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

        # Stage 2: Compute all big X's and send commits along with X to other nodes. Is used for stage three in veto
        commit_x_dict = {}
        for i in range(len(self.bit_commitments)):
            x = number.getRandomRange(1, self.p - 1)
            self.small_xs.append(x)

            big_x = self.pd.cp.mul_point(x, self.g)

            temp_dict = {
                "commit": {
                    "x": self.bit_commitments[i][0].x,
                    "y": self.bit_commitments[i][0].y
                },
                "big_x": {
                    "x": big_x.x,
                    "y": big_x.y
                }
            }
            commit_x_dict[i] = temp_dict

        reset_all_node_msgs(self.all_nodes)

        commits_w_index = {
            "client_index": int(self.index),
            "commit_x": commit_x_dict
        }

        # maybe also send identification of yourself along ?
        self.send_to_nodes(
            (commits_w_index), exclude=[self.bc_node])

        for i in range(len(self.clients) + 1):
            self.commitments.append([])  # add room for another client
            self.big_xs.append([])  # add room for another client

        time.sleep(0.2)

        commit_and_X_arr = get_all_messages_arr(self, len(self.clients))

        time.sleep(0.5)

        unpack_commitments_x(self, [commits_w_index])
        unpack_commitments_x_arr(self, commit_and_X_arr)

        time.sleep(0.2)

        # unpack_commitment_and_x(self, commit_and_X_array)

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

    def generate_bfv_nizk(self, bit, c, v, big_y, big_x, r, x, r_bar):
        curve = self.pd.cp

        v_s = self.sample_from_field_arr(4)
        w_1, w_2 = 0, 0

        if bit == 0:  # F_1
            alpha = 1
            w_2 = self.sample_from_field()
        else:  # F_2
            alpha = 2
            w_1 = self.sample_from_field()

        c_div_g = curve.sub_point(c, self.g)

        t_1 = curve.add_point(curve.mul_point(
            w_1, c), curve.mul_point(v_s[1], self.h))

        t_2 = curve.add_point(curve.mul_point(
            w_1, v), curve.mul_point(v_s[2], big_y))

        t_3 = curve.add_point(curve.mul_point(
            w_1, big_x), curve.mul_point(v_s[2], self.g))

        t_4 = curve.add_point(curve.mul_point(
            w_2, c_div_g), curve.mul_point(v_s[3], self.h))

        t_5 = curve.add_point(curve.mul_point(
            w_2, v), curve.mul_point(v_s[4], self.g))

        h = hash(self.concatenate_points(
            [self.h, c, big_y, v, self.g, big_x, c_div_g, t_1, t_2, t_3, t_4, t_5])) % self.p

        if alpha == 1:  # F_1
            gamma1 = (h - (w_1 + w_2)) % self.p
            gamma2 = w_2

            x1, x2, x3, x4 = r, x, 0, 0

            r1 = (v_s[1] - (gamma1 * x1)) % self.p
            r2 = (v_s[2] - (gamma1 * x2)) % self.p
            r3 = r2
            r4 = (v_s[3] - (gamma1 * x3)) % self.p
            r5 = (v_s[4] - (gamma1 * x4)) % self.p

        else:  # F_2
            gamma1 = w_1
            gamma2 = (h - (w_1 + w_2)) % self.p

            x1, x2, x3, x4 = 0, 0, r, r_bar

            r1 = (v_s[1] - (gamma2 * x1)) % self.p
            r2 = (v_s[2] - (gamma2 * x2)) % self.p
            r3 = r2
            r4 = (v_s[3] - (gamma2 * x3)) % self.p
            r5 = (v_s[4] - (gamma2 * x4)) % self.p

        return {
            "gamma1": gamma1,
            "gamma2": gamma2,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "r4": r4,
            "r5": r5,
            "Y": {
                "x": big_y.x,
                "y": big_y.y
            }
        }

    def verify_bfv_nizk(self, nizk, index, v, c, big_x):
        gamma1 = nizk["gamma1"]
        gamma2 = nizk["gamma2"]
        r1 = nizk["r1"]
        r2 = nizk["r2"]
        r3 = nizk["r3"]
        r4 = nizk["r4"]
        r5 = nizk["r5"]

        # THIS HAS TO BE MODULO P
        gamma_res = (gamma1 + gamma2) % self.p

        curve = self.pd.cp

        # This one should've been broadcasted earlier
        big_y = Point(nizk["Y"]["x"], nizk["Y"]["y"], curve)

        c_div_g = curve.sub_point(c, self.g)

        t_1_p = curve.add_point(curve.mul_point(
            gamma1, c), curve.mul_point(r1, self.h))

        t_2_p = curve.add_point(curve.mul_point(
            gamma1, v), curve.mul_point(r2, big_y))

        t_3_p = curve.add_point(curve.mul_point(
            gamma1, big_x), curve.mul_point(r3, self.g))

        t_4_p = curve.add_point(curve.mul_point(
            gamma2, c_div_g), curve.mul_point(r4, self.h))

        t_5_p = curve.add_point(curve.mul_point(
            gamma2, v), curve.mul_point(r5, self.g))

        # HAS TO BE MODULO P
        h = hash(self.concatenate_points(
            [self.h, c, big_y, v, self.g, big_x, c_div_g, t_1_p, t_2_p, t_3_p, t_4_p, t_5_p])) % self.p

        # Check if gamma = H
        if h == gamma_res:
            return True
        else:
            return False

    def generate_afv_nizk(self, bit, bit_lvr, d_ir, c, v, big_y, big_x, big_y_lvr, big_x_lvr, r, x, r_hat_lvr, r_hat, x_lvr):
        curve = self.pd.cp

        v_s = self.sample_from_field_arr(8)
        w_1, w_2, w_3 = 0, 0, 0

        if bit == 0:  # F_1
            alpha = 1
            w_2 = self.sample_from_field()
            w_3 = self.sample_from_field()
        elif bit_lvr == 1 and bit == 1:  # F_2
            alpha = 2
            w_1 = self.sample_from_field()
            w_3 = self.sample_from_field()
        else:  # F_3
            alpha = 3
            w_1 = self.sample_from_field()
            w_2 = self.sample_from_field()

        c_div_g = curve.sub_point(c, self.g)

        t_1 = curve.add_point(curve.mul_point(
            w_1, c), curve.mul_point(v_s[1], self.h))

        t_2 = curve.add_point(curve.mul_point(
            w_1, v), curve.mul_point(v_s[2], big_y))

        t_3 = curve.add_point(curve.mul_point(
            w_1, big_x), curve.mul_point(v_s[2], self.g))

        t_4 = curve.add_point(curve.mul_point(
            w_2, c_div_g), curve.mul_point(v_s[3], self.h))

        t_5 = curve.add_point(curve.mul_point(
            w_2, d_ir), curve.mul_point(v_s[4], self.g))

        t_6 = curve.add_point(curve.mul_point(
            w_2, v), curve.mul_point(v_s[5], self.g))

        t_7 = curve.add_point(curve.mul_point(
            w_3, c_div_g), curve.mul_point(v_s[6], self.h))

        t_8 = curve.add_point(curve.mul_point(
            w_3, d_ir), curve.mul_point(v_s[7], big_y_lvr))

        t_9 = curve.add_point(curve.mul_point(
            w_3, big_x_lvr), curve.mul_point(v_s[7], self.g))

        t_10 = curve.add_point(curve.mul_point(
            w_3, v), curve.mul_point(v_s[8], big_y))

        t_11 = curve.add_point(curve.mul_point(
            w_3, big_x), curve.mul_point(v_s[8], self.g))

        h = hash(self.concatenate_points(
            [self.h, c, big_y, v, self.g, big_x, c_div_g, d_ir, big_y_lvr, big_x_lvr, t_1, t_2, t_3, t_4, t_5, t_6, t_7, t_8, t_9, t_10, t_11])) % self.p

        if alpha == 1:  # F_1
            gamma1 = (h - (w_1 + w_2 + w_3)) % self.p
            gamma2 = w_2
            gamma3 = w_3

            x1, x2, x3, x4, x5, x6, x7, x8 = r, x, 0, 0, 0, 0, 0, 0

            r1 = (v_s[1] - (gamma1 * x1)) % self.p
            r2 = (v_s[2] - (gamma1 * x2)) % self.p
            r3 = r2
            r4 = (v_s[3] - (gamma1 * x3)) % self.p
            r5 = (v_s[4] - (gamma1 * x4)) % self.p
            r6 = (v_s[5] - (gamma1 * x5)) % self.p
            r7 = (v_s[6] - (gamma1 * x6)) % self.p
            r8 = (v_s[7] - (gamma1 * x7)) % self.p
            r9 = r8
            r10 = (v_s[8] - (gamma1 * x8)) % self.p
            r11 = r10

        elif alpha == 2:  # F_2
            gamma1 = w_1
            gamma2 = (h - (w_1 + w_2 + w_3)) % self.p
            gamma3 = w_3

            x1, x2, x3, x4, x5, x6, x7, x8 = 0, 0, r, r_hat_lvr, r_hat, 0, 0, 0

            r1 = (v_s[1] - (gamma2 * x1)) % self.p
            r2 = (v_s[2] - (gamma2 * x2)) % self.p
            r3 = r2
            r4 = (v_s[3] - (gamma2 * x3)) % self.p
            r5 = (v_s[4] - (gamma2 * x4)) % self.p
            r6 = (v_s[5] - (gamma2 * x5)) % self.p
            r7 = (v_s[6] - (gamma2 * x6)) % self.p
            r8 = (v_s[7] - (gamma2 * x7)) % self.p
            r9 = r8
            r10 = (v_s[8] - (gamma2 * x8)) % self.p
            r11 = r10

        else:  # F_3
            gamma1 = w_1
            gamma2 = w_2
            gamma3 = (h - (w_1 + w_2 + w_3)) % self.p

            x1, x2, x3, x4, x5, x6, x7, x8 = 0, 0, 0, 0, 0, r, x_lvr, x

            r1 = (v_s[1] - (gamma3 * x1)) % self.p
            r2 = (v_s[2] - (gamma3 * x2)) % self.p
            r3 = r2
            r4 = (v_s[3] - (gamma3 * x3)) % self.p
            r5 = (v_s[4] - (gamma3 * x4)) % self.p
            r6 = (v_s[5] - (gamma3 * x5)) % self.p
            r7 = (v_s[6] - (gamma3 * x6)) % self.p
            r8 = (v_s[7] - (gamma3 * x7)) % self.p
            r9 = r8
            r10 = (v_s[8] - (gamma3 * x8)) % self.p
            r11 = r10

        # if self.index == 2:
        #     print(f"Create NIZK: t1 {t_1}")
        #     print(f"Create NIZK: t2 {t_2}")
        #     print(f"Create NIZK: t3 {t_3}")
        #     print(f"Create NIZK: t4 {t_4}")
        #     print(f"Create NIZK: t5 {t_5}")
        #     print(f"Create NIZK: t6 {t_6}")
        #     print(f"Create NIZK: t7 {t_7}")
        #     print(f"Create NIZK: t8 {t_8}")
        #     print(f"Create NIZK: t9 {t_9}")
        #     print(f"Create NIZK: t10 {t_10}")
        #     print(f"Create NIZK: t11 {t_11}")

        return {
            "gamma1": gamma1,
            "gamma2": gamma2,
            "gamma3": gamma3,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "r4": r4,
            "r5": r5,
            "r6": r6,
            "r7": r7,
            "r8": r8,
            "r9": r9,
            "r10": r10,
            "r11": r11,
            "Y": {
                "x": big_y.x,
                "y": big_y.y
            },
            "Y_lvr": {
                "x": big_y_lvr.x,
                "y": big_y_lvr.y
            }
        }

    def verify_afv_nizk(self, nizk, c, v, big_x, big_x_lvr, index, d_ir):
        gamma1 = nizk["gamma1"]
        gamma2 = nizk["gamma2"]
        gamma3 = nizk["gamma3"]
        r1 = nizk["r1"]
        r2 = nizk["r2"]
        r3 = nizk["r3"]
        r4 = nizk["r4"]
        r5 = nizk["r5"]
        r6 = nizk["r6"]
        r7 = nizk["r7"]
        r8 = nizk["r8"]
        r9 = nizk["r9"]
        r10 = nizk["r10"]
        r11 = nizk["r11"]

        # THIS HAS TO BE MODULO P, paper doesn't mention it
        gamma_res = (gamma1 + gamma2 + gamma3) % self.p

        curve = self.pd.cp

        big_y = Point(nizk["Y"]["x"], nizk["Y"]["y"], curve)
        big_y_lvr = Point(nizk["Y_lvr"]["x"], nizk["Y_lvr"]["y"], curve)

        c_div_g = curve.sub_point(c, self.g)

        t_1_p = curve.add_point(curve.mul_point(
            gamma1, c), curve.mul_point(r1, self.h))

        t_2_p = curve.add_point(curve.mul_point(
            gamma1, v), curve.mul_point(r2, big_y))

        t_3_p = curve.add_point(curve.mul_point(
            gamma1, big_x), curve.mul_point(r3, self.g))

        t_4_p = curve.add_point(curve.mul_point(
            gamma2, c_div_g), curve.mul_point(r4, self.h))

        t_5_p = curve.add_point(curve.mul_point(
            gamma2, d_ir), curve.mul_point(r5, self.g))

        t_6_p = curve.add_point(curve.mul_point(
            gamma2, v), curve.mul_point(r6, self.g))

        t_7_p = curve.add_point(curve.mul_point(
            gamma3, c_div_g), curve.mul_point(r7, self.h))

        t_8_p = curve.add_point(curve.mul_point(
            gamma3, d_ir), curve.mul_point(r8, big_y_lvr))

        t_9_p = curve.add_point(curve.mul_point(
            gamma3, big_x_lvr), curve.mul_point(r9, self.g))

        t_10_p = curve.add_point(curve.mul_point(
            gamma3, v), curve.mul_point(r10, big_y))

        t_11_p = curve.add_point(curve.mul_point(
            gamma3, big_x), curve.mul_point(r11, self.g))

        # if index == 2 and self.index == 1:
        #     print(f"Verify NIZK: t1 {t_1_p}")
        #     print(f"Verify NIZK: t2 {t_2_p}")
        #     print(f"Verify NIZK: t3 {t_3_p}")
        #     print(f"Verify NIZK: t4 {t_4_p}")
        #     print(f"Verify NIZK: t5 {t_5_p}")
        #     print(f"Verify NIZK: t6 {t_6_p}")
        #     print(f"Verify NIZK: t7 {t_7_p}")
        #     print(f"Verify NIZK: t8 {t_8_p}")
        #     print(f"Verify NIZK: t9 {t_9_p}")
        #     print(f"Verify NIZK: t10 {t_10_p}")
        #     print(f"Verify NIZK: t11 {t_11_p}")

        h = hash(self.concatenate_points(
            [self.h, c, big_y, v, self.g, big_x, c_div_g, d_ir, big_y_lvr, big_x_lvr, t_1_p, t_2_p, t_3_p, t_4_p, t_5_p, t_6_p, t_7_p, t_8_p, t_9_p, t_10_p, t_11_p])) % self.p

        if h == gamma_res:
            return True
        else:
            return False

    def sample_from_field(self):
        return number.getRandomRange(1, self.p-1)

    def sample_from_field_arr(self, amount):
        lst = [None]
        for i in range(amount):
            lst.append(self.sample_from_field())

        return lst

    def concatenate_points(self, points):
        res_string = ""
        for point in points:
            if (type(point) == int):
                res_string += str(point)
            elif (type(point) == Point):
                res_string += f"{point.x}{point.y}"
            else:
                res_string += str(point)

        return res_string

    def veto(self):
        bfv = True  # Before First Veto

        previous_vetos = []
        veto_randomness = []
        lvr = None
        previous_vetos_points = []

        for i in range(len(self.clients) + 1):
            previous_vetos_points.append([])

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

                v_arr = []
                v_arr.append(v)
                previous_vetos_points[self.index].append(v)

                nizk = self.generate_bfv_nizk(
                    self.bits[i], self.commitments[self.index][i], v, self.big_ys[self.index][i], self.big_xs[self.index][i], self.bit_commitments[i][1], self.small_xs[i], r_hat)

                nizk_msg = {
                    "v_ir": {
                        "x": v.x,
                        "y": v.y,
                    },
                    "BV": nizk,
                    "index": self.index,
                }

                self.send_to_nodes(
                    (nizk_msg), exclude=[self.bc_node])

                time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

                vs = get_all_messages_arr(self, len(self.clients))

                for j in range(len(self.clients)):
                    party = vs[j]["index"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                   ["v_ir"]["y"], self.pd.cp)

                    previous_vetos_points[party].append(v_to_i)

                    nizk_verification = self.verify_bfv_nizk(
                        vs[j]["BV"], party, v_to_i, self.commitments[party][i], self.big_xs[party][i])

                    if not nizk_verification:
                        # Go to recovery with the index of the party that sent the wrong NIZK
                        print(f"NIZK verification failed for {party}")
                    else:
                        v_arr.append(v_to_i)

                point = self.g

                for j in range(len(v_arr)):
                    point = self.pd.cp.add_point(point, v_arr[j])

                if point != self.g:
                    bfv = False
                    lvr = i
                    self.vetos.append(1)
                else:
                    self.vetos.append(0)

                print(i)

            else:  # After first veto
                # If the bit is 1 and the previous veto was true
                r_hat = number.getRandomRange(1, self.p - 1)
                veto_randomness.append(r_hat)
                if self.bits[i] == 1 and previous_vetos[lvr] == True:
                    v = self.pd.cp.mul_point(r_hat, self.g)
                    previous_vetos.append(True)
                # If the bit is 1 and the previous veto was false
                elif self.bits[i] == 1 and previous_vetos[lvr] == False:
                    v = self.pd.cp.mul_point(
                        self.small_xs[i], self.big_ys[self.index][i])
                    previous_vetos.append(False)
                else:  # If the bit is 0
                    v = self.pd.cp.mul_point(
                        self.small_xs[i], self.big_ys[self.index][i])
                    previous_vetos.append(False)

                v_arr = []
                v_arr.append(v)
                previous_vetos_points[self.index].append(v)

                nizk = self.generate_afv_nizk(
                    self.bits[i], self.bits[lvr], previous_vetos_points[self.index][lvr], self.bit_commitments[i][0], v, self.big_ys[self.index][i], self.big_xs[self.index][i], self.big_ys[self.index][lvr], self.big_xs[self.index][lvr], self.bit_commitments[i][1], self.small_xs[i], veto_randomness[lvr], r_hat, self.small_xs[lvr])

                nizk_msg = {
                    "v_ir": {
                        "x": v.x,
                        "y": v.y,
                    },
                    "AV": nizk,
                    "index": self.index,
                }

                self.send_to_nodes(
                    (nizk_msg), exclude=[self.bc_node])

                time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

                vs = get_all_messages_arr(self, len(self.clients))

                for j in range(len(self.clients)):
                    party = vs[j]["index"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                   ["v_ir"]["y"], self.pd.cp)

                    previous_vetos_points[party].append(v_to_i)

                    nizk_verification = self.verify_afv_nizk(
                        vs[j]["AV"], self.commitments[party][i], v_to_i, self.big_xs[party][i], self.big_xs[party][lvr], party, previous_vetos_points[party][lvr])

                    if not nizk_verification:
                        # Go to recovery with the index of the party that sent the wrong NIZK
                        print(f"NIZK verification failed for {party}")
                    else:
                        v_arr.append(v_to_i)

                point = self.g

                for j in range(len(v_arr)):
                    point = self.pd.cp.add_point(point, v_arr[j])

                if point != self.g:  # veto
                    lvr = i
                    self.vetos.append(1)
                else:
                    self.vetos.append(0)

                print(i)

            time.sleep(0.1)

    def veto_output(self):
        self.send_to_nodes(({"winner": self.vetos}), exclude=[self.bc_node])

        winner = get_all_messages_arr(self, len(self.clients))

        first_win = winner[0]["winner"]

        for win in winner:
            if win["winner"] != first_win:
                print("OH NOOO")
                break

        if self.bits == first_win:
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

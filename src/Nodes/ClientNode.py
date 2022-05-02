import json
import random
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
        self.bit_randomness = []

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
            commitment = self.pd.commit(bit)
            self.bit_commitments.append(commitment)
            self.bit_randomness.append(commitment[1])

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

        self.contractparams = get_message(self.bc_node)

        self.p = self.contractparams["p"]
        self.h = Point(self.contractparams["h"]["x"],
                       self.contractparams["h"]["y"], self.pd.cp)
        self.g = Point(self.contractparams["g"]["x"],
                       self.contractparams["g"]["y"], self.pd.cp)

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

        # Something might be wrong with picking the non H gamma
        if alpha == 1:  # F_1
            gamma1 = (h - (w_1 + w_2)) % self.p
            gamma2 = w_2

            x1, x2, x3, x4 = r, x, 0, 0

            r1 = (v_s[1] - (gamma1 * x1)) % self.p  # Something's wrong with r
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
            r4 = (v_s[3] - (gamma2 * x3)) % self.p  # Something's wrong with r
            r5 = (v_s[4] - (gamma2 * x4)) % self.p

        if self.index == 2:
            print(f"Create NIZK: t1 {t_1}")
            print(f"Create NIZK: t2 {t_2}")
            print(f"Create NIZK: t3 {t_3}")
            print(f"Create NIZK: t4 {t_4}")
            print(f"Create NIZK: t5 {t_5}")

        return {
            "gamma1": gamma1,
            "gamma2": gamma2,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "r4": r4,
            "r5": r5,
            "v": {
                "x": v.x,
                "y": v.y
            },
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

        # Incorrect
        t_1_prime = curve.add_point(curve.mul_point(
            gamma1, c), curve.mul_point(r1, self.h))

        # Correct
        t_2_prime = curve.add_point(curve.mul_point(
            gamma1, v), curve.mul_point(r2, big_y))

        # Correct
        t_3_prime = curve.add_point(curve.mul_point(
            gamma1, big_x), curve.mul_point(r3, self.g))

        # Correct
        t_4_prime = curve.add_point(curve.mul_point(
            gamma2, c_div_g), curve.mul_point(r4, self.h))

        # Correct
        t_5_prime = curve.add_point(curve.mul_point(
            gamma2, v), curve.mul_point(r5, self.g))

        if index == 2 and self.index == 1:
            print(f"Verify NIZK: t1 {t_1_prime}")
            print(f"Verify NIZK: t2 {t_2_prime}")
            print(f"Verify NIZK: t3 {t_3_prime}")
            print(f"Verify NIZK: t4 {t_4_prime}")
            print(f"Verify NIZK: t5 {t_5_prime}")

        # HAS TO BE MODULO P
        h = hash(self.concatenate_points(
            [self.h, c, big_y, v, self.g, big_x, c_div_g, t_1_prime, t_2_prime, t_3_prime, t_4_prime, t_5_prime])) % self.p

        # Check if gamma = H
        if h == gamma_res:
            # print(h == gamma_res)
            return True
        else:
            # print(h == gamma_res)
            return False

    def sample_from_field(self):
        return random.randint(1, self.p-1)

    def sample_from_field_arr(self, amount):
        lst = [None]
        for i in range(amount):
            lst.append(self.sample_from_field())

        return lst

    def concatenate_points(self, points):
        res_string = ""
        for point in points:
            res_string += f"{point.x}{point.y}"

        return res_string

    def veto(self):
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

                nizk = self.generate_bfv_nizk(
                    self.bits[i], self.commitments[self.index][i], v, self.big_ys[self.index][i], self.big_xs[self.index][i], self.bit_randomness[i], self.small_xs[i], r_hat)

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

                v_arr = []
                v_arr.append(v)
                for j in range(len(self.clients)):
                    party = vs[j]["index"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                   ["v_ir"]["y"], self.pd.cp)

                    nizk_verification = self.verify_bfv_nizk(
                        vs[j]["BV"], party, v_to_i, self.commitments[party][i], self.big_xs[party][i])

                    if not nizk_verification:
                        # Go to recovery with the index of the party that sent the wrong NIZK
                        # print(f"{self.index}: Party {party} sent a wrong NIZK")
                        pass
                    else:
                        pass
                    v_arr.append(v_to_i)

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

                self.send_to_nodes(
                    ({"v_ir": str(v)}), exclude=[self.bc_node])

                time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

                vs = get_all_messages_arr(self, len(self.clients))

                v_arr = []

                v_arr.append(v)
                for j in range(len(self.clients)):
                    v_arr.append(str_to_point(vs[j]["v_ir"], self.pd.cp))

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

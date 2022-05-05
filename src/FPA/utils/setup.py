from Crypto.Util import number
import time
from ecdsa.curves import *
from src.utils.node import *


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
    # change 
    change = 0.1
    # fee: work
    work = 0.1
    # build secret deposit
    bid_param = {
        "bid": self.bid,
        "change": change,
        "work": work
    }

    # (a) send to smart contract FSC
    self.send_to_node(self.bc_node, (bid_param)) 

    self.contractparams = get_message(self.bc_node)

    # Receive from smart contract
    self.p = self.contractparams["p"]
    self.h = Point(self.contractparams["h"]["x"],
                   self.contractparams["h"]["y"], self.pd.cp)
    self.g = Point(self.contractparams["g"]["x"],
                   self.contractparams["g"]["y"], self.pd.cp)

    # (b) compute bit commitments
    bid_decomposition(self)


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

    self.bid_commit = self.pd.commit((self.p, self.g, self.h), self.bid)

    commitment_to_bid = {
        "commitment_to_bid": {
            "x": self.bid_commit[0].x,
            "y": self.bid_commit[0].y 
        },
        "client_index": self.index
    }

    commits_w_index = {
        "client_index": self.index,
        "commit_x": commit_x_dict
    }

    self.send_to_nodes(
        (commits_w_index), exclude=[self.bc_node])
    self.send_to_node(self.bc_node,commitment_to_bid)

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

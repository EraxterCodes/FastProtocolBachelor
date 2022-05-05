import time
from Crypto.Util import number
from ecpy.curves import Point
from src.FPA.utils.nizk_bfv import *
from src.FPA.utils.nizk_afv import *
from src.utils.node import *
import threading
from multiprocessing import Process

Threadtoggle = False

def afv_nizk_thread(args):
    self, vs, i, lvr, previous_vetos_points, v_arr = args

    party = vs["index"]
    v_to_i = Point(vs["v_ir"]["x"], vs
                    ["v_ir"]["y"], self.pd.cp)

    previous_vetos_points[party].append(v_to_i)

    nizk_verification = verify_afv_nizk(
        self, vs["AV"], self.commitments[party][i], v_to_i, self.big_xs[party][i], self.big_xs[party][lvr], previous_vetos_points[party][lvr])

    if not nizk_verification:
        # Go to recovery with the index of the party that sent the wrong NIZK
        print(f"NIZK verification failed for {party}")
    else:
        v_arr.append(v_to_i)

def bfv_nizk_thread(args):
    self, vs, i, previous_vetos_points, v_arr = args

    party = vs["index"]
    v_to_i = Point(vs["v_ir"]["x"], vs
                    ["v_ir"]["y"], self.pd.cp)

    previous_vetos_points[party].append(v_to_i)

    nizk_verification = verify_bfv_nizk(self,
                                        vs["BV"], v_to_i, self.commitments[party][i], self.big_xs[party][i])

    if not nizk_verification:
        # Go to recovery with the index of the party that sent the wrong NIZK
        print(f"NIZK verification failed for {party}")
    else:
        v_arr.append(v_to_i)


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

            nizk = generate_bfv_nizk(self,
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

            if Threadtoggle:
                process_list = []
                for j in range(len(self.clients)):
                    param_thread = Process(target=bfv_nizk_thread, args=((self, vs[j], i, previous_vetos_points, v_arr), ))
                    param_thread.start()
                    param_thread.join()
                    process_list.append(param_thread)
                    
            else:
                for j in range(len(self.clients)):
                    party = vs[j]["index"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                ["v_ir"]["y"], self.pd.cp)

                    previous_vetos_points[party].append(v_to_i)

                    nizk_verification = verify_bfv_nizk(self,
                                                        vs[j]["BV"], v_to_i, self.commitments[party][i], self.big_xs[party][i])

                    if not nizk_verification:
                        # Go to recovery with the index of the party that sent the wrong NIZK
                        print(f"NIZK verification failed for {party}")
                    else:
                        v_arr.append(v_to_i)

            while len(v_arr) != len(self.clients) + 1:
                time.sleep(0.1)

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

            nizk = generate_afv_nizk(
                self, self.bits[i], previous_vetos[lvr], previous_vetos_points[self.index][lvr], self.bit_commitments[i][0], v, self.big_ys[self.index][i], self.big_xs[self.index][i], self.big_ys[self.index][lvr], self.big_xs[self.index][lvr], self.bit_commitments[i][1], self.small_xs[i], veto_randomness[lvr], r_hat, self.small_xs[lvr])

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
            
            if Threadtoggle :
                for j in range(len(self.clients)):
                    param_thread = threading.Thread(target=afv_nizk_thread, args=((self, vs[j], i,lvr, previous_vetos_points, v_arr), ))
                    param_thread.start()
            else:
                for j in range(len(self.clients)):
                    party = vs[j]["index"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                ["v_ir"]["y"], self.pd.cp)

                    previous_vetos_points[party].append(v_to_i)

                    nizk_verification = verify_afv_nizk(
                        self, vs[j]["AV"], self.commitments[party][i], v_to_i, self.big_xs[party][i], self.big_xs[party][lvr], previous_vetos_points[party][lvr])

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


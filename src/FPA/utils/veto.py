from __future__ import annotations
from typing import TYPE_CHECKING
import time
from Crypto.Util import number
from ecpy.curves import Point
from src.FPA.utils.nizk_bfv import *
from src.FPA.utils.nizk_afv import *
from src.utils.node import *
import threading

execute_threads = False

if TYPE_CHECKING:
    from src.Nodes.ClientNode import ClientNode


def afv_nizk_thread(args):
    nizk, c, v_to_i, big_x, big_x_lvr, d_ir, curve, p, g, h, thread_res, j = args

    nizk_verification = verify_afv_nizk(
        nizk, c, v_to_i, big_x, big_x_lvr, d_ir, curve, p, g, h)

    if not nizk_verification:
        # Go to recovery with the index of the party that sent the wrong NIZK
        print(f"NIZK verification failed for ")
    else:
        thread_res[j] = v_to_i


def bfv_nizk_thread(args):
    nizk, c, v_to_i, big_x, curve, p, g, h, thread_res, j = args

    nizk_verification = verify_bfv_nizk(
        nizk, v_to_i, c, big_x, curve, p, g, h)

    if not nizk_verification:
        # Go to recovery with the index of the party that sent the wrong NIZK
        print(f"NIZK verification failed for")
    else:
        thread_res[j] = v_to_i


def veto(self: ClientNode):
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

            v_arr = [None] * (len(self.clients) + 1)
            v_arr[len(self.clients)] = v
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

            time.sleep(0.01)

            vs = get_all_messages_arr(self, len(self.clients))

            if execute_threads:
                thread_args = []

                for j in range(len(self.clients)):
                    party = vs[j]["index"]

                    nizk = vs[j]["BV"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                   ["v_ir"]["y"], self.pd.cp)
                    c = self.commitments[party][i]
                    big_x = self.big_xs[party][i]
                    curve = self.pd.cp
                    p = self.p
                    g = self.g
                    h = self.h

                    args = (nizk, c, v_to_i, big_x,
                            curve, p, g, h, v_arr, j)
                    thread_args.append(args)
                    previous_vetos_points[party].append(v_to_i)

                threads = [None] * len(self.clients)

                for j in range(len(self.clients)):
                    threads[j] = threading.Thread(
                        target=bfv_nizk_thread, args=(thread_args[j],))
                    threads[j].start()

                for j in range(len(self.clients)):
                    threads[j].join()

            else:
                for j in range(len(self.clients)):
                    party = vs[j]["index"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                   ["v_ir"]["y"], self.pd.cp)

                    previous_vetos_points[party].append(v_to_i)

                    nizk_verification = verify_bfv_nizk(
                        vs[j]["BV"], v_to_i, self.commitments[party][i], self.big_xs[party][i], self.pd.cp, self.p, self.g, self.h)

                    if not nizk_verification:
                        # Go to recovery with the index of the party that sent the wrong NIZK
                        print(f"NIZK verification failed for {party}")
                        break
                    else:
                        v_arr[j] = v_to_i

            point = self.g

            for j in range(len(v_arr)):
                point = self.pd.cp.add_point(point, v_arr[j])

            if point != self.g:
                bfv = False
                lvr = i
                self.vetos.append(1)
            else:
                self.vetos.append(0)

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

            v_arr = [None] * (len(self.clients) + 1)
            v_arr[len(self.clients)] = v
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

            time.sleep(0.05)

            vs = get_all_messages_arr(self, len(self.clients))

            start = time.time()

            if execute_threads:
                thread_args = []

                for j in range(len(self.clients)):
                    party = vs[j]["index"]

                    nizk = vs[j]["AV"]
                    c = self.commitments[party][i]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                   ["v_ir"]["y"], self.pd.cp)
                    big_x = self.big_xs[party][i]
                    big_x_lvr = self.big_xs[party][lvr]
                    d_ir = previous_vetos_points[party][lvr]
                    curve = self.pd.cp
                    p, g, h = self.p, self.g, self.h

                    args = (nizk, c, v_to_i, big_x,
                            big_x_lvr, d_ir, curve, p, g, h, v_arr, j)
                    thread_args.append(args)

                    previous_vetos_points[party].append(v_to_i)

                threads = [None] * len(self.clients)

                for j in range(len(self.clients)):
                    threads[j] = threading.Thread(
                        target=afv_nizk_thread, args=(thread_args[j],))
                    threads[j].start()

                for j in range(len(self.clients)):
                    threads[j].join()

            else:
                for j in range(len(self.clients)):
                    party = vs[j]["index"]
                    v_to_i = Point(vs[j]["v_ir"]["x"], vs[j]
                                   ["v_ir"]["y"], self.pd.cp)

                    previous_vetos_points[party].append(v_to_i)

                    nizk_verification = verify_afv_nizk(
                        vs[j]["AV"], self.commitments[party][i], v_to_i, self.big_xs[party][i], self.big_xs[party][lvr], previous_vetos_points[party][lvr], self.pd.cp, self.p, self.g, self.h)

                    if not nizk_verification:
                        # Go to recovery with the index of the party that sent the wrong NIZK
                        print(f"NIZK verification failed for {party}")
                    else:
                        v_arr[j] = v_to_i

            point = self.g

            for j in range(len(v_arr)):
                point = self.pd.cp.add_point(point, v_arr[j])

            if point != self.g:  # veto
                lvr = i
                self.vetos.append(1)
            else:
                self.vetos.append(0)

        print(f"Round {i}")

        time.sleep(0.01)

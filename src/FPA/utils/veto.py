from src.FPA.utils.nizk_bfv import *
from src.FPA.utils.nizk_afv import *
import time
from Crypto.Util import number


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

            nizk_msg = {
                "v_ir": {
                    "x": v.x,
                    "y": v.y,
                },
                "BV": bfv_nizk,
                "index": self.index,
                "bit_commitment": {
                    "x": self.bit_commitments[i][0].x,
                    "y": self.bit_commitments[i][0].y,
                },
            }

            self.send_to_nodes(
                (nizk_msg), exclude=[self.bc_node])

            time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

            vs = get_all_messages_arr(self, len(self.clients))

            v_arr = []
            v_arr.append(v)
            for j in range(len(self.clients)):
                index = vs[j]["index"]
                v_to_index = Point(
                    vs[j]["v_ir"]["x"], vs[j]["v_ir"]["y"], self.pd.cp)
                commit_to_index = Point(
                    vs[j]["bit_commitment"]["x"], vs[j]["bit_commitment"]["y"], self.pd.cp)
                self.verify_bfv_nizk(vs[j]["BV"], self.h, commit_to_index,
                                     self.big_ys[index][i], v_to_index, self.g, self.big_xs[index][i])
                v_arr.append(
                    Point(vs[j]["v_ir"]["x"], vs[j]["v_ir"]["y"], self.pd.cp))

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

            # afv_nizk = self.generate_afv_nizk(
            #     self.bits[i], self.bits[latest_veto_r], self.bit_commitments[i][0], v, self.big_ys[self.index][i], self.big_xs[
            #         self.index][i], self.big_ys[self.index][latest_veto_r], self.big_xs[self.index][latest_veto_r],
            #     self.bit_commitments[i][1], self.small_xs[i], r_hat, veto_randomness[latest_veto_r], self.small_xs[latest_veto_r])

            self.send_to_nodes(
                ({"v_ir": str(v)}), exclude=[self.bc_node])
            # self.send_to_nodes(
            #     ({"v_ir": str(v), "AV": afv_nizk}), exclude=[self.bc_node])

            time.sleep(0.01)  # Can be adjusted to 0.01 for improved speed

            vs = get_all_messages_arr(self, len(self.clients))

            v_arr = []

            v_arr.append(v)
            for j in range(len(self.clients)):
                # self.verify_afv_nizk(json_data["AV"], self.bit_commitments[i][0], self.big_ys[self.index][i], v, self.big_xs[
                #                      self.index][i], self.bits[latest_veto_r], self.big_ys[latest_veto_r], self.big_xs[latest_veto_r])
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

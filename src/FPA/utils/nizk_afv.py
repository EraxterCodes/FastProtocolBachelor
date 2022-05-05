from ecpy.curves import Point
from src.utils.utils import *


def generate_afv_nizk(self, bit, bit_lvr, d_ir, c, v, big_y, big_x, big_y_lvr, big_x_lvr, r, x, r_hat_lvr, r_hat, x_lvr):
    curve = self.pd.cp

    v_s = sample_from_field_arr(8, self.p)
    w_1, w_2, w_3 = 0, 0, 0

    if bit == 1 and bit_lvr == True:  # F_2
        alpha = 2
        w_1 = sample_from_field(self.p)
        w_3 = sample_from_field(self.p)
    elif bit == 1 and bit_lvr == False:  # F_3
        alpha = 3
        w_1 = sample_from_field(self.p)
        w_2 = sample_from_field(self.p)
    else:  # F_1
        alpha = 1
        w_2 = sample_from_field(self.p)
        w_3 = sample_from_field(self.p)

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

    h = hash(concatenate_points(
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
        },
    }


def verify_afv_nizk(self, nizk, c, v, big_x, big_x_lvr, d_ir):
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

    h = hash(concatenate_points(
        [self.h, c, big_y, v, self.g, big_x, c_div_g, d_ir, big_y_lvr, big_x_lvr, t_1_p, t_2_p, t_3_p, t_4_p, t_5_p, t_6_p, t_7_p, t_8_p, t_9_p, t_10_p, t_11_p])) % self.p

    if h == gamma_res:
        return True
    else:
        return False

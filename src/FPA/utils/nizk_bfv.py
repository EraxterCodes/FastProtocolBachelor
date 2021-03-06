from __future__ import annotations
from typing import TYPE_CHECKING
from ecpy.curves import Point, Curve
from src.utils.utils import *
import hashlib

if TYPE_CHECKING:
    from src.Nodes.ClientNode import ClientNode


def generate_bfv_nizk(self: ClientNode, bit, c, v, big_y, big_x, r, x, r_bar):
    curve = self.pd.cp

    v_s = sample_from_field_arr(4, self.p)
    w_1, w_2 = 0, 0

    if bit == 0:  # F_1
        alpha = 1
        w_2 = sample_from_field(self.p)
    else:  # F_2
        alpha = 2
        w_1 = sample_from_field(self.p)

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

    concatenated_points = concatenate_points(
        [self.h, c, big_y, v, self.g, big_x, c_div_g, t_1, t_2, t_3, t_4, t_5])

    h = int(hashlib.sha256(concatenated_points.encode()).hexdigest(), 16) % self.p

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


def verify_bfv_nizk(nizk: dict, v: Point, c: Point, big_x: Point, curve: Curve, p: int, g: Point, h: Point):
    gamma1 = nizk["gamma1"]
    gamma2 = nizk["gamma2"]
    r1 = nizk["r1"]
    r2 = nizk["r2"]
    r3 = nizk["r3"]
    r4 = nizk["r4"]
    r5 = nizk["r5"]

    # THIS HAS TO BE MODULO P
    gamma_res = (gamma1 + gamma2) % p

    big_y = Point(nizk["Y"]["x"], nizk["Y"]["y"], curve)

    c_div_g = curve.sub_point(c, g)

    t_1_p = curve.add_point(curve.mul_point(
        gamma1, c), curve.mul_point(r1, h))

    t_2_p = curve.add_point(curve.mul_point(
        gamma1, v), curve.mul_point(r2, big_y))

    t_3_p = curve.add_point(curve.mul_point(
        gamma1, big_x), curve.mul_point(r3, g))

    t_4_p = curve.add_point(curve.mul_point(
        gamma2, c_div_g), curve.mul_point(r4, h))

    t_5_p = curve.add_point(curve.mul_point(
        gamma2, v), curve.mul_point(r5, g))

    # HAS TO BE MODULO P
    concatenated_points = concatenate_points(
        [h, c, big_y, v, g, big_x, c_div_g, t_1_p, t_2_p, t_3_p, t_4_p, t_5_p])

    h = int(hashlib.sha256(concatenated_points.encode()).hexdigest(), 16) % p

    # Check if gamma = H
    if h == gamma_res:
        return True
    else:
        return False

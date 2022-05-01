from ecpy.curves import Curve, Point


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

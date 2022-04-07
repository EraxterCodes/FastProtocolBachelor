# uses pycryptodome, NOT pycrypto
from Crypto.Random import random
from ecpy.curves import Curve

from modules.Crypto.Util import number


class Pedersen:
    def __init__(self):
        self.cp = None
        self.param = self.setup()

    def setup(self):
        self.cp = Curve.get_curve("secp256k1")

        # 2^256
        size = 2**self.cp.size

        # Order of the group to sample Z_p from
        p = self.cp.order

        # Generator of group
        g = self.cp.generator

        # Random scalar from G (Blinding factor)
        r = random.randint(1, size)
        # Random generator value
        h = g * r

        return p, g, h

    # r is number.getRandomRange(1, p - 1)
    def commit(self, m):
        p, g, h = self.param

        # Randomness of Z_p
        r = number.getRandomRange(1, p-1)

        # Create to scalar points on the curve
        mg = self.cp.mul_point(m, g)
        rh = self.cp.mul_point(r, h)

        # Commitment which is the two points on the curve
        c = self.cp.add_point(mg, rh)

        return c, r

    def open(self, m, c, r):
        _, g, h = self.param

        # Compute the opening of the commitment
        mg = self.cp.mul_point(m, g)
        rh = self.cp.mul_point(r, h)

        # Open the commitment
        o = self.cp.add_point(mg, rh)

        # Check if the commitment is valid
        if o == c:
            return True
        else:
            return False

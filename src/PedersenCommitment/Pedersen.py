from ecpy.curves import Curve
from src.utils.utils import sample_from_field


class Pedersen:
    def __init__(self):
        self.cp = Curve.get_curve("secp256k1")

        self.param = self.setup()

    def setup(self):

        # Order of the group to sample Z_p from
        p = self.cp.order

        # Generator of group
        g = self.cp.generator

        # Random scalar from G (Blinding factor)
        r = sample_from_field(p)

        h = self.cp.mul_point(r, g)

        return p, g, h

    def create_commit(self, param, m, r):
        g, h = param

       
        mg = self.cp.mul_point(m, g)
        rh = self.cp.mul_point(r, h)

        # Commitment which is the sum of the 2 points.  
        c = self.cp.add_point(mg, rh)

        return c, r

    def commit(self, param, m):
        p, g, h = param

        # Randomness of Z_p
        r = sample_from_field(p)

        c, _ = self.create_commit((g, h), m, r)

        return c, r

    def open(self, g, h, m, c, r):
        # Check if the commitment is valid

        o, _ = self.create_commit((g, h), m, r)

        # Check if the commitment is valid
        if o == c:
            return True
        else:
            return False

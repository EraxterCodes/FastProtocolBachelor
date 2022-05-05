from src.FPA.utils.setup import setup
from src.FPA.utils.veto import veto


def fpa(self):
    setup(self)

    veto(self)

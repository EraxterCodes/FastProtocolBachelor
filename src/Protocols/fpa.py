from src.Protocols.FPA_utils.setup import setup
from src.Protocols.FPA_utils.veto import veto


def fpa(self):
    setup(self)

    veto(self)

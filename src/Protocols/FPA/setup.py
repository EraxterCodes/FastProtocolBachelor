from src.Protocols.FPA.stage1 import stage1
from src.Protocols.FPA.stage2 import stage2
from src.Protocols.FPA.stage3 import stage3


def setup_phase():
    stage1()

    stage2()

    stage3()

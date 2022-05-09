from __future__ import annotations
from typing import TYPE_CHECKING
from src.FPA.utils.setup import setup
from src.FPA.utils.veto import veto

if TYPE_CHECKING:
    from src.Nodes.ClientNode import ClientNode


def fpa(self: ClientNode):
    setup(self)

    veto(self)

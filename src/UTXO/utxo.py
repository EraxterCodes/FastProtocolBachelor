class utxo:
    def __init__(self, amount, addr):
        self.amount = amount
        self.spent = False

        self.addr = addr

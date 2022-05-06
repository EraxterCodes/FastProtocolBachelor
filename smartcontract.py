from src.Nodes.Fsc import Fsc

parties = int(input("How many parties?: "))

smartcontract = Fsc("172.20.10.2", 8001, "Broadcast", parties)
smartcontract.start()

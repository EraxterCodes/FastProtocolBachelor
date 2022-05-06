from src.Nodes.Fsc import Fsc

parties = int(input("How many parties?: "))

smartcontract = Fsc("127.0.0.1", 8001, "Broadcast", parties)
smartcontract.start()

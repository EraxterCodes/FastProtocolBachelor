from src.Nodes.Fsc import Fsc
from src.utils.node import get_ip

parties = int(input("How many parties?: "))

ip = get_ip()

smartcontract = Fsc(ip, 8001, "Broadcast", parties)
smartcontract.start()

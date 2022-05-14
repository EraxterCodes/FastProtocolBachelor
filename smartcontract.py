from src.Nodes.Fsc import Fsc
from src.utils.node import get_ip

parties = int(input("How many parties?: "))

ip = get_ip()
print(ip)

smartcontract = Fsc("25.32.252.190", 8001, "Broadcast", parties)
smartcontract.start()

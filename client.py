from src.Nodes.ClientNode import ClientNode
from src.utils.node import get_free_port, get_ip

bid = input("Bid of client: ")

ip = str(get_ip())
port = get_free_port()
bc_ip = str(get_ip())

print(ip)

client = ClientNode(ip, port, int(bid), bc_ip)
client.start()

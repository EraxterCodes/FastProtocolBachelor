from src.Nodes.ClientNode import ClientNode
from src.utils.node import get_free_port, get_ip

bid = input("Bid of client: ")

ip = str(get_ip())
port = get_free_port()
bc_ip = "Insert IP of broadcast node"

client = ClientNode("25.32.252.190", port, int(bid), "25.32.252.190")
client.start()


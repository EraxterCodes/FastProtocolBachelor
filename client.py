from src.Nodes.ClientNode import ClientNode
from src.utils.node import get_free_port

bid = input("Bid of client: ")

port = get_free_port()

client = ClientNode("127.0.0.1", port, int(bid))
client.start()

from src.Nodes.ClientNode import ClientNode

input("Press Enter to start the client...")
bid = input("Bid of client: ")
port = input("Port of client: ")

client = ClientNode("127.0.0.1", int(port), int(bid))
client.start()

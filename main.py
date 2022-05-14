from src.Nodes.ClientNode import ClientNode
from src.Nodes.Fsc import Fsc
import time
from src.utils.node import get_free_port, get_ip

selfinput = False
manyclients = False
Client_Node_list = []


if selfinput:
    Num_Client = input("How many clients?: ")
    for i in range(int(Num_Client)):
        id = i+1

        Bid_Input = input(f"Bid for party: ID {str(id)}: ")
        Client_Node_list.append(ClientNode(
            "127.0.0.1", 8003 + (i*2), int(Bid_Input), id))

else:
    if manyclients:
        Node1 = ClientNode("127.0.0.1", get_free_port(), 42)
        Node2 = ClientNode("127.0.0.1", get_free_port(), 123)
        Node3 = ClientNode("127.0.0.1", get_free_port(), 99)
        Node4 = ClientNode("127.0.0.1", get_free_port(), 100)
        Node5 = ClientNode("127.0.0.1", get_free_port(), 2348)
        Node6 = ClientNode("127.0.0.1", get_free_port(), 8434)
        Node7 = ClientNode("127.0.0.1", get_free_port(), 2346)
        Node8 = ClientNode("127.0.0.1", get_free_port(), 9999)
        Node9 = ClientNode("127.0.0.1", get_free_port(), 123)
        Node10 = ClientNode("127.0.0.1", get_free_port(), 542)

        Client_Node_list = [Node1, Node2, Node3,
                            Node4, Node5, Node6, Node7, Node8]
    else:
        Node1 = ClientNode("127.0.0.1", get_free_port(), 100)
        Node2 = ClientNode("127.0.0.1", get_free_port(), 200)
        Node3 = ClientNode("127.0.0.1", get_free_port(), 50)

        Client_Node_list = [Node1, Node2, Node3]

broadcastNode = Fsc("127.0.0.1", 8001, "Broadcast", len(Client_Node_list))
broadcastNode.start()

for n in Client_Node_list:
    n.start()
    time.sleep(0.05)

from src.Nodes.ClientNode import ClientNode
from src.Nodes.Fsc import Fsc
import time

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
        Node1 = ClientNode("127.0.0.1", 8003, 42, 1)
        Node2 = ClientNode("127.0.0.1", 8005, 1000, 2)
        Node3 = ClientNode("127.0.0.1", 8007, 6116, 3)
        Node4 = ClientNode("127.0.0.1", 8009, 634, 4)
        Node5 = ClientNode("127.0.0.1", 8011, 2348, 5)
        Node6 = ClientNode("127.0.0.1", 8013, 8434, 6)
        Node7 = ClientNode("127.0.0.1", 8015, 2346, 7)
        Node8 = ClientNode("127.0.0.1", 8017, 9999, 8)

        Client_Node_list = [Node1, Node2, Node3,
                            Node4, Node5, Node6, Node7, Node8]
    else:
        Node1 = ClientNode("127.0.0.1", 8003, 100, 1)
        Node2 = ClientNode("127.0.0.1", 8005, 200, 2)
        Node3 = ClientNode("127.0.0.1", 8007, 50, 3)

        Client_Node_list = [Node1, Node2, Node3]


broadcastNode = Fsc("127.0.0.1", 8001, "Broadcast", Client_Node_list)
broadcastNode.start()

for n in Client_Node_list:
    n.start()
    time.sleep(0.1)

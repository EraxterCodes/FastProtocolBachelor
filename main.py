from src.Nodes.ClientNode import ClientNode
from src.Nodes.BroadcastNode import BroadcastNode
import time

selfinput = False
Client_Node_list = []

if selfinput:
    Num_Client = input("How many clients?: ")
    for i in range(int(Num_Client)):
        id = i+1

        Bid_Input = input(f"Bid for party: ID {str(id)}: ")
        Client_Node_list.append(ClientNode(
            "127.0.0.1", 8003 + (i*2), int(Bid_Input), id))

else:
    Node1 = ClientNode("127.0.0.1", 8003, 42, 1)
    Node2 = ClientNode("127.0.0.1", 8005, 123, 2)
    Node3 = ClientNode("127.0.0.1", 8007, 666, 3)
    # Node4 = ClientNode("127.0.0.1", 8009, 667, 4)
    Client_Node_list = [Node1, Node2, Node3]


broadcastNode = BroadcastNode("127.0.0.1", 8001, "Broadcast", Client_Node_list)
broadcastNode.start()

for n in Client_Node_list:
    n.start()
    time.sleep(0.01)

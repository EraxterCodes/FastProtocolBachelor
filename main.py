from operator import indexOf
from src.Nodes.ClientNode import ClientNode
from src.Nodes.BroadcastNode import BroadcastNode
import time

Client_Node_list = []
Num_Client = input("How many clients?")
for i in range(int(Num_Client)):
    Bid_Input = input("Bid for party: " + str(i)) 
    Client_Node_list.append(ClientNode("127.0.0.1",8000 + (i*2),Bid_Input,2))

 

broadcastNode = BroadcastNode("127.0.0.1", 8001,1, Client_Node_list)
broadcastNode.start()

for n in Client_Node_list:
    n.start()
    time.sleep(0.1)



from src.Nodes.ClientNode import ClientNode
from src.Nodes.Fsc import Fsc
import time
from src.utils.node import get_free_port, get_ip
import os

selfinput = True
Client_Node_list = []




clear_command = 'cls'
if os.name == 'nt':
    clear_command = 'cls'
else:
    clear_command = 'clear'

os.system(clear_command)

def getBid(party_id):
    bid = input(f"Bid for party {party_id}:")
    while int(bid) > 4294967295 or int(bid) < 0:
        os.system(clear_command)
        bid = input("Bids have to be between 0 and 4294967295: please select a new bid: ")
        
    return bid

auction_type = input("Type 1 to run automatic auction or 2 to run custom auction: ")

if int(auction_type) == 1:
    os.system(clear_command)
    self_input = input("Type 1 to start auction or 2 to enter self inputs: ")
    if int(self_input) == 1:
        selfinput = False

    if selfinput:
        os.system(clear_command)
        Num_Client = input("How many clients?: ")
        for i in range(int(Num_Client)):
            
            os.system(clear_command)
            Bid_Input = getBid(str(i))
            Client_Node_list.append(ClientNode(
                "127.0.0.1", get_free_port(), int(Bid_Input)))

    else:
        os.system(clear_command)
        Bid_Input1 = getBid("1")
        os.system(clear_command)
        Bid_Input2 = getBid("2")
        os.system(clear_command)
        Bid_Input3 = getBid("3")
        os.system(clear_command)
        Node1 = ClientNode("127.0.0.1", get_free_port(), int(Bid_Input1))
        Node2 = ClientNode("127.0.0.1", get_free_port(), int(Bid_Input2))
        Node3 = ClientNode("127.0.0.1", get_free_port(), int(Bid_Input3))

        Client_Node_list = [Node1, Node2, Node3]

    broadcastNode = Fsc("127.0.0.1", 8001, "Broadcast", len(Client_Node_list))
    broadcastNode.start()

    for n in Client_Node_list:
        n.start()
        time.sleep(0.05)
        
elif int(auction_type) == 2:
    contract_auction = input("Type 1 to start an auction (Smartcontract) or 2 to join an auction: ")
    ip = str(get_ip())

    if int(contract_auction) == 1:
        parties = int(input("How many parties?: "))
        print(f"Parties can connect to: {ip}")

        smartcontract = Fsc(ip, 8001, "Broadcast", parties)
        smartcontract.start()
    elif int(contract_auction) == 2:
        # Will always assume that Smartcontract is on port 8001.
        os.system(clear_command)
        print(f"Your ip: {ip}")

        port = get_free_port()

        smartcontract_ip = input("Enter IP of smartcontract: ")

        bid = getBid("")

        client = ClientNode(ip, port, int(bid), smartcontract_ip)
        client.start()



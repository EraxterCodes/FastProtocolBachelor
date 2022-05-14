from src.Nodes.ClientNode import ClientNode
from src.Nodes.Fsc import Fsc
import time

from src.utils.node import get_ip, get_free_port

selfinput = False
manyclients = False
Client_Node_list = []

if __name__ == '__main__':
    auction = int(
        input("Press 1 for automatic auction and 2 for custom auction: "))
    if auction == 1:
        if selfinput:
            Num_Client = input("How many clients?: ")
            for i in range(int(Num_Client)):
                id = i+1

                Bid_Input = input(f"Bid for party: ID {str(id)}: ")
                Client_Node_list.append(ClientNode(
                    "127.0.0.1", 8003 + (i*2), int(Bid_Input), id))

        else:
            if manyclients:
                Node1 = ClientNode("127.0.0.1", 8003, 42)
                Node2 = ClientNode("127.0.0.1", 8005, 123)
                Node3 = ClientNode("127.0.0.1", 8007, 99)
                Node4 = ClientNode("127.0.0.1", 8009, 100)
                Node5 = ClientNode("127.0.0.1", 8011, 2348)
                Node6 = ClientNode("127.0.0.1", 8013, 8434)
                Node7 = ClientNode("127.0.0.1", 8015, 2346)
                Node8 = ClientNode("127.0.0.1", 8017, 9999)
                Node9 = ClientNode("127.0.0.1", 8019, 123)
                Node10 = ClientNode("127.0.0.1", 8021, 542)

                Client_Node_list = [Node1, Node2, Node3,
                                    Node4, Node5, Node6, Node7, Node8]
            else:
                Node1 = ClientNode("127.0.0.1", 8003, 100)
                Node2 = ClientNode("127.0.0.1", 8005, 200)
                Node3 = ClientNode("127.0.0.1", 8007, 50)

                Client_Node_list = [Node1, Node2, Node3]

        broadcastNode = Fsc("127.0.0.1", 8001, "Broadcast",
                            len(Client_Node_list))
        broadcastNode.start()

        for n in Client_Node_list:
            n.start()
            time.sleep(0.05)
    else:
        client_input = int(input("1 for smart contract and 2 for client: "))
        if client_input == 1:
            parties = int(input("How many parties?: "))

            ip = get_ip()

            smartcontract = Fsc(ip, 8001, "Broadcast", parties)
            smartcontract.start()
        else:
            bid = input("Bid of client: ")

            ip = str(get_ip())
            port = get_free_port()
            bc_ip = str(get_ip())

            client = ClientNode(ip, port, int(bid), bc_ip)
            client.start()

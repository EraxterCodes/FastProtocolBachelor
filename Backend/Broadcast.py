from Backend.Nodes.ClientNode import ClientNode
from Backend.Nodes.BroadcastNode import BroadcastNode
import time

class Broadcast:
    def main():
        broadcastNode = BroadcastNode("127.0.0.1", 8001,1)
        Node1 = ClientNode("127.0.0.1",8005,2)
        Node2 = ClientNode("127.0.0.1",8007,3)
        Node3 = ClientNode("127.0.0.1",8003,4)

        nodeList = [Node1, Node2, Node3]

        broadcastNode.start()
        time.sleep(1)

        for n in nodeList:
            n.start()
            time.sleep(0.1)
from Backend.Nodes.ClientNode import ClientNode
from Backend.Nodes.BroadcastNode import BroadcastNode
import time

class Broadcast:
    def main():
        Node1 = ClientNode("127.0.0.1",8003,2)
        Node2 = ClientNode("127.0.0.1",8005,3)
        Node3 = ClientNode("127.0.0.1",8007,4)
        Node4 = ClientNode("127.0.0.1",8009,5)

        nodeList = [Node1, Node2, Node3]

        broadcastNode = BroadcastNode("127.0.0.1", 8001,1, nodeList)
        broadcastNode.start()

        for n in nodeList:
            n.start()
            time.sleep(0.1)
            
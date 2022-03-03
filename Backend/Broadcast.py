from Fastnode import FASTnode as Node
from BroadcastNode import BroadcastNode as bNode
import sys
import time
import socket

broadcastNode = bNode("127.0.0.1", 8001,1)
Node1 = Node("127.0.0.1",8005,2)
Node2 = Node("127.0.0.1",8007,3)
Node3 = Node("127.0.0.1",8003,4)

nodeList = [Node1, Node2, Node3]

broadcastNode.start()
time.sleep(1)

for n in nodeList:
    n.start()
    time.sleep(0.1)



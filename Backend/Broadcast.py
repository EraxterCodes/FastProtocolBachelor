from Fastnode import FASTnode as Node
from BroadcastNode import BroadcastNode as bNode
import sys
import time
import socket

broadcastNode = bNode("127.0.0.1", 8001,1)
Node1 = Node("127.0.0.1",8005,2)

broadcastNode.start()
time.sleep(1)
Node1.start()



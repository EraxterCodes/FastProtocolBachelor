from modules.p2pnetwork import FASTNode
import sys
import time
import socket

node_1 = FASTNode("127.0.0.1", 8001, 1)
node_2 = FASTNode("127.0.0.1", 8005, 2)
node_3 = FASTNode("127.0.0.1", 8003, 3)

nodelist = [node_1,node_2,node_3]

for n in nodelist:
    n.start()

node_1.connect_with_node(node_2.host,node_2.port)
node_1.connect_with_node(node_3.host,node_3.port)
time.sleep(1)


node_1.signature_share_init()   

from Fastnode import FASTnode as Node
import sys
import time
import socket

node_1 = Node("127.0.0.1", 8001,1)
node_2 = Node("127.0.0.1", 8005,2)
node_3 = Node("127.0.0.1", 8003,3)

nodelist = [node_1,node_2,node_3]

for n in nodelist:
    n.start()

node_1.connect_with_node(node_2.host,node_2.port)
node_1.connect_with_node(node_3.host,node_3.port)
time.sleep(1)


node_1.signature_share_init()   

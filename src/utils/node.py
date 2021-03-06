import json
from random import randint
import socket
import time
from ecpy.curves import Point


def utf8len(s):
    return len(s.encode('utf-8'))


def get_broadcast_node(node_list):
    for node in node_list:
        if "Broadcast" in str(node):
            return node


def reset_all_node_msgs(node_list):
    for node in node_list:
        node.reset_node_message()
    time.sleep(0.1)


def get_message(node):
    while node.get_node_message() == "":
        time.sleep(0.01)
    msg = node.get_node_message()
    node.reset_node_message()

    # time.sleep(0.1)

    return json.loads(msg)


def get_all_messages(self, num_messages):
    while (len(self.messages) != num_messages):
        for node in self.all_nodes:
            msg = node.get_node_message()

            if msg != "":
                self.messages.append(msg)
                node.reset_node_message()
            time.sleep(0.01)


def get_all_messages_arr(self, num_messages):
    messages = []

    while (len(messages)) != num_messages:

        for node in self.all_nodes:
            msg = node.get_node_message()
            if msg != "":

                messages.append(json.loads(msg))
                node.reset_node_message()
            time.sleep(0.01)

    return messages


def unpack_commitments_x_arr(self, commits_x):
    for i in range(len(commits_x)):
        index = commits_x[i]["client_index"]

        for j in range(len(commits_x[i]["commit_x"])):
            commit_x = commits_x[i]["commit_x"][str(j)]
            commit = commit_x["commit"]
            big_x = commit_x["big_x"]

            self.commitments[index].append(
                Point(commit["x"], commit["y"], self.pd.cp))
            self.big_xs[index].append(
                Point(big_x["x"], big_x["y"], self.pd.cp))


def unpack_commitments_x(self, commits_x):
    for i in range(len(commits_x)):
        index = commits_x[i]["client_index"]

        for j in range(len(commits_x[i]["commit_x"])):
            commit_x = commits_x[i]["commit_x"][j]
            commit = commit_x["commit"]
            big_x = commit_x["big_x"]

            self.commitments[index].append(
                Point(commit["x"], commit["y"], self.pd.cp))
            self.big_xs[index].append(
                Point(big_x["x"], big_x["y"], self.pd.cp))


def unpack_commitments_x2(self, commits_x):
    for i in range(len(commits_x)):
        index = commits_x[i]["index"]
        commit = Point(commits_x[i]["commit"]["x"],
                       commits_x[i]["commit"]["y"], self.pd.cp)
        big_x = Point(commits_x[i]["big_x"]["x"],
                      commits_x[i]["big_x"]["y"], self.pd.cp)

        self.commitments[index].append(commit)
        self.big_xs[index].append(big_x)


def get_free_port():
    while True:
        port = randint(32768, 61000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not (sock.connect_ex(('127.0.0.1', port)) == 0):
            return port


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))

    ip = s.getsockname()[0]

    s.close()

    return ip

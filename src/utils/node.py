import json
import time
from ecpy.curves import Curve, Point


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

import time


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

    return msg


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
                messages.append(msg)
                node.reset_node_message()
            time.sleep(0.01)

    return messages

import time


def get_broadcast_node(node_list):
    for node in node_list:
        if "Broadcast" in str(node):
            return node


def reset_all_node_msgs(node_list):
    for node in node_list:
        node.reset_node_message()
    time.sleep(0.2)


def get_message(node):
    while node.get_node_message() == "":
        time.sleep(0.01)
    msg = node.get_node_message()
    node.reset_node_message()

    time.sleep(0.1)

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


def get_trimmed_info(self, node_info=str):
    try:
        info_array = []

        remove_braces = node_info.strip("[]")
        temp_info = remove_braces.split(" ")
        for info in temp_info:
            remove_commas = info.strip(',')
            remove_ticks = remove_commas.strip("'")
            index, host, port = remove_ticks.split(":")

            converted_port = int(port)

            if(self.host == host and self.port == converted_port):
                self.index = int(index)

            info_tuple = (host, converted_port)
            info_array.append(info_tuple)

        print(info_array)
        return info_array
    except:
        print(f"{self.id} has crashed when splitting node_info")
        self.sock.close()


def add_index_to_node_info():
    pass

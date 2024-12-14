import tkinter as tk
from acceptor import AcceptorRole
from learner import LearnerRole
from proposer import ProposerRole
from gui import PaxosGUI

class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.cluster = None
        self.is_leader = False
        self.crashed = False
        self.acceptor = AcceptorRole()
        self.learner = LearnerRole()
        self.proposer = ProposerRole()
        self.acceptor.node = self
        self.learner.node = self
        self.proposer.node = self
        self.gui = None
        self.last_action = None

    def set_cluster(self, cluster):
        self.cluster = cluster

    def set_gui(self, gui):
        self.gui = gui

    def gui_log(self, msg):
        if self.gui:
            self.gui.log(msg)

    def update_visual_state(self):
        pass

    def crash(self):
        self.crashed = True
        self.last_action = "Crashed"

    def recover(self):
        self.crashed = False
        self.last_action = "Recovered"

    def start_proposal(self, value):
        if self.is_leader and not self.crashed:
            self.last_action = f"Proposing {value}"
            if self.gui:
                self.gui.update_phase("Prepare")
            self.proposer.start_proposal(value)

    def learned(self, value):
        if self.crashed:
            return
        self.last_action = f"Committed {value}"
        self.gui_log(f"Node {self.id} commits value: {value}")

    def send_message(self, msg_type, target_node, payload, inbound=True):
        if self.gui:
            self.gui.show_message_pass(self.id, target_node.id, msg_type)
        if self.crashed:
            return None
        if target_node.crashed:
            return None

        if msg_type == "PREPARE":
            ballot = payload["ballot"]
            resp = target_node.on_prepare_msg(ballot, self)
            return resp
        elif msg_type == "ACCEPT":
            ballot = payload["ballot"]
            value = payload["value"]
            resp = target_node.on_accept_msg(ballot, value, self)
            return resp
        elif msg_type == "ACCEPTED":
            ballot = payload["ballot"]
            value = payload["value"]
            target_node.on_accepted_msg(ballot, value, self)
            return None
        elif msg_type == "COMMIT":
            ballot = payload["ballot"]
            value = payload["value"]
            target_node.on_commit_msg(ballot, value, self)
            return None
        return None

    def on_prepare_msg(self, ballot, sender):
        if self.crashed:
            return None
        return self.acceptor.on_prepare(ballot)

    def on_accept_msg(self, ballot, value, sender):
        if self.crashed:
            return False
        return self.acceptor.on_accept(ballot, value)

    def on_accepted_msg(self, ballot, value, sender):
        if self.crashed:
            return
        self.learner.on_accepted(ballot, value)

    def on_commit_msg(self, ballot, value, sender):
        if self.crashed:
            return
        self.learned(value)

def run():
    nodes = [Node(i) for i in range(5)]
    for n in nodes:
        n.set_cluster(nodes)
    root = tk.Tk()
    root.title("Paxos Visualization")
    gui = PaxosGUI(root, nodes)
    for n in nodes:
        n.set_gui(gui)
    root.mainloop()

if __name__ == "__main__":
    run()

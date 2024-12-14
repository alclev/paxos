class ProposerRole:
    def __init__(self):
        self.ballot_num = 0
        self.promises = []
        self.accepted = []
        self.prepare_sent = False
        self.accept_sent = False
        self.committed = False
        self.current_value = None

    def start_proposal(self, value):
        if self.node.crashed:
            return
        self.current_value = value
        self.ballot_num += 1
        self.promises = []
        self.accepted = []
        self.prepare_sent = True
        self.accept_sent = False
        self.committed = False
        self.node.gui_log(f"Node {self.node.id} sending PREPARE with ballot {self.ballot_num}")
        for n in self.node.cluster:
            if n != self.node:
                resp = self.node.send_message("PREPARE", n, {"ballot": self.ballot_num})
                if resp is not None:
                    self.promises.append(resp)
        self.node.last_action = f"Received {len(self.promises)} promises"
        self.check_promises()

    def check_promises(self):
        if len(self.promises) >= (len(self.node.cluster)//2)+1:
            chosen_value = self.choose_value_from_promises()
            self.node.gui_log(f"Node {self.node.id} quorum reached on promises. Moving to ACCEPT phase.")
            if self.node.gui:
                self.node.gui.update_phase("Accept")
            self.send_accept_requests(chosen_value)

    def choose_value_from_promises(self):
        highest = None
        val = self.current_value
        for (_, aballot, avalue) in self.promises:
            if aballot is not None:
                if highest is None or aballot > highest:
                    highest = aballot
                    val = avalue
        return val

    def send_accept_requests(self, value):
        if self.node.crashed:
            return
        self.accept_sent = True
        self.node.gui_log(f"Node {self.node.id} sending ACCEPT requests with ballot {self.ballot_num}, value={value}")
        for n in self.node.cluster:
            if n != self.node:
                ok = self.node.send_message("ACCEPT", n, {"ballot": self.ballot_num, "value": value})
                if ok:
                    self.accepted.append(n.id)
                    self.node.send_message("ACCEPTED", n, {"ballot": self.ballot_num, "value": value}, inbound=False)
        self.node.last_action = f"Received {len(self.accepted)} accepts"
        self.check_accepts()

    def check_accepts(self):
        if len(self.accepted) >= (len(self.node.cluster)//2)+1:
            self.committed = True
            self.node.gui_log(f"Node {self.node.id} quorum on ACCEPT. COMMITTING value={self.current_value}")
            if self.node.gui:
                self.node.gui.update_phase("Commit")
            for n in self.node.cluster:
                self.node.send_message("COMMIT", n, {"ballot": self.ballot_num, "value": self.current_value})
            self.node.last_action = f"Committed {self.current_value}"

class AcceptorRole:
    def __init__(self):
        self.promised_ballot = None
        self.accepted_ballot = None
        self.accepted_value = None

    def on_prepare(self, ballot):
        if self.node.crashed:
            return None
        if self.promised_ballot is None or ballot > self.promised_ballot:
            self.promised_ballot = ballot
            self.node.last_action = f"Promised b={ballot}"
            self.node.update_visual_state()
            return (self.node.id, self.accepted_ballot, self.accepted_value)
        self.node.last_action = f"Rejected Prepare b={ballot}"
        self.node.update_visual_state()
        return None

    def on_accept(self, ballot, value):
        if self.node.crashed:
            return False
        if self.promised_ballot is None or ballot >= self.promised_ballot:
            self.promised_ballot = ballot
            self.accepted_ballot = ballot
            self.accepted_value = value
            self.node.last_action = f"Accepted b={ballot}"
            self.node.update_visual_state()
            return True
        self.node.last_action = f"Rejected Accept b={ballot}"
        self.node.update_visual_state()
        return False

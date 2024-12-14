class LearnerRole:
    def __init__(self):
        self.accepted_count = {}
        self.learned_value = None

    def on_accepted(self, ballot, value):
        if self.node.crashed:
            return
        if self.learned_value is not None:
            return
        key = (ballot, value)
        if key not in self.accepted_count:
            self.accepted_count[key] = set()
        self.accepted_count[key].add(self.node.id)
        quorum = (len(self.node.cluster)//2) + 1
        count = len(self.accepted_count[key])
        self.node.last_action = f"Learner sees {count} accepts"
        self.node.update_visual_state()
        if count >= quorum:
            self.learned_value = value
            for n in self.node.cluster:
                n.learned(value)

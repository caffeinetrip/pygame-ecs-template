from util.framework.core.component import Component


class RunComponent(Component):
    def __init__(self):
        super().__init__()
        self.run = None
        self.stats = {}

    def create_new_run(self):
        self.run = {
            "id": id(self),
            "turn": 0,
            "score": 0,
            "state": "active"
        }

    def end_run(self, victory=False):
        if self.run:
            self.run["state"] = "victory" if victory else "defeat"

    def increment_turn(self):
        if self.run:
            self.run["turn"] += 1

    def add_score(self, points):
        if self.run:
            self.run["score"] += points
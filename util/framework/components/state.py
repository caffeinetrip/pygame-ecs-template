from util.framework.core.component import Component

class State:
    def __init__(self):
        self.world = None

    def init(self, world):
        self.world = world

    def enter(self, prev_state=None):
        pass

    def exit(self, next_state=None):
        pass

    def update(self, dt):
        pass

    def handle_input(self, input_event):
        pass


class StateComponent(Component):
    def __init__(self):
        super().__init__()
        self.states = {}
        self.current_state = None
        self.previous_state = None

    def add_state(self, name, state):
        self.states[name] = state
        state.init(self.e)
        return state

    def get_state(self, name):
        return self.states.get(name)

    def change_state(self, name):
        if name not in self.states:
            raise ValueError(f"State '{name}' does not exist")

        next_state = self.states[name]

        if self.current_state:
            self.current_state.exit(next_state)

        self.previous_state = self.current_state
        self.current_state = next_state

        self.current_state.enter(self.previous_state)

    def update(self, dt):
        if self.current_state:
            self.current_state.update(dt)
from util.framework.core.system import System
from util.framework.components.state import StateComponent


class StateSystem(System):
    def __init__(self):
        super().__init__()
        self.priority = -5

    def update(self, dt):
        for entity in self.e.get_entities_with(StateComponent):
            state_comp = entity.get_component(StateComponent)
            state_comp.update(dt)
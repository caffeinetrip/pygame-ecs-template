from util.framework.core.system import System
from util.framework.components.interactor import InteractorComponent


class InteractorSystem(System):
    def __init__(self):
        super().__init__()
        self.priority = -10

    def update(self, dt):
        for entity in self.e.get_entities_with(InteractorComponent):
            interactor_comp = entity.get_component(InteractorComponent)
            interactor_comp.update(dt)
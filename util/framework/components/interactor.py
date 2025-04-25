from util.framework.core.component import Component


class Interactor:
    def __init__(self):
        self.world = None
        self.active = True

    def init(self, world):
        self.world = world

    def update(self, dt):
        pass

    def handle_input(self, input_event):
        pass


class InteractorComponent(Component):
    def __init__(self):
        super().__init__()
        self.interactors = {}

    def add_interactor(self, name, interactor):
        self.interactors[name] = interactor
        interactor.init(self.e)
        return interactor

    def get_interactor(self, name):
        return self.interactors.get(name)

    def update(self, dt):
        for interactor in self.interactors.values():
            if interactor.active:
                interactor.update(dt)
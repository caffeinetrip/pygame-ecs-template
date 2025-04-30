class GlobalManager:
    def __init__(self):
        self._components = {}
        self._interactors = {}
        self._instances = {}
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        self._initialized = True

    def register(self, name, instance):
        self._instances[name] = instance
        setattr(self, name, instance)

    def register_component(self, name, component):
        self._components[name] = component
        setattr(self, name, component)

    def register_interactor(self, name, interactor):
        self._interactors[name] = interactor
        setattr(self, name, interactor)

    def get(self, name):
        return self._instances.get(name)


G = GlobalManager()

__all__ = ['G']
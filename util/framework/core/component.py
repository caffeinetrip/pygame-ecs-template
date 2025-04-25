class Component:
    _dynamic_component = True

    def __init__(self, entity=None):
        self.entity = entity
        self.e = None

    def update(self):
        pass

    def on_attach(self, entity):
        self.entity = entity
        self.e = entity.e
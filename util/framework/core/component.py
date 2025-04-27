class Component:
    _dynamic_component = True

    def __init__(self, entity=None):
        self.entity = entity
        self.e = None
        self._enabled = True
        self._initialized = False
        self._started = False

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self._enabled != value:
            self._enabled = value
            if value:
                self.on_enable()
            else:
                self.on_disable()

    def update(self, dt=None):
        pass

    def awake(self):
        self._initialized = True

    def start(self):
        self._started = True

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def on_destroy(self):
        pass

    def on_attach(self, entity):
        self.entity = entity
        self.e = entity

        if entity and entity.active and not self._initialized:
            self.awake()

        return self

    def on_detach(self):
        old_entity = self.entity
        self.entity = None
        self.e = None
        return old_entity

    def get_component(self, component_type):
        if self.entity:
            return self.entity.get_component(component_type)
        return None

    def get_components(self, component_type):
        if self.entity:
            return self.entity.get_components(component_type)
        return []

    def add_component(self, component_type, *args, **kwargs):
        if self.entity:
            return self.entity.add_component(component_type, *args, **kwargs)
        return None

    def remove_component(self, component):
        if self.entity:
            return self.entity.remove_component(component)
        return False

    def __str__(self):
        return f"{self.__class__.__name__}(enabled={self._enabled})"
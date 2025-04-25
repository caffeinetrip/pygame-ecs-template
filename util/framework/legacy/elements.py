class ElementSingleton:
    _dynamic_component = True

    def __init__(self, custom_id=None):
        from util.framework import world
        self.e = world
        self._name = self.__class__.__name__ if not custom_id else custom_id
        self._singleton = True
        self.entity = world.create_singleton(self._name)
        self.entity.add_component(self.__class__)

    def update(self):
        pass

    def delete(self):
        from util.framework import world
        self.entity.delete()


class Element:
    _dynamic_component = True

    def __init__(self, custom_id=None, singleton=False, register=False):
        from util.framework import world
        self.e = world
        self._name = self.__class__.__name__ if not custom_id else custom_id
        self._singleton = singleton

        if register:
            self.entity = world.create_entity(self._name, singleton)
            self.entity.add_component(self.__class__)

    def update(self):
        pass

    def delete(self):
        if hasattr(self, 'entity'):
            self.entity.delete()
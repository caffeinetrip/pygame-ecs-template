class Entity:
    def __init__(self, entity_id=None, singleton=False):
        self.id = entity_id if entity_id else id(self)
        self._singleton = singleton
        self.components = {}
        self.e = None
        self.tags = set()

    def add_component(self, component_class, *args, **kwargs):
        component = component_class(*args, **kwargs)
        component.on_attach(self)
        component_name = component_class.__name__
        self.components[component_name] = component

        if self.e:
            self.e._index_component(self, component_class)

        return component

    def get_component(self, component_class):
        component_name = component_class.__name__
        return self.components.get(component_name)

    def has_component(self, component_class):
        component_name = component_class.__name__
        return component_name in self.components

    def remove_component(self, component_class):
        component_name = component_class.__name__
        if component_name in self.components:
            if self.e:
                self.e._unindex_component(self, component_class)
            del self.components[component_name]

    def delete(self):
        if self.e:
            self.e.delete_entity(self)

    def add_tag(self, tag):
        self.tags.add(tag)
        if self.e:
            self.e._index_tag(self, tag)

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)
            if self.e:
                self.e._unindex_tag(self, tag)

    def has_tag(self, tag):
        return tag in self.tags
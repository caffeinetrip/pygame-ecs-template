class Entity:

    def __init__(self, entity_id=None, singleton=False, name=None, active=True):
        self.id = entity_id if entity_id else id(self)
        self.name = name if name else f"Entity_{self.id}"
        self._singleton = singleton
        self.components = {}
        self.e = self
        self._parent = None
        self._children = []
        self.tags = set()
        self._active = active
        self._marked_for_deletion = False
        self._component_cache = {}

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        if self._active != value:
            self._active = value

            for component in self.components.values():
                if hasattr(component, 'enabled'):
                    component.enabled = value

            for child in self._children:
                child.active = value

    def add_component(self, component_class, *args, **kwargs):
        if not isinstance(component_class, type):
            component = component_class
            component_class = component.__class__
        else:
            component = component_class(*args, **kwargs)

        component.on_attach(self)
        component_name = component_class.__name__

        if component_name in self.components and not getattr(component_class, '_dynamic_component', False):
            self.remove_component(component_class)

        self.components[component_name] = component

        self._component_cache = {}

        if self.e and hasattr(self.e, '_index_component'):
            self.e._index_component(self, component_class)

        if self._active:
            if hasattr(component, 'awake') and not getattr(component, '_initialized', False):
                component.awake()

            if hasattr(component, 'start') and not getattr(component, '_started', False):
                component.start()

        return component

    def get_component(self, component_type):
        if isinstance(component_type, str):
            component_name = component_type
        else:
            component_name = component_type.__name__

        if component_name in self._component_cache:
            return self._component_cache[component_name]

        component = self.components.get(component_name)
        self._component_cache[component_name] = component
        return component

    def get_components(self, component_type=None):
        if component_type is None:
            return list(self.components.values())

        if isinstance(component_type, str):
            component_name = component_type
            return [c for c in self.components.values() if c.__class__.__name__ == component_name]
        else:
            return [c for c in self.components.values() if isinstance(c, component_type)]

    def has_component(self, component_type):
        if isinstance(component_type, str):
            component_name = component_type
        else:
            component_name = component_type.__name__

        return component_name in self.components

    def remove_component(self, component_type):
        if not isinstance(component_type, type) and not isinstance(component_type, str):
            component = component_type
            component_type = component.__class__
            component_name = component_type.__name__

            if self.components.get(component_name) != component:
                return False
        else:
            if isinstance(component_type, str):
                component_name = component_type
            else:
                component_name = component_type.__name__

            if component_name not in self.components:
                return False

            component = self.components[component_name]

        if hasattr(component, 'on_destroy'):
            component.on_destroy()

        if hasattr(component, 'on_detach'):
            component.on_detach()

        if self.e and hasattr(self.e, '_unindex_component'):
            self.e._unindex_component(self, component_type)

        del self.components[component_name]

        self._component_cache = {}

        return True

    def delete(self):
        self._marked_for_deletion = True

        for component in list(self.components.values()):
            self.remove_component(component)

        for child in list(self._children):
            child.delete()

        if self._parent:
            self._parent.remove_child(self)

        if self.e and hasattr(self.e, 'delete_entity') and self.e != self:
            self.e.delete_entity(self)

    def add_tag(self, tag):
        self.tags.add(tag)
        if self.e and hasattr(self.e, '_index_tag') and self.e != self:
            self.e._index_tag(self, tag)

        return self

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)
            if self.e and hasattr(self.e, '_unindex_tag') and self.e != self:
                self.e._unindex_tag(self, tag)

        return self

    def has_tag(self, tag):
        return tag in self.tags

    def add_child(self, entity):
        if entity._parent:
            entity._parent.remove_child(entity)

        entity._parent = self
        self._children.append(entity)

        if self.e and self.e != self:
            entity.e = self.e

        return entity

    def remove_child(self, entity):
        if entity in self._children:
            entity._parent = None
            self._children.remove(entity)

            if entity.e == self.e and self.e != self:
                entity.e = entity

            return True
        return False

    def get_children(self):
        return list(self._children)

    def find_child_by_name(self, name):
        for child in self._children:
            if child.name == name:
                return child
        return None

    def find_children_with_tag(self, tag):
        return [child for child in self._children if child.has_tag(tag)]

    def get_component_in_children(self, component_type, include_inactive=False):
        component = self.get_component(component_type)
        if component:
            return component

        for child in self._children:
            if not child.active and not include_inactive:
                continue

            component = child.get_component_in_children(component_type, include_inactive)
            if component:
                return component

        return None

    def get_components_in_children(self, component_type, include_inactive=False):
        result = self.get_components(component_type)

        for child in self._children:
            if not child.active and not include_inactive:
                continue

            child_components = child.get_components_in_children(component_type, include_inactive)
            result.extend(child_components)

        return result

    def update(self, dt=None):
        if not self._active:
            return

        for component in list(self.components.values()):
            if hasattr(component, 'enabled') and component.enabled and hasattr(component, 'update'):
                component.update(dt)

        for child in list(self._children):
            if child.active:
                child.update(dt)

    def late_update(self, dt=None):
        if not self._active:
            return

        for component in list(self.components.values()):
            if hasattr(component, 'enabled') and component.enabled and hasattr(component, 'late_update'):
                component.late_update(dt)

        for child in list(self._children):
            if child.active:
                child.late_update(dt)

    def broadcast_message(self, message, *args, **kwargs):
        results = []

        for component in list(self.components.values()):
            if hasattr(component, message) and callable(getattr(component, message)):
                method = getattr(component, message)
                results.append(method(*args, **kwargs))

        return results

    def __str__(self):
        component_str = ", ".join(self.components.keys())
        return f"{self.name}(id={self.id}, active={self._active}, components=[{component_str}])"
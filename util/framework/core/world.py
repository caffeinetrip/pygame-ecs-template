import asyncio
from typing import List, Dict, Any, Type, Set

class World:
    def __init__(self):
        self.entities = []
        self.singleton_entities = {}
        self.systems = []
        self._entity_groups = {}
        self._tag_groups = {}
        self._systems_by_priority = {}

    def register_entity(self, entity):
        entity.e = self

        if entity._singleton:
            self.singleton_entities[entity.id] = entity
        else:
            self.entities.append(entity)

        for component_name, component in entity.components.items():
            component_class = component.__class__
            self._index_component(entity, component_class)

        for tag in entity.tags:
            self._index_tag(entity, tag)

        return entity

    def _index_component(self, entity, component_class):
        component_name = component_class.__name__
        if component_name not in self._entity_groups:
            self._entity_groups[component_name] = []
        if entity not in self._entity_groups[component_name]:
            self._entity_groups[component_name].append(entity)

    def _unindex_component(self, entity, component_class):
        component_name = component_class.__name__
        if component_name in self._entity_groups and entity in self._entity_groups[component_name]:
            self._entity_groups[component_name].remove(entity)

    def _index_tag(self, entity, tag):
        if tag not in self._tag_groups:
            self._tag_groups[tag] = []
        if entity not in self._tag_groups[tag]:
            self._tag_groups[tag].append(entity)

    def _unindex_tag(self, entity, tag):
        if tag in self._tag_groups and entity in self._tag_groups[tag]:
            self._tag_groups[tag].remove(entity)

    def delete_entity(self, entity):
        if entity._singleton:
            if entity.id in self.singleton_entities:
                del self.singleton_entities[entity.id]
        else:
            if entity in self.entities:
                self.entities.remove(entity)

        for component_class in [comp.__class__ for comp in entity.components.values()]:
            self._unindex_component(entity, component_class)

        for tag in entity.tags:
            self._unindex_tag(entity, tag)

        entity.e = None

    def add_system(self, system, priority=0):
        system.e = self
        system.priority = priority
        self.systems.append(system)

        if priority not in self._systems_by_priority:
            self._systems_by_priority[priority] = []
        self._systems_by_priority[priority].append(system)

        return system

    def remove_system(self, system):
        if system in self.systems:
            self.systems.remove(system)
            priority = system.priority
            if priority in self._systems_by_priority and system in self._systems_by_priority[priority]:
                self._systems_by_priority[priority].remove(system)
            system.e = None

    async def initialize_systems(self):
        for system in self.systems:
            await system.start()

    def update(self, dt):
        priorities = sorted(self._systems_by_priority.keys())

        for priority in priorities:
            for system in self._systems_by_priority[priority]:
                if system.active:
                    system.update(dt)

    def __getitem__(self, key):
        return self.singleton_entities.get(key)

    def get_entities_with(self, component_class):
        component_name = component_class.__name__
        if component_name in self._entity_groups:
            return self._entity_groups[component_name]
        return []

    def get_entities_with_tag(self, tag):
        if tag in self._tag_groups:
            return self._tag_groups[tag]
        return []

    def get_entities_with_all(self, *component_classes):
        if not component_classes:
            return []

        entities = set(self.get_entities_with(component_classes[0]))

        for component_class in component_classes[1:]:
            entities &= set(self.get_entities_with(component_class))

        return list(entities)

    def create_entity(self, entity_id=None, singleton=False):
        from util.framework.core.entity import Entity
        entity = Entity(entity_id, singleton)
        return self.register_entity(entity)

    def create_singleton(self, entity_id):
        return self.create_entity(entity_id, singleton=True)
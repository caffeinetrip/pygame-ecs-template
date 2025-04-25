import pygame
from util.framework import world
from util.framework.components.camera import CameraComponent


class Camera:
    def __init__(self, size, pos=(0, 0), slowness=1, tilemap_lock=None):
        from util.framework import world
        self.e = world
        self._name = "Camera"
        self._singleton = True

        self.entity = world.create_singleton(self._name)
        self.camera_component = self.entity.add_component(CameraComponent, size, pos, slowness, tilemap_lock)

    @property
    def size(self):
        return self.camera_component.size

    @size.setter
    def size(self, value):
        self.camera_component.size = value

    @property
    def pos(self):
        return self.camera_component.pos

    @pos.setter
    def pos(self, value):
        self.camera_component.pos = value

    @property
    def int_pos(self):
        return self.camera_component.int_pos

    @int_pos.setter
    def int_pos(self, value):
        self.camera_component.int_pos = value

    @property
    def target_entity(self):
        return self.camera_component.target_entity

    @target_entity.setter
    def target_entity(self, value):
        self.camera_component.target_entity = value

    @property
    def target_pos(self):
        return self.camera_component.target_pos

    @target_pos.setter
    def target_pos(self, value):
        self.camera_component.target_pos = value

    @property
    def slowness(self):
        return self.camera_component.slowness

    @slowness.setter
    def slowness(self, value):
        self.camera_component.slowness = value

    @property
    def tilemap_lock(self):
        return self.camera_component.tilemap_lock

    @tilemap_lock.setter
    def tilemap_lock(self, value):
        self.camera_component.tilemap_lock = value

    @property
    def rect(self):
        return self.camera_component.rect

    @rect.setter
    def rect(self, value):
        self.camera_component.rect = value

    @property
    def target(self):
        return self.camera_component.target

    @property
    def center(self):
        return self.camera_component.center

    def set_target(self, target):
        self.camera_component.set_target(target)

    def __iter__(self):
        return self.camera_component.__iter__()

    def __getitem__(self, item):
        return self.camera_component.__getitem__(item)

    def move(self, movement):
        self.camera_component.move(movement)

    def update(self):
        pass

    def delete(self):
        self.entity.delete()
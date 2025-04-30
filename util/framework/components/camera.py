import pygame
from util.framework.globals import G
from util.framework.core.component import Component


class CameraComponent(Component):
    def __init__(self, size, pos=(0, 0), slowness=1, tilemap_lock=None):
        super().__init__()
        self.size = size
        self.slowness = slowness
        self.pos = list(pos)
        self.int_pos = (int(self.pos[0]), int(self.pos[1]))
        self.target_entity = None
        self.target_pos = None
        self.tilemap_lock = tilemap_lock
        self.rect = pygame.Rect(self.pos[0] - 20, self.pos[1] - 20, self.size[0] + 40, self.size[1] + 40)

    @property
    def target(self):
        if self.target_entity:
            return (self.target_entity.center[0] - self.size[0] // 2, self.target_entity.center[1] - self.size[1] // 2)
        elif self.target_pos:
            return (self.target_pos[0] - self.size[0] // 2, self.target_pos[1] - self.size[1] // 2)
        return None

    @property
    def center(self):
        return (self.pos[0] + self.size[0] / 2, self.pos[1] + self.size[1] / 2)

    def set_target(self, target):
        if hasattr(target, 'center'):
            self.target_entity = target
            self.target_pos = None
        elif target:
            self.target_pos = tuple(target)
            self.target_entity = None
        else:
            self.target_pos = None
            self.target_entity = None

    def __iter__(self):
        for v in self.int_pos:
            yield v

    def __getitem__(self, item):
        return self.int_pos[item]

    def move(self, movement):
        self.pos[0] += movement[0]
        self.pos[1] += movement[1]

    def update(self):
        target = self.target
        if target:
            if self.tilemap_lock:
                target_x = max(0, min(target[0], self.tilemap_lock.width * self.tilemap_lock.tile_size - self.size[0]))
                target_y = max(0, min(target[1], self.tilemap_lock.height * self.tilemap_lock.tile_size - self.size[1]))
                target = (target_x, target_y)

            self.pos[0] = smooth_approach(self.pos[0], target[0], self.slowness)
            self.pos[1] = smooth_approach(self.pos[1], target[1], self.slowness)

        self.int_pos = (int(self.pos[0]), int(self.pos[1]))
        self.rect = pygame.Rect(self.pos[0] - 20, self.pos[1] - 20, self.size[0] + 40, self.size[1] + 40)


def smooth_approach(current, target, slowness=10, min_speed=0.1):
    if current == target:
        return current

    diff = target - current
    movement = diff / slowness

    if abs(movement) < min_speed and diff != 0:
        movement = min_speed if diff > 0 else -min_speed

    if abs(movement) > abs(diff):
        return target

    return current + movement
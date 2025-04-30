import pygame
from util.framework.components.camera import CameraComponent
from util.framework.utils.gfx import smooth_approach


class CameraSystem:
    def __init__(self):
        self.e = None
        self.active = True

        self.priority = 5

    def update(self, dt):
        for entity in self.e.get_entities_with(CameraComponent):
            camera = entity.get_component(CameraComponent)

            camera.rect = pygame.Rect(camera.pos[0] - 30, camera.pos[1] - 30,
                                      camera.size[0] + 60, camera.size[1] + 60)
            target = camera.target
            if target:
                camera.pos[0] = smooth_approach(camera.pos[0], target[0], slowness=camera.slowness)
                camera.pos[1] = smooth_approach(camera.pos[1], target[1], slowness=camera.slowness)

                if camera.tilemap_lock:
                    map_width = camera.tilemap_lock.dimensions[0] * camera.tilemap_lock.tile_size[0]
                    map_height = camera.tilemap_lock.dimensions[1] * camera.tilemap_lock.tile_size[1]

                    camera.pos[0] = max(0, min(map_width - camera.size[0], camera.pos[0]))
                    camera.pos[1] = max(0, min(map_height - camera.size[1], camera.pos[1]))

            camera.int_pos = (int(camera.pos[0]), int(camera.pos[1]))
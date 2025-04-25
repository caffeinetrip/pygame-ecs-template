from util.framework.components.camera import CameraComponent

class Camera:
    def __init__(self, size=(800, 600), pos=(0, 0), slowness=5):
        from util.framework import world
        self.e = world
        self._name = "Camera"
        self._singleton = True

        self.entity = world.create_singleton(self._name)
        self.camera_component = self.entity.add_component(CameraComponent, size, pos, slowness)

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
    def target(self):
        return self.camera_component.target

    @target.setter
    def target(self, value):
        self.camera_component.target = value

    @property
    def slowness(self):
        return self.camera_component.slowness

    @slowness.setter
    def slowness(self, value):
        self.camera_component.slowness = value

    def update(self):
        self.camera_component.update()

    def follow(self, target_pos):
        self.camera_component.follow(target_pos)

    def world_to_screen(self, world_pos):
        return self.camera_component.world_to_screen(world_pos)

    def screen_to_world(self, screen_pos):
        return self.camera_component.screen_to_world(screen_pos)

    def delete(self):
        self.entity.delete()
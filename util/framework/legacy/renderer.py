from util.framework import world
from util.framework.components.renderer import RenderComponent


class Renderer:
    def __init__(self):
        from util.framework import world
        self.e = world
        self._name = "Renderer"
        self._singleton = True

        self.entity = world.create_singleton(self._name)
        self.renderer_component = self.entity.add_component(RenderComponent)

    def add_surface(self, name, surface):
        self.renderer_component.add_surface(name, surface)

    def set_render_order(self, order):
        self.renderer_component.set_render_order(order)

    def get_surface(self, name):
        return self.renderer_component.get_surface(name)

    def cycle(self, surfaces={}):
        self.renderer_component.cycle(surfaces)

    def delete(self):
        self.entity.delete()
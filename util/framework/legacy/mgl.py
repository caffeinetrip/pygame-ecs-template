from array import array
import moderngl
import pygame
from util.framework import world
from util.framework.components.mgl import MGLComponent, RenderObject as MGLRenderObject


class RenderObject:
    def __init__(self, frag_shader, vert_shader=None, default_ro=False, vao_args=['2f 2f', 'vert', 'texcoord'],
                 buffer=None):
        from util.framework import world
        self.e = world
        self._name = f"RenderObject_{id(self)}"
        self._singleton = False

        self.mgl_entity = world["MGL"]
        if not self.mgl_entity:
            self.mgl_entity = world.create_singleton("MGL")
            self.mgl_entity.add_component(MGLComponent)

        self.mgl_component = self.mgl_entity.get_component(MGLComponent)

        if default_ro:
            self.render_object = self.mgl_component.default_ro()
        else:
            if isinstance(frag_shader, str) and not frag_shader.startswith("#version"):
                self.render_object = self.mgl_component.render_object(frag_shader, vert_shader, vao_args, buffer)
            else:
                if not vert_shader:
                    vert_shader = self.mgl_component.default_vert
                self.render_object = MGLRenderObject(frag_shader, vert_shader, default_ro, vao_args, buffer,
                                                     self.mgl_component)

    @property
    def default(self):
        return self.render_object.default

    @property
    def frag_raw(self):
        return self.render_object.frag_raw

    @property
    def vert_raw(self):
        return self.render_object.vert_raw

    @property
    def vao_args(self):
        return self.render_object.vao_args

    @property
    def program(self):
        return self.render_object.program

    @property
    def vao(self):
        return self.render_object.vao

    @property
    def temp_textures(self):
        return self.render_object.temp_textures

    @property
    def debug(self):
        return self.render_object.debug

    @debug.setter
    def debug(self, value):
        self.render_object.debug = value

    def update(self, uniforms={}):
        return self.render_object.update(uniforms)

    def parse_uniforms(self, uniforms):
        return self.render_object.parse_uniforms(uniforms)

    def render(self, dest=None, uniforms={}):
        return self.render_object.render(dest, uniforms)


class MGL:
    def __init__(self):
        from util.framework import world
        self.e = world
        self._name = "MGL"
        self._singleton = True

        self.entity = world.create_singleton(self._name)
        self.mgl_component = self.entity.add_component(MGLComponent)

    @property
    def ctx(self):
        return self.mgl_component.ctx

    @property
    def quad_buffer(self):
        return self.mgl_component.quad_buffer

    @property
    def quad_buffer_notex(self):
        return self.mgl_component.quad_buffer_notex

    @property
    def default_vert(self):
        return self.mgl_component.default_vert

    @property
    def default_frag(self):
        return self.mgl_component.default_frag

    @staticmethod
    def render_object(frag_path, vert_shader=None, vao_args=['2f 2f', 'vert', 'texcoord'], buffer=None):
        return RenderObject(frag_path, vert_shader, False, vao_args, buffer)

    def default_ro(self):
        render_object = self.mgl_component.default_ro()
        return RenderObject(render_object.frag_raw, render_object.vert_raw, True, render_object.vao_args)

    def pg2tx(self, surf):
        return self.mgl_component.pg2tx(surf)

    def pg2tx_update(self, tex, surf):
        return self.mgl_component.pg2tx_update(tex, surf)

    def delete(self):
        self.entity.delete()

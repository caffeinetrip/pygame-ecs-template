from array import array
import moderngl
import pygame
from util.framework.core.component import Component
from util.framework.utils.io import read_f

default_vert_shader = '''
#version 330
in vec2 vert;
in vec2 texcoord;
out vec2 uv;
void main() {
  uv = texcoord;
  gl_Position = vec4(vert, 0.0, 1.0);
}
'''

default_frag_shader = '''
#version 330
uniform sampler2D surface;
out vec4 f_color;
in vec2 uv;
void main() {
  f_color = vec4(texture(surface, uv).rgb, 1.0);
}
'''


class RenderObject:
    def __init__(self, frag_shader, vert_shader=None, default_ro=False, vao_args=['2f 2f', 'vert', 'texcoord'],
                 buffer=None, mgl_component=None):
        self.e = mgl_component.entity.e
        self.mgl = mgl_component

        if not vert_shader:
            vert_shader = self.mgl.default_vert

        self.default = default_ro
        self.frag_raw = frag_shader
        self.vert_raw = vert_shader
        self.vao_args = vao_args

        try:
            self.program = self.mgl.ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
        except Exception as e:
            print(f"Create shader programm error: {e}")
            self.program = self.mgl.ctx.program(
                vertex_shader=self.mgl.default_vert,
                fragment_shader=self.mgl.default_frag
            )

        if not buffer:
            buffer = self.mgl.quad_buffer

        self.vao = self.mgl.ctx.vertex_array(self.program, [(buffer, *vao_args)])
        self.temp_textures = []
        self.textures = {}
        self.debug = False

    def update(self, uniforms={}):
        tex_id = 0
        uniform_list = list(self.program)

        for uniform in uniforms:
            if uniform in uniform_list:
                if isinstance(uniforms[uniform], moderngl.Texture):
                    try:
                        uniforms[uniform].use(tex_id)
                        self.program[uniform].value = tex_id
                        tex_id += 1
                    except AttributeError as e:
                        print(f"Tex error {uniform}: {e}")
                else:
                    try:
                        self.program[uniform].value = uniforms[uniform]
                    except Exception as e:
                        print(f"uniform init error: {uniform}: {e}")

    def parse_uniforms(self, uniforms):
        processed_uniforms = {}

        for name, value in uniforms.items():
            if isinstance(value, pygame.Surface):
                try:
                    if id(value) in self.textures:
                        tex = self.textures[id(value)]
                        self.mgl.pg2tx_update(tex, value)
                    else:
                        tex = self.mgl.pg2tx(value)
                        self.textures[id(value)] = tex

                    processed_uniforms[name] = tex
                    self.temp_textures.append(tex)
                except Exception as e:
                    print(f"Error with create tex for {name}: {e}")
            else:
                processed_uniforms[name] = value

        return processed_uniforms

    def render(self, dest=None, uniforms={}):
        try:
            if not dest:
                dest = self.mgl.ctx.screen

            dest.use()
            processed_uniforms = self.parse_uniforms(uniforms)
            self.update(uniforms=processed_uniforms)
            self.vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception as e:
            print(f"Error with rendering: {e}")
        finally:
            for tex in self.temp_textures:
                try:
                    if tex and not tex.mglo.released:
                        tex.release()
                except AttributeError:
                    pass
            self.temp_textures = []


class MGLComponent(Component):
    def __init__(self):
        super().__init__()

        try:
            self.ctx = moderngl.create_context(require=330)

            self.quad_buffer = self.ctx.buffer(data=array('f', [
                -1.0, 1.0, 0.0, 0.0,
                -1.0, -1.0, 0.0, 1.0,
                1.0, 1.0, 1.0, 0.0,
                1.0, -1.0, 1.0, 1.0,
            ]))

            self.quad_buffer_notex = self.ctx.buffer(data=array('f', [
                -1.0, 1.0,
                -1.0, -1.0,
                1.0, 1.0,
                1.0, -1.0,
            ]))

            self.default_vert = default_vert_shader
            self.default_frag = default_frag_shader
            self.initialized = True

        except Exception as e:
            print(f"Error with ModernGL initialization: {e}")
            self.initialized = False

    def default_ro(self):
        if not self.initialized:
            print("ModernGL not initialized!")
            return None
        return RenderObject(self.default_frag, default_ro=True, mgl_component=self)

    def render_object(self, frag_path, vert_shader=None, vao_args=['2f 2f', 'vert', 'texcoord'], buffer=None):
        if not self.initialized:
            print("ModernGL not initialized!")
            return None

        try:
            frag_shader = read_f(frag_path)
            if vert_shader:
                vert_shader = read_f(vert_shader)
            return RenderObject(frag_shader, vert_shader=vert_shader, vao_args=vao_args, buffer=buffer,
                                mgl_component=self)
        except Exception as e:
            print(f"Create render_object error: {e}")
            return self.default_ro()

    def pg2tx(self, surf):
        if not self.initialized:
            return None

        try:
            channels = 4
            new_tex = self.ctx.texture(surf.get_size(), channels)
            new_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            new_tex.swizzle = 'BGRA'
            new_tex.write(surf.get_view('1'))
            return new_tex
        except Exception as e:
            print(f"Create tex error: {e}")
            return None

    def pg2tx_update(self, tex, surf):
        if not self.initialized:
            return None

        try:
            if tex and not getattr(tex.mglo, 'released', False):
                tex.write(surf.get_view('1'))
                return tex
        except Exception as e:
            print(f"Update Tex error: {e}")
        return None
import time
import pygame
import asyncio
from util.framework.core.component import Component

class WindowComponent(Component):
    def __init__(self, dimensions=(640, 480), caption='pygpen window', flags=0, fps_cap=60, dt_cap=1, opengl=False,
                 frag_path=None):
        super().__init__()
        self.opengl = opengl
        self.frag_path = frag_path
        self.dimensions = dimensions
        self.flags = flags
        if self.opengl:
            self.flags = self.flags | pygame.DOUBLEBUF | pygame.OPENGL
        self.fps_cap = fps_cap
        self.dt_cap = dt_cap
        self.background_color = (0, 0, 0)
        self.time = time.time()
        self.start_time = time.time()
        self.runtime_ = self.time - self.start_time
        self.frames = 0
        self.frame_log = []

        pygame.init()
        pygame.display.set_caption(caption)
        self.screen = pygame.display.set_mode(self.dimensions, self.flags)
        self.clock = pygame.time.Clock()

        self.last_frame = time.time()
        self.dt = 0.1
        self.tremor = 0
        self.fight = False

        self.input_comp = None

        self.trans_val = 0

        self.transition = 0.0
        self.transition_speed = 0.7
        self.transitioning = False

        self.e_transition = 1.0
        self.e_transitioning = False

        self.open = True
        self.noise_gain = 1

        self.render_object = None
        self.initialized_opengl = False

        self.debug = False

    def initialize_opengl(self):
        if self.opengl and not self.initialized_opengl:
            from util.framework.components.mgl import MGLComponent

            mgl_entity = self.e["MGL"]
            if not mgl_entity:
                mgl_entity = self.e.create_singleton("MGL")
                mgl_entity.add_component(MGLComponent)

            mgl = mgl_entity.get_component(MGLComponent)

            if mgl and mgl.initialized:
                if not self.frag_path:
                    self.render_object = mgl.default_ro()
                else:
                    self.render_object = mgl.render_object(self.frag_path)

                self.initialized_opengl = True
                return True
            else:
                print("opengl init failed")
                return False
        return False

    @property
    def fps(self):
        return len(self.frame_log) / sum(self.frame_log) if self.frame_log else 0

    def start_transition(self, alternative=False):
        if not alternative:
            if self.open:
                self.transition = 0.0
            else:
                self.transition = 1.0

            self.transitioning = True
        else:
            if self.open:
                self.e_transition = 0.0
            else:
                self.e_transition = 1.0

            self.e_transitioning = True

    def update_transition(self, alternative=False):
        if self.transitioning or self.e_transitioning:
            self.trans_val += self.dt * self.transition_speed * (1 if self.open else -1)

            if not alternative:
                self.transition = self.trans_val
                if self.open:
                    if self.transition >= 1.0:
                        self.transition = 1.0
                        self.transitioning = False
                else:
                    if self.transition <= 0.0:
                        self.transition = 0.0
                        self.transitioning = False
            else:
                self.e_transition = self.trans_val
                if self.open:
                    if self.e_transition >= 1.0:
                        self.e_transition = 1.0
                        self.e_transitioning = False
                else:
                    if self.e_transition <= 0.0:
                        self.e_transition = 0.0
                        self.e_transitioning = False

    def cycle(self, uniforms):
        if self.debug:
            print(f"Window.cycle: OpenGL={self.opengl}, have surfs: {list(uniforms.keys())}")

        if self.opengl:
            if not self.initialized_opengl:
                success = self.initialize_opengl()
                if not success and self.debug:
                    print("init OpenGL error!")

            if self.render_object:
                if self.debug:
                    print(f"Render with ModernGL render_object")

                shader_uniforms = uniforms.copy()
                shader_uniforms['time'] = self.dt
                shader_uniforms['tremor'] = self.tremor
                shader_uniforms['fight'] = self.fight
                shader_uniforms['transition'] = self.transition
                shader_uniforms['e_transition'] = self.e_transition
                shader_uniforms['noise_gain'] = self.noise_gain

                try:
                    self.render_object.render(uniforms=shader_uniforms)
                except Exception as e:
                    print(f"mgl render error: {e}")
            else:
                if self.debug:
                    print("use default pygame render_object")
                self._fallback_render(uniforms)
        else:
            self._fallback_render(uniforms)

        self.update_transition()
        pygame.display.flip()

        self.clock.tick(self.fps_cap)
        self.dt = min(time.time() - self.last_frame, self.dt_cap)
        self.frame_log.append(self.dt)
        self.frame_log = self.frame_log[-60:]
        self.last_frame = time.time()

        if not self.opengl:
            self.screen.fill(self.background_color)
        else:
            from util.framework.components.mgl import MGLComponent
            mgl_entity = self.e["MGL"]
            if mgl_entity:
                mgl = mgl_entity.get_component(MGLComponent)
                if mgl and mgl.initialized:
                    try:
                        mgl.ctx.clear(*[self.background_color[i] / 255 for i in range(3)], 1.0)
                    except Exception as e:
                        print(f"ctx clear error: {e}")

        self.time = time.time()
        self.frames += 1
        self.runtime_ = self.time - self.start_time

    def _fallback_render(self, uniforms):
        self.screen.fill(self.background_color)

        if 'surface' in uniforms and uniforms['surface']:
            surface = uniforms['surface']

            if surface.get_size() != self.screen.get_size():
                scale_x = self.screen.get_width() / surface.get_width()
                scale_y = self.screen.get_height() / surface.get_height()
                scale = min(scale_x, scale_y)

                scaled_width = int(surface.get_width() * scale)
                scaled_height = int(surface.get_height() * scale)

                try:
                    scaled_surface = pygame.transform.scale(surface, (scaled_width, scaled_height))

                    x = (self.screen.get_width() - scaled_width) // 2
                    y = (self.screen.get_height() - scaled_height) // 2

                    self.screen.blit(scaled_surface, (x, y))
                except Exception as e:
                    print(f"Transform error: {e}")
            else:
                self.screen.blit(surface, (0, 0))

        if 'background' in uniforms and uniforms['background']:
            pass

        if 'ui_surf' in uniforms and uniforms['ui_surf']:
            ui = uniforms['ui_surf']

            if ui.get_size() != self.screen.get_size():
                scale_x = self.screen.get_width() / ui.get_width()
                scale_y = self.screen.get_height() / ui.get_height()
                scale = min(scale_x, scale_y)

                scaled_width = int(ui.get_width() * scale)
                scaled_height = int(ui.get_height() * scale)

                try:
                    scaled_ui = pygame.transform.scale(ui, (scaled_width, scaled_height))

                    x = (self.screen.get_width() - scaled_width) // 2
                    y = (self.screen.get_height() - scaled_height) // 2

                    self.screen.blit(scaled_ui, (x, y))
                except Exception as e:
                    print(f"Transform UI error: {e}")
            else:
                self.screen.blit(ui, (0, 0))
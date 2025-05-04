import time

import pygame

from ..utils.elements import ElementSingleton
from ..mgl.mgl import MGL

class Window(ElementSingleton):
    def __init__(self, dimensions=(640, 480), caption='pygpen window', flags=0, fps_cap=60, dt_cap=1, opengl=False, frag_path=None):
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
        
        self.render_object = None
        if self.opengl:
            MGL()
            if not self.frag_path:
                self.render_object = self.e['MGL'].default_ro()
            else:
                self.render_object = self.e['MGL'].render_object(frag_path)

    @property
    def fps(self):
        return len(self.frame_log) / sum(self.frame_log)
    
    def cycle(self, uniforms={}):
        if self.render_object:
            if self.render_object.default and ('surface' not in uniforms):
                uniforms['surface'] = self.screen
            uniforms['time'] = self.time
            self.render_object.render(uniforms=uniforms)
        pygame.display.flip()
        self.clock.tick(self.fps_cap)
        self.dt = min(time.time() - self.last_frame, self.dt_cap)
        self.frame_log.append(self.dt)
        self.frame_log = self.frame_log[-60:]
        self.last_frame = time.time()
        self.screen.fill(self.background_color)
        if self.render_object:
            self.e['MGL'].ctx.clear(*[self.background_color[i] / 255 for i in range(3)], 1.0)
        self.e['Input'].update()
        self.time = time.time()
        self.frames += 1
        self.runtime_ = self.time - self.start_time
        
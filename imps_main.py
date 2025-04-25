import pygame

from util.framework import initialize, GameComponent
from util.framework.legacy.window import Window
from util.framework.legacy.input import Input
from util.framework.legacy.camera import Camera
from util.framework.legacy import Renderer

WINDOW_SIZE = (1020, 660)
DISPLAY_SIZE = (340, 220)

class SimpleGame(GameComponent):
    def __init__(self):
        super().__init__()

        self.window = Window(dimensions=WINDOW_SIZE, caption="Template", fps_cap=60, opengl=True)

        self.renderer = Renderer()

        self.window.frag_path = 'resources/shaders/shader.frag'
        self.window.render_object = self.renderer

        self.input = Input(path=None)

        self.bg_surf = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.display = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.ui_surf = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)

        self.renderer.add_surface('background', self.bg_surf)
        self.renderer.add_surface('default', self.display)
        self.renderer.add_surface('ui', self.ui_surf)

        self.camera = Camera(size=(800, 600), pos=(0, 0), slowness=5)

    def reset(self):
        self.e['Window'].start_transition()

    def game_update(self):
        self._update_gameplay()

        self.display.fill((0, 0, 0, 0))
        self.ui_surf.fill((0, 0, 0, 0))
        self.bg_surf.fill((0, 0, 0, 0))

        self.renderer.cycle({'default': self.display, 'ui': self.ui_surf, 'background': self.bg_surf})
        self.window.cycle({'surface': self.display, 'bg_surf': self.bg_surf, 'ui_surf': self.ui_surf})

    def _update_gameplay(self):
        self.camera.update()

initialize()

if __name__ == "__main__":
    pygame.init()

    # Input(None).config.update(config)

    game = SimpleGame()
    game.run()
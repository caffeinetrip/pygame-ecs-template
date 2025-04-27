from abc import ABCMeta, abstractmethod
import pygame
import asyncio
from util.framework import initialize, GameComponent
from util.framework.legacy.window import Window
from util.framework.legacy.input import Input
from util.framework.legacy.camera import Camera
from util.framework.legacy import Renderer
from util.framework.components import InteractorManager
from util.framework.utils.yaml import auto_save_all, auto_load_all

WINDOW_SIZE = (1020, 660)
DISPLAY_SIZE = (340, 220)
FPS_CAP = 60
CAMERA_SIZE = (800, 600)
CAMERA_SLOWNESS = 5

class Game(GameComponent, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()

        saved_instances = auto_load_all()

        self.window = Window(dimensions=WINDOW_SIZE, caption="Template", fps_cap=FPS_CAP, opengl=True)
        self.renderer = Renderer()
        self.window.frag_path = 'resources/shaders/shader.frag'
        self.window.render_object = self.renderer

        self.im = InteractorManager

        self.input = Input('resources/configs/hotkeys.json')

        self.number = saved_instances['NumberManager']

        self.input.register_handler('action', self._handle_action, priority=0)

        self.background_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.display_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.ui_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)

        self.renderer.add_surface('background', self.background_surface)
        self.renderer.add_surface('default', self.display_surface)
        self.renderer.add_surface('ui', self.ui_surface)

        self.camera = Camera(size=CAMERA_SIZE, pos=(0, 0), slowness=CAMERA_SLOWNESS)

        self.reset()
        self.input_processing_task = None

    async def _handle_action(self):
        await self.number.add_damage()

    def cleanup(self):
        auto_save_all({
            'NumberManager': self.number
        })

    def reset(self):
        self.window.start_transition()

    async def run(self):
        try:
            self.input_processing_task = await self.input.start_processing()
            await super().run()
        finally:
            self.cleanup()

    async def game_update(self):
        self._update_gameplay()

        self.display_surface.fill((255, 255, 255))
        self.ui_surface.fill((0, 0, 0, 0))
        self.background_surface.fill((0, 0, 0, 0))

        surface_dict = {'default': self.display_surface, 'ui': self.ui_surface, 'background': self.background_surface}
        self.renderer.cycle(surface_dict)

        window_surfaces = {'surface': self.display_surface, 'bg_surf': self.background_surface, 'ui_surf': self.ui_surface}
        self.window.cycle(window_surfaces)

        await self.input.update()

    def _update_gameplay(self):
        self.camera.update()

initialize()

if __name__ == "__main__":
    pygame.init()
    game = Game()
    try:
        asyncio.run(game.run())
    except KeyboardInterrupt:
        game.cleanup()
    finally:
        pygame.quit()
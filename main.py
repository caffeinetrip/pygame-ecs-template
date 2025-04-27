from abc import ABCMeta, abstractmethod
import pygame
import asyncio
from util.framework import initialize, Game
from util.framework.components import WindowComponent, InputComponent, CameraComponent, RenderComponent, MGLComponent
from util.framework.core import EnhancedInteractorManager
from util.framework.utils.yaml import auto_save_all, auto_load_all

WINDOW_SIZE = (1020, 660)
DISPLAY_SIZE = (340, 220)
FPS_CAP = 60
CAMERA_SIZE = (800, 600)
CAMERA_SLOWNESS = 5

class Main(Game, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        saved_instances = auto_load_all()

        self.window = self.add_component(WindowComponent, dimensions=WINDOW_SIZE, caption="Template", fps_cap=FPS_CAP, opengl=True)
        self.camera =  self.add_component(CameraComponent, size=CAMERA_SIZE, pos=(0, 0), slowness=CAMERA_SLOWNESS)
        self.renderer = self.add_component(RenderComponent)
        self.mgl = self.add_component(MGLComponent)
        self.input = self.add_component(InputComponent, 'resources/configs/hotkeys.json')

        self.im = EnhancedInteractorManager()

        self.window.frag_path = 'resources/shaders/shader.frag'
        self.window.render_object = self.renderer

        self.number = saved_instances['NumberManager']
        self.input.register_handler('action', self._handle_action, priority=0)

        self.background_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.display_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.ui_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)

        self.renderer.add_surface('background', self.background_surface)
        self.renderer.add_surface('default', self.display_surface)
        self.renderer.add_surface('ui', self.ui_surface)

        self.reset()
        self.input_processing_task = None

    async def _handle_action(self):
        await self.number.add_damage()

    # end point game script (save all data)
    def cleanup(self):
        auto_save_all({
            'NumberManager': self.number
        })

    def reset(self):
        self.window.start_transition()

    # game point chek (start or end) -> load/save
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
    main = Main()
    try:
        asyncio.run(main.run())
    except KeyboardInterrupt:
        main.cleanup()
    finally:
        pygame.quit()
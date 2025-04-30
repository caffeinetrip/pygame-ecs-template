import asyncio
import pygame

from util.framework.components import *
from util.framework.core.interactors.intManager import InteractorManager
from util.framework.globals import G
from util.framework.utils.yaml import auto_save_all, auto_load_all
from util import CMS, CMSEntity

# import interactors
from scripts import *
from content import NumbersEntity

WINDOW_SIZE = (1020, 660)
DISPLAY_SIZE = (340, 220)
FPS_CAP = 60
CAMERA_SIZE = (800, 600)
CAMERA_SLOWNESS = 5


class Main(Game):
    def __init__(self):
        super().__init__()

        data = auto_load_all()
        G.register('data', data)

        self.window = self.add_component(WindowComponent, dimensions=WINDOW_SIZE, caption="Template", fps_cap=FPS_CAP,
                                         opengl=True)
        self.camera = self.add_component(CameraComponent, size=CAMERA_SIZE, pos=(0, 0), slowness=CAMERA_SLOWNESS)
        self.renderer = self.add_component(RenderComponent)
        self.mgl = self.add_component(MGLComponent)
        self.input = self.add_component(InputComponent)

        self.im = InteractorManager()

        self.im.add_interactor('NumbersEntity', NumbersEntity)

        self.window.frag_path = 'resources/shaders/shader.frag'
        self.window.render_object = self.renderer

        self.background_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.display_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.ui_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)

        self.renderer.add_surface('background', self.background_surface)
        self.renderer.add_surface('default', self.display_surface)
        self.renderer.add_surface('ui', self.ui_surface)
        self.reset()

        self.input_processing_task = None

    def reset(self):
        G.window.start_transition()

    async def run(self):
        try:
            await G.im.trigger_encounter_start()
            await super().run()
        finally:
            await G.im.trigger_encounter_end()

    async def game_update(self):
        self._update_gameplay()

        self.display_surface.fill((255, 255, 255))
        self.ui_surface.fill((0, 0, 0, 0))
        self.background_surface.fill((0, 0, 0, 0))

        if G.input.pressed(pygame.K_e):
            await self._handle_action()

        surface_dict = {'default': self.display_surface, 'ui': self.ui_surface, 'background': self.background_surface}
        self.renderer.cycle(surface_dict)

        window_surfaces = {'surface': self.display_surface, 'bg_surf': self.background_surface, 'ui_surf': self.ui_surface}
        G.window.cycle(window_surfaces)

        await G.input.update()

    def _update_gameplay(self):
        G.camera.update()

    async def _handle_action(self):
        numbers_entity = G.im.get_interactor('NumbersEntity')
        if numbers_entity:
            await numbers_entity.add_damage()

def initialize():
    pygame.init()

if __name__ == "__main__":
    initialize()
    main = Main()

    try:
        asyncio.run(main.run())
    except KeyboardInterrupt:
        main.cleanup()
    finally:
        pygame.quit()
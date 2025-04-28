from util.framework import *
from util.framework.core.intManager import InteractorManager
from util.framework.utils.yaml import auto_save_all, auto_load_all

# import interactors
from scripts import *
from content import *

WINDOW_SIZE = (1020, 660)
DISPLAY_SIZE = (340, 220)
FPS_CAP = 60
CAMERA_SIZE = (800, 600)
CAMERA_SLOWNESS = 5

class Main(Game):
    def __init__(self):
        super().__init__()
        self.saved_instances = auto_load_all()

        self.window = self.add_component(WindowComponent, dimensions=WINDOW_SIZE, caption="Template", fps_cap=FPS_CAP,opengl=True)
        self.camera = self.add_component(CameraComponent, size=CAMERA_SIZE, pos=(0, 0), slowness=CAMERA_SLOWNESS)
        self.renderer = self.add_component(RenderComponent)
        self.mgl = self.add_component(MGLComponent)
        self.input = self.add_component(InputComponent, 'resources/configs/hotkeys.json')

        self.im = InteractorManager()
        self.im.e = self

        self.im.add_interactor('NumberManager', self.saved_instances['NumberManager'])

        self.window.frag_path = 'resources/shaders/shader.frag'
        self.window.render_object = self.renderer

        self.input.register_handler('action', self._handle_action, priority=0)

        self.background_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.display_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.ui_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)

        self.renderer.add_surface('background', self.background_surface)
        self.renderer.add_surface('default', self.display_surface)
        self.renderer.add_surface('ui', self.ui_surface)
        self.reset()

        self.input_processing_task = None

    def cleanup(self):
        auto_save_all(self.im.get_all_interactors())

    def reset(self):
        self.window.start_transition()

    async def run(self):
        try:
            self.input_processing_task = await self.input.start_processing()
            await self.im.trigger_encounter_start()
            await super().run()
        finally:
            await self.im.trigger_encounter_end()
            self.cleanup()

    async def game_update(self):
        self._update_gameplay()

        self.display_surface.fill((255, 255, 255))
        self.ui_surface.fill((0, 0, 0, 0))
        self.background_surface.fill((0, 0, 0, 0))

        surface_dict = {
            'default': self.display_surface,
            'ui': self.ui_surface,
            'background': self.background_surface
        }
        self.renderer.cycle(surface_dict)

        window_surfaces = {
            'surface': self.display_surface,
            'bg_surf': self.background_surface,
            'ui_surf': self.ui_surface
        }
        self.window.cycle(window_surfaces)

        await self.input.update()

    def _update_gameplay(self):
        self.camera.update()

    async def _handle_action(self):
        number_manager = self.im.get_interactor('NumberManager')
        if number_manager:
            await number_manager.add_damage()


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
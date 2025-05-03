import asyncio
import pygame

from util.framework.components import *
from util.framework.core.assets.assets import AssetsComponent
from util.framework.core.interactors.intManager import InteractorManager
from util.framework.core.object.objectCollections import ObjectCollections
from util.framework.core.object.AssetLibrary import AssetLibrary
from util.framework.globals import G
from util.framework.utils.yaml import auto_load_all
from util.framework.utils.tilemap import Tilemap
from util.hooks import gen_hook

from scripts import *
from content import NumbersEntity, PlayerEntity

WINDOW_SIZE = (1020, 660)
DISPLAY_SIZE = (340, 220)
FPS_CAP = 60
TILE_SIZE = (16, 16)
CAMERA_SLOWNESS = 5


class Main(Game):
    def __init__(self):
        super().__init__()

        data = auto_load_all()
        G.register('data', data)

        self.window = self.add_component(WindowComponent, dimensions=WINDOW_SIZE, caption="Template", fps_cap=FPS_CAP,
                                         opengl=True)
        self.camera = self.add_component(CameraComponent, size=DISPLAY_SIZE, pos=(0, 0), slowness=CAMERA_SLOWNESS)
        self.renderer = self.add_component(RenderComponent)
        self.mgl = self.add_component(MGLComponent)
        self.input = self.add_component(InputComponent)
        self.mouse = self.add_component(MouseComponent)
        self.assets = self.add_component(AssetsComponent, spritesheet_path="data/images/spritesheets")

        self.im = InteractorManager()

        self.im.add_interactor('AssetLibrary', AssetLibrary, 'data/images/entities')
        asset_library = self.im.get_interactor('AssetLibrary')
        G.register('AssetLibrary', asset_library)

        self.im.add_interactor('NumbersEntity', NumbersEntity)
        self.object_collections = self.im.add_interactor('ObjectCollections', ObjectCollections,
                                                         spatial_collections=['entities'])

        self.window.frag_path = 'resources/shaders/shader.frag'
        self.window.render_object = self.renderer

        self.tilemap = Tilemap(tile_size=TILE_SIZE)
        self.tilemap.load('data/maps/1.pmap', spawn_hook=gen_hook())

        self.background_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.display_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.ui_surface = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)

        self.renderer.add_surface('background', self.background_surface)
        self.renderer.add_surface('default', self.display_surface)
        self.renderer.add_surface('ui', self.ui_surface)

        self.player = PlayerEntity((100, 100))
        self.object_collections.register(self.player, 'entities')

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
        self.display_surface.fill((255, 255, 255))
        self.ui_surface.fill((0, 0, 0, 0))
        self.background_surface.fill((0, 0, 0, 0))

        self._update_gameplay()
        pygame.display.set_caption((str(round(G.window.fps, 1))))

        if G.input.pressed(pygame.K_e):
            await self._handle_action()

        surface_dict = {'default': self.display_surface, 'ui': self.ui_surface, 'background': self.background_surface}
        self.renderer.cycle(surface_dict)

        window_surfaces = {'surface': self.display_surface, 'bg_surf': self.background_surface,
                           'ui_surf': self.ui_surface}
        G.window.cycle(window_surfaces)

        await G.input.update()

    def _update_gameplay(self):
        self.camera.set_target(self.player)
        G.camera.update()

        visible_rect = pygame.Rect(
            self.camera[0] - 16,
            self.camera[1] - 16,
            self.display_surface.get_width() + 48,
            self.display_surface.get_height() + 48
        )

        self.object_collections.update(view_area=visible_rect)
        self.player.physics_update(self.tilemap)

        self.tilemap.renderz(visible_rect, offset=self.camera)
        self.object_collections.renderz(layer_group='game', camera_offset=self.camera)

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
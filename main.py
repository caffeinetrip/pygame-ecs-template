import asyncio
from util.framework import initialize, world
from util.framework.components.interactor import InteractorComponent, Interactor
from util.framework.components.flags import NameFlagComponent
from util.framework.components.grid import GridComponent
from util.framework.components.meta_state import MetaStateComponent, MetaState
from util.framework.components.run import RunComponent
# from util.framework.components.button import ButtonComponent


class GameInteractor(Interactor):
    def update(self, dt):
        pass

    def handle_input(self, input_event):
        pass


class InitializationSystem:
    def __init__(self, world):
        self.e = world

    async def start(self):
        main_entity = self.e.create_entity("MainController", singleton=True)

        interactor_comp = main_entity.add_component(InteractorComponent)
        game_interactor = GameInteractor()
        interactor_comp.add_interactor("game", game_interactor)
        game_interactor.init(self.e)

        main_entity.add_component(NameFlagComponent)

        grid_entity = self.e.create_entity("Grid", singleton=True)
        grid_comp = grid_entity.add_component(GridComponent)
        grid_comp.init(width=10, height=10, cell_size=1.0)

        meta_entity = self.e.create_entity("Metadata", singleton=True)
        meta_comp = meta_entity.add_component(MetaStateComponent)

        if meta_comp.meta is None:
            meta_comp.meta = MetaState.load_or_initialize_new()

        game_controller = self.e.create_entity("GameController", singleton=True)
        run_comp = game_controller.add_component(RunComponent)

        if run_comp.run is None:
            run_comp.create_new_run()

        # button_entity = self.e.create_entity("EndTurnButton", singleton=True)
        # button_comp = button_entity.add_component(ButtonComponent)
        # button_comp.add_listener(self.on_button_end_turn)

        await self.init_encounter()

    def on_button_end_turn(self):
        game_controller = self.e["GameController"]
        run_comp = game_controller.get_component(RunComponent)
        run_comp.increment_turn()

    async def init_encounter(self):
        await asyncio.sleep(0.1)


async def main():
    initialize()

    init_system = InitializationSystem(world)
    await init_system.start()

    frame_count = 0
    while frame_count < 100:
        world.update(0.016)  # ~60 FPS
        frame_count += 1
        await asyncio.sleep(0.016)

    print("Game encountered")


if __name__ == "__main__":
    asyncio.run(main())
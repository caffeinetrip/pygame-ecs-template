from util.framework.core.system import System
from util.framework.components.grid import GridComponent


class GridSystem(System):
    def __init__(self):
        super().__init__()

    async def start(self):
        grid_entities = self.e.get_entities_with(GridComponent)
        if not grid_entities:
            grid_entity = self.e.create_singleton("Grid")
            grid_entity.add_component(GridComponent)

    def update(self, dt):
        pass
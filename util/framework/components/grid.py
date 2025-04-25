from util.framework.core.component import Component


class GridComponent(Component):
    def __init__(self, width=0, height=0, cell_size=1.0):
        super().__init__()
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = {}

    def init(self, width=None, height=None, cell_size=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if cell_size is not None:
            self.cell_size = cell_size

        self.grid = {}

    def world_to_cell(self, x, y):
        cell_x = int(x / self.cell_size)
        cell_y = int(y / self.cell_size)
        return cell_x, cell_y

    def cell_to_world(self, cell_x, cell_y):
        world_x = (cell_x + 0.5) * self.cell_size
        world_y = (cell_y + 0.5) * self.cell_size
        return world_x, world_y

    def is_valid_cell(self, cell_x, cell_y):
        return 0 <= cell_x < self.width and 0 <= cell_y < self.height

    def place_entity(self, entity, cell_x, cell_y):
        if not self.is_valid_cell(cell_x, cell_y):
            return False

        position = (cell_x, cell_y)
        if position not in self.grid:
            self.grid[position] = []

        if entity not in self.grid[position]:
            self.grid[position].append(entity)

        if not entity.has_component(GridPositionComponent):
            entity.add_component(GridPositionComponent, cell_x, cell_y)
        else:
            grid_pos = entity.get_component(GridPositionComponent)
            grid_pos.set_position(cell_x, cell_y)

        return True

    def remove_entity(self, entity):
        if entity.has_component(GridPositionComponent):
            grid_pos = entity.get_component(GridPositionComponent)
            position = (grid_pos.x, grid_pos.y)

            if position in self.grid and entity in self.grid[position]:
                self.grid[position].remove(entity)

        return True

    def move_entity(self, entity, new_cell_x, new_cell_y):
        self.remove_entity(entity)
        return self.place_entity(entity, new_cell_x, new_cell_y)

    def get_entities_at(self, cell_x, cell_y):
        position = (cell_x, cell_y)
        return self.grid.get(position, [])

    def get_neighbors(self, cell_x, cell_y, include_diagonals=False):
        neighbors = []

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = cell_x + dx, cell_y + dy
            if self.is_valid_cell(nx, ny):
                neighbors.append((nx, ny))

        if include_diagonals:
            for dx, dy in [(1, 1), (1, -1), (-1, -1), (-1, 1)]:
                nx, ny = cell_x + dx, cell_y + dy
                if self.is_valid_cell(nx, ny):
                    neighbors.append((nx, ny))

        return neighbors

    def get_entities_in_area(self, start_x, start_y, width, height):
        entities = []

        for x in range(start_x, start_x + width):
            for y in range(start_y, start_y + height):
                if self.is_valid_cell(x, y):
                    entities.extend(self.get_entities_at(x, y))

        return entities


class GridPositionComponent(Component):
    def __init__(self, x=0, y=0):
        super().__init__()
        self.x = x
        self.y = y

    def set_position(self, x, y):
        self.x = x
        self.y = y
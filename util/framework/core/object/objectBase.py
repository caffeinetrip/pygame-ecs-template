import pygame
from util.framework.globals import G
from util.framework.core.component import Component

ADJACENT_DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]

WALKABLE_TILES = [
   'walk_zone',
]


def apply_friction(value, amount):
   if abs(value) < amount:
       return 0
   elif value > 0:
       return value - amount
   else:
       return value + amount


class Object(Component):
   def __init__(self, position, depth=0):
       super().__init__()
       self.kind = getattr(self, 'kind', type)
       self.position = list(position)
       self.depth = depth

       asset_data = G.AssetLibrary[self.kind]
       if asset_data is None:
           raise ValueError(f"No asset data found for kind '{self.kind}'")

       self.specs = asset_data.specs
       self.resources = asset_data.resources
       self.sequences = asset_data.sequences
       self.state = self.specs.get('initial', 'idle/down')

       if self.state in self.sequences:
           self.source_type = 'sequences'
           self.sequence = self.sequences[self.state].copy()
       else:
           if self.sequences:
               self.state = list(self.sequences.keys())[0]
               self.source_type = 'sequences'
               self.sequence = self.sequences[self.state].copy()
           else:
               raise ValueError(f"No sequences found for {self.kind}")

       self.dimensions = self.specs.get('size', [16, 16])
       self.transparency = 255
       self.resize = [1, 1]
       self.angle = 0
       self.mirror = [False, False]
       self.show = True
       self.modified = False
       self.highlight = None

   @property
   def center(self):
       return self.hitbox.center

   @property
   def hitbox(self):
       return pygame.Rect(*self.position, *self.dimensions)

   @property
   def offset_coords(self):
       res_offset = self.specs[self.source_type][self.state]['offset']
       obj_offset = self.specs['offset']
       return res_offset[0] + obj_offset[0], res_offset[1] + obj_offset[1]

   @property
   def source_image(self):
       if self.source_type == 'sequences':
           return self.sequence.img
       return None

   @property
   def render_image(self):
       src_img = self.source_image
       if src_img is None:
           placeholder = pygame.Surface(self.dimensions)
           placeholder.fill((255, 0, 255))
           return placeholder

       img = src_img
       orig_size = img.get_size()
       if self.resize != [1, 1]:
           img = pygame.transform.scale(img, (int(self.resize[0] * orig_size[0]),
                                              int(self.resize[1] * orig_size[1])))
           self.modified = True
       if any(self.mirror):
           img = pygame.transform.flip(img, self.mirror[0], self.mirror[1])
       if self.angle:
           img = pygame.transform.rotate(img, self.angle)
           self.modified = True
       if self.transparency != 255:
           if img == src_img:
               img = img.copy()
           img.set_alpha(self.transparency)
       return img

   def set_state(self, state, override=False):
       if not override and (self.state == state):
           return
       self.state = state
       self.source_type = 'sequences' if self.state in self.sequences else 'images'
       if self.source_type == 'sequences':
           self.sequence = self.sequences[self.state].copy()

   def draw_position(self, camera_offset=(0, 0)):
       img_dims = self.render_image.get_size()
       if (not self.modified) or self.specs['centered']:
           center_shift = (img_dims[0] // 2, img_dims[1] // 2) if self.specs['centered'] else (0, 0)
           return (self.position[0] - camera_offset[0] + self.offset_coords[0] - center_shift[0],
                   self.position[1] - camera_offset[1] + self.offset_coords[1] - center_shift[1])
       else:
           raw_dims = self.source_image.get_size()
           size_delta = (img_dims[0] - raw_dims[0], img_dims[1] - raw_dims[1])
           auto_shift = [-size_delta[0] // 2, -size_delta[1] // 2]
           return (self.position[0] - camera_offset[0] + self.offset_coords[0] + auto_shift[0],
                   self.position[1] - camera_offset[1] + self.offset_coords[1] + auto_shift[1])

   def tick(self, delta):
       super().update()
       if self.source_type == 'sequences':
           self.sequence.update(delta)

   def draw(self, surface, camera_offset=(0, 0)):
       if self.show:
           surface.blit(self.render_image, self.draw_position(camera_offset))

   def renderz(self, camera_offset=(0, 0), group='game'):
       if self.show:
           pos = self.draw_position(camera_offset)
           if self.highlight:
               outline = pygame.mask.from_surface(self.render_image).to_surface(setcolor=self.highlight,
                                                                                unsetcolor=(0, 0, 0, 0))
               outline.set_alpha(self.transparency)
               for shift in ADJACENT_DIRS:
                   G.render.blit(outline, (pos[0] + shift[0], pos[1] + shift[1]),
                                 z=self.depth - 0.000001)
           G.render.blit(self.render_image, pos, z=self.depth)


class MovingObject(Object):
    def __init__(self, position, depth=0):
        super().__init__(position, depth=depth)
        self.prev_pos = (0, 0)
        self.speed = [0, 0]
        self.acceleration = [0, 0]
        self.size = [16, 16]
        self.max_speed = [99999, 99999]
        self.friction = [0, 0]
        self.delta_move = [0, 0]
        self.prev_move = (0, 0)
        self.rebound = 0
        self.auto_mirror = 0
        self.collision_list = []
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.pass_through = 0
        self.no_collide = False
        self.walkable_only = True
        self.collision_offsets = [5, 0, -8, -5]
        self.initialize()

    @property
    def rebound_factors(self):
        if type(self.rebound) not in {list, tuple}:
            return self.rebound, self.rebound
        return tuple(self.rebound)

    @property
    def center(self):
        return self.rect.center

    @property
    def rect(self):
        return pygame.Rect(*self.prev_pos, *self.size)

    def initialize(self):
        pass

    def check_walkable_collision(self, new_position, level_map):
        if not self.walkable_only:
            return True

        world_width = level_map.dimensions[0] * level_map.tile_size[0]
        world_height = level_map.dimensions[1] * level_map.tile_size[1]

        left_offset, top_offset, right_offset, bottom_offset = self.collision_offsets

        if (new_position[0] - left_offset < 0 or
                new_position[0] + self.size[0] + right_offset > world_width):
            return False
        if (new_position[1] - top_offset < 0 or
                new_position[1] + self.size[1] + bottom_offset > world_height):
            return False

        corners = [
            (new_position[0] - left_offset, new_position[1] - top_offset),
            (new_position[0] + self.size[0] + right_offset, new_position[1] - top_offset),
            (new_position[0] - left_offset, new_position[1] + self.size[1] + bottom_offset),
            (new_position[0] + self.size[0] + right_offset, new_position[1] + self.size[1] + bottom_offset)
        ]

        center = (new_position[0] + self.size[0] // 2, new_position[1] + self.size[1] // 2)
        corners.append(center)

        for corner in corners:
            grid_x = int(corner[0] // level_map.tile_size[0])
            grid_y = int(corner[1] // level_map.tile_size[1])

            if (grid_x, grid_y) in level_map.grid_tiles:
                found_walkable = False
                for layer, tile in level_map.grid_tiles[(grid_x, grid_y)].items():
                    if tile.group in WALKABLE_TILES:
                        found_walkable = True
                        break
                if not found_walkable:
                    return False
            else:
                return False

        return True

    def behavior_update(self):
        pass

    def physics_update(self, level_map):
        delta = G.window.dt
        self.behavior_update()
        if self.delta_move[0] * -self.auto_mirror > 0:
            self.mirror[0] = True
        if self.delta_move[0] * self.auto_mirror > 0:
            self.mirror[0] = False
        self.delta_move[0] += self.speed[0] * delta
        self.delta_move[1] += self.speed[1] * delta
        self.move_with_physics(self.delta_move, level_map)
        self.prev_move = (self.delta_move[0] / delta, self.delta_move[1] / delta)
        self.speed[0] += self.acceleration[0] * delta
        self.speed[1] += self.acceleration[1] * delta
        self.speed[0] = apply_friction(self.speed[0], self.friction[0] * delta)
        self.speed[1] = apply_friction(self.speed[1], self.friction[1] * delta)
        self.speed[0] = max(-self.max_speed[0], min(self.max_speed[0], self.speed[0]))
        self.speed[1] = max(-self.max_speed[1], min(self.max_speed[1], self.speed[1]))
        self.delta_move = [0, 0]
        self.pass_through = max(0, self.pass_through - delta)

    def apply_impulse(self, vector):
        self.delta_move[0] += vector[0] * G.window.dt
        self.delta_move[1] += vector[1] * G.window.dt

    def move_with_physics(self, movement, level_map):
        self.collision_list = []
        self.prev_pos = tuple(self.position)
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        if self.walkable_only:
            if movement[1] != 0:
                test_pos_y = [self.position[0], self.position[1] + movement[1]]
                if self.check_walkable_collision(test_pos_y, level_map):
                    self.position[1] += movement[1]
                else:
                    self.collisions['down' if movement[1] > 0 else 'up'] = True
                    self.speed[1] = 0

            if movement[0] != 0:
                test_pos_x = [self.position[0] + movement[0], self.position[1]]
                if self.check_walkable_collision(test_pos_x, level_map):
                    self.position[0] += movement[0]
                else:
                    self.collisions['right' if movement[0] > 0 else 'left'] = True
                    self.speed[0] = 0
        else:
            self.position[1] += movement[1]
            tiles = level_map.nearby_grid_physics(self.center)
            self.handle_collisions((0, movement[1]), tiles)
            self.position[0] += movement[0]
            tiles = level_map.nearby_grid_physics(self.center)
            self.handle_collisions((movement[0], 0), tiles)
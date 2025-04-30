import pygame
from util.framework.globals import G
from util.framework.core.component import Component

ADJACENT_DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]

class Object(Component):
    def __init__(self, position, depth=0):
        super().__init__()
        self.kind = type
        self.position = list(position)
        self.depth = depth
        self.specs = G.ObjectDB[self.kind].specs
        self.resources = G.ObjectDB[self.kind].resources
        self.sequences = G.ObjectDB[self.kind].sequences
        self.state = self.specs['default']
        self.source_type = 'sequences' if self.state in self.sequences else 'images'
        self.sequence = None if self.source_type != 'sequences' else self.sequences[self.state].copy()
        self.dimensions = self.specs['size']

        self.transparency = 255
        self.resize = [1, 1]
        self.angle = 0
        self.mirror = [False, False]
        self.show = True

        # tracks if advanced rendering is needed
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
            return self.sequence.image
        return self.resources[self.state]

    @property
    def render_image(self):
        src_img = self.source_image
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

    def draw_position(self, camera_shift=(0, 0)):
        img_dims = self.render_image.get_size()
        if (not self.modified) or self.specs['centered']:
            center_shift = (img_dims[0] // 2, img_dims[1] // 2) if self.specs['centered'] else (0, 0)
            return (self.position[0] - camera_shift[0] + self.offset_coords[0] - center_shift[0],
                    self.position[1] - camera_shift[1] + self.offset_coords[1] - center_shift[1])
        else:
            raw_dims = self.source_image.get_size()
            size_delta = (img_dims[0] - raw_dims[0], img_dims[1] - raw_dims[1])
            auto_shift = [-size_delta[0] // 2, -size_delta[1] // 2]
            return (self.position[0] - camera_shift[0] + self.offset_coords[0] + auto_shift[0],
                    self.position[1] - camera_shift[1] + self.offset_coords[1] + auto_shift[1])

    def tick(self, delta):
        super().update()
        if self.source_type == 'sequences':
            self.sequence.update(delta)

    def draw(self, surface, camera_shift=(0, 0)):
        if self.show:
            surface.blit(self.render_image, self.draw_position(camera_shift))

    def draw_layered(self, camera_shift=(0, 0), layer='game'):
        if self.show:
            pos = self.draw_position(camera_shift)
            if self.highlight:
                outline = pygame.mask.from_surface(self.render_image).to_surface(setcolor=self.highlight,
                                                                           unsetcolor=(0, 0, 0, 0))
                outline.set_alpha(self.transparency)
                for shift in ADJACENT_DIRS:
                    G.renderer.blit(outline, (pos[0] + shift[0], pos[1] + shift[1]),
                                    z=self.depth - 0.000001, group=layer)
            G.renderer.blit(self.render_image, pos, z=self.depth, group=layer)


class MovingObject(Object):
    def __init__(self, position, depth=0):
        super().__init__(position, depth=depth)
        self.prev_pos = (0, 0)
        self.speed = [0, 0]
        self.acceleration = [0, 0]
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
        self.initialize()

    @property
    def rebound_factors(self):
        if type(self.rebound) not in {list, tuple}:
            return self.rebound, self.rebound
        return tuple(self.rebound)

    def initialize(self):
        pass

    def handle_collisions(self, movement, objects):
        box = self.hitbox
        for obj in objects:
            if box.colliderect(obj.hitbox) and not self.no_collide:
                if obj.collision_type == 'solid':
                    if movement[0] > 0:
                        box.right = obj.hitbox.left
                        self.speed[0] *= -self.rebound_factors[0]
                        self.collisions['right'] = True
                    if movement[0] < 0:
                        box.left = obj.hitbox.right
                        self.speed[0] *= -self.rebound_factors[0]
                        self.collisions['left'] = True
                    if movement[1] > 0:
                        box.bottom = obj.hitbox.top
                        self.speed[1] *= -self.rebound_factors[1]
                        self.collisions['down'] = True
                    if movement[1] < 0:
                        box.top = obj.hitbox.bottom
                        self.speed[1] *= -self.rebound_factors[1]
                        self.collisions['up'] = True
                elif obj.collision_type == 'ramp_right':
                    if (movement[1] > 0) or (movement[0] > 0):
                        check_x = (box.right - obj.hitbox.left) / obj.hitbox.width
                        if 0 <= check_x <= 1:
                            if box.bottom > (1 - check_x) * obj.hitbox.height + obj.hitbox.top:
                                box.bottom = (1 - check_x) * obj.hitbox.height + obj.hitbox.top
                                self.speed[1] *= -self.rebound_factors[1]
                                self.collisions['down'] = True
                elif obj.collision_type == 'ramp_left':
                    if (movement[1] > 0) or (movement[0] < 0):
                        check_x = (box.left - obj.hitbox.left) / obj.hitbox.width
                        if 0 <= check_x <= 1:
                            if box.bottom > check_x * obj.hitbox.height + obj.hitbox.top:
                                box.bottom = check_x * obj.hitbox.height + obj.hitbox.top
                                self.speed[1] *= -self.rebound_factors[1]
                                self.collisions['down'] = True
                elif obj.collision_type == 'platform':
                    if not self.pass_through:
                        if movement[1] > 0:
                            if (box.bottom > obj.hitbox.top) and (box.bottom - movement[1] <= obj.hitbox.top + 1):
                                box.bottom = obj.hitbox.top
                                self.speed[1] *= -self.rebound_factors[1]
                                self.collisions['down'] = True

                if box.x != self.hitbox.x:
                    self.position[0] = box.x
                if box.y != self.hitbox.y:
                    self.position[1] = box.y
                box = self.hitbox
                self.collision_list.append(obj)

    def behavior_update(self):
        pass

    def physics_tick(self, level_map):
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
        self.position[1] += movement[1]
        tiles = level_map.nearby_grid_physics(self.middle)
        self.handle_collisions((0, movement[1]), tiles)
        self.position[0] += movement[0]
        tiles = level_map.nearby_grid_physics(self.middle)
        self.handle_collisions((movement[0], 0), tiles)


def apply_friction(value, amount):
    if abs(value) < amount:
        return 0
    elif value > 0:
        return value - amount
    else:
        return value + amount
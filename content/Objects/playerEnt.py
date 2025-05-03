import pygame
from util.framework.core.object.objectBase import MovingObject
from util.framework.globals import G


class PlayerEntity(MovingObject):
    def __init__(self, position):
        self.kind = 'player'
        super().__init__(position)
        self.walkable_only = True
        self.speed = [0, 0]
        self.max_speed = [150, 150]
        self.size = [16, 16]
        self.direction = 'down'
        self.moving = False

    def behavior_update(self):
        move_x = 0
        move_y = 0

        self.max_speed = [150, 150]

        if G.input.holding(pygame.K_LEFT) or G.input.holding(pygame.K_a):
            move_x -= 1
            self.direction = 'right'
            self.mirror[0] = True
            self.max_speed[1] = 100

        if G.input.holding(pygame.K_RIGHT) or G.input.holding(pygame.K_d):
            move_x += 1
            self.direction = 'right'
            self.mirror[0] = False
            self.max_speed[1] = 100

        if G.input.holding(pygame.K_UP) or G.input.holding(pygame.K_w):
            move_y -= 1
            self.direction = 'top'
            self.max_speed[0] = 100

        if G.input.holding(pygame.K_DOWN) or G.input.holding(pygame.K_s):
            move_y += 1
            self.direction = 'down'
            self.max_speed[0] = 100

        self.speed[0] = move_x * self.max_speed[0]
        self.speed[1] = move_y * self.max_speed[1]

        self.moving = move_x != 0 or move_y != 0

        if self.moving:
            self.set_state(f'walk/{self.direction}')
        else:
            self.set_state(f'idle/{self.direction}')
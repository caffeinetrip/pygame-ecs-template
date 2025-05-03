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

        if G.input.holding(pygame.K_LEFT):
            move_x -= 1
            self.direction = 'right'
            self.mirror[0] = True
        if G.input.holding(pygame.K_RIGHT):
            move_x += 1
            self.direction = 'right'
            self.mirror[0] = False
        if G.input.holding(pygame.K_UP):
            move_y -= 1
            self.direction = 'top'
        if G.input.holding(pygame.K_DOWN):
            move_y += 1
            self.direction = 'down'

        self.speed[0] = move_x * self.max_speed[0]
        self.speed[1] = move_y * self.max_speed[1]

        self.moving = move_x != 0 or move_y != 0

        if self.moving:
            self.set_state(f'walk/{self.direction}')
        else:
            self.set_state(f'idle/{self.direction}')
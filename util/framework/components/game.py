import asyncio
import pygame
from util.framework.globals import G
from util.framework.core.component import Component


class Game(Component):
    def __init__(self):
        super().__init__()
        self.active = True

        G.initialize()
        G.register('game', self)
        self.e = G

    async def run(self):
        running = True
        while running and self.active:
            await self.game_update()
            await asyncio.sleep(0.001)

    async def game_update(self):
        pass
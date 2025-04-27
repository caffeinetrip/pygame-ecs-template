import sys
import  asyncio
import pygame
from abc import ABC, abstractmethod
from util.framework.core import Entity


class Game(Entity, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def game_update(self):
        pass

    async def run(self):
        while True:
            await self.game_update()
            await asyncio.sleep(0)

    @staticmethod
    def quit(self):
        pygame.quit()
        sys.exit()
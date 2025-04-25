import sys
import  asyncio
import pygame
from abc import ABC, abstractmethod
from util.framework.core.component import Component
from util.framework.components.window import WindowComponent


class GameComponent(Component):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def game_update(self):
        pass

    def run(self):
        self.load()
        while True:
            self.game_update()

    @staticmethod
    def quit(self):
        pygame.quit()
        sys.exit()
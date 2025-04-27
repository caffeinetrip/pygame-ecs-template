from util.framework.core.world import World
from util.framework.core.component import Component
from util.framework.core.entity import Entity
from util.framework.core.system import System

from util.framework.systems.camera_system import CameraSystem

from util.framework.components.camera import CameraComponent
from util.framework.components.interactor import Interactor, InteractorManager
from util.framework.components.input import InputComponent, MouseComponent
from util.framework.components.window import WindowComponent
from util.framework.components.game import GameComponent
from util.framework.components.mgl import MGLComponent

world = World()
elems = world

def initialize():
    world.add_system(CameraSystem())
    return world

from util.framework.legacy.elements import ElementSingleton, Element
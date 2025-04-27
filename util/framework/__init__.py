from util.framework.core import *
from util.framework.systems.camera_system import *
from util.framework.components import *

world = World()
elems = world

def initialize():
    world.add_system(CameraSystem())
    return world
from util.framework.core.world import World
from util.framework.core.component import Component
from util.framework.core.entity import Entity
from util.framework.core.system import System

from util.framework.systems.interactor_system import InteractorSystem
from util.framework.systems.state_system import StateSystem
from util.framework.systems.grid_system import GridSystem
from util.framework.systems.button_system import ButtonSystem

from util.framework.components.button import ButtonComponent
from util.framework.components.flags import (
    FlagComponent, NameFlagComponent, SelectedFlagComponent,
    ActiveFlagComponent, VisibleFlagComponent
)
from util.framework.components.grid import GridComponent, GridPositionComponent
from util.framework.components.interactor import InteractorComponent, Interactor
from util.framework.components.meta_state import MetaStateComponent, MetaState
from util.framework.components.run import RunComponent
from util.framework.components.state import StateComponent, State

world = World()
elems = world

def initialize():
    world.add_system(InteractorSystem())
    world.add_system(StateSystem())
    world.add_system(GridSystem())
    world.add_system(ButtonSystem())
    return world

from util.framework.legacy.elements import ElementSingleton, Element
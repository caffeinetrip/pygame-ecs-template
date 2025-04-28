import inspect
import asyncio
from enum import Enum, auto
from typing import Dict, List, Type, TypeVar
from util.framework.core.component import Component


class InteractorState(Enum):
    INACTIVE = auto()
    ACTIVE = auto()
    PAUSED = auto()
    DESTROYED = auto()


class PriorityLayers:
    FIRST = -10000
    NORMAL = 0
    LAST = 10000
    LAST_SPECIAL = 10001


class BaseInteraction:

    def __init__(self):
        self._enabled = True

    def priority(self) -> int:
        return PriorityLayers.NORMAL

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        if self._enabled != value:
            self._enabled = value
            if value:
                self.on_enable()
            else:
                self.on_disable()

    def on_enable(self):
        pass

    def on_disable(self):
        pass


# Define type variable for interactions
T = TypeVar('T', bound=BaseInteraction)


class InteractionCache:
    _cache: Dict[Type, List] = {}

    @classmethod
    def find_all(cls, interactions: List[BaseInteraction], interaction_type: Type[T]) -> List[T]:
        cache_key = (tuple(interactions), interaction_type)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        result = [i for i in interactions if isinstance(i, interaction_type) and i.enabled]

        result.sort(key=lambda x: x.priority())

        cls._cache[cache_key] = result

        return result

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()


class Interactor(Component):

    def __init__(self):
        super().__init__()
        self._enabled = True
        self._started = False
        self._coroutines = []
        self._loop = asyncio.get_running_loop() if asyncio._get_running_loop() else asyncio.get_event_loop()
        self._state = InteractorState.INACTIVE
        self._timers = {}
        self._child_interactors = []
        self._parent_interactor = None
        self._tag = ""
        self._layer = PriorityLayers.NORMAL

        self.interactions = []
        self.e = None

    def awake(self):
        self._state = InteractorState.ACTIVE

    def start(self):
        self._started = True

    def update(self, dt):
        pass

    def fixed_update(self, fixed_dt):
        pass

    def on_destroy(self):
        self.stop_all_coroutines()
        self._state = InteractorState.DESTROYED

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    async def on_encounter_start(self, args=None):
        pass

    async def on_encounter_end(self, args=None):
        pass

    def start_coroutine(self, coroutine_func):
        try:
            if inspect.iscoroutinefunction(coroutine_func):
                task = asyncio.create_task(coroutine_func())
            elif inspect.iscoroutine(coroutine_func):
                task = asyncio.create_task(coroutine_func)
            else:
                task = asyncio.create_task(coroutine_func())

            task.add_done_callback(self._task_done_callback)
            self._coroutines.append(task)
            return task
        except RuntimeError as e:
            print(f"Error creating task: {e}")
            return None

    def _task_done_callback(self, task):
        if task in self._coroutines:
            self._coroutines.remove(task)

        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Exception in coroutine: {e}")

    def stop_coroutine(self, task):
        if task in self._coroutines:
            task.cancel()
            self._coroutines.remove(task)

    def stop_all_coroutines(self):
        for task in self._coroutines.copy():
            task.cancel()
        self._coroutines.clear()

        for timer_name in list(self._timers.keys()):
            self.cancel_timer(timer_name)

    async def wait_for_seconds(self, seconds):
        await asyncio.sleep(seconds)

    async def wait_until(self, predicate):
        while not predicate():
            await asyncio.sleep(0.01)

    async def wait_while(self, predicate):
        while predicate():
            await asyncio.sleep(0.01)

    def set_timer(self, name, seconds, callback, repeat=False):
        if name in self._timers:
            task = self._timers[name]
            self.stop_coroutine(task)
            del self._timers[name]

        async def timer_coroutine():
            try:
                if repeat:
                    while True:
                        await asyncio.sleep(seconds)
                        callback()
                else:
                    await asyncio.sleep(seconds)
                    callback()
                    if name in self._timers:
                        del self._timers[name]
            except asyncio.CancelledError:
                raise

        task = self.start_coroutine(timer_coroutine)
        self._timers[name] = task
        return task

    def cancel_timer(self, name):
        if name in self._timers:
            task = self._timers[name]
            self.stop_coroutine(task)
            del self._timers[name]
            return True
        return False

    def get_component(self, component_type):
        return self.e.get_component(component_type)

    def get_components(self, component_type):
        return self.e.get_components(component_type)

    def get_component_in_children(self, component_type):
        for child in self._child_interactors:
            component = child.get_component(component_type)
            if component:
                return component
        return None

    def get_component_in_parent(self, component_type):
        if self._parent_interactor:
            return self._parent_interactor.get_component(component_type)
        return None

    def add_component(self, component_type, *args, **kwargs):
        return self.e.add_component(component_type, *args, **kwargs)

    def add_interaction(self, interaction: BaseInteraction):
        self.interactions.append(interaction)
        InteractionCache.clear_cache()
        return interaction

    def remove_interaction(self, interaction: BaseInteraction):
        if interaction in self.interactions:
            self.interactions.remove(interaction)
            InteractionCache.clear_cache()
            return True
        return False

    def find_interactions(self, interaction_type: Type[T]) -> List[T]:
        return InteractionCache.find_all(self.interactions, interaction_type)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if value != self._enabled:
            self._enabled = value
            if value:
                self.on_enable()
            else:
                self.on_disable()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        old_state = self._state
        self._state = value

        if old_state != value:
            if value == InteractorState.ACTIVE:
                self.on_enable()
            elif value == InteractorState.PAUSED:
                self.on_disable()
            elif value == InteractorState.DESTROYED:
                self.on_destroy()
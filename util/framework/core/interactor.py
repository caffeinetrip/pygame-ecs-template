import inspect
import asyncio
from typing import Any, List, Dict, Callable, Optional, Union, Coroutine
from enum import Enum, auto
from util.framework.core.component import Component

class OnEncounterStartInt:

    def __init__(self, debug: bool = True):
        self.debug = debug

    def activate(self, target: Any) -> None:
        if hasattr(target, 'on_encounter_start') and callable(target.on_encounter_start):
            if self.debug:
                print(f"Calling on_encounter_start on {target.__class__.__name__}")
            target.on_encounter_start()
        else:
            if self.debug:
                print(f"Object {target.__class__.__name__} does not implement on_encounter_start")


class InteractorState(Enum):
    INACTIVE = auto()
    ACTIVE = auto()
    PAUSED = auto()
    DESTROYED = auto()

class Interactor(Component):

    def __init__(self):
        super().__init__()
        self._enabled = True
        self._started = False
        self._coroutines = []
        self._loop = asyncio.get_event_loop()
        self._state = InteractorState.INACTIVE
        self._timers = {}
        self._child_interactors = []
        self._parent_interactor = None
        self._tag = ""
        self._layer = 0

    def awake(self):
        self._state = InteractorState.ACTIVE
        pass

    def start(self):
        pass

    def update(self, dt):
        pass

    def on_destroy(self):
        self.stop_all_coroutines()
        self._state = InteractorState.DESTROYED
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def on_encounter_start(self, args=None):
        pass

    def on_encounter_end(self, args=None):
        pass

    def start_coroutine(self, coroutine_func):
        if inspect.iscoroutinefunction(coroutine_func):
            task = self._loop.create_task(coroutine_func())
        elif inspect.iscoroutine(coroutine_func):
            task = self._loop.create_task(coroutine_func)
        else:
            task = self._loop.create_task(coroutine_func())

        self._coroutines.append(task)
        return task

    def stop_coroutine(self, task):
        if task in self._coroutines:
            task.cancel()
            self._coroutines.remove(task)

    def stop_all_coroutines(self):
        for task in self._coroutines:
            task.cancel()
        self._coroutines.clear()

    async def wait_for_seconds(self, seconds):
        await asyncio.sleep(seconds)

    async def wait_until(self, predicate):
        while not predicate():
            await asyncio.sleep(0.01)

    async def wait_while(self, predicate):
        while predicate():
            await asyncio.sleep(0.01)

    def set_timer(self, name, seconds, callback, repeat=False):

        async def timer_coroutine():
            if repeat:
                while True:
                    await asyncio.sleep(seconds)
                    callback()
            else:
                await asyncio.sleep(seconds)
                callback()
                del self._timers[name]

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
        pass

    def get_component_in_parent(self, component_type):
        pass

    def add_component(self, component_type, *args, **kwargs):
        return self.e.add_component(component_type, *args, **kwargs)

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

class EnhancedInteractorManager(Component):

    def __init__(self):
        super().__init__()
        self.interactors = {}
        self._pending_start = []
        self._encounter_interactors = set()
        self._loop = asyncio.get_event_loop()
        self._event_listeners = {}

    def add_interactor(self, name, interactor_type, *args, **kwargs):
        if inspect.isclass(interactor_type):
            interactor = interactor_type(*args, **kwargs)
        else:
            interactor = interactor_type

        self.interactors[name] = interactor
        interactor.e = self.e
        interactor.awake()
        self._pending_start.append(interactor)

        if hasattr(interactor, 'on_encounter_start') and callable(interactor.on_encounter_start):
            self._encounter_interactors.add(interactor)

        return interactor

    def get_interactor(self, name):
        return self.interactors.get(name)

    def get_interactors_of_type(self, interactor_type):
        return [i for i in self.interactors.values() if isinstance(i, interactor_type)]

    def remove_interactor(self, name):
        if name in self.interactors:
            interactor = self.interactors[name]

            if interactor in self._encounter_interactors:
                self._encounter_interactors.remove(interactor)

            interactor.on_destroy()
            interactor.stop_all_coroutines()
            del self.interactors[name]
            return True
        return False

    def update(self, dt):
        for interactor in self._pending_start:
            if interactor.enabled:
                interactor.start()
                interactor._started = True
        self._pending_start.clear()

        for interactor in self.interactors.values():
            if interactor.enabled and interactor.state == InteractorState.ACTIVE:
                interactor.update(dt)

        self._loop.call_soon(self._loop.stop)
        self._loop.run_forever()

    def fixed_update(self, fixed_dt):
        for interactor in self.interactors.values():
            if interactor.enabled and interactor.state == InteractorState.ACTIVE:
                interactor.fixed_update(fixed_dt)

    def register_event_listener(self, event_name, listener, callback):
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append((listener, callback))

    def unregister_event_listener(self, event_name, listener):
        if event_name in self._event_listeners:
            self._event_listeners[event_name] = [
                (l, c) for l, c in self._event_listeners[event_name] if l != listener
            ]

    def dispatch_event(self, event_name, event_data=None):
        if event_name in self._event_listeners:
            for listener, callback in self._event_listeners[event_name]:
                if listener.enabled and listener.state == InteractorState.ACTIVE:
                    callback(event_data)

    def trigger_encounter_start(self, args=None):
        for interactor in self._encounter_interactors:
            if interactor.enabled and interactor.state == InteractorState.ACTIVE:
                interaction = OnEncounterStartInt()
                interaction.activate(interactor)

        self.dispatch_event("encounter_start", args)

    def trigger_encounter_end(self, args=None):
        for interactor in self.interactors.values():
            if (interactor.enabled and interactor.state == InteractorState.ACTIVE and
                    hasattr(interactor, 'on_encounter_end') and callable(interactor.on_encounter_end)):
                interactor.on_encounter_end(args)

        self.dispatch_event("encounter_end", args)
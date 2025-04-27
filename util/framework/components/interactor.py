import asyncio
from util.framework.core.component import Component
import inspect

class Interactor(Component):

    def __init__(self):
        super().__init__()
        self.enabled = True
        self._started = False
        self._coroutines = []
        self._loop = asyncio.get_event_loop()

    def awake(self):
        pass

    def start(self):
        pass

    def update(self, dt):
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def handle_input(self, input_event):
        pass

    def on_collision_enter(self, other):
        pass

    def on_trigger_enter(self, other):
        pass

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

    def get_component(self, component_type):
        return self.e.get_component(component_type)

    def get_components(self, component_type):
        return self.e.get_components(component_type)

class InteractorManager(Component):

    def __init__(self):
        super().__init__()
        self.interactors = {}
        self._pending_start = []
        self._loop = asyncio.get_event_loop()

    def add_interactor(self, name, interactor_type, *args, **kwargs):
        if inspect.isclass(interactor_type):
            interactor = interactor_type(*args, **kwargs)
        else:
            interactor = interactor_type

        self.interactors[name] = interactor
        interactor.e = self.e
        interactor.awake()
        self._pending_start.append(interactor)
        return interactor

    def get_interactor(self, name):
        return self.interactors.get(name)

    def get_interactors_of_type(self, interactor_type):
        return [i for i in self.interactors.values() if isinstance(i, interactor_type)]

    def remove_interactor(self, name):
        if name in self.interactors:
            self.interactors[name].stop_all_coroutines()
            del self.interactors[name]

    def update(self, dt):
        for interactor in self._pending_start:
            if interactor.enabled:
                interactor.start()
                interactor._started = True
        self._pending_start.clear()

        for interactor in self.interactors.values():
            if interactor.enabled:
                interactor.update(dt)

        self._loop.call_soon(self._loop.stop)
        self._loop.run_forever()

    def handle_input(self, input_event):
        for interactor in self.interactors.values():
            if interactor.enabled:
                interactor.handle_input(input_event)

    def on_collision(self, other):
        for interactor in self.interactors.values():
            if interactor.enabled:
                interactor.on_collision_enter(other)
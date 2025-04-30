import inspect
import asyncio

from util.framework.globals import G
from util.framework.core.interactor import Interactor, InteractorState
from util.framework.core.intRegistry import InteractionRegistry

term_colors = {
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'RESET': '\033[0m'
}


class OnEncounterStartInt:
    def __init__(self, debug: bool = False):
        self.debug = debug

    async def activate(self, target):
        if hasattr(target, 'on_encounter_start') and callable(target.on_encounter_start):
            if self.debug:
                print(
                    f"{term_colors['GREEN']}{target.__class__.__name__} interactor successful load{term_colors['RESET']}")
            await target.on_encounter_start()
            if self.debug:
                print(
                    f"{term_colors['RED']}Object {target.__class__.__name__} does not implement on_encounter_start{term_colors['RESET']}")


class InteractorManager(Interactor):
    def __init__(self):
        super().__init__()
        self.interactors = {}
        self._pending_start = []
        self._encounter_interactors = set()
        self._encounter_update_interactors = set()
        self._encounter_pause_interactors = set()
        self._encounter_resume_interactors = set()
        self._loop = asyncio.get_running_loop() if asyncio._get_running_loop() else asyncio.get_event_loop()
        self._event_listeners = {}
        self._encounter_active = False

        self.start_interactions = []
        self.end_interactions = []
        self.update_interactions = []
        self._load_auto_interactions()

        G.register_component('im', self)

    def _load_auto_interactions(self):
        try:
            self.start_interactions = InteractionRegistry.get_encounter_start_instances()
            self.end_interactions = InteractionRegistry.get_encounter_end_instances()
            self.update_interactions = InteractionRegistry.get_encounter_update_instances()

            print(f"\033[92mLoaded auto-discovered interactions:\033[0m")
            print(f"\033[92m - {len(self.start_interactions)} encounter start interactions\033[0m")
            print(f"\033[92m - {len(self.end_interactions)} encounter end interactions\033[0m")
            print(f"\033[92m - {len(self.update_interactions)} encounter update interactions\033[0m")

        except Exception as e:
            print(f"\033[91mError loading auto interactions: {e}\033[0m")

    def add_interactor(self, name, interactor_type, *args, **kwargs):
        if inspect.isclass(interactor_type):
            interactor = interactor_type(*args, **kwargs)
        else:
            interactor = interactor_type

        self.interactors[name] = interactor
        interactor.e = G
        interactor.awake()
        self._pending_start.append(interactor)

        if hasattr(interactor, 'on_encounter_start') and callable(interactor.on_encounter_start):
            self._encounter_interactors.add(interactor)

        if hasattr(interactor, 'on_encounter_update') and callable(interactor.on_encounter_update):
            self._encounter_update_interactors.add(interactor)

        G.register_interactor(name, interactor)

        return interactor

    def get_interactor(self, name):
        return self.interactors.get(name)

    def get_all_interactors(self):
        return self.interactors

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

        if self._encounter_active:
            self.update_encounter()

        self._loop.call_soon(self._loop.stop)
        self._loop.run_forever()

    async def trigger_encounter_start(self, args=None):
        self._encounter_active = True

        for interactor in self._encounter_interactors:
            if interactor.enabled and interactor.state == InteractorState.ACTIVE:
                interaction = OnEncounterStartInt()
                self.start_coroutine(interaction.activate(interactor))

        for interaction in self.start_interactions:
            if interaction.enabled:
                print(f"\033[92mActivating auto interaction: {interaction.__class__.__name__}\033[0m")
                self.start_coroutine(interaction.on_encounter_start(args))

        self.dispatch_event("encounter_start", args)

    async def trigger_encounter_end(self, args=None):
        self._encounter_active = False

        for interactor in self.interactors.values():
            if (interactor.enabled and interactor.state == InteractorState.ACTIVE and
                    hasattr(interactor, 'on_encounter_end') and callable(interactor.on_encounter_end)):
                self.start_coroutine(interactor.on_encounter_end(args))

        for interaction in self.end_interactions:
            if interaction.enabled:
                print(f"\033[92mActivating auto interaction: {interaction.__class__.__name__}\033[0m")
                self.start_coroutine(interaction.on_encounter_end(args))

        self.dispatch_event("encounter_end", args)

    async def update_encounter(self, args=None):
        if not self._encounter_active:
            return

        for interaction in self.update_interactions:
            if interaction.enabled:
                self.start_coroutine(interaction.on_encounter_update(args))

        self.dispatch_event("encounter_update", args)

    def dispatch_event(self, event_name, event_data=None):
        if event_name in self._event_listeners:
            for listener, callback in self._event_listeners[event_name]:
                if listener.enabled and listener.state == InteractorState.ACTIVE:
                    callback(event_data)
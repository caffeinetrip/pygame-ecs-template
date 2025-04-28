import asyncio
import pygame
import sys
import json
from util.framework.core.component import Component
from util.framework.components.window import WindowComponent


class InputState:
    __slots__ = ('pressed', 'just_pressed', 'just_released', 'held_since')

    def __init__(self):
        self.pressed = False
        self.just_pressed = False
        self.just_released = False
        self.held_since = 0

    def update(self):
        self.just_pressed = False
        self.just_released = False

    def press(self, time=None):
        self.pressed = True
        self.just_pressed = True
        self.held_since = time or asyncio.get_event_loop().time()

    def unpress(self):
        self.pressed = False
        self.just_released = True


class MouseComponent(Component):
    def __init__(self):
        super().__init__()
        self.pos = pygame.Vector2(0, 0)
        self.ui_pos = pygame.Vector2(0, 0)
        self.movement = pygame.Vector2(0, 0)

    async def update(self):
        mpos = pygame.mouse.get_pos()
        self.movement.x, self.movement.y = mpos[0] - self.pos.x, mpos[1] - self.pos.y
        self.pos.x, self.pos.y = mpos[0], mpos[1]
        self.ui_pos.x, self.ui_pos.y = mpos[0] // 2, mpos[1] // 2


class InputComponent(Component):
    def __init__(self, path=None):
        super().__init__()
        self.state = 'main'
        self.text_buffer = None
        self.path = path

        # Load config once
        self.config = self._load_config(path) if path else {}
        self.config['__backspace'] = ['button', pygame.K_BACKSPACE]

        # Pre-process config for faster lookups
        self._mouse_configs = {}
        self._button_configs = {}
        for key, (input_type, value) in self.config.items():
            if input_type == 'mouse':
                if value not in self._mouse_configs:
                    self._mouse_configs[value] = []
                self._mouse_configs[value].append(key)
            elif input_type == 'button':
                if value not in self._button_configs:
                    self._button_configs[value] = []
                self._button_configs[value].append(key)

        self.input = {key: InputState() for key in self.config}
        self.hidden_keys = ['__backspace']
        self.repeat_rate = 0.02
        self.repeat_delay = 0.5
        self.repeat_times = {key: 0 for key in self.config}

        self.valid_chars_set = set(' .abcdefghijklmnopqrstuvwxyz0123456789,;-=/\\[]\'')

        self._char_code_map = {ord(char): char for char in self.valid_chars_set}

        self.shift_mappings = {
            '1': '!', '8': '*', '9': '(', '0': ')', ';': ':', ',': '<',
            '.': '>', '/': '?', '\'': '"', '-': '_', '=': '+',
        }
        self.shift = False
        self.mouse_entity = None
        self.event_handlers = {}
        self.priority_queue = asyncio.PriorityQueue()
        self._action_locks = {}
        self._actions_processed_this_frame = set()
        self._action_priorities = {}

        self._window_component = None

    def _load_config(self, path):
        if not path:
            return {}

        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def initialize(self):
        if not self.mouse_entity:
            self.mouse_entity = self.e.create_singleton("Mouse")
            self.mouse_entity.add_component(MouseComponent)

    def register_handler(self, action, handler, priority=0):
        self.event_handlers[action] = handler
        self._action_priorities[action] = priority
        if action not in self._action_locks:
            self._action_locks[action] = asyncio.Lock()

    def pressed(self, key):
        input_state = self.input.get(key)
        return input_state.just_pressed if input_state else False

    def holding(self, key):
        input_state = self.input.get(key)
        return input_state.pressed if input_state else False

    def released(self, key):
        input_state = self.input.get(key)
        return input_state.just_released if input_state else False

    def set_text_buffer(self, text_buffer=None):
        self.text_buffer = text_buffer

    async def process_event(self, event):
        event_type = event.type

        if event_type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event_type == pygame.MOUSEBUTTONDOWN:
            for mapping in self._mouse_configs.get(event.button, []):
                self.input[mapping].press()
                if mapping not in self._actions_processed_this_frame:
                    await self.trigger_action(mapping)
                    self._actions_processed_this_frame.add(mapping)

        elif event_type == pygame.MOUSEBUTTONUP:
            for mapping in self._mouse_configs.get(event.button, []):
                self.input[mapping].unpress()

        elif event_type == pygame.KEYDOWN:
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.shift = True

            if self.text_buffer:
                char = self._char_code_map.get(event.key)
                if char:
                    if self.shift:
                        char = char.upper()
                        if char in self.shift_mappings:
                            char = self.shift_mappings[char]
                    self.text_buffer.insert(char)
                elif event.key == pygame.K_RETURN:
                    self.text_buffer.enter()

            # Process keyboard mappings
            mappings = self.hidden_keys if self.text_buffer else self.config
            for mapping in self._button_configs.get(event.key, []):
                if mapping in mappings:
                    self.input[mapping].press()
                    if mapping not in self._actions_processed_this_frame:
                        await self.trigger_action(mapping)
                        self._actions_processed_this_frame.add(mapping)

        elif event_type == pygame.KEYUP:
            for mapping in self._button_configs.get(event.key, []):
                self.input[mapping].unpress()

            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.shift = False

    async def trigger_action(self, action):
        if action not in self._action_locks:
            self._action_locks[action] = asyncio.Lock()

        lock = self._action_locks[action]
        if lock.locked():
            return

        async with lock:
            handler = self.event_handlers.get(action)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()

            priority = self._action_priorities.get(action, 10)
            await self.priority_queue.put((priority, action))

    async def update(self):
        self._actions_processed_this_frame.clear()

        triggered_actions = [action for action, state in self.input.items() if state.just_pressed]

        for state in self.input.values():
            state.update()

        if self.mouse_entity:
            mouse_comp = self.mouse_entity.get_component(MouseComponent)
            if mouse_comp:
                await mouse_comp.update()

        for event in pygame.event.get():
            await self.process_event(event)

        if self.text_buffer:
            if not self._window_component:
                self._window_component = WindowComponent()
            window_time = self._window_component.time

            if self.pressed('__backspace'):
                self.repeat_times['__backspace'] = window_time
                self.text_buffer.delete()

            if self.holding('__backspace'):
                next_repeat = self.repeat_times['__backspace'] + self.repeat_delay
                if window_time > next_repeat:
                    repeats = int((window_time - next_repeat) / self.repeat_rate)
                    if repeats > 0:
                        self.repeat_times['__backspace'] += repeats * self.repeat_rate
                        for _ in range(min(repeats, 10)):
                            self.text_buffer.delete()

        for action in triggered_actions:
            if action not in self._actions_processed_this_frame:
                await self.trigger_action(action)
                self._actions_processed_this_frame.add(action)

    async def process_actions(self):
        while True:
            priority, action = await self.priority_queue.get()
            self.priority_queue.task_done()
            await asyncio.sleep(0)  # Yield to event loop

    async def start_processing(self):
        return asyncio.create_task(self.process_actions())
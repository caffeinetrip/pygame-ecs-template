import asyncio
import pygame
import sys
from util.framework.core.component import Component


class InputState:
    def __init__(self):
        self.pressed = False
        self.just_pressed = False
        self.just_released = False
        self.held_since = 0

    def update(self):
        self.just_pressed = False
        self.just_released = False

    def press(self):
        self.pressed = True
        self.just_pressed = True
        self.held_since = asyncio.get_event_loop().time()

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
        self.movement = pygame.Vector2(mpos[0] - self.pos[0], mpos[1] - self.pos[1])
        self.pos = pygame.Vector2(mpos[0], mpos[1])
        self.ui_pos = pygame.Vector2(mpos[0] // 2, mpos[1] // 2)


class InputComponent(Component):
    def __init__(self, path=None):
        super().__init__()
        self.state = 'main'
        self.text_buffer = None
        self.path = path
        self.config = self.load_config(path) if path else {}
        self.config['__backspace'] = ['button', pygame.K_BACKSPACE]
        self.input = {key: InputState() for key in self.config}
        self.hidden_keys = ['__backspace']
        self.repeat_rate = 0.02
        self.repeat_delay = 0.5
        self.repeat_times = {key: 0 for key in self.config}
        self.valid_chars = [' ', '.', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                            'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7',
                            '8', '9', ',', ';', '-', '=', '/', '\\', '[', ']', '\'']
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

    def load_config(self, path):
        try:
            with open(path, 'r') as f:
                import json
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def initialize(self):
        if not self.mouse_entity:
            self.mouse_entity = self.e.create_singleton("Mouse")
            self.mouse_entity.add_component(MouseComponent)

    def register_handler(self, action, handler, priority=0):
        self.event_handlers[action] = handler
        self._action_locks[action] = asyncio.Lock()
        self._action_priorities[action] = priority

    def pressed(self, key):
        return self.input[key].just_pressed if key in self.input else False

    def holding(self, key):
        return self.input[key].pressed if key in self.input else False

    def released(self, key):
        return self.input[key].just_released if key in self.input else False

    def set_text_buffer(self, text_buffer=None):
        self.text_buffer = text_buffer

    async def process_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            for mapping in self.config:
                if self.config[mapping][0] == 'mouse' and event.button == self.config[mapping][1]:
                    self.input[mapping].press()
                    if mapping not in self._actions_processed_this_frame:
                        await self.trigger_action(mapping)
                        self._actions_processed_this_frame.add(mapping)

        elif event.type == pygame.MOUSEBUTTONUP:
            for mapping in self.config:
                if self.config[mapping][0] == 'mouse' and event.button == self.config[mapping][1]:
                    self.input[mapping].unpress()

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                self.shift = True

            if self.text_buffer:
                for char in self.valid_chars:
                    if event.key == ord(char):
                        new_char = char
                        if self.shift:
                            new_char = new_char.upper()
                            if new_char in self.shift_mappings:
                                new_char = self.shift_mappings[new_char]
                        self.text_buffer.insert(new_char)

                if event.key == pygame.K_RETURN:
                    self.text_buffer.enter()

            mappings = self.hidden_keys if self.text_buffer else self.config

            for mapping in mappings:
                if self.config[mapping][0] == 'button' and event.key == self.config[mapping][1]:
                    self.input[mapping].press()
                    if mapping not in self._actions_processed_this_frame:
                        await self.trigger_action(mapping)
                        self._actions_processed_this_frame.add(mapping)

        elif event.type == pygame.KEYUP:
            for mapping in self.config:
                if self.config[mapping][0] == 'button' and event.key == self.config[mapping][1]:
                    self.input[mapping].unpress()

            if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                self.shift = False

    async def trigger_action(self, action):
        if action not in self._action_locks:
            self._action_locks[action] = asyncio.Lock()

        if self._action_locks[action].locked():
            return

        async with self._action_locks[action]:
            if action in self.event_handlers:
                handler = self.event_handlers[action]
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()

            priority = self._action_priorities.get(action, 10)
            await self.priority_queue.put((priority, action))

    async def update(self):
        self._actions_processed_this_frame = set()

        triggered_actions = []
        for action, state in self.input.items():
            if state.just_pressed:
                triggered_actions.append(action)

        for state in self.input.values():
            state.update()

        mouse_comp = self.e["Mouse"].get_component(MouseComponent)
        await mouse_comp.update()

        for event in pygame.event.get():
            await self.process_event(event)

        window_entity = self.e["Window"]
        if window_entity and self.text_buffer:
            from util.framework.components.window import WindowComponent
            window_time = window_entity.get_component(WindowComponent).time

            if self.pressed('__backspace'):
                self.repeat_times['__backspace'] = window_time
                self.text_buffer.delete()

            if self.holding('__backspace'):
                while window_time > self.repeat_times['__backspace'] + self.repeat_delay + self.repeat_rate:
                    self.repeat_times['__backspace'] += self.repeat_rate
                    self.text_buffer.delete()

        for action in triggered_actions:
            if action not in self._actions_processed_this_frame:
                await self.trigger_action(action)
                self._actions_processed_this_frame.add(action)

    async def process_actions(self):
        while True:
            priority, action = await self.priority_queue.get()
            self.priority_queue.task_done()
            await asyncio.sleep(0)

    async def start_processing(self):
        loop = asyncio.get_event_loop()
        return loop.create_task(self.process_actions())
import asyncio
import pygame
import sys
from util.framework.globals import G
from util.framework.core.component import Component


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
    def __init__(self):
        super().__init__()
        self.state = 'main'
        self.text_buffer = None

        self.key_states = {}
        self.mouse_states = {}

        self.shift = False
        self.repeat_rate = 0.02
        self.repeat_delay = 0.5
        self.last_backspace_time = 0

        self.valid_chars_set = set(' .abcdefghijklmnopqrstuvwxyz0123456789,;-=/\\[]\'')
        self._char_code_map = {ord(char): char for char in self.valid_chars_set}

        self.shift_mappings = {
            '1': '!', '8': '*', '9': '(', '0': ')', ';': ':', ',': '<',
            '.': '>', '/': '?', '\'': '"', '-': '_', '=': '+',
        }

        self.mouse_entity = None
        self.event_handlers = {}
        self.priority_queue = asyncio.PriorityQueue()
        self._action_locks = {}
        self._window_component = None

    def initialize(self):
        if not self.mouse_entity:
            self.mouse_entity = G.game.create_singleton("Mouse")
            self.mouse_entity.add_component(MouseComponent)

    def register_handler(self, key, handler, priority=0):
        self.event_handlers[key] = handler
        if key not in self._action_locks:
            self._action_locks[key] = asyncio.Lock()

    def pressed(self, key):
        state = self.key_states.get(key)
        return state.just_pressed if state else False

    def holding(self, key):
        state = self.key_states.get(key)
        return state.pressed if state else False

    def released(self, key):
        state = self.key_states.get(key)
        return state.just_released if state else False

    def mouse_pressed(self, button):
        state = self.mouse_states.get(button)
        return state.just_pressed if state else False

    def mouse_holding(self, button):
        state = self.mouse_states.get(button)
        return state.pressed if state else False

    def mouse_released(self, button):
        state = self.mouse_states.get(button)
        return state.just_released if state else False

    def set_text_buffer(self, text_buffer=None):
        self.text_buffer = text_buffer

    async def process_event(self, event):
        event_type = event.type

        if event_type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event_type == pygame.MOUSEBUTTONDOWN:
            if event.button not in self.mouse_states:
                self.mouse_states[event.button] = InputState()
            self.mouse_states[event.button].press()
            await self.trigger_action(f"mouse_{event.button}")

        elif event_type == pygame.MOUSEBUTTONUP:
            if event.button in self.mouse_states:
                self.mouse_states[event.button].unpress()

        elif event_type == pygame.KEYDOWN:
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.shift = True

            if event.key not in self.key_states:
                self.key_states[event.key] = InputState()
            self.key_states[event.key].press()

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
                elif event.key == pygame.K_BACKSPACE:
                    self.text_buffer.delete()
                    self.last_backspace_time = asyncio.get_event_loop().time()

            await self.trigger_action(event.key)

        elif event_type == pygame.KEYUP:
            if event.key in self.key_states:
                self.key_states[event.key].unpress()

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

    async def update(self):
        for state in self.key_states.values():
            state.update()

        for state in self.mouse_states.values():
            state.update()

        if self.mouse_entity:
            mouse_comp = self.mouse_entity.get_component(MouseComponent)
            if mouse_comp:
                await mouse_comp.update()

        for event in pygame.event.get():
            await self.process_event(event)

        if self.text_buffer and self.holding(pygame.K_BACKSPACE):
            current_time = asyncio.get_event_loop().time()
            next_repeat = self.last_backspace_time + self.repeat_delay

            if current_time > next_repeat:
                repeats = int((current_time - next_repeat) / self.repeat_rate)
                if repeats > 0:
                    self.last_backspace_time += repeats * self.repeat_rate
                    for _ in range(min(repeats, 10)):
                        self.text_buffer.delete()

    def get_mouse_position(self):
        if self.mouse_entity:
            mouse_comp = self.mouse_entity.get_component(MouseComponent)
            if mouse_comp:
                return mouse_comp.pos
        return pygame.Vector2(0, 0)

    def get_mouse_ui_position(self):
        if self.mouse_entity:
            mouse_comp = self.mouse_entity.get_component(MouseComponent)
            if mouse_comp:
                return mouse_comp.ui_pos
        return pygame.Vector2(0, 0)
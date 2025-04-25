import sys
import time
import pygame
from util.framework.core.component import Component
from util.framework.components.flags import FlagComponent
from util.framework.utils.io import read_json


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
        self.held_since = time.time()

    def unpress(self):
        self.pressed = False
        self.just_released = True


class MouseComponent(Component):
    def __init__(self):
        super().__init__()
        self.pos = pygame.Vector2(0, 0)
        self.ui_pos = pygame.Vector2(0, 0)
        self.movement = pygame.Vector2(0, 0)

    def update(self):
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
        self.config = read_json(path) if path else {}
        self.config['__backspace'] = ['button', pygame.K_BACKSPACE]
        self.input = {key: InputState() for key in self.config}
        self.hidden_keys = ['__backspace']

        self.repeat_rate = 0.02
        self.repeat_delay = 0.5
        self.repeat_times = {key: time.time() for key in self.config}
        self.valid_chars = [' ', '.', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                            'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7',
                            '8', '9', ',', ';', '-', '=', '/', '\\', '[', ']', '\'']
        self.shift_mappings = {
            '1': '!',
            '8': '*',
            '9': '(',
            '0': ')',
            ';': ':',
            ',': '<',
            '.': '>',
            '/': '?',
            '\'': '"',
            '-': '_',
            '=': '+',
        }
        self.shift = False
        self.mouse_entity = None

    def initialize(self):
        if not self.mouse_entity:
            self.mouse_entity = self.e.create_singleton("Mouse")
            self.mouse_entity.add_component(MouseComponent)

    def pressed(self, key):
        return self.input[key].just_pressed if key in self.input else False

    def holding(self, key):
        return self.input[key].pressed if key in self.input else False

    def released(self, key):
        return self.input[key].just_released if key in self.input else False

    def movement(self):
        pass

    def set_text_buffer(self, text_buffer=None):
        self.text_buffer = text_buffer

    def update(self):
        for state in self.input.values():
            state.update()

        mouse_comp = self.e["Mouse"].get_component(MouseComponent)
        mouse_comp.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for mapping in self.config:
                    if self.config[mapping][0] == 'mouse':
                        if event.button == self.config[mapping][1]:
                            self.input[mapping].press()
            if event.type == pygame.MOUSEBUTTONUP:
                for mapping in self.config:
                    if self.config[mapping][0] == 'mouse':
                        if event.button == self.config[mapping][1]:
                            self.input[mapping].unpress()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                    self.shift = True

                if self.text_buffer:
                    for char in self.valid_chars:
                        new_char = None
                        if event.key == ord(char):
                            new_char = char
                        if new_char:
                            if self.shift:
                                new_char = new_char.upper()
                                if new_char in self.shift_mappings:
                                    new_char = self.shift_mappings[new_char]
                            self.text_buffer.insert(new_char)

                    if event.key == pygame.K_RETURN:
                        self.text_buffer.enter()

                mappings = self.config
                if self.text_buffer:
                    mappings = self.hidden_keys

                for mapping in mappings:
                    if self.config[mapping][0] == 'button':
                        if event.key == self.config[mapping][1]:
                            self.input[mapping].press()

            if event.type == pygame.KEYUP:
                for mapping in self.config:
                    if self.config[mapping][0] == 'button':
                        if event.key == self.config[mapping][1]:
                            self.input[mapping].unpress()

                if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                    self.shift = False

        window_entity = self.e["Window"]
        if window_entity and self.text_buffer:
            window_time = window_entity.get_component(WindowComponent).time

            if self.pressed('__backspace'):
                self.repeat_times['__backspace'] = window_time
                self.text_buffer.delete()

            if self.holding('__backspace'):
                while window_time > self.repeat_times['__backspace'] + self.repeat_delay + self.repeat_rate:
                    self.repeat_times['__backspace'] += self.repeat_rate
                    self.text_buffer.delete()
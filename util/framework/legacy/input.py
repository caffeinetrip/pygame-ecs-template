import sys
import time
import pygame
from util.framework import world
from util.framework.components.input import InputComponent, MouseComponent


class Mouse:
    def __init__(self):
        from util.framework import world
        self.e = world
        self._name = "Mouse"
        self._singleton = True

        self.entity = world.create_singleton(self._name)
        self.mouse_component = self.entity.add_component(MouseComponent)

    @property
    def pos(self):
        return self.mouse_component.pos

    @pos.setter
    def pos(self, value):
        self.mouse_component.pos = value

    @property
    def ui_pos(self):
        return self.mouse_component.ui_pos

    @ui_pos.setter
    def ui_pos(self, value):
        self.mouse_component.ui_pos = value

    @property
    def movement(self):
        return self.mouse_component.movement

    @movement.setter
    def movement(self, value):
        self.mouse_component.movement = value

    def update(self):
        self.mouse_component.update()

    def delete(self):
        self.entity.delete()


class Input:
    def __init__(self, path=None):
        from util.framework import world
        self.e = world
        self._name = "Input"
        self._singleton = True

        self.entity = world.create_singleton(self._name)
        self.input_component = self.entity.add_component(InputComponent, path)
        self.input_component.initialize()
        self.mouse = Mouse()

    @property
    def state(self):
        return self.input_component.state

    @state.setter
    def state(self, value):
        self.input_component.state = value

    @property
    def text_buffer(self):
        return self.input_component.text_buffer

    @text_buffer.setter
    def text_buffer(self, value):
        self.input_component.text_buffer = value

    @property
    def config(self):
        return self.input_component.config

    @config.setter
    def config(self, value):
        self.input_component.config = value

    @property
    def input(self):
        return self.input_component.input

    @input.setter
    def input(self, value):
        self.input_component.input = value

    @property
    def hidden_keys(self):
        return self.input_component.hidden_keys

    @hidden_keys.setter
    def hidden_keys(self, value):
        self.input_component.hidden_keys = value

    @property
    def repeat_rate(self):
        return self.input_component.repeat_rate

    @repeat_rate.setter
    def repeat_rate(self, value):
        self.input_component.repeat_rate = value

    @property
    def repeat_delay(self):
        return self.input_component.repeat_delay

    @repeat_delay.setter
    def repeat_delay(self, value):
        self.input_component.repeat_delay = value

    @property
    def repeat_times(self):
        return self.input_component.repeat_times

    @repeat_times.setter
    def repeat_times(self, value):
        self.input_component.repeat_times = value

    @property
    def valid_chars(self):
        return self.input_component.valid_chars

    @valid_chars.setter
    def valid_chars(self, value):
        self.input_component.valid_chars = value

    @property
    def shift_mappings(self):
        return self.input_component.shift_mappings

    @shift_mappings.setter
    def shift_mappings(self, value):
        self.input_component.shift_mappings = value

    @property
    def shift(self):
        return self.input_component.shift

    @shift.setter
    def shift(self, value):
        self.input_component.shift = value

    def pressed(self, key):
        return self.input_component.pressed(key)

    def holding(self, key):
        return self.input_component.holding(key)

    def released(self, key):
        return self.input_component.released(key)

    def movement(self):
        return self.input_component.movement()

    def set_text_buffer(self, text_buffer=None):
        self.input_component.set_text_buffer(text_buffer)

    def update(self):
        self.input_component.update()

    def delete(self):
        self.entity.delete()
        if hasattr(self, 'mouse') and self.mouse:
            self.mouse.delete()
import pygame

from threading import Timer

from ..misc.errors import InvalidAsset
from ..utils.elements import ElementSingleton
from ..utils.io import recursive_file_op

class Sounds(ElementSingleton):
    def __init__(self, path=None, filetype='wav'):
        super().__init__()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(64)
        self.path = path
        self.filetype = filetype
        self.pan_vol = True
        if path:
            self.load(path)
    
    def load(self, path):
        self.path = path
        self.sounds = recursive_file_op(self.path, lambda x: pygame.mixer.Sound(x), filetype=self.filetype)

    def play(self, sound_id, volume=1.0, pan=0, times=0):
        sound_id_split = sound_id.split('/')
        s = self.sounds
        while len(sound_id_split):
            next_id = sound_id_split.pop(0)
            if (type(s) == dict) and (next_id in s):
                s = s[next_id]
            else:
                raise InvalidAsset(sound_id)
        if type(s) != pygame.mixer.Sound:
            raise InvalidAsset(sound_id)

        channel = s.play(times)
        if pan:
            volumes = (1 - (pan + 1) / 2, (pan + 1) / 2)
            if self.pan_vol:
                volume *= 1 - abs(pan) * 0.9
            channel.set_volume(volumes[0] * volume, volumes[1] * volume)
        else:
            channel.set_volume(volume)
        
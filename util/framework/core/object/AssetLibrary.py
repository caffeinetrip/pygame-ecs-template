import os
import pygame

from ..interactors.interactor import Interactor
from ...utils import load_img_directory, read_json, write_json
from ..assets.animation import Animation


class ObjectData:
    def __init__(self, settings, sequences=None):
        self.settings = settings
        self.graphics = load_img_directory(self.settings['resource_path'], colorkey=self.settings['transparency'])
        self.sequences = {}
        for sequence in self.settings['sequences']:
            if sequence in self.graphics:
                first_frame = list(self.graphics[sequence])[0]
                index_part = first_frame.split('_')[-1]
                if len(index_part) and index_part.isnumeric():
                    indexed_frames = [(int(fname.split('_')[-1]), '_'.join(fname.split('_')[:-1])) for fname
                                      in self.graphics[sequence] if fname.split('_')[-1].isnumeric()]
                    indexed_frames.sort()
                    ordered_frames = [frame[1] + ('_' if len(frame[1]) else '') + str(frame[0]) for
                                      frame in indexed_frames]
                    sequence_frames = [self.graphics[sequence][fname] for fname in ordered_frames if
                                       type(self.graphics[sequence][fname]) == pygame.Surface]
                else:
                    sequence_frames = [img for img in self.graphics[sequence].values() if type(img) == pygame.Surface]
                self.sequences[sequence] = Animation(sequence_frames, config=self.settings['sequences'][sequence])


class AssetLibrary(Interactor):
    def __init__(self, directory=None):
        super().__init__()
        self.directory = directory
        self.assets = {}
        if directory:
            self.initialize(directory)

    def initialize(self, directory):
        self.directory = directory
        self.build_asset_registry()

    def __getitem__(self, key):
        if key in self.assets:
            return self.assets[key]
        else:
            return None

    def build_asset_registry(self):
        for object_dir in os.listdir(self.directory):
            sequences = []
            static_images = []

            settings = {
                'images': {},
                'sequences': {},
                'resource_path': self.directory + '/' + object_dir,
                'uid': object_dir,
                'centered': False,
                'offset': [0, 0],
                'transparency': [0, 0, 0],
                'dimensions': [1, 1],
                'category': 'object',
                'collisions': [],
                'initial': None
            }

            for file in os.listdir(self.directory + '/' + object_dir):
                if file.find('.') == -1:
                    sequences.append(file)
                elif file.split('.')[-1] == 'png':
                    static_images.append(file.split('.')[0])
                if file == 'config.json':
                    settings = read_json(self.directory + '/' + object_dir + '/' + file)

            for img in static_images:
                if img not in settings['images']:
                    settings['images'][img] = {'offset': [0, 0]}

            for seq in sequences:
                if seq not in settings['sequences']:
                    frames = os.listdir(self.directory + '/' + object_dir + '/' + seq)
                    settings['sequences'][seq] = {
                        'offset': [0, 0],
                        'rate': 1.0,
                        'repeat': True,
                        'frozen': False,
                        'durations': []
                    }
                    for frame in frames:
                        if frame.split('.')[-1] == 'png':
                            settings['sequences'][seq]['durations'].append(0.1)

            if not settings['initial']:
                if len(sequences):
                    settings['initial'] = sequences[0]
                elif len(static_images):
                    settings['initial'] = static_images[0]

            write_json(self.directory + '/' + object_dir + '/config.json', settings)
            self.assets[settings['uid']] = ObjectData(settings)
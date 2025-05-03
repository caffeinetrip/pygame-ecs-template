import os
import pygame
import json

from ..interactors.interactor import Interactor
from ...utils import load_img_directory, read_json, write_json
from ..assets.animation import Animation


class ObjectData:
    def __init__(self, settings, resources=None):
        self.specs = settings
        self.settings = settings
        self.resources = resources or {}
        self.sequences = {}

        for sequence_name, sequence_config in self.specs.get('sequences', {}).items():
            sequence_images = []

            sequence_parts = sequence_name.split('/')
            current_dict = self.resources

            for i, part in enumerate(sequence_parts):
                if isinstance(current_dict, dict) and part in current_dict:
                    current_dict = current_dict[part]
                else:
                    current_dict = None
                    break

            if current_dict and isinstance(current_dict, dict):
                sorted_items = []
                for key, value in current_dict.items():
                    if isinstance(value, pygame.Surface):
                        try:
                            num = int(key.split('_')[-1])
                            sorted_items.append((num, value))
                        except ValueError:
                            sorted_items.append((0, value))

                sorted_items.sort(key=lambda x: x[0])
                sequence_images = [item[1] for item in sorted_items]

            if sequence_images:
                self.sequences[sequence_name] = Animation(
                    sequence_images,
                    config=sequence_config
                )


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
        return self.assets.get(key, None)

    def build_asset_registry(self):
        if not os.path.exists(self.directory):
            return

        for object_dir in os.listdir(self.directory):
            object_path = os.path.join(self.directory, object_dir)
            if not os.path.isdir(object_path):
                continue

            settings = {
                'uid': object_dir,
                'size': [16, 16],
                'offset': [0, 0],
                'transparency': [0, 0, 0],
                'centered': False,
                'category': 'object',
                'images': {},
                'sequences': {},
                'initial': None,
                'resource_path': object_path
            }

            config_path = os.path.join(object_path, 'config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        loaded_settings = json.load(f)
                        settings.update(loaded_settings)
                except Exception as e:
                    pass

            resources = load_img_directory(object_path, colorkey=settings.get('transparency', [0, 0, 0]))
            self.assets[settings['uid']] = ObjectData(settings, resources)
import yaml
import os
import datetime
from typing import Any, Dict, List
import pygame

_serializable_registry = {}
_auto_save_classes = []

DEFAULT_SAVE_PATH = "data/saves"


def yaml_serializable(cls=None, *, auto_save=True, folder=None):
    def decorator(cls):
        _serializable_registry[cls.__name__] = cls

        if auto_save:
            _auto_save_classes.append(cls)

        save_folder = os.path.join(DEFAULT_SAVE_PATH, folder or cls.__name__.lower())

        def to_dict(self):
            result = {
                '__class__': self.__class__.__name__,
                '__timestamp__': datetime.datetime.now().isoformat()
            }

            for field in self.__dict__:
                if not field.startswith('_'):
                    value = getattr(self, field, None)
                    result[field] = _serialize_value(value)

            return result

        def to_yaml(self, filepath=None):
            if filepath is None:
                os.makedirs(save_folder, exist_ok=True)
                filepath = os.path.join(save_folder, f"{self.__class__.__name__}.yaml")

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False)

            return filepath

        @classmethod
        def from_dict(cls, data):
            instance = cls.__new__(cls)

            try:
                instance.__init__()
            except:
                pass

            for field, value in data.items():
                if not field.startswith('__'):
                    setattr(instance, field, _deserialize_value(value))

            return instance

        @classmethod
        def from_yaml(cls, filepath=None):
            if filepath is None:
                filepath = os.path.join(save_folder, f"{cls.__name__}.yaml")

            if not os.path.exists(filepath):
                return cls()

            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            return cls.from_dict(data)

        cls.to_dict = to_dict
        cls.to_yaml = to_yaml
        cls.from_dict = from_dict
        cls.from_yaml = from_yaml

        return cls

    if cls is None:
        return decorator
    return decorator(cls)

def _serialize_value(value):
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    elif isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, pygame.Vector2):
        return {'__type__': 'pygame.Vector2', 'x': value.x, 'y': value.y}
    elif isinstance(value, pygame.Rect):
        return {'__type__': 'pygame.Rect', 'x': value.x, 'y': value.y,
                'width': value.width, 'height': value.height}
    elif hasattr(value, 'to_dict') and callable(value.to_dict):
        return value.to_dict()
    else:
        return str(value)

def _deserialize_value(value):
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    elif isinstance(value, list):
        return [_deserialize_value(item) for item in value]
    elif isinstance(value, dict):
        if '__type__' in value:
            if value['__type__'] == 'pygame.Vector2':
                return pygame.Vector2(value['x'], value['y'])
            elif value['__type__'] == 'pygame.Rect':
                return pygame.Rect(value['x'], value['y'], value['width'], value['height'])

        if '__class__' in value and value['__class__'] in _serializable_registry:
            return _serializable_registry[value['__class__']].from_dict(value)

        return {k: _deserialize_value(v) for k, v in value.items()}
    else:
        return value

def auto_save_all(instances_dict):
    for class_name, instance in instances_dict.items():
        instance.to_yaml()


def auto_load_all():
    instances = {}
    for cls in _auto_save_classes:
        instances[cls.__name__] = cls.from_yaml()
    return instances
import yaml
import os
import datetime
from typing import Any, Dict, List
import pygame
from util.framework import G

_serializable_registry = {}
_auto_save_classes = []

DEFAULT_SAVE_PATH = "data/saves"


def yaml_serializable(cls=None, *, auto_save=True, folder=None):
    def decorator(cls):
        _serializable_registry[cls.__name__] = cls
        if auto_save:
            _auto_save_classes.append(cls)

        save_folder = os.path.join(DEFAULT_SAVE_PATH, folder or cls.__name__.lower())
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            if getattr(self, '_loading_from_dict', False):
                return

            try:
                filepath = os.path.join(save_folder, f"{cls.__name__}.yaml")
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        data = yaml.safe_load(f)
                    if data.get('__class__') == cls.__name__:
                        for field, value in data.items():
                            if not field.startswith('__'):
                                setattr(self, field, _deserialize_value(value))
            except Exception as e:
                print(f"Could not load data for {cls.__name__}: {e}")

        cls.__init__ = new_init

        def to_dict(self):
            result = {
                '__class__': self.__class__.__name__,
                '__timestamp__': datetime.datetime.now().isoformat()
            }
            for field in self.__dict__:
                if not field.startswith('_'):
                    result[field] = _serialize_value(getattr(self, field, None))
            return result

        def to_yaml(self, filepath=None):
            if filepath is None:
                os.makedirs(save_folder, exist_ok=True)
                filepath = os.path.join(save_folder, f"{self.__class__.__name__}.yaml")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False)
            return filepath

        def from_dict(cls_param, data):
            instance = cls_param.__new__(cls_param)
            instance._loading_from_dict = True
            try:
                instance.__init__()
            except Exception as e:
                print(f"Error in __init__ during from_dict: {e}")
            instance._loading_from_dict = False
            for field, value in data.items():
                if not field.startswith('__'):
                    setattr(instance, field, _deserialize_value(value))
            return instance

        def from_yaml(cls_param, filepath=None):
            if filepath is None:
                filepath = os.path.join(save_folder, f"{cls_param.__name__}.yaml")
            if not os.path.exists(filepath):
                return cls_param()
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            return from_dict(cls_param, data)

        cls.to_dict = to_dict
        cls.to_yaml = to_yaml
        cls.from_dict = classmethod(from_dict)
        cls.from_yaml = classmethod(from_yaml)
        return cls

    return decorator if cls is None else decorator(cls)


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


def auto_save_all(instances_dict=None):
    if instances_dict is None:
        return
    for class_name, instance in instances_dict.items():
        if hasattr(instance, 'to_yaml') and callable(instance.to_yaml):
            instance.to_yaml()


def auto_load_all():
    instances = {}
    for cls in _auto_save_classes:
        instance = cls()
        instances[cls.__name__] = instance
        if hasattr(G, 'register'):
            G.register(cls.__name__, instance)
    return instances
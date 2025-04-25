import json
from util.framework.core.component import Component


class MetaState:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def save(self, filepath='meta_state.json'):
        with open(filepath, 'w') as f:
            json.dump(self.data, f)

    @classmethod
    def load(cls, filepath='meta_state.json'):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            meta_state = cls()
            meta_state.data = data
            return meta_state
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    @classmethod
    def load_or_initialize_new(cls, filepath='meta_state.json'):
        meta_state = cls.load(filepath)
        if meta_state is None:
            meta_state = cls()
        return meta_state


class MetaStateComponent(Component):
    def __init__(self, filepath='meta_state.json'):
        super().__init__()
        self.filepath = filepath
        self.meta = None

    def init(self):
        self.meta = MetaState.load_or_initialize_new(self.filepath)

    def save(self):
        if self.meta:
            self.meta.save(self.filepath)
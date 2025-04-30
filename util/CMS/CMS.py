import inspect
import os
import importlib
import yaml
from typing import Dict, List, Type, TypeVar, Any, Tuple, Optional, Generic, Union, get_type_hints

from util.framework.globals import G

T = TypeVar('T', bound='EntityComponentDefinition')
E = TypeVar('E', bound='CMSEntity')


class EntityComponentDefinition:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class CMSEntity:
    def __init__(self, entity_id: str = None):
        self.id = entity_id or self.__class__.__name__
        self.components: List[EntityComponentDefinition] = []

    def define(self, component_class: Type[T], **kwargs) -> T:
        existing = self.get(component_class)
        if existing:
            return existing

        component = component_class(**kwargs)
        self.components.append(component)
        return component

    def is_a(self, component_class: Type[T], out_component: List[T] = None) -> bool:
        component = self.get(component_class)
        if component and out_component is not None:
            out_component.append(component)
        return component is not None

    def get(self, component_class: Type[T]) -> Optional[T]:
        for component in self.components:
            if isinstance(component, component_class):
                return component
        return None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'components': []
        }

        for component in self.components:
            if hasattr(component, 'to_dict') and callable(component.to_dict):
                result['components'].append(component.to_dict())
            else:
                comp_dict = {'__class__': component.__class__.__name__}
                for key, value in component.__dict__.items():
                    if not key.startswith('_'):
                        comp_dict[key] = value
                result['components'].append(comp_dict)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CMSEntity':
        entity = cls(data.get('id'))

        for comp_data in data.get('components', []):
            comp_class_name = comp_data.pop('__class__', None)
            if comp_class_name:
                comp_class = CMS.find_component_class(comp_class_name)
                if comp_class:
                    kwargs = {k: v for k, v in comp_data.items() if not k.startswith('__')}
                    entity.define(comp_class, **kwargs)

        return entity


class CMSTable(Generic[E]):
    def __init__(self):
        self.entities: List[E] = []
        self.entity_map: Dict[str, E] = {}

    def add(self, entity: E) -> None:
        if not entity.id:
            entity.id = entity.__class__.__name__

        self.entities.append(entity)
        self.entity_map[entity.id] = entity

    def get_all(self) -> List[E]:
        return self.entities

    def find_by_id(self, entity_id: str) -> Optional[E]:
        return self.entity_map.get(entity_id)

    def find_by_type(self, entity_class: Type[E]) -> List[E]:
        return [e for e in self.entities if isinstance(e, entity_class)]


class CMS:
    _entities = CMSTable[CMSEntity]()
    _initialized = False
    _component_classes: Dict[str, Type[EntityComponentDefinition]] = {}

    @classmethod
    def init(cls) -> None:
        if cls._initialized:
            return

        cls._initialized = True
        cls._auto_add()

    @classmethod
    def _auto_add(cls) -> None:
        cls._discover_component_classes()

        for entity_class in cls._find_entity_classes():
            try:
                entity = entity_class()
                cls._entities.add(entity)
                print(f"Registered entity: {entity.id}")
            except Exception as e:
                print(f"Error creating entity {entity_class.__name__}: {e}")

        cls._load_yaml_entities()

    @classmethod
    def _discover_component_classes(cls) -> None:
        for component_class in cls._find_all_subclasses(EntityComponentDefinition):
            cls._component_classes[component_class.__name__] = component_class

    @classmethod
    def _find_entity_classes(cls) -> List[Type[CMSEntity]]:
        return cls._find_all_subclasses(CMSEntity)

    @classmethod
    def _find_all_subclasses(cls, base_class: Type) -> List[Type]:
        all_subclasses = []

        for subclass in base_class.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(cls._find_all_subclasses(subclass))

        return all_subclasses

    @classmethod
    def _load_yaml_entities(cls, folder: str = "resources/cms") -> None:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            return

        for filename in os.listdir(folder):
            if filename.endswith((".yaml", ".yml")):
                filepath = os.path.join(folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)

                    if isinstance(data, list):
                        for entity_data in data:
                            entity = CMSEntity.from_dict(entity_data)
                            cls._entities.add(entity)
                            print(f"Loaded entity from YAML: {entity.id}")
                    elif isinstance(data, dict):
                        entity = CMSEntity.from_dict(data)
                        cls._entities.add(entity)
                        print(f"Loaded entity from YAML: {entity.id}")

                except Exception as e:
                    print(f"Error loading YAML file {filename}: {e}")

    @classmethod
    def get(cls, entity_id: str = None, entity_class: Type[E] = None) -> Optional[Union[CMSEntity, E]]:
        if not cls._initialized:
            cls.init()

        if entity_id is None and entity_class is not None:
            entity_id = entity_class.__name__

        return cls._entities.find_by_id(entity_id)

    @classmethod
    def get_data(cls, component_class: Type[T], entity_id: str = None) -> Optional[T]:
        entity = cls.get(entity_id)
        if entity:
            return entity.get(component_class)
        return None

    @classmethod
    def get_all(cls, entity_class: Type[E] = None) -> List[Union[CMSEntity, E]]:
        if not cls._initialized:
            cls.init()

        if entity_class:
            return [e for e in cls._entities.get_all() if isinstance(e, entity_class)]
        return cls._entities.get_all()

    @classmethod
    def get_all_data(cls, component_class: Type[T]) -> List[Tuple[CMSEntity, T]]:
        if not cls._initialized:
            cls.init()

        result = []
        for entity in cls._entities.get_all():
            component = entity.get(component_class)
            if component:
                result.append((entity, component))

        return result

    @classmethod
    def find_component_class(cls, class_name: str) -> Optional[Type[EntityComponentDefinition]]:
        return cls._component_classes.get(class_name)

    @classmethod
    def save_entities(cls, folder: str = "resources/cms") -> None:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        all_entities = cls._entities.get_all()

        entity_types = {}
        for entity in all_entities:
            type_name = entity.__class__.__name__
            if type_name not in entity_types:
                entity_types[type_name] = []
            entity_types[type_name].append(entity)

        for type_name, entities in entity_types.items():
            filepath = os.path.join(folder, f"{type_name.lower()}.yaml")

            with open(filepath, 'w', encoding='utf-8') as f:
                entity_dicts = [entity.to_dict() for entity in entities]
                yaml.dump(entity_dicts, f, default_flow_style=False)

            print(f"Saved {len(entities)} entities of type {type_name} to {filepath}")

    @classmethod
    def create_entity(cls, entity_id: str) -> CMSEntity:
        if not cls._initialized:
            cls.init()

        entity = CMSEntity(entity_id)
        cls._entities.add(entity)
        return entity
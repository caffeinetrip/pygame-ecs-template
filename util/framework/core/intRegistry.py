import inspect
import sys
from .intBase import BaseInteraction, IOnEncounterStart, IOnEncounterUpdate, IOnEncounterEnd


class InteractionRegistry:
    @classmethod
    def find_all_interactions(cls, base_type=BaseInteraction):
        interactions = []

        for module_name, module in list(sys.modules.items()):
            if module is None:
                continue
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, base_type) and
                        obj != base_type and
                        not inspect.isabstract(obj)):
                    interactions.append(obj)

        return interactions

    @classmethod
    def find_encounter_start_interactions(cls):
        all_interactions = cls.find_all_interactions()
        return [i for i in all_interactions if issubclass(i, IOnEncounterStart)]

    @classmethod
    def find_encounter_update_interactions(cls):
        all_interactions = cls.find_all_interactions()
        return [i for i in all_interactions if issubclass(i, IOnEncounterUpdate)]

    @classmethod
    def find_encounter_end_interactions(cls):
        all_interactions = cls.find_all_interactions()
        return [i for i in all_interactions if issubclass(i, IOnEncounterEnd)]

    @classmethod
    def create_instances(cls, interaction_classes):
        instances = []
        for interaction_class in interaction_classes:
            instances.append(interaction_class())
        return instances

    @classmethod
    def get_encounter_start_instances(cls):
        classes = cls.find_encounter_start_interactions()
        return cls.create_instances(classes)

    @classmethod
    def get_encounter_end_instances(cls):
        classes = cls.find_encounter_end_interactions()
        return cls.create_instances(classes)

    @classmethod
    def get_encounter_update_instances(cls):
        classes = cls.find_encounter_update_interactions()
        return cls.create_instances(classes)
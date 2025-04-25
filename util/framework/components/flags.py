from util.framework.core.component import Component

class FlagComponent(Component):
    def __init__(self, value=True):
        super().__init__()
        self.value = value


class NameFlagComponent(FlagComponent):
    pass


class SelectedFlagComponent(FlagComponent):
    pass


class ActiveFlagComponent(FlagComponent):
    pass


class VisibleFlagComponent(FlagComponent):
    pass
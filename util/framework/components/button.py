from util.framework.core.component import Component


class ButtonComponent(Component):
    def __init__(self):
        super().__init__()
        self.on_click_handlers = []
        self.enabled = True

    def add_listener(self, handler):
        if handler not in self.on_click_handlers:
            self.on_click_handlers.append(handler)

    def remove_listener(self, handler):
        if handler in self.on_click_handlers:
            self.on_click_handlers.remove(handler)

    def click(self):
        if not self.enabled:
            return

        for handler in self.on_click_handlers:
            handler()
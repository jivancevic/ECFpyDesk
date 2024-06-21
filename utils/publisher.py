class Publisher():
    def __init__(self):
        self.callbacks = {}

    def register_callback(self, name, callback):
        if name not in self.callbacks:
            self.callbacks[name] = []
        self.callbacks[name].append(callback)

    def invoke_callback(self, name, *args, **kwargs):
        if name in self.callbacks:
            for callback in self.callbacks[name]:
                callback(*args, **kwargs)
        else:
            print(f"No callback registered under the name: {name}:: {args}")
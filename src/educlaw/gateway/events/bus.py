
class EventBus:
    def __init__(self):
        self.listeners = {}

    def on(self, event: str, fn):
        self.listeners.setdefault(event, []).append(fn)

    async def emit(self, event: str, payload=None):
        for fn in self.listeners.get(event, []):
            await fn(payload)    
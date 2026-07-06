
from collections import defaultdict
class EventBus:
    def __init__(self):
        self._subs=defaultdict(list)
    def subscribe(self,event,cb):
        self._subs[event].append(cb)
    def unsubscribe(self,event,cb):
        if cb in self._subs[event]: self._subs[event].remove(cb)
    def publish(self,event,payload=None):
        for cb in list(self._subs[event]):
            cb(payload)
event_bus=EventBus()

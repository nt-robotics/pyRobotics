
class Event(object):
    def __init__(self):
        self.__handlers = set()

    def handle(self, handler):
        self.__handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.__handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.__handlers:
            handler(*args, **kargs)

    def get_handlers_count(self):
        return len(self.__handlers)

    def clear_handlers(self):
        self.__handlers = []

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = get_handlers_count

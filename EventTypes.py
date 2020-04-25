class StopApplication:
    def __init__(self, exception=None):
        self.exception = exception


class ExceptionOccured:
    def __init__(self, exception):
        self.exception = exception


class KeyStroke:
    def __init__(self, key):
        self.key = key
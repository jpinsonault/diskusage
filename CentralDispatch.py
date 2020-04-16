from asyncio import Queue


class SerialDispatchQueue:
    def __init__(self, threadpool):
        self.threadpool = threadpool
        self.task_queue = Queue()
        self.futures_queue = Queue()

        self.start_queue()

    def start_queue(self):


class CentralDispatch:
    def __init__(self):
        pass

    def create_serial_queue(self):
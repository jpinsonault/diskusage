from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue, Empty

from funcutils import wrap_with_try


@wrap_with_try
def wait_on_futures(futures_queue: Queue):
    try:
        future = futures_queue.get_nowait()

        while True:
            _ = future.result()
            future = futures_queue.get_nowait()
    except Empty:
        print("***** Got empty")
        return


class AppShutDownSignal: pass


class SerialDispatchQueue:
    def __init__(self):
        self.task_threadpool = ThreadPoolExecutor(1)
        self.futures_queue = Queue()

    def submit_async(self, block, *args, **kwargs) -> Future:
        task = wrap_with_try(block)

        future = self.task_threadpool.submit(task, *args, **kwargs)
        self.futures_queue.put(future)

        return future

    def await_result(self, block, *args, **kwargs):
        future = self.submit_async(block, *args, **kwargs)

        return future.result()

    def finish_work(self) -> Future:
        return CentralDispatch.exhaust_futures(self.futures_queue)


class ConcurrentDispatchQueue:
    def __init__(self, size):
        self.task_threadpool = ThreadPoolExecutor(size)
        self.futures_queue = Queue()

    def submit_async(self, block, *args, **kwargs) -> Future:
        task = wrap_with_try(block)

        future = self.task_threadpool.submit(task, *args, **kwargs)
        self.futures_queue.put(future)

        return future

    def await_result(self, block, *args, **kwargs):
        future = self.submit_async(block, *args, **kwargs)

        return future.result()

    def finish_work(self) -> Future:
        return CentralDispatch.exhaust_futures(self.futures_queue)


class CentralDispatch:
    global_concurrent_queue = ConcurrentDispatchQueue(20)
    global_serial_queue = SerialDispatchQueue()

    @staticmethod
    def create_serial_queue() -> SerialDispatchQueue:
        return SerialDispatchQueue()

    @staticmethod
    def create_concurrent_queue(size) -> ConcurrentDispatchQueue:
        return ConcurrentDispatchQueue(size)

    @staticmethod
    def future(block, *args, **kwargs) -> Future:
        dispatch_queue = SerialDispatchQueue()
        return dispatch_queue.submit_async(block, *args, **kwargs)

    @staticmethod
    def exhaust_futures(future_queue: Queue) -> Future:
        return CentralDispatch.future(wait_on_futures, future_queue)

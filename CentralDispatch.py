import traceback
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue, Empty
import functools


def perform_on(func, dispatch_queue, do_async=False):
    @functools.wraps(func)
    def inner_function(*args, **kwargs):
        future = dispatch_queue.submit_async(func, *args, **kwargs)
        if do_async:
            return future
        else:
            return future.result()

    return inner_function


def wait_on_futures(futures_queue: Queue):
    try:
        future = futures_queue.get_nowait()

        while True:
            _ = future.result()
            future = futures_queue.get_nowait()
    except Empty:
        return


def wrap_with_try(func):
    @functools.wraps(func)
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())
            raise e

    return inner_function


class AppShutDownSignal: pass


class SerialDispatchQueue:
    def __init__(self, exception_handler):
        self.exception_handler = exception_handler
        self.task_threadpool = ThreadPoolExecutor(1)
        self.futures_queue = Queue()

    def submit_async(self, block, *args, **kwargs) -> Future:
        task = self.exception_handler(block)

        future = self.task_threadpool.submit(task, *args, **kwargs)
        self.futures_queue.put(future)

        return future

    def await_result(self, block, *args, **kwargs):
        future = self.submit_async(block, *args, **kwargs)

        return future.result()

    def finish_work(self) -> Future:
        return CentralDispatch.exhaust_futures(self.futures_queue)


class ConcurrentDispatchQueue:
    def __init__(self, size, exception_handler):
        self.exception_handler = exception_handler
        self.task_threadpool = ThreadPoolExecutor(size)
        self.futures_queue = Queue()

    def submit_async(self, block, *args, **kwargs) -> Future:
        task = self.exception_handler(block)

        future = self.task_threadpool.submit(task, *args, **kwargs)
        self.futures_queue.put(future)

        return future

    def await_result(self, block, *args, **kwargs):
        future = self.submit_async(block, *args, **kwargs)

        return future.result()

    def finish_work(self) -> Future:
        return CentralDispatch.exhaust_futures(self.futures_queue)


class CentralDispatch:

    default_exception_handler = wrap_with_try

    @staticmethod
    def create_serial_queue() -> SerialDispatchQueue:
        return SerialDispatchQueue(exception_handler=CentralDispatch.default_exception_handler)

    @staticmethod
    def create_concurrent_queue(size) -> ConcurrentDispatchQueue:
        return ConcurrentDispatchQueue(size, exception_handler=CentralDispatch.default_exception_handler)

    @staticmethod
    def future(block, *args, **kwargs) -> Future:
        dispatch_queue = SerialDispatchQueue(exception_handler=CentralDispatch.default_exception_handler)
        return dispatch_queue.submit_async(block, *args, **kwargs)

    @staticmethod
    def exhaust_futures(future_queue: Queue) -> Future:
        return CentralDispatch.future(wait_on_futures, future_queue)

    @classmethod
    def concat(cls, *args):
        def _concat(*args):
            for future in args:
                future.result()

        return CentralDispatch.future(_concat, *args)

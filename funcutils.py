import functools
import traceback


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

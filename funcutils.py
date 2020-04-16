import traceback


def wrap_with_try(function):
    def inner_function(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())

    return inner_function

import functools as ft
import inspect
from logging import ERROR, Formatter, Logger, StreamHandler
from typing import Callable


def get_logger() -> Logger:
    """Get application logger.

    Returns:
        Logger: logging object.
    """
    logger_ = Logger(__name__)

    stream_handler = StreamHandler()
    stream_formatter = Formatter("%(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger_.addHandler(stream_handler)

    logger_.setLevel(ERROR)

    return logger_


logger = get_logger()


def logdec(func: Callable) -> Callable:
    """Decorator for logging function calls and arguments.

    Args:
        func (Callable): any function that should be logged.

    Raises:
        e: exception raised by `func`.

    Returns:
        Callable: decorated function.
    """

    @ft.wraps(func)
    def wrapper(*args, **kwargs):
        module_name = getattr(inspect.getmodule(func), "__name__", "")
        func_name = f"{module_name}.{func.__name__}"
        args_repr = [str(a) for a in args]
        kwargs_repr = [f"{k}={v}" for k, v in kwargs.items()]
        args_and_kwargs = args_repr + kwargs_repr
        signature = ", ".join(args_and_kwargs) if args_and_kwargs else "<no args>"
        logger.debug("Called: '%s' with: '%s'", func_name, signature)
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.exception("Exception raised in %s. exception: %s", func_name, e)
            raise e

    return wrapper

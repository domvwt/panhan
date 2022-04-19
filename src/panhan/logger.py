import functools as ft
import inspect
from logging import ERROR, Formatter, Logger, StreamHandler
from typing import Callable


def get_logger() -> Logger:
    """Get application logger.

    Returns:
        Logger: logging object.
    """
    logger = Logger(__name__)

    stream_handler = StreamHandler()
    stream_formatter = Formatter("%(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    logger.setLevel(ERROR)

    return logger


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
        logger.debug(f"Called: '{func_name}' with: '{signature}'")
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.exception(f"Exception raised in {func_name}. exception: {str(e)}")
            raise e

    return wrapper

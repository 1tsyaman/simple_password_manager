from threading import Timer
from functools import wraps
from collections.abc import Callable
from typing import ParamSpec, TypeVar

TIMEOUT_SECONDS = 60

_watchdog       			= None	# global Timer object
_exit_func: Callable[..., None] | None	= None
_timed_out				= False

P = ParamSpec("P")	# generic parameter types
R = TypeVar("R")	# generic return type

def init_watchdog(exit_func=None) -> None:
    global _exit_func
    _exit_func = exit_func

    reset_timer()


"""
    Wrapper that sets the timeout flag
"""
def _exit_func_wrapper(*args, **kwargs) -> None:
    global _timed_out, _exit_func

    print("TIMEOUT")

    _timed_out = True

    if _exit_func is not None:
    	_exit_func(*args, **kwargs)

def reset_timer() -> None:
    global _watchdog

    if _watchdog is not None:
        _watchdog.cancel()
    
    _watchdog = Timer(TIMEOUT_SECONDS, _exit_func_wrapper)
    _watchdog.start()

def cancel_watchdog() -> None:
    global _watchdog, _exit_func, _timed_out

    if _watchdog is not None:
        _watchdog.cancel()

    _watchdog = None
    _exit_func = None
    _timed_out = False

def timeout_occurred() -> bool:
    return _timed_out


def reset_on_call(calling_func: Callable[P, R]) -> Callable[P, R]:
        @wraps(calling_func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                reset_timer()
                return calling_func(*args, **kwargs)

        return wrapper

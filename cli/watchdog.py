from threading import Timer
from functools import wraps

TIMEOUT_SECONDS = 10

_watchdog       = None	# global Timer object
_exit_func      = None
_timed_out      = False

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

    return _exit_func(*args, **kwargs)

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


def reset_on_call(calling_func) -> None:
    @wraps(calling_func)

    def wrapper(*args, **kwargs):
        reset_timer()

        return calling_func(*args, **kwargs)
    
    return wrapper

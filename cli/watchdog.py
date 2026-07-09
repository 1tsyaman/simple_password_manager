from threading import Timer
from functools import wraps

TIMEOUT_SECONDS = 60
watchdog        = None	# global Timer object
func            = None

def init_watchdog(exit_func) -> None:
    global watchdog
    global func
    func = exit_func
    watchdog = Timer(TIMEOUT_SECONDS, exit_func)

    watchdog.start()

def reset_timer() -> None:
    global watchdog
    global func

    if watchdog is not None:
        watchdog.cancel()

        init_watchdog(func)

def reset_on_call(calling_func) -> None:
    @wraps(calling_func)

    def wrapper(*args, **kwargs):
        reset_timer()

        return calling_func(*args, **kwargs)
    
    return wrapper
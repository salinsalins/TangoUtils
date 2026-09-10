import sys
from functools import wraps

def preserve_log_level():
    def log_decorator(func):
        @wraps(func)
        def wrapper(self, msg, *args, **kwargs):
            sl = kwargs.pop('stacklevel', 1)
            if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
                kwargs['stacklevel'] = sl + 2
            result = self.logger.func(f'{self.pre} {msg}', *args, **kwargs)
            return result
        return wrapper
    return log_decorator


import inspect
import logging
import sys


def exception_short_info():
    ex_type, ex_value, traceback = sys.exc_info()
    if ex_type:
        return ' %s: %s' % (ex_type.__name__, ex_value)
    else:
        return 'Unknown exception'


def log_exception(logger, message=None, *args, level=logging.ERROR, **kwargs):
    tail = exception_short_info()
    if message is None:
        message = 'Exception: '
    message += tail
    try:
        message = message % args
        if isinstance(logger, str):
            # raise ValueError('Incorrect argument for logger')
            # caller = sys._getframe(1).f_code.co_name
            if message is not None:
                message = logger % ([message] + args)
            logger = inspect.stack()[1].frame.f_locals['self'].logger
        if not isinstance(logger, logging.Logger):
            if hasattr(logger, 'logger'):
                logger = logger.logger
            elif hasattr(logger, 'LOGGER'):
                logger = logger.LOGGER
        if not isinstance(logger, logging.Logger):
            return message
        if 'stacklevel' not in kwargs:
            kwargs['stacklevel'] = 2
        logger.log(level, message, **kwargs)
        logger.debug('Exception: ', exc_info=True)
        return message
    except:
        tail = exception_short_info()
        print('Unexpected exception in log_exception ', tail)
        print('Previous exception:', message)
        return message

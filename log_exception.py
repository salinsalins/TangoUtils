import inspect
import logging
import sys


def exception_shot_info():
    ex_type, ex_value, traceback = sys.exc_info()
    return ' %s: %s' % (ex_type.__name__, ex_value)


def log_exception(logger, message=None, *args, level=logging.ERROR, **kwargs):
    tail = exception_shot_info()
    if message is None:
        message = 'Exception'
    message += tail
    try:
        message = message % args
        if isinstance(logger, str):
            # caller = sys._getframe(1).f_code.co_name
            logger = inspect.stack()[1].frame.f_locals['self'].logger
            # raise ValueError('Incorrect argument for logger')
        if not isinstance(logger, logging.Logger):
            if hasattr(logger, 'logger'):
                logger = logger.logger
            elif hasattr(logger, 'LOGGER'):
                logger = logger.LOGGER
        if not isinstance(logger, logging.Logger):
            return message
        logger.log(level, message, stacklevel=2, **kwargs)
        logger.debug('Exception: ', exc_info=True)
        return message
    except:
        tail = exception_shot_info()
        print('Unexpected exception in log_exception ', tail)
        print('Previous exception:', message)
        return message

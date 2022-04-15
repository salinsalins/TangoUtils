import inspect
import logging
import sys


def log_exception(logger, message=None, *args, level=logging.ERROR, **kwargs):
    ex_type, ex_value, traceback = sys.exc_info()
    tail = ' %s: %s' % (ex_type.__name__, ex_value)
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
        ex_type, ex_value, traceback = sys.exc_info()
        tail = ' %s: %s' % (ex_type.__name__, ex_value)
        print('Unexpected exception in log_exception ', tail)
        print('Previous exception:', message)
        return message

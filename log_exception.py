import inspect
import logging
import sys


def exception_short_info():
    ex_type, ex_value, traceback = sys.exc_info()
    if ex_type:
        return ' %s: %s' % (ex_type.__name__, ex_value)
    else:
        return 'Unknown exception'


def log_exception(logger=None, message=None, *args, level=logging.ERROR, **kwargs):
    info1 = 'Exception Info can not be determined'
    try:
        info1 = exception_short_info()
        if logger is None or isinstance(logger, str):
            # raise ValueError('Incorrect argument for logger')
            # caller = sys._getframe(1).f_code.co_name
            if message is not None:
                args = tuple([message] + list(args))
            message = logger
            logger = inspect.stack()[1].frame.f_locals['self'].logger
        if not isinstance(logger, logging.Logger):
            if hasattr(logger, 'logger'):
                logger = logger.logger
            elif hasattr(logger, 'LOGGER'):
                logger = logger.LOGGER
        if not isinstance(logger, logging.Logger):
            print('Logger can not be determined')
            return message

        if message is None:
            message = 'Exception: '
        message += info1
        message = message % args

        if 'stacklevel' not in kwargs:
            if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
                kwargs['stacklevel'] = 2
        logger.log(level, message, **kwargs)
        logger.debug('Exception Info: ', exc_info=True)
        return message
    except:
        info2 = exception_short_info()
        print('Unexpected exception in log_exception:', info2)
        print('Previous exception:', info1)
        return message

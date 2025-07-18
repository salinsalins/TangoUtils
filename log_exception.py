import inspect
import logging
import sys
import traceback

import config_logger


def exception_short_info():
    ex_type, ex_value, traceback = sys.exc_info()
    if ex_type:
        if hasattr(ex_value.args[0], 'desc'):
            txt = ex_value.args[0].desc
        else:
            txt = str(ex_value.args[0])
        return ' %s %s' % (ex_type.__name__, txt)
    else:
        return 'Unknown exception'


def log_exception(logger=None, message=None, *args, level=logging.ERROR, **kwargs):
    if isinstance(logger, str):
        if message is not None:
            args = tuple([message] + list(args))
        message = logger
    if message is None:
        message = ' Exception: '
    prefix = getattr(log_exception, 'prefix', '')
    message = prefix + message
    info1 = 'Exception Info can not be determined'
    ex_type, ex_value, tb = sys.exc_info()
    try:
        info1 = exception_short_info()
        #
        message += info1
        try:
            message = message % args
        except KeyboardInterrupt:
           raise
        except:
            message += 'Args parse error ' + str(args)
            message = message.replace('%', '_')
        #
        if logger is None or isinstance(logger, str):
            temp = inspect.stack()[1].frame.f_locals
            if 'self' in temp:
                logger = inspect.stack()[1].frame.f_locals['self'].logger
        if not isinstance(logger, logging.Logger):
            if hasattr(logger, 'logger'):
                logger = logger.logger
            elif hasattr(logger, 'LOGGER'):
                logger = logger.LOGGER
        if not isinstance(logger, logging.Logger):
            if hasattr(config_logger.config_logger, 'logger'):
                logger = config_logger.config_logger.logger
        if not isinstance(logger, logging.Logger):
            # print('Logger can not be determined.')
            print(message)
            return message
        #
        stlvl = kwargs.pop('stacklevel', 1)
        if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
            kwargs['stacklevel'] = stlvl + 1
        if 'no_info' in kwargs:
            exc_info = not kwargs.pop('no_info', True)
        else:
            exc_info = kwargs.pop('exc_info', True)
        message += " " + info1
        kwargs['exc_info'] = exc_info
        logger.log(level, message, **kwargs)
        # if exc_info:
        #     logger.debug('Exception Info: ', exc_info=True)
        return message
    except KeyboardInterrupt:
        raise
    except:
        info2 = exception_short_info()
        ex_type2, ex_value2, tb2 = sys.exc_info()
        print('Unexpected exception in log_exception:', info2)
        print('Previous exception:', info1)
        print('*********************')
        # print(ex_type, ex_value, tb)
        traceback.print_tb(tb)
        print('=====================')
        # print(ex_type2, ex_value2, tb2)
        traceback.print_tb(tb2)
        return message


def log(message=None, *args, logger=None, level=logging.DEBUG, stacklevel=1, **kwargs):
    msg = 'Message can not be determined'
    try:
        if len(args) > 0 and args[0] is not None:
            msg = message % args
        else:
            msg = message
        if logger is None:
            self = inspect.stack()[stacklevel].frame.f_locals['self']
            if hasattr(self, 'logger'):
                logger = self.logger
            elif hasattr(self, 'LOGGER'):
                logger = self.LOGGER
        if not isinstance(logger, logging.Logger):
            raise ValueError('Logger can not be determined')
        if (sys.version_info.major >= 3 and sys.version_info.minor >= 8):
            kwargs['stacklevel'] = kwargs.get('stacklevel', 1) + 1
        else:
            kwargs.pop('stacklevel', None)
        logger.log(level, msg, **kwargs)
    except KeyboardInterrupt:
       raise
    except:
        info2 = exception_short_info()
        print('Unexpected exception: ', info2)
        print('Log message: ', str(msg))


def debug(message=None, *args, logger=None, **kwargs):
    log(message, *args, logger, level=logging.DEBUG, stacklevel=2, **kwargs)


def info(message=None, *args, logger=None, **kwargs):
    log(message, *args, logger, level=logging.INFO, stacklevel=2, **kwargs)


def warning(message=None, *args, logger=None, **kwargs):
    log(message, *args, logger, level=logging.WARNING, stacklevel=2, **kwargs)


def error(message=None, *args, logger=None, **kwargs):
    log(message, *args, logger, level=logging.ERROR, stacklevel=2, **kwargs)

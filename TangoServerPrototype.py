#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prototype for Python based tango device server
A. L. Sanin, started 05.07.2021
"""
import collections
import io
import sys

import logging
import os
import time
from multiprocessing import Lock
from threading import RLock

import numpy
import tango
from tango import AttrWriteType, DispLevel, DevState
from tango.server import Device, attribute, command

if '../TangoUtils' not in sys.path: sys.path.append('../TangoUtils')
from Configuration import Configuration
from TangoUtils import TangoLogHandler, TANGO_LOG_LEVELS, TangoDeviceProperties
from config_logger import config_logger, LOG_FORMAT_STRING
from log_exception import log_exception

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = 'Python Prototype Tango Server'
APPLICATION_NAME_SHORT = 'Python Prototype Tango Server'
APPLICATION_VERSION = '5.0'     # from 3.0 save config to properties removed (unsafe)
                                # from 4.0 TangoServerPrototype.devices is dictionary
LOG_LIST_LENGTH = 50


class TangoServerPrototype(Device):
    # ******** class variables ***********
    server_version_value = APPLICATION_VERSION
    server_name_value = APPLICATION_NAME_SHORT
    devices = {}
    POLLING_ENABLE_DELAY = 0.2
    DO_NOT_USE_PROPERTIES = ('polled_attr', '_polled_attr')

    # ******** attributes ***********
    server_version = attribute(label="server_version", dtype=str,
                               display_level=DispLevel.OPERATOR,
                               access=AttrWriteType.READ,
                               unit="", format="%s",
                               doc="Server version")

    server_name = attribute(label="server_name", dtype=str,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ,
                            unit="", format="%s",
                            doc="Server name")

    log_level = attribute(label="log_level", dtype=str,
                          display_level=DispLevel.EXPERT,
                          access=AttrWriteType.READ_WRITE,
                          unit="", format="%7s",
                          doc="Server log level")

    log_messages = attribute(label="log_messages", dtype=[str],
                             access=AttrWriteType.READ,
                             display_level = DispLevel.EXPERT,
                             # unit="", format="%s",
                             max_dim_x=LOG_LIST_LENGTH,
                             max_dim_y=0,
                             doc="Last logger messages")

    # ******** init_device ***********
    def init_device(self):
        super().init_device()
        self.set_state(DevState.INIT, 'Prototype server initialization')
        self.name = self.get_name()
        # default logger
        self.logger = config_logger(level=logging.INFO)
        # logging to deque
        self.dlh = None
        self.configure_deque_logging(LOG_LIST_LENGTH)
        # default configuration
        self.config = Configuration()
        # config from file
        self.read_config_from_file()
        # config from properties
        self.properties = TangoDeviceProperties(self.get_name())
        self.read_config_from_properties()
        # created attributes if any
        self.created_attributes = {}
        # set log level
        level = self.config.get('log_level', logging.INFO)
        self.logger.setLevel(level)
        self.logger.debug('Log level has been set to %s',
                          logging.getLevelName(self.logger.getEffectiveLevel()))
        self.log_level.set_write_value(logging.getLevelName(self.logger.getEffectiveLevel()))
        # register device
        TangoServerPrototype.devices[self.get_name()] = self
        # set final state
        self.set_state(DevState.RUNNING, 'Prototype initialization finished')

    def delete_device(self):
        TangoServerPrototype.devices.pop(self.get_name(), None)
        super().delete_device()

    # ******** attribute r/w procedures ***********
    def read_server_version(self):
        return self.server_version_value

    def read_server_name(self):
        return self.server_name_value

    def read_log_level(self):
        return logging.getLevelName(self.logger.getEffectiveLevel())

    def write_log_level(self, value):
        try:
            try:
                v = int(value)
            except KeyboardInterrupt:
                raise
            except:
                v = value.upper()
            self.logger.setLevel(v)
            # configure tango logging
            util = tango.Util.instance()
            dserver = util.get_dserver_device()
            # 5 - DEBUG; 4 - INFO; 3 - WARNING; 2 - ERROR; 1 - FATAL; 0 - OFF
            level = TANGO_LOG_LEVELS[self.read_log_level()]
            tango.DeviceProxy(dserver.get_name()).command_inout('SetLoggingLevel', [[level], [self.get_name()]])
            self.set_running()
        except KeyboardInterrupt:
            raise
        except:
            self.set_fault('Can not set Log level to %s' % value)
            self.log_exception('Can not set Log level to %s', value)

    def set_tango_log_level(self, level=None):
        self.util = tango.Util.instance(self)
        self.dserver = self.util.get_dserver_device()
        self.dserver_name = self.dserver.get_name()
        self.dserver_proxy = tango.DeviceProxy(self.dserver_name)
        if level is None:
            level = TANGO_LOG_LEVELS[self.read_log_level()]
        elif isinstance(level, str):
            level = TANGO_LOG_LEVELS[level.upper()]
        # 5 - DEBUG; 4 - INFO; 3 - WARNING; 2 - ERROR; 1 - FATAL; 0 - OFF
        self.dserver_proxy.command_inout('SetLoggingLevel', [[level], [self.get_name()]])

    def read_log_messages(self, attr):
        v = ['']
        if hasattr(self, 'dlh') and self.dlh:
            # return self.dlh.get_value()
            v = self.dlh.get_value()
        attr.set_value(v)
        return v

    # ******** commands ***********
    @command(dtype_in=int)
    def set_log_level(self, level):
        self.write_log_level(level)
        msg = '%s Log level has been set to %s' % (self.get_name(), self.read_log_level())
        self.logger.info(msg)

    # ******** additional helper functions ***********
    def save_polling_state(self, target_property='_polled_attr'):
        self.config[target_property] = []
        dev_name = self.get_name()
        pv = self.properties.get('polled_attr', [])
        result = []
        i = 0
        while i < len(pv):
            try:
                v = int(pv[i + 1])
                result.append(pv[i])
                result.append(pv[i + 1])
                i += 1
            except KeyboardInterrupt:
                raise
            except:
                log_exception(self.logger)
            i += 1
        if result:
            self.properties[target_property] = result
            self.logger.debug(f'Polling state {result} saved to {target_property}')
            return True
        else:
            if pv:
                self.logger.info(f'Wrong format for polled_attr {dev_name}: {pv}, save ignored')
                return False
            else:
                del self.properties[target_property]
                # db.delete_device_property(dev_name, target_property)
                self.logger.debug(f'Polling for {dev_name} is not set, {target_property} deleted')

    def get_saved_polling_period(self, attr_name, prop_name='_polled_attr'):
        try:
            pa = self.properties.get(prop_name)
            i = pa.index(attr_name)
            if i < 0:
                return -1
            return int(pa[i + 1])
        except KeyboardInterrupt:
            raise
        except:
            return -1

    def restore_polling(self, attr_name=None):
        try:
            dp = tango.DeviceProxy(self.get_name())
            for name in self.created_attributes:
                if attr_name is None or attr_name == name:
                    pp = self.get_saved_polling_period(name)
                    if pp > 0:
                        dp.poll_attribute(name, pp)
                        # workaround to prevent tango feature
                        time.sleep(self.POLLING_ENABLE_DELAY)
                        self.logger.info(f'Polling for {self.get_name()} {name} {pp} restored')
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger)

    def log_exception(self, message='', *args, level=logging.ERROR, **kwargs):
        msg = '%s %s ' % (self.get_name(), message)
        log_exception(self, msg, *args, level=level, stacklevel=3, **kwargs)

    def log_log(self, level, message='', *args, **kwargs):
        message = f'{self.get_name()}  {message}'
        if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
            self.logger.log(level, message, *args, stacklevel=3, **kwargs)
        else:
            self.logger.log(level, message, *args, **kwargs)

    def log_debug(self, message='', *args, **kwargs):
        self.log_log(logging.DEBUG, message, *args, **kwargs)

    def log_info(self, message='', *args, **kwargs):
        message = self.get_name() + ' ' + message
        if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
            self.logger.info(message, *args, stacklevel=2, **kwargs)
        else:
            self.logger.info(message, *args, **kwargs)

    def log_warning(self, message='', *args, **kwargs):
        message = self.get_name() + ' ' + message
        if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
            self.logger.warning(message, *args, stacklevel=2, **kwargs)
        else:
            self.logger.warning(message, *args, **kwargs)

    def log_error(self, message='', *args, **kwargs):
        message = self.get_name() + ' ' + message
        # kwargs['stacklevel'] = kwargs.copy().pop('stacklevel', 1) +1
        if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
            self.logger.error(message, *args, stacklevel=2, **kwargs)
        else:
            self.logger.error(message, *args, **kwargs)

    def get_device_property(self, prop: str, default=None):
        try:
            db = tango.Database()
            pr = db.get_device_property(self.get_name(), prop)[prop]
            # pr = self.device_proxy.get_property(prop)[prop]
            result = None
            if len(pr) > 0:
                result = pr[0]
            if default is None:
                return result
            if result is None or result == '':
                return default
            else:
                return type(default)(result)
        except KeyboardInterrupt:
            raise
        except:
            return default

    def set_device_property(self, prop: str, value: str):
        prop = str(prop)
        try:
            db = tango.Database()
            # self.device_proxy.put_property({prop: value})
            db.put_device_property(self.get_name(), {prop: [value]})
        except KeyboardInterrupt:
            raise
        except:
            self.log_exception('Error writing property %s for %s' % (prop, self.get_name()))

    def get_attribute_property(self, attr_name, prop_name=None):
        db = tango.Database()
        # db = self.device_proxy.get_device_db()
        apr = db.get_device_attribute_property(self.get_name(), attr_name)
        if prop_name is None:
            return apr[attr_name]
        return apr[attr_name][prop_name][0]

    def set_attribute_property(self, attr_name, prop_name, value):
        db = tango.Database()
        # db = self.device_proxy.get_device_db()
        apr = db.get_device_attribute_property(self.get_name(), attr_name)
        apr[attr_name][prop_name] = str(value)
        db.put_device_attribute_property(self.get_name(), apr)

    def initialize_dynamic_attributes(self):
        # overwrite to continue device initialization after init_device()
        pass

    def read_config_from_properties(self):
        props = self.properties
        if not hasattr(self, 'config'):
            self.config = Configuration()
        for p in props:
            if p in self.config:
                self.config[p] = type(self.config[p])(props[p][0])
            else:
                self.config[p] = props[p][0]
        # remove properties internally used by tango system
        for attr_name in TangoServerPrototype.DO_NOT_USE_PROPERTIES:
            self.config.pop(attr_name, None)

    def write_config_to_properties(self):
        return
        # for p in self.config:
        #     if p not in self.properties:
        #         self.properties[p] = self.config[p]
        # # self.device_proxy.put_property(self.config.data)

    def read_config_from_file(self, file_name=None):
        if file_name is None:
            file_name = self.__class__.__name__ + '.json'
        if not hasattr(self, 'config'):
            self.config = Configuration(file_name)
        else:
            self.config.read(file_name)

    def configure_deque_logging(self, maxlen=100):
        if hasattr(self.logger, 'tango_dlh'):
            self.dlh = self.logger.tango_dlh
            return
        self.dlh = DequeLogHandler(maxlen)
        self.logger.addHandler(self.dlh)
        self.logger.tango_dlh = self.dlh

    def configure_tango_logging(self):
        # add logging to TLS
        tlh = TangoLogHandler(self)
        self.logger.addHandler(tlh)

        # set logging level via dserver !!! Working only after server start, not during init !!!
        # util = tango.Util.instance()
        # dserver = util.get_dserver_device()
        # 5 - DEBUG; 4 - INFO; 3 - WARNING; 2 - ERROR; 1 - FATAL; 0 - OFF
        # level = TANGO_LOG_LEVELS[self.logger.getEffectiveLevel()]
        # dserver.command_inout('SetLoggingLevel',[[level],[self.get_name()]])

        # set device logging properties - has no effect
        # self.set_device_property('logging_level', self.logger.getEffectiveLevel())
        # self.set_device_property('logging_level', "5")
        # self.set_device_property('logging_target', 'console')
        # self.init_logger() # has no effect
        # self.start_logging() # has no effect
        # self.tango_logging = True

    def set_running(self, msg='I/O OK'):
        self.set_state(DevState.RUNNING)
        self.set_status(msg)

    def set_fault(self, msg='Error during I/O'):
        self.set_state(DevState.FAULT)
        self.set_status(msg)

    def set_state(self, state, msg=None):
        super().set_state(state)
        if msg is not None:
            self.set_status(msg)


def correct_polled_attr_for_server(server_name=None):
    d_b = tango.Database()
    if not server_name:
        server_name = os.path.basename(sys.argv[0]).replace('.py', '')
        # server_name = os.path.basename(__file__).replace('.py', '')
    pr_n = 'polled_attr'
    dev_cl = d_b.get_device_class_list(server_name + '/' + sys.argv[1])
    vst = dev_cl.value_string
    i = 0
    for st in vst:
        if st == server_name:
            dev_n = vst[i - 1]
            # d_b.delete_device_property(dev_n, pr_n)
            pr_v = d_b.get_device_property(dev_n, pr_n)[pr_n]
            result = []
            for j in range(len(pr_v)):
                try:
                    val = int(pr_v[j + 1])
                    result.append(pr_v[j])
                    result.append(pr_v[j + 1])
                    j += 1
                except KeyboardInterrupt:
                    raise
                except:
                    # print('Wrong syntax for', pr_v[j], dev_n)
                    pass
            # print('Corrected syntax for', dev_n, result)
            d_b.put_device_property(dev_n, {pr_n: result})


def delete_property_for_server(property_name='polled_attr', server_name=None):
    db = tango.Database()
    if server_name is None:
        # get server name from command line
        server_name = os.path.basename(sys.argv[0]).replace('.py', '')
    dev_class_list = db.get_device_class_list(server_name + '/' + sys.argv[1]).value_string
    i = 0
    for st in dev_class_list:
        if st == server_name:
            # next is device name
            device_name = st[i - 1]
            db.delete_device_property(device_name, property_name)
        # scip line with device name
        i += 1


def looping():
    for dev in TangoServerPrototype.devices:
        pass
    print('Empty loop. Overwrite or disable.')
    time.sleep(1.0)
    pass


def post_init_callback():
    print('Empty post_init_callback. Overwrite or disable.')


class DequeLogHandler(logging.Handler):
    def __init__(self, maxlen=100, level=logging.DEBUG, formatter=None):
        super().__init__(level)
        self.deque = collections.deque(maxlen=maxlen)
        self.my_lock123 = Lock()
        with self.my_lock123:
            if formatter is None:
                try:
                    self.setFormatter(config_logger.log_formatter)
                except:
                    try:
                        log_formatter = logging.Formatter(LOG_FORMAT_STRING, datefmt='%H:%M:%S')
                        self.setFormatter(log_formatter)
                    except:
                        print('ERROR: Formatter is not defined')
            else:
                self.setFormatter(formatter)
        self.setLevel(level)

    def emit(self, record):
        log_entry = self.format(record)
        self.deque.append(log_entry)

    def get_value(self):
        # with self.my_lock123:
            # for i in self.deque:
            #     if i:
            #         print(i)
        # print('exit2', self.my_lock123)
        #     return self.deque[0]
        return list(self.deque)


if __name__ == "__main__":
    # TangoServerPrototype.run_server(post_init_callback=post_init_callback)
    # TangoServerPrototype.run_server(post_init_callback=post_init_callback, event_loop=looping)
    # TangoServerPrototype.run_server(event_loop=looping)
    TangoServerPrototype.run_server()

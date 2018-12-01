import os
import threading
import types
import ctypes
import functools
import logging
import datetime
import collections

logger = logging.getLogger(__name__)

class Bang:
    lock_in_process = threading.Lock()
    libc = ctypes.CDLL('libc.so.6')
    threading_logs = collections.defaultdict(lambda: dict(level=0, logs=list()))

    @classmethod
    def get_thread_id(cls):
        return cls.libc.syscall(186)

    @classmethod
    def get_curr_level(cls):
        tid = cls.get_thread_id()
        return cls.threading_logs[tid]['level']

    @classmethod
    def step_curr_level(cls):
        tid = cls.get_thread_id()
        cls.threading_logs[tid]['level'] += 1

    @classmethod
    def back_curr_level(cls):
        tid = cls.get_thread_id()
        cls.threading_logs[tid]['level'] -= 1

    @classmethod
    def log(cls, instance: object, func: types.FunctionType, timecost: float):

        tid = cls.get_thread_id()
        curr_level = cls.get_curr_level()

        cls.threading_logs[tid]['logs'].append((
            curr_level,
            id(instance),
            instance.__class__.__qualname__,
            func.__name__,
            timecost
        ))

    @classmethod
    def method_wrapper(cls, func):

        @functools.wraps(func)
        def _w(instance, *args, **kargs):
            start_time = datetime.datetime.now()
            cls.log(instance, func, None)

            cls.step_curr_level()


            ret = func(instance, *args, **kargs)

            cls.back_curr_level()

            end_time = datetime.datetime.now()
            cls.log(instance, func, (end_time - start_time).total_seconds())

            return ret

        return _w

    @classmethod
    def monitor_class(cls, target_type: type):
        for name, value in target_type.__dict__.items():
            if isinstance(value, types.FunctionType):
                setattr(target_type, name, cls.method_wrapper(value))

                logger.debug("monitor registed {classname}.{method}".format(
                    classname=target_type.__qualname__,
                    method=value.__name__
                ))

    @classmethod
    def print_results(cls):
        for thread_id, state in cls.threading_logs.items():
            for level, instance_id, instance_type, func_name, time_cost in state['logs']:
                print(
                    '{thread_id:10d} {level:4d} {instance_id} {timecost} {indent}{wrap} {instance_type}.{func_name}'.format(
                        thread_id=thread_id,
                        level=level,
                        instance_id=instance_id,
                        indent=' ' * level,
                        wrap='∧' if time_cost is None else '∨',
                        instance_type=instance_type,
                        func_name=func_name,
                        timecost=' ' * 10 if time_cost is None else '%-10.6f' % time_cost,
                    ))

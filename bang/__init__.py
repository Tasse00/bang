import os
import threading
import types
import ctypes
import functools
import logging
import datetime
import collections

logger = logging.getLogger(__name__)


class Monitor:

    def log_start(self, instance: object, func: types.FunctionType):
        pass

    def log_end(self, instance: object, func: types.FunctionType, timecost: float):
        pass

    def step_curr_level(self):
        pass

    def back_curr_level(self):
        pass


class ProfileContext:

    def __init__(self, bang: Monitor, instance, func):
        self.instance = instance
        self.func = func
        self.bang = bang

    def __enter__(self):
        self.start_time = datetime.datetime.now()
        self.bang.log_start(self.instance, self.func)

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.datetime.now()
        self.bang.log_end(self.instance, self.func, (end_time - self.start_time).total_seconds())


class LevelContext:

    def __init__(self, bang: Monitor):
        self.bang = bang

    def __enter__(self):
        self.bang.step_curr_level()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bang.back_curr_level()


class Bang:
    
    
    def __init__(self):
    
        self.lock_in_process = threading.Lock()
        self.libc = ctypes.CDLL('libc.so.6')
        self.threading_logs = collections.defaultdict(lambda: dict(level=0, logs=list()))

    
    def get_thread_id(self):
        return self.libc.syscall(186)

    
    def get_curr_level(self):
        tid = self.get_thread_id()
        return self.threading_logs[tid]['level']

    def step_curr_level(self):
        tid = self.get_thread_id()
        self.threading_logs[tid]['level'] += 1

    def back_curr_level(self):
        tid = self.get_thread_id()
        self.threading_logs[tid]['level'] -= 1


    def log_start(self, instance: object, func: types.FunctionType, timecost: float):

        tid = self.get_thread_id()
        curr_level = self.get_curr_level()

        self.threading_logs[tid]['logs'].append((
            curr_level,
            id(instance),
            instance.__class__.__qualname__,
            func.__name__,
            timecost
        ))

    def log_end(self, instance: object, func: types.FunctionType, timecost: float):

        tid = self.get_thread_id()
        curr_level = self.get_curr_level()

        self.threading_logs[tid]['logs'].append((
            curr_level,
            id(instance),
            instance.__class__.__qualname__,
            func.__name__,
            timecost
        ))

    def deep_level(self):
        return LevelContext(self)

    def collect_profile(self, instance, func):
        return ProfileContext(self, instance, func)

    def method_wrapper(self, func):

        @functools.wraps(func)
        def _w(instance, *args, **kargs):
            with self.collect_profile(instance, func):
                with self.deep_level():
                    ret = func(instance, *args, **kargs)
            return ret

        return _w

    @classmethod
    def monitor_class(self, target_type: type):
        for name, value in target_type.__dict__.items():
            if isinstance(value, types.FunctionType):
                setattr(target_type, name, self.method_wrapper(value))

                logger.debug("monitor registed {classname}.{method}".format(
                    classname=target_type.__qualname__,
                    method=value.__name__
                ))

    @classmethod
    def print_results(self):
        for thread_id, state in self.threading_logs.items():
            for level, instance_id, instance_type, func_name, time_cost in state['logs']:
                print(
                    '{thread_id:10d} {level:4d} {instance_id} {timecost} {indent}{wrap}{instance_type}.{func_name}'.format(
                        thread_id=thread_id,
                        level=level,
                        instance_id=instance_id,
                        indent=' ' * level,
                        wrap='∧' if time_cost is None else '∨',
                        instance_type=instance_type,
                        func_name=func_name,
                        timecost=' ' * 10 if time_cost is None else '%-10.6f' % time_cost,
                    ))

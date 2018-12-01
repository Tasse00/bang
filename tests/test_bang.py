from bang import Bang

from time import sleep
from typing import List


class SimpleWorker:

    def __init__(self):
        pass

    def say_hello(self):
        print("Hello!")

    def wait_1s(self):
        sleep(1)

    def say_hello_after_1s(self):
        self.wait_1s()
        self.say_hello()


class HighLevelCaller:

    def __init__(self, testers: List[SimpleWorker]):
        self._testers = testers

    def deligate_say_hello_after_1s(self):
        for test in self._testers:
            test.say_hello_after_1s()


def test_bang():

    # monitor class: HighLevelCaller and SimpleWorker
    Bang.monitor_class(HighLevelCaller)
    Bang.monitor_class(SimpleWorker)

    # do work
    hlc = HighLevelCaller([SimpleWorker(), SimpleWorker()])
    hlc.deligate_say_hello_after_1s()

    # collect and show results
    Bang.print_results()

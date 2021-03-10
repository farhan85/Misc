#!/usr/bin/env python3

import time
from datetime import datetime
from threading import Event, Thread


def timer(interval_sec, function, count=None, args=None, kwargs=None):
    args, kwargs = args or [], kwargs or {}
    start_time = time.perf_counter()
    counter = 0
    while True:
        function(*args, **kwargs)
        counter += 1
        if count and counter == count:
            break
        else:
            wait_time = interval_sec - (time.perf_counter() - start_time) % interval_sec
            time.sleep(wait_time)


class BackgroundTimer(Thread):
    def __init__(self, interval_sec, function, count=None, args=None, kwargs=None):
        super().__init__()
        self.daemon = True

        self.interval_sec = interval_sec
        self.count = count
        self.func = function
        self.func_args = args or []
        self.func_kwargs = kwargs or {}
        self.stop_event = Event()

    def run(self):
        start_time = time.perf_counter()
        counter = 0
        while True:
            self.func(*self.func_args, **self.func_kwargs)
            counter += 1
            if self.count and counter == self.count:
                break
            wait_time = self.interval_sec - (time.perf_counter() - start_time) % self.interval_sec
            if self.stop_event.wait(wait_time):
                break

    def stop(self):
        self.stop_event.set()


def test_func(name, id=''):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - hello {name} {id}')


timer(1, test_func, count=3, kwargs={'id':'John', 'name':'123'})

thread = BackgroundTimer(2, test_func, args=('Jane', '456'))
thread.start()
time.sleep(5)
thread.stop()
thread.join()

thread = BackgroundTimer(2, test_func, count=2, kwargs={'name':'Tom', 'id':'789'})
thread.start()
thread.join()

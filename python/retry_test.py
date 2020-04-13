#!/usr/bin/env python3

import random
from tenacity import retry, retry_if_exception_type, retry_if_result, wait_exponential, wait_fixed


count = 0


class MyException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


@retry(wait=wait_exponential(1),
       retry=retry_if_exception_type(MyException))
def test1():
    global count
    count += 1
    print('trying again. count =', count)
    if count < 5:
        raise MyException('test')


@retry(wait=wait_fixed(0.5),
       retry=retry_if_result(lambda x: x < 5))
def test2():
    global count
    count += 1
    print('trying again. count =', count)
    return count


@retry(wait=wait_fixed(0.5),
       retry=(retry_if_exception_type(MyException) |
              retry_if_result(lambda x: x < 5)))
def test3():
    global count
    count += 1
    print('trying again. count =', count)
    if random.choice([True, False]):
        print('returning count')
        return count
    else:
        print('throwing exception')
        raise MyException('test')


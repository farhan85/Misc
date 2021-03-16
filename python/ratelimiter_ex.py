import time
from datetime import datetime
from ratelimiter import RateLimiter


def timestamp_s():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@RateLimiter(max_calls=3, period=1)
def do_something():
    print(f'{timestamp_s()} - hello world')


def do_something2():
    print(f'{timestamp_s()} - hello world 2')


def test_with_decorator():
    for _ in range(12):
        print(f'{timestamp_s()} - Call do_something()')
        do_something()


def test_with_context_obj():
    rate_limiter = RateLimiter(max_calls=3, period=1)
    for _ in range(12):
        with rate_limiter:
            print(f'{timestamp_s()} - Call do_something2()')
            do_something2()


def test_with_timer(func):
    start = time.perf_counter()
    func()
    elapsed = time.perf_counter() - start
    print(f'Time taken: {elapsed:0.2f} seconds')


test_with_timer(test_with_decorator)
print()
test_with_timer(test_with_context_obj)

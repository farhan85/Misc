import time
from datetime import datetime
from limits import parse, storage, strategies, RateLimitItemPerSecond


# This is the recommended rate limiter library to use based on the tests done here:
# https://gist.github.com/justinvanwinkle/d9f04950083c4554835c1a35f9d22dad


class RateLimiter:
    def __init__(self, rate_limit=None, rate_limit_map=None):
        if (rate_limit is None and rate_limit_map is None) or \
                (rate_limit is not None and rate_limit_map is not None):
            raise ValueError("Only one of rate_limit/rate_limit_map can be provided")

        self.rate_limiter = strategies.MovingWindowRateLimiter(storage.MemoryStorage())
        self.single_limit = rate_limit
        self.rate_limits = rate_limit_map

    @staticmethod
    def tps(tps):
        #return RateLimiter(rate_limit=parse(f'{tps}/second'))
        return RateLimiter(rate_limit=RateLimitItemPerSecond(tps))

    @staticmethod
    def tps_limits(tps_limits):
        return RateLimiter(rate_limit_map={limit_name: RateLimitItemPerSecond(tps)
                                           for limit_name, tps in tps_limits.items()})

    # The namespace/identifier is only needed if the same limit needs to be used for multiple
    # independent resources (e.g. use the same limit for different resources, but don't let the
    # resources eat into each other's available limits)
    def _wait(self, rate_limit_item, *identifiers):
        while not self.rate_limiter.hit(rate_limit_item, *identifiers):
            window_stats = self.rate_limiter.get_window_stats(rate_limit_item, *identifiers)
            duration = window_stats.reset_time - time.time()
            # The max() protects against both negative and zero duration
            # Negative duration causes sleep to raise a ValueError
            # Zero duration will not let this loop pause at all, calling hit() as quickly as possible,
            # wasting CPU cycles until the window actually resets.
            time.sleep(max(duration, 0.001))

    def wait(self):
        self._wait(self.single_limit)

    def acquire(self, limit_name, *identifiers):
        self._wait(self.rate_limits[limit_name], limit_name, *identifiers)


if __name__ == '__main__':
    r = RateLimiter.tps(3)
    for _ in range(9):
        r.wait()
        print('{} - {}'.format(datetime.now(), 'Do work'))

    limits = {'limitA': 1, 'limitB': 2}
    r = RateLimiter.tps_limits(limits)
    for _ in range(5):
        r.acquire('limitA', 'resource1')
        print('{} - {}'.format(datetime.now(), 'Do work - limitA/resource1'))
        r.acquire('limitA', 'resource2', 'component-x')
        print('{} - {}'.format(datetime.now(), 'Do work - limitA/resource2/component-x'))
        r.acquire('limitA', 'resource2', 'component-y')
        print('{} - {}'.format(datetime.now(), 'Do work - limitA/resource2/component-y'))
    for _ in range(5):
        r.acquire('limitB')
        print('{} - {}'.format(datetime.now(), 'Do work - limitB'))

import time
from datetime import datetime, timezone
from limits import parse, storage, strategies, RateLimitItemPerSecond


# This is the recommended rate limiter library to use based on the tests done here:
# https://gist.github.com/justinvanwinkle/d9f04950083c4554835c1a35f9d22dad


class RateLimiter:
    def __init__(self, rate_limit_map=None, rate_limit=None):
        self.rate_limiter = strategies.MovingWindowRateLimiter(storage.MemoryStorage())
        self.rate_limits = rate_limit_map
        self.default_limit = rate_limit

    @staticmethod
    def tps(tps):
        #return RateLimiter(rate_limit=parse(f'{tps}/second'))
        return RateLimiter(rate_limit=RateLimitItemPerSecond(tps))

    @staticmethod
    def tps_limits(tps_limits):
        rate_limits = { limit_name: RateLimitItemPerSecond(tps) for limit_name, tps in tps_limits }
        return RateLimiter(rate_limit_map=rate_limits)

    # The namespace/identifier is only needed if the same limit needs to be used for multiple
    # independent resources (e.g. use the same limit for different resources, but don't let the
    # resources eat into each other's available limits)
    def wait(self, limit_name=None, *identifiers):
        ratelimit = self.default_limit if limit_name is None else self.rate_limits[limit_name]
        while not self.rate_limiter.hit(ratelimit, limit_name, *identifiers):
            window_stats = self.rate_limiter.get_window_stats(ratelimit)
            now = int(datetime.now(timezone.utc).timestamp())
            time.sleep(window_stats.reset_time - now)


if __name__ == '__main__':
    r = RateLimiter.tps(3)
    for _ in range(9):
        r.wait()
        print('{} - {}'.format(datetime.now(), 'Do work'))

    limits = [('limitA', 1), ('limitB', 2)]
    r = RateLimiter.tps_limits(limits)
    for _ in range(5):
        r.wait('limitA', 'resource1')
        print('{} - {}'.format(datetime.now(), 'Do work - limitA/resource1'))
        r.wait('limitA', 'resource2', 'component-x')
        print('{} - {}'.format(datetime.now(), 'Do work - limitA/resource2/component-x'))
        r.wait('limitA', 'resource2', 'component-y')
        print('{} - {}'.format(datetime.now(), 'Do work - limitA/resource2/component-y'))
    for _ in range(5):
        r.wait('limitB')
        print('{} - {}'.format(datetime.now(), 'Do work - limitB'))

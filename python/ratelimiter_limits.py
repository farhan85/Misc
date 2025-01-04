import time
from datetime import datetime, timezone
from limits import RateLimitItemPerSecond, storage, strategies


ratelimiter = strategies.MovingWindowRateLimiter(storage.MemoryStorage())
limit = RateLimitItemPerSecond(2)

for _ in range(10):
    # The namespace/identifier is only needed if the same limit needs to be used for multiple
    # independent resources (e.g. use the same limit for different resources, but don't let the
    # resources eat into each other's available limits)
    while not ratelimiter.hit(limit, "namespace", "identifier"):
        reset_time, _ = ratelimiter.get_window_stats(limit)
        now = int(datetime.now(timezone.utc).timestamp())
        diff = reset_time - now
        print('{} - Waiting till {} ({} seconds)'.format(datetime.now(), reset_time, diff))
        time.sleep(diff)
    print('{} - {}'.format(datetime.now(), 'Do work'))

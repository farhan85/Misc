#!/usr/bin/env python

import math

def percentile(samples, percent):
    """Find the percentile of a list of values.

    :param samples: the list of samples/values from which to extract score.
    :param percent: percentile (between 0.0 and 1.0) at which to extract score.
    :type percent: float
    :rtype: the percentile of the values
    """

    if not samples:
        return None

    samples = sorted(samples)

    rank = percent * (len(samples) - 1)
    frac = rank % 1 # Fractional part

    lower = int(math.floor(rank))
    lower_val = samples[lower]

    # If rank is a whole number
    if frac == 0:
        return lower_val

    upper = int(math.ceil(rank))
    upper_val = samples[upper]
    return lower_val + frac*(upper_val - lower_val)


a = range(20,3, -1)
a = [79, 67, 44, 68, 30, 13, 22, 49, 65, 20, 20, 46, 65, 69, 58, 28, 27, 47, 14, 78, 60, 77, 79]
print percentile(a, 0.0)
print percentile(a, 0.25)
print percentile(a, 0.5)
print percentile(a, 0.95)
print percentile(a, 0.99)
print percentile(a, 1.0)

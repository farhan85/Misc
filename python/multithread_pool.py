#!/usr/bin/env python3

import random
import time

# Uses separate processes
#from multiprocessing import Pool

# Uses separate threads
from multiprocessing.pool import ThreadPool as Pool


def f(params):
    id, x, y = params
    rand = random.randint(x, y)
    print(f'f-{id}: Long-running process (sleeping) for {rand}s')
    time.sleep(rand)
    print(f'f-{id}: Done. Returning {x+1}')
    return x + 1


def g(id, x, y):
    rand = random.randint(x, y)
    print(f'g-{id}: Long-running process (sleeping) for {rand}s')
    time.sleep(rand)
    print(f'g-{id}: Done. Returning {x*x}')
    return x*x


with Pool(processes=2) as pool:
    results = pool.map(f, [(1, 4, 5), (2, 3, 4), (3, 2, 3), (4, 1, 2)])
    print(results)
    print()

    results = []
    results.append(pool.apply_async(g, (1, 3, 4)))
    results.append(pool.apply_async(g, (2, 2, 3)))
    results.append(pool.apply_async(g, (3, 1, 2)))
    try:
        results = [r.get(timeout=5) for r in results]
        print(results)
    except TimeoutError:
        raise

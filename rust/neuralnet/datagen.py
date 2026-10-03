#!/usr/bin/env python3

import random

if __name__ == '__main__':
    for _ in range(0, 100):
        a = random.uniform(0, 1)
        b = random.uniform(0, 1)
        c = 0 if a < b else 1
        print(f'{a}, {b}, {c}')

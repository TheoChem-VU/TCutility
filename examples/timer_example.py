from time import sleep

import numpy as np

from tcutility.timer import timer


@timer()
def test():
    with timer("test.loop.loop.loop.outer"):
        for _ in range(5):
            with timer("test.loop.loop.inner"):
                sleep(0.041 + (np.random.rand() - 0.5) / 30)


@timer()
def test2():
    sleep(0.231 + (np.random.rand() - 0.5) / 7)


[test() for _ in range(3)]
[test2() for _ in range(5)]

for i in range(10):
    with timer("loop"):
        sleep(i / 1000)

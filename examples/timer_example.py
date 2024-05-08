from tcutility.timer import timer
from time import sleep
import numpy as np


@timer
def test():
    with timer('test.loop.loop.loop.outer'):
        for _ in range(5):
            with timer('test.loop.loop.inner'):
                sleep(.041 + (np.random.rand() - .5)/30)

@timer
def test2():
    sleep(.231 + (np.random.rand() - .5)/7)

[test() for _ in range(3)]
[test2() for _ in range(5)]

for i in range(10):
    with timer('loop'):
        sleep(i/1000)

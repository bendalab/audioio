import pytest
import numpy as np
import audioio.bufferedarray as ba


def test_blocks():
    x = np.arange(100)
    
    n = 0
    for y in ba.blocks(x, 10, 0):
        n += len(y)
    assert n == len(x), 'blocks'
    
    n = 0
    for y in ba.blocks(x, 10, 0, 0, 25):
        n += len(y)
    assert n == 25, 'blocks with stop'
    
    n = 0
    for y in ba.blocks(x, 10, 0, 25, 50):
        n += len(y)
    assert n == 50 - 25, 'blocks with start and stop'

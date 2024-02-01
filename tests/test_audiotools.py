from nose.tools import assert_true, assert_false, assert_equal
import numpy as np
import audioio.audiotools as at


def test_despike():
    duration = 0.1
    samplerate = 44100.0
    channels = 4
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = 0.9*np.sin(2.0*np.pi*880.0*t)
    idx = np.random.randint(1, len(t)//10-1, 20)*10
    data[idx] += 1
    data[idx+25] -= 1
    
    sdata = data[:]
    at.despike(sdata, 0.5)
    assert_equal(len(sdata), len(t), 'despike keeps frames')
    assert_equal(sdata.ndim, 1, 'despike keeps single dimension')
    assert_true(np.max(sdata) <= 1.0, 'despike does not expand beyond +1')
    assert_true(np.min(sdata) >= -1.0, 'despike does not expand below -1')

    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))

    cdata = data.copy()
    at.despike(cdata, 0.5)
    assert_equal(len(cdata), len(t), 'despike keeps frames')
    assert_equal(cdata.shape[1], channels, 'despike keeps channels')
    assert_true(np.max(cdata) <= 1.0, 'despike does not expand beyond +1')
    assert_true(np.min(cdata) >= -1.0, 'despike does not expand below -1')

    at.has_numba = False
    at.despike(data, 0.5)
    assert_equal(len(data), len(t), 'despike keeps frames')
    assert_equal(data.shape[1], channels, 'despike keeps channels')
    assert_true(np.max(data) <= 1.0, 'despike does not expand beyond +1')
    assert_true(np.min(data) >= -1.0, 'despike does not expand below -1')
    at.has_numba = True


def test_despike2():
    duration = 0.1
    samplerate = 44100.0
    channels = 4
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = 0.9*np.sin(2.0*np.pi*880.0*t)
    idx = np.random.randint(1, len(t)//10-1, 20)*10
    data[idx] += 1
    data[idx+1] += 1
    data[idx+25] -= 1
    data[idx+26] -= 1
    
    sdata = data[:]
    at.despike(sdata, 0.5, 2)
    assert_equal(len(sdata), len(t), 'despike keeps frames')
    assert_equal(sdata.ndim, 1, 'despike keeps single dimension')
    assert_true(np.max(sdata) <= 1.0, 'despike does not expand beyond +1')
    assert_true(np.min(sdata) >= -1.0, 'despike does not expand below -1')

    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))

    cdata = data.copy()
    at.despike(cdata, 0.5, 2)
    assert_equal(len(cdata), len(t), 'despike keeps frames')
    assert_equal(cdata.shape[1], channels, 'despike keeps channels')
    assert_true(np.max(cdata) <= 1.0, 'despike does not expand beyond +1')
    assert_true(np.min(cdata) >= -1.0, 'despike does not expand below -1')

    at.has_numba = False
    at.despike(data, 0.5, 2)
    assert_equal(len(data), len(t), 'despike keeps frames')
    assert_equal(data.shape[1], channels, 'despike keeps channels')
    assert_true(np.max(data) <= 1.0, 'despike does not expand beyond +1')
    assert_true(np.min(data) >= -1.0, 'despike does not expand below -1')
    at.has_numba = True


def test_unwrap():
    duration = 0.1
    samplerate = 44100.0
    channels = 4
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = 1.5*np.sin(2.0*np.pi*880.0*t) * 2**15
    data = data.astype(dtype=np.int16).astype(dtype=float)/2**15
    sdata = data[:]

    at.unwrap(sdata)
    assert_equal(len(sdata), len(t), 'unwrap keeps frames')
    assert_equal(sdata.ndim, 1, 'unwrap keeps single dimension')
    assert_true(np.max(sdata) > 1.4, 'unwrap expands beyond +1')
    assert_true(np.min(sdata) < -1.4, 'unwrap expands below -1')

    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))

    cdata = data.copy()
    at.unwrap(cdata)
    assert_equal(len(cdata), len(t), 'unwrap keeps frames')
    assert_equal(cdata.shape[1], channels, 'unwrap keeps channels')
    assert_true(np.max(cdata) > 1.4, 'unwrap expands beyond +1')
    assert_true(np.min(cdata) < -1.4, 'unwrap expands below -1')

    at.has_numba = False
    did = id(data)
    at.unwrap(data)
    assert_equal(did, id(data), 'without numba unwrap does not touch the array')
    at.has_numba = True


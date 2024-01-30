"""Tools for fixing audio data.

- `despike()`: remove spikes.
- `unwrap()`: unwrap clipped data that are folded into the available data range.
"""
 
import warnings
import numpy as np

has_numba = False
try:
    from numba import jit, prange
    has_numba = True
except ImportError:
    def jit(*args, **kwargs):
        def decorator_jit(func):
            return func
        return decorator_jit
    prange = range


def despike(data, thresh=1.0, n=1):
    """Remove spikes. 

    If single data points stick out by more than a threshold, they are
    replaced by the mean of the two directly preceeding and succeeding
    data points.

    Parameters
    ----------
    data: 1D or 2D ndarray
        Data to be fixed in place.
    thresh: float
        Threshold defining a spike.
    n: int
        Maximum width of spike.
    """
    @jit(nopython=True)
    def despike_trace(data, thresh, n):
        for k in range(n, 0, -1):
            for i in range(1, len(data)-k):
                if (data[i] - data[i-1] > thresh and \
                    data[i+k-1] - data[i+k] > thresh) or \
                   (data[i-1] - data[i] > thresh and \
                    data[i+k-1] - data[i+k] > thresh):
                    for j in range(k):
                        data[i+j] = ((k-j)*data[i-1] + (1+j)*data[i+k])/(k+1)
        
    @jit(nopython=True, parallel=True)
    def despike_traces(data, thresh, n):
        for c in prange(data.shape[1]):
            despike_trace(data[:,c], thresh, n)

    if data.ndim > 1:
        if has_numba and data.shape[1] > 1:
            despike_traces(data, thresh, n)
        else:
            for c in range(data.shape[1]):
                despike(data[:,c], thresh, n)
    else:
        # not faster: 
        #if has_numba:
        #    despike_trace(data, thresh, n)
        #else:
            for k in range(n, 0, -1):
                # find k-spikes:
                diff = np.diff(data)
                sel = ((diff[:-k] > thresh) & (diff[k:] < -thresh)) | \
                      ((diff[:-k] < -thresh) & (diff[k:] > thresh))
                # replace with weighted average of neighbors:
                for j in range(1, k+1):
                    data[j:-k-1+j][sel] = ((k+1-j)*data[:-1-k][sel] + \
                                           j*data[1+k:][sel])/(k+1)


def unwrap(data, thresh=1.5):
    """Unwrap clipped data that are folded into the available data range.

    In some amplifiers/ADCs clipped data appear on the opposite side
    of the input range. This function tries to undo this wrapping.
    
    Parameters
    ----------
    data: 1D or 2D ndarray of floats
        Data to be fixed in place.
    thresh: float
        Minimum difference between succeeding data points required
        for initiating unwrapping.
    """

    @jit(nopython=True)
    def unwrap_trace(data, delta):
        thresh = delta - 1.0
        step = 0.0
        for i in range(1, len(data)):
            cstep = 0.0
            dd = data[i] - data[i-1]
            if data[i] >= 0:
                if abs(dd - 2.0) < abs(dd):
                    cstep = -2.0
            if data[i] <= 0:
                if abs(dd + 2.0) < abs(dd + cstep):
                    cstep = +2.0
            #if step != cstep and (cstep == 0.0 or \
            #                      (abs(data[i-1]) > thresh and \
            #                       abs(dd) > delta)):
            if step != cstep and (cstep == 0.0 or abs(dd) > delta):
                step = cstep
            data[i] += step
        
    @jit(nopython=True, parallel=True)
    def unwrap_traces(data, thresh):
        for c in prange(data.shape[1]):
            unwrap_trace(data[:,c], thresh)

    if not has_numba:
        warnings.warn('unwrap() requires numba to work')
    if data.ndim > 1:
        unwrap_traces(data, thresh)
    else:
        unwrap_trace(data, thresh)

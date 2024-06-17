"""Buffered time-series data.

- `blocks()`: generator for blockwise processing of array data.
- class `BufferedArray()`: random access to time-series data of which only a part is held in memory.
"""


import numpy as np

            
def blocks(data, block_size, noverlap=0, start=0, stop=None):
    """Generator for blockwise processing of array data.

    Parameters
    ----------
    data: ndarray
        Data to loop over. First dimension is time.
    block_size: int
        Len of data blocks to be returned.
    noverlap: int
        Number of indices successive data points should overlap.
    start: int
        Optional first index from which on to return blocks of data.
    stop: int
        Optional last index until which to return blocks of data.

    Yields
    ------
    data: ndarray
        Successive slices of the input data.

    Raises
    ------
    ValueError
        `noverlap` larger or equal to `block_size`.

    Examples
    --------
    ```
    import numpy as np
    from audioio import blocks
    data = np.arange(20)
    for x in blocks(data, 6, 2):
        print(x)
    ```
    results in
    ```text
    [0 1 2 3 4 5]
    [4 5 6 7 8 9]
    [ 8  9 10 11 12 13]
    [12 13 14 15 16 17]
    [16 17 18 19]
    ```

    Use it for processing long audio data, like computing a
    spectrogram with overlap:
    ```
    from scipy.signal import spectrogram
    from audioio import AudioLoader, blocks
    nfft = 2048
    with AudioLoader('some/audio.wav') as data:
        for x in blocks(data, 100*nfft, nfft//2):
            f, t, Sxx = spectrogram(x, fs=data.rate,
                                    nperseg=nfft, noverlap=nfft//2)
    ```

    """
    if noverlap >= block_size:
        raise ValueError(f'noverlap={noverlap} larger than block_size={block_size}')
    if stop is None:
        stop = len(data)
    step = block_size - noverlap
    n = (stop - start - noverlap)//step
    if n == 0:
        yield data[start:stop]
    else:
        for k in range(n):
            yield data[start + k*step:start + k*step + block_size]
        if stop - start - (k*step + block_size) > 0:
            yield data[start + (k + 1)*step:stop]


class BufferedArray(object):
    """Random access to time-series data of which only a part is held in memory.
    
    This is a base class for accessing large audio recordings either
    from a file (class ` AudioLoader`) or by computing its contents on
    the fly (e.g. filtered data, envelopes or spectrograms).  The
    `BufferedArray` behaves like a single big ndarray with first
    dimension indexing the frames and second dimension indexing the
    channels of the data. Higher dimensions are also supported.  For
    example, a third dimension for frequencies needed for
    spectrograms. Internally the class holds only a part of the data
    in memory. The size of this buffer is set to `bufferframes`
    frames. If more data are requested, the buffer is enlarged
    accordingly.

    Classes inheriting `BufferedArray` just need to implement
    ```
    self.load_buffer(offset, nsamples, pbuffer)
    ```
    This function needs to load the supplied `pbuffer` with
    `nframes` frames of data starting at frame `offset`.

    In the constructor or some kind of opening function, you need to
    set the following member variables, followed by a call to
    `init_buffer()`:

    ```
    self.rate            # number of frames per second
    self.channels        # number of channels per frame
    self.frames          # total number of frames
    self.shape = (self.frames, self.channels, ...)        
    self.bufferframes    # number of frames the buffer should hold
    self.backframes      # number of frames kept for moving back
    self.init_buffer()
    ```

    or provide all this information via the constructor:
    
    Parameters
    ----------
    rate: float
        The sampling rate of the data in seconds.
    channels: int
        The number of channels.
    frames: int
        The number of frames.
    bufferframes: int
        Number of frames the curent data buffer holds.
    backframes: int
        Number of frames the curent data buffer should keep
        before requested data ranges.
    verbose: int
        If larger than zero show detailed error/warning messages.

    Attributes
    ----------
    rate: float
        The sampling rate of the data in seconds.
    channels: int
        The number of channels.
    frames: int
        The number of frames. Same as `len()`.
    shape: tuple
        Frames and channels of the data. Optional higher dimensions.
    ndim: int
        Number of dimensions: 2 (frames and channels) or higher.
    size: int
        Total number of samples: frames times channels.
    offset: int
        Index of first frame in the current buffer.
    buffer: ndarray of floats
        The curently available data. First dimension is time, second channels.
        Optional higher dimensions according to `ndim` and `shape`.
    bufferframes: int
        Number of samples the curent data buffer holds.
    backframes: int
        Number of samples the curent data buffer should keep
        before requested data ranges.
    follow: int
        If zero (default), move buffer position only for requests outside
        the current buffer.
        If larger than zero then buffer position follows requested data ranges
        if buffer can be moved by more than `follow`frames.
        This results in more frequent but smaller buffer updates.
        Set it after calling the constructor or `init_buffer()`.
    buffer_changed: ndarray of bool
        For each channel a flag, whether the buffer content has been changed.
        Set to `True`, whenever `load_buffer()` was called.

    Methods
    -------
    - `len()`: Number of frames.
    - `__getitem__`: Access data.
    - `blocks()`: Generator for blockwise processing of AudioLoader data.
    - `update_buffer()`: make sure that the buffer contains data of a range of indices.
    - `update_time()`: make sure that the buffer contains data of a given time range.
    - `reload_buffer()`: reload the current buffer.
    - `load_buffer()`: load a range of samples into a buffer.
    - `move_buffer()`: move and resize buffer.
    - `buffer_position()`: compute position and size of buffer.
    - `recycle_buffer()`: move buffer to new position and recycle content if possible.

    Notes
    -----
    Access via `__getitem__` or `__next__` is slow!
    Even worse, using numpy functions on this class first converts
    it to a numpy array - that is something we actually do not want!
    We should subclass directly from numpy.ndarray .
    For details see http://docs.scipy.org/doc/numpy/user/basics.subclassing.html
    When subclassing, there is an offset argument, that might help to
    speed up `__getitem__` .

    """
    
    def __init__(self, rate=0, channels=0, frames=0, bufferframes=0,
                 backframes=0, verbose=0):
        """ Construtor for initializing 2D arrays (times x channels).
        """
        self.rate = rate
        self.channels = channels
        self.frames = frames
        self.shape = (self.frames, self.channels)
        self.ndim = 2
        self.size = self.frames * self.channels
        self.bufferframes = bufferframes   # number of frames the buffer can hold
        self.backframes = backframes       # number of frames kept before
        self.follow = 0
        self.verbose = verbose
        self.offset = 0     # index of first frame in buffer
        self.init_buffer()

        
    def __enter__(self):
        return self

    
    def __exit__(self, ex_type, ex_value, tb):
        self.__del__()
        return (ex_value is None)

    
    def __len__(self):
        return self.frames

    
    def __iter__(self):
        self.iter_counter = -1
        return self

    
    def __next__(self):
        self.iter_counter += 1
        if self.iter_counter >= self.frames:
            raise StopIteration
        else:
            self.update_buffer(self.iter_counter, self.iter_counter + 1)
            return self.buffer[self.iter_counter - self.offset]

        
    def __getitem__(self, key):
        """Access data of the audio file."""
        if type(key) is tuple:
            index = key[0]
        else:
            index = key
        if isinstance(index, slice):
            start = index.start
            stop = index.stop
            step = index.step
            if start is None:
                start = 0
            else:
                start = int(start)
            if start < 0:
                start += len(self)
            if stop is None:
                stop = len(self)
            else:
                stop = int(stop)
            if stop < 0:
                stop += len(self)
            if stop > self.frames:
                stop = self.frames
            if step is None:
                step = 1
            else:
                step = int(step)
            self.update_buffer(start, stop)
            newindex = slice(start - self.offset, stop - self.offset, step)
        elif hasattr(index, '__len__'):
            index = [inx if inx >= 0 else inx + len(self) for inx in index]
            start = min(index)
            stop = max(index)
            self.update_buffer(start, stop + 1)
            newindex = [inx - self.offset for inx in index]
        else:
            if index > self.frames:
                raise IndexError
            index = int(index)
            if index < 0:
                index += len(self)
            self.update_buffer(index, index + 1)
            newindex = index - self.offset
        if type(key) is tuple:
            newkey = (newindex,) + key[1:]
            return self.buffer[newkey]
        else:
            return self.buffer[newindex]

        
    def blocks(self, block_size, noverlap=0, start=0, stop=None):
        """Generator for blockwise processing of AudioLoader data.

        Parameters
        ----------
        block_size: int
            Len of data blocks to be returned.
        noverlap: int
            Number of indices successive data points should overlap.
        start: int
            Optional first index from which on to return blocks of data.
        stop: int
            Optional last index until which to return blocks of data.

        Yields
        ------
        data: ndarray
            Successive slices of the data managed by AudioLoader.

        Raises
        ------
        ValueError
            `noverlap` larger or equal to `block_size`.

        Examples
        --------
        Use it for processing long audio data, like computing a spectrogram with overlap:
        ```
        from scipy.signal import spectrogram
        from audioio import AudioLoader  # AudioLoader is a BufferedArray
        nfft = 2048
        with AudioLoader('some/audio.wav') as data:
            for x in data.blocks(100*nfft, nfft//2):
                f, t, Sxx = spectrogram(x, fs=data.rate,
                                        nperseg=nfft, noverlap=nfft//2)
        ```
        """
        return blocks(self, block_size, noverlap, start, stop)

    
    def init_buffer(self):
        """Allocate a buffer with zero frames but all the channels.

        Fix `bufferframes` and `backframes` to not exceed the total
        number of frames.

        """
        self.ndim = len(self.shape)
        self.size = self.frames * self.channels
        if self.bufferframes > self.frames:
            self.bufferframes = self.frames
            self.backframes = 0
        shape = list(self.shape)
        shape[0] = 0
        self.buffer = np.empty(shape)
        self.offset = 0
        self.follow = 0
        self.buffer_changed = np.zeros(self.channels, dtype=bool)

        
    def allocate_buffer(self, nframes=None, force=False):
        """Reallocate the buffer to have the right size.

        Parameters
        ----------
        nframes: int or None
            Number of frames the buffer should hold.
            If None, use `self.bufferframes`.
        force: bool
            If True, reallocate buffer even if it has the same size as before.
        """
        if self.bufferframes > self.frames:
            self.bufferframes = self.frames
            self.backframes = 0
        if nframes is None:
            nframes = self.bufferframes
        if nframes == 0:
            return
        if force or nframes != len(self.buffer) or \
           self.shape[1:] != self.buffer.shape[1:]:
            shape = list(self.shape)
            shape[0] = nframes
            self.buffer = np.empty(shape)

            
    def reload_buffer(self):
        """Reload the current buffer.
        """
        if len(self.buffer) > 0:
            self.load_buffer(self.offset, len(self.buffer), self.buffer)
            self.buffer_changed[:] = True
            if self.verbose > 1:
                print(f'  reloaded {len(self.buffer)} frames from {self.offset} up to {self.offset + len(self.buffer)}')

            
    def update_buffer(self, start, stop):
        """Make sure that the buffer contains data of a range of indices.

        Parameters
        ----------
        start: int
            Index of the first requested frame.
        stop: int
            Index of the last requested frame.
        """
        offset, nframes = self.buffer_position(start, stop)
        self.move_buffer(offset, nframes)

                
    def update_time(self, start, stop):
        """Make sure that the buffer contains data of a given time range.

        Parameters
        ----------
        start: float
            Time point of first requested frame.
        stop: int
            Time point of last requested frame.
        """
        self.update_buffer(int(start*self.rate), int(stop*self.rate) + 1)

            
    def move_buffer(self, offset, nframes):
        """Move and resize buffer.

        Parameters
        ----------
        offset: int
           Frame index of the first frame in the new buffer.
        nframes: int
           Number of frames the new buffer should hold.
        """
        if offset < 0:
            offset = 0
        if offset + nframes > self.frames:
            nframes = self.frames - offset
        if offset != self.offset or nframes != len(self.buffer):
            r_offset, r_nframes = self.recycle_buffer(offset, nframes)
            self.offset = offset
            if r_nframes > 0:
                # load buffer content, this is backend specific:
                pbuffer = self.buffer[r_offset - self.offset:
                                      r_offset - self.offset + r_nframes]
                self.load_buffer(r_offset, r_nframes, pbuffer)
                self.buffer_changed[:] = True
            if self.verbose > 1:
                print(f'  loaded {len(pbuffer)} frames from {r_offset} up to {r_offset + r_nframes}')

        
    def buffer_position(self, start, stop):
        """Compute position and size of buffer.

        You usually should not need to call this function
        directly. This is handled by `update_buffer()`.

        Takes `bufferframes` and `backframes` into account.

        Parameters
        ----------
        start: int
            Index of the first requested frame.
        stop: int
            Index of the last requested frame.

        Returns
        -------
        offset: int
           Frame index of the first frame in the new buffer.
        nframes: int
           Number of frames the new buffer should hold.

        """
        if start < 0:
            start = 0
        if stop > self.frames:
            stop = self.frames
        offset = start
        nframes = stop - start
        if start < self.offset or stop > self.offset + len(self.buffer):
            # we need to move the buffer:
            if nframes < self.bufferframes:
                # find optimal new position of buffer that accomodates start:stop
                back = self.backframes
                if self.bufferframes - nframes < 2*back:
                    back = (self.bufferframes - nframes)//2
                offset -= back
                nframes = self.bufferframes
                if offset < 0:
                    offset = 0
                if offset + nframes > self.frames:
                    offset = self.frames - nframes
                    if offset < 0:
                        offset = 0
                        nframes = self.frames - offset
                # expand buffer to accomodate nearby beginning or end:
                elif self.frames - offset - nframes < self.bufferframes//2:
                    nframes = self.frames - offset
                elif offset < self.bufferframes//2:
                    nframes += offset
                    offset = 0
            if self.verbose > 2:
                print(f'  request {nframes:6d} frames at {offset}-{offset+nframes}')
            return offset, nframes
        elif self.follow > 0 and \
             nframes < len(self.buffer) and \
             abs(start - self.offset - self.backframes) >= self.follow:
            offset = start - self.backframes
            nframes = len(self.buffer)
            if offset < 0:
                offset = 0
            if offset + nframes > self.frames:
                offset = self.frames - nframes
                if offset < 0:
                    offset = 0
                    nframes = self.frames - offset
            # expand buffer to accomodate nearby beginning or end:
            elif self.frames - offset - nframes < self.bufferframes//2:
                nframes = self.frames - offset
            elif offset < self.bufferframes//2:
                nframes += offset
                offset = 0
            if start < offset:
                print('invalid buffer start', start, offset)
            if stop > offset + nframes:
                print('invalid buffer end', stop, offset + nframes)
            if self.verbose > 2:
                print(f'  request {nframes:6d} frames at {offset}-{offset+nframes}')
            return offset, nframes
        # no need to move buffer:
        return self.offset, len(self.buffer)

    
    def recycle_buffer(self, offset, nframes):
        """Move buffer to new position and recycle content if possible.

        You usually should not need to call this function
        directly. This is handled by `update_buffer()`.

        Move already existing parts of the buffer to their new position (as
        returned by `buffer_position()`) and return position and size of
        data chunk that still needs to be loaded from file.

        Parameters
        ----------
        offset: int
           Frame index of the new first frame in the buffer.
        nframes: int
           Number of frames the new buffer should hold.

        Returns
        -------
        r_offset: int
           First frame to be read from file.
        r_nframes: int
           Number of frames to be read from file.

        """
        r_offset = offset
        r_nframes = nframes
        if (offset >= self.offset and
            offset < self.offset + len(self.buffer)):
            i = offset - self.offset
            n = len(self.buffer) - i
            if n > nframes:
                n = nframes
            tmp_buffer = self.buffer[i:i + n]
            self.allocate_buffer(nframes)
            self.buffer[:n] = tmp_buffer
            r_offset += n
            r_nframes -= n
            if self.verbose > 2:
                print(f'  recycle {n:6d} frames from {self.offset + i} - {self.offset + i + n} of the old to the front at {offset} - {offset + n} ({0} - {n} in buffer)')
        elif (offset + nframes > self.offset and
              offset + nframes <= self.offset + len(self.buffer)):
            n = offset + nframes - self.offset
            m = len(self.buffer)
            tmp_buffer = self.buffer[:n]
            self.allocate_buffer(nframes)
            self.buffer[-n:] = tmp_buffer
            r_nframes -= n
            if self.verbose > 2:
                print(f'  recycle {n:6d} frames from {self.offset} - {self.offset + n} of the old {m}-sized buffer to the end at {offset + nframes - n} - {offset + nframes} ({nframes - n} - {nframes} in buffer)')
        else:
            # new buffer is somewhere else or larger than current buffer:
            self.allocate_buffer(nframes)
        return r_offset, r_nframes


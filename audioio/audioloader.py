"""
Loading data from audio files.

- `load_audio()` loads a whole audio file at once.
- `AudioLoader` allow to read data from audio files in chunks.
- `blocks()`: generator for blockwise processing of array data.
- `unwrap()` unwraps clipped data that are folded into the available data range.

The read in data are always numpy arrays of floats ranging between -1 and 1.
The arrays are 2-D arrays with first axis time and second axis channel,
even for single channel data.

If an audio file cannot be loaded, you might need to install additional packages.
See [installation](https://bendalab.github.io/audioio/installation)
for further instructions.

For a demo run the module as:
```
python -m audioio.audioloader audiofile.wav
```
"""
 
import warnings
import os.path
import numpy as np
from .audiomodules import *


def load_wave(filepath, verbose=0):
    """Load wav file using the wave module from pythons standard libray.
    
    Documentation
    -------------
    https://docs.python.org/3.8/library/wave.html

    Parameters
    ----------
    filepath: string
        The full path and name of the file to load.
    verbose: int
        If >0 show detailed error/warning messages.
        If 2 print information about soundfile

    Returns
    -------
    data: array
        All data traces as an 2-D numpy array, first dimension is time, second is channel
    rate: float
        The sampling rate of the data in Hertz.

    Raises
    ------
    ImportError
        The wave module is not installed
    *
        Loading of the data failed
    """
    if not audio_modules['wave']:
        raise ImportError

    wf = wave.open(filepath, 'r')   # 'with' is not supported by wave
    (nchannels, sampwidth, rate, nframes, comptype, compname) = wf.getparams()
    if verbose > 1:
        # this should be a separate function with the sndheader module and for all audio formats
        print('channels       : %d' % nchannels)
        print('bytes          : %d' % sampwidth)
        print('sampling rate  : %g' % rate)
        print('frames         : %d' % nframes)
        print('compression type: %s' % comptype)
        print('compression name: %s' % compname)
    buffer = wf.readframes(nframes)
    factor = 2.0**(sampwidth*8-1)
    if sampwidth == 1:
        dtype = 'u1'
        buffer = np.frombuffer(buffer, dtype=dtype).reshape(-1, nchannels)
        data = buffer.astype('d')/factor - 1.0
    else:
        dtype = 'i%d' % sampwidth
        buffer = np.frombuffer(buffer, dtype=dtype).reshape(-1, nchannels)
        data = buffer.astype('d')/factor
    wf.close()
    return data, float(rate)

    
def load_ewave(filepath, verbose=0):
    """Load wav file using ewave module.

    Documentation
    -------------
    https://github.com/melizalab/py-ewave

    Parameters
    ----------
    filepath: string
        The full path and name of the file to load.
    verbose: int
        If >0 show detailed error/warning messages (not used).

    Returns
    -------
    data: array
        All data traces as an 2-D numpy array, first dimension is time, second is channel.
    rate: float
        The sampling rate of the data in Hertz.

    Raises
    ------
    ImportError
        The ewave module is not installed
    *
        Loading of the data failed
    """
    if not audio_modules['ewave']:
        raise ImportError

    data = np.array([])
    rate = 0.0
    with ewave.open(filepath, 'r') as wf:
        rate = wf.sampling_rate
        buffer = wf.read()
        data = ewave.rescale(buffer, 'float')
    if len(data.shape) == 1:
        data = np.reshape(data,(-1, 1))
    return data, float(rate)

    
def load_wavfile(filepath, verbose=0):
    """Load wav file using scipy.io.wavfile.

    Documentation
    -------------
    http://docs.scipy.org/doc/scipy/reference/io.html
    Does not support blocked read.
    
    Parameters
    ----------
    filepath: string
        The full path and name of the file to load.
    verbose: int
        If >0 show detailed error/warning messages.

    Returns
    -------
    data: array
        All data traces as an 2-D numpy array, first dimension is time, second is channel.
    rate: float
        The sampling rate of the data in Hertz.

    Raises
    ------
    ImportError
        The scipy.io module is not installed
    *
        Loading of the data failed
    """
    if not audio_modules['scipy.io.wavfile']:
        raise ImportError

    if verbose < 2:
        warnings.filterwarnings("ignore")
    rate, data = wavfile.read(filepath)
    if verbose < 2:
        warnings.filterwarnings("always")
    if data.dtype == np.uint8:
        data = data / 128.0 - 1.0
    elif np.issubdtype(data.dtype, np.signedinteger):
        data = data / (2.0**(data.dtype.itemsize*8-1))
    else:
        data = data.astype(np.float64, copy=False)
    if len(data.shape) == 1:
        data = np.reshape(data,(-1, 1))
    return data, float(rate)


def load_soundfile(filepath, verbose=0):
    """Load audio file using SoundFile (based on libsndfile).

    Documentation
    -------------
    http://pysoundfile.readthedocs.org
    http://www.mega-nerd.com/libsndfile

    Parameters
    ----------
    filepath: string
        The full path and name of the file to load.
    verbose: int
        If >0 show detailed error/warning messages (not used).

    Returns
    -------
    data: array
        All data traces as an 2-D numpy array, first dimension is time, second is channel.
    rate: float
        The sampling rate of the data in Hertz.

    Raises
    ------
    ImportError
        The soundfile module is not installed.
    *
        Loading of the data failed.
    """
    if not audio_modules['soundfile']:
        raise ImportError

    data = np.array([])
    rate = 0.0
    with soundfile.SoundFile(filepath, 'r') as sf:
        rate = sf.samplerate
        data = sf.read(frames=-1, dtype='float64', always_2d=True)
    return data, float(rate)


def load_wavefile(filepath, verbose=0):
    """Load audio file using wavefile (based on libsndfile).

    Documentation
    -------------
    https://github.com/vokimon/python-wavefile

    Parameters
    ----------
    filepath: string
        The full path and name of the file to load.
    verbose: int
        If >0 show detailed error/warning messages (not used).

    Returns
    -------
    data: array
        All data traces as an 2-D numpy array, first dimension is time, second is channel.
    rate: float
        The sampling rate of the data in Hertz.

    Raises
    ------
    ImportError
        The wavefile module is not installed.
    *
        Loading of the data failed.
    """
    if not audio_modules['wavefile']:
        raise ImportError

    rate, data = wavefile.load(filepath)
    return data.astype(np.float64, copy=False).T, float(rate)


def load_audioread(filepath, verbose=0):
    """Load audio file using audioread.

    Documentation
    -------------
    https://github.com/beetbox/audioread

    Parameters
    ----------
    filepath: string
        The full path and name of the file to load.
    verbose: int
        If >0 show detailed error/warning messages (not used).

    Returns
    -------
    data: array
        All data traces as an 2-D numpy array, first dimension is time, second is channel.
    rate: float
        The sampling rate of the data in Hertz.

    Raises
    ------
    ImportError
        The audioread module is not installed.
    *
        Loading of the data failed.
    """
    if not audio_modules['audioread']:
        raise ImportError
    
    data = np.array([])
    rate = 0.0
    with audioread.audio_open(filepath) as af:
        rate = af.samplerate
        data = np.zeros((int(np.ceil(af.samplerate*af.duration)), af.channels),
                        dtype="<i2")
        index = 0
        for buffer in af:
            fulldata = np.frombuffer(buffer, dtype='<i2').reshape(-1, af.channels)
            n = fulldata.shape[0]
            if index + n > len(data):
                n = len(fulldata) - index
            if n <= 0:
                break
            data[index:index+n,:] = fulldata[:n,:]
            index += n
    return data/(2.0**15-1.0), float(rate)


audio_loader_funcs = (
    ('soundfile', load_soundfile),
    ('audioread', load_audioread),
    ('wave', load_wave),
    ('wavefile', load_wavefile),
    ('ewave', load_ewave),
    ('scipy.io.wavfile', load_wavfile)
    )
"""List of implemented load functions.

Each element of the list is a tuple with the module's name and the load function.
"""    


def load_audio(filepath, verbose=0):
    """Call this function to load all channels of audio data from a file.
    
    This function tries different python modules to load the audio file.

    Parameters
    ----------
    filepath: string
        The full path and name of the file to load.
    verbose: int
        If >0 show detailed error/warning messages.

    Returns
    -------
    data: array
        All data traces as an 2-D numpy array, even for single channel data.
        First dimension is time, second is channel.
        Data values range maximally between -1 and 1.
    rate: float
        The sampling rate of the data in Hertz.

    Raises
    ------
    ValueError
        Empty `filepath`.
    FileNotFoundError
        `filepath` is not an existing file.
    EOFError
        File size of `filepath` is zero.
    IOError
        Failed to load data.

    Example
    -------
    ```
    import matplotlib.pyplot as plt
    from audioio import load_audio
    
    data, rate = load_audio('some/audio.wav')
    plt.plot(np.arange(len(data))/rate, data[:,0])
    plt.show()
    ```
    """
    # check values:
    if filepath is None or len(filepath) == 0:
        raise ValueError('input argument filepath is empty string!')
    if not os.path.isfile(filepath):
        raise FileNotFoundError('file "%s" not found' % filepath)
    if os.path.getsize(filepath) <= 0:
        raise EOFError('file "%s" is empty (size=0)!' % filepath)

    # load an audio file by trying various modules:
    success = False
    not_installed = []
    for lib, load_file in audio_loader_funcs:
        if not audio_modules[lib]:
            if verbose > 1:
                print('unable to load data from file "%s" using %s module: module not available' %
                      (filepath, lib))
            not_installed.append(lib)
            continue
        try:
            data, rate = load_file(filepath, verbose)
            if len(data) > 0:
                success = True
                if verbose > 0:
                    print('loaded data from file "%s" using %s module' %
                          (filepath, lib))
                    if verbose > 1:
                        print('  sampling rate: %g Hz' % rate)
                        print('  channels     : %d' % data.shape[1])
                        print('  data values  : %d' % len(data))
                break
        except Exception as e:
            pass
    if not success:
        need_install = ""
        if len(not_installed) > 0:
            need_install = " You may need to install one of the " + \
              ', '.join(not_installed) + " packages."
        raise IOError('failed to load data from file "%s".%s' %
                      (filepath, need_install))
    return data, rate


def blocks(data, block_size, noverlap=0):
    """Generator for blockwise processing of array data.

    Parameters
    ----------
    data: array
        Data to loop over. First dimension is time.
    block_size: int
        Len of data blocks to be returned.
    noverlap: int
        Number of indices successive data points should overlap.

    Yields
    ------
    data: array
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

    Use it for processing long audio data, like computing a spectrogram with overlap:
    ```
    from scipy.signal import spectrogram
    from audioio import AudioLoader, blocks
    nfft = 2048
    with AudioLoader('some/audio.wav') as data:
        for x in blocks(data, 100*nfft, nfft//2):
            f, t, Sxx = spectrogram(x, nperseg=nfft, noverlap=nfft//2)
    ```
    """
    if noverlap >= block_size:
        raise ValueError('noverlap=%d larger than block_size=%d' % (noverlap, block_size))
    m = block_size - noverlap
    n = (len(data)-noverlap)//m
    if n == 0:
        yield data[:]
    else:
        for k in range(n):
            yield data[k*m:k*m+block_size]
        if len(data) - (k*m+block_size) > 0:
            yield data[(k+1)*m:]


def unwrap(data):
    """Fixes data that exceeded the -1 to 1 range.

    If data that exceed the range from -1.0 to 1.0 are stored in a wav file,
    they get wrapped around. This functions tries to undo this wrapping.
    
    Parameters
    ----------
    data: 1D or 2D ndarray
        Data to be fixed.

    Returns
    -------
    data: same as input data
        The fixed data.
    """
    if len(data.shape) > 1:
        for c in range(data.shape[1]):
            data[:,c] = unwrap(data[:,c])
    else:
        for k in range(20):
            dd = (data[1:] < -0.8) & (np.diff(data) <= -1.0)
            du = (data[1:] > 0.8) & (np.diff(data) >= 1.0)
            if np.sum(dd) == 0 and np.sum(du) == 0:
                break
            data[1:][dd] += 2.0
            data[1:][du] -= 2.0
    return data


class AudioLoader(object):
    """Buffered reading of audio data for random access of the data in the file.
    
    The class allows for reading very large audio files that do not fit into memory.
    An AudioLoader instance can be used like a huge read-only numpy array, i.e.
    ```
    data = AudioLoader('path/to/audio/file.wav')
    x = data[10000:20000,0]
    ```
    The first index specifies the frame, the second one the channel.

    Behind the scenes AudioLoader tries to open the audio file with all available
    audio modules until it succeeds (first line). It then reads data from the file
    as necessary for the requested data (second line).

    Reading sequentially through the file is always possible. Some
    modules, however, (e.g. audioread, needed for mp3 files) can only
    read forward. If previous data are requested, then the file is read
    from the beginning. This slows down access to previous data
    considerably. Use the `backsize` argument of the open function to
    make sure some data are loaded into the buffer before the requested
    frame. Then a subsequent access to the data within backsize `seconds`
    before that frame can still be handled without the need to reread
    the file from the beginning.

    Usage
    -----
    With context management:
    ```
    import audioio as aio
    with aio.AudioLoader(filepath, 60.0, 10.0) as data:
        # do something with the content of the file:
        x = data[0:10000]
        y = data[10000:20000]
        z = x + y
    ```

    For using a specific audio module, here the audioread module:
    ```
    data = aio.AudioLoader()
    with data.open_audioread(filepath, 60.0, 10.0):
        # do something ...
    ```

    Use `blocks()` for sequential, blockwise reading and processing:
    ```
    from scipy.signal import spectrogram
    nfft = 2048
    with aio.AudioLoader('some/audio.wav') as data:
        for x in data.blocks(100*nfft, nfft//2):
            f, t, Sxx = spectrogram(x, nperseg=nfft, noverlap=nfft//2)
    ```

    For loop iterates over single frames (1-D arrays containing samples for each channel):
    ```
    with aio.AudioLoader('some/audio.wav') as data:
        for x in data:
            print(x)
    ```
    
    Traditional open and close:
    ```
    data = aio.AudioLoader(filepath, 60.0)
    x = data[:,:]  # read the whole file
    data.close()
    ```
        
    this is the same as:
    ```
    data = aio.AudioLoader()
    data.open(filepath, 60.0)
    ...
    ```
    
    Parameters
    ----------
    filepath: string
        Name of the file.
    buffersize: float
        Size of internal buffer in seconds.
    backsize: float
        Part of the buffer to be loaded before the requested start index in seconds.
    verbose: int
        If >0 show detailed error/warning messages.

    Attributes
    ----------
    samplerate: float
        The sampling rate of the data in seconds.
    channels: int
        The number of channels.
    frames: int
        The number of frames in the file.
    shape: tuple
        Frames and channels of the data.

    Methods
    -------
    len()
        Number of frames.
    open()
        Open an audio file by trying available audio modules.
    open_*()
        Open an audio file with the respective audio module.
    __getitem__
        Access data of the audio file.
    blocks()
        Generator for blockwise processing of AudioLoader data.
    close()
        Close the file.

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
    
    def __init__(self, filepath=None, buffersize=10.0, backsize=0.0, verbose=0):
        self.sf = None
        self.samplerate = 0.0
        self.channels = 0
        self.frames = 0
        self.shape = (0, 0)
        self.offset = 0
        self.buffersize = 0
        self.backsize = 0
        self.buffer = np.zeros((0,0))
        self.verbose = verbose
        self.close = self._close
        if filepath is not None:
            self.open(filepath, buffersize, backsize, verbose)

    def _close(self):
        pass

    def __del__(self):
        self.close()

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
            self._update_buffer(self.iter_counter, self.iter_counter+1)
            return self.buffer[self.iter_counter-self.offset,:]

    def next(self):  # python 2
        return self.__next__()

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
                start=0
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
            self._update_buffer(start, stop)
            newindex = slice(start-self.offset, stop-self.offset, step)
        elif hasattr(index, '__len__'):
            index = [inx if inx >= 0 else inx+len(self) for inx in index]
            start = min(index)
            stop = max(index)
            self._update_buffer(start, stop+1)
            newindex = [inx-self.offset for inx in index]
        else:
            if index > self.frames:
                raise IndexError
            index = int(index)
            if index < 0:
                index += len(self)
            self._update_buffer(index, index+1)
            newindex = index-self.offset
        if type(key) is tuple:
            newkey = (newindex,) + key[1:]
            return self.buffer[newkey]
        else:
            return self.buffer[newindex]

    def blocks(self, block_size, noverlap=0):
        """Generator for blockwise processing of AudioLoader data.

        Parameters
        ----------
        block_size: int
            Len of data blocks to be returned.
        noverlap: int
            Number of indices successive data points should overlap.

        Yields
        ------
        data: array
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
        from audioio import AudioLoader, blocks
        nfft = 2048
        with AudioLoader('some/audio.wav') as data:
            for x in data.blocks(100*nfft, nfft//2):
                f, t, Sxx = spectrogram(x, nperseg=nfft, noverlap=nfft//2)
        ```
        """
        return blocks(self, block_size, noverlap)

    def _init_buffer(self):
        """Allocate a buffer of size zero."""
        self.buffer = np.empty((0, self.channels))

    def _update_buffer(self, start, stop):
        """Make sure that the buffer contains data between start and stop.

        Parameters
        ----------
        start: int
            Index of the first frame for the buffer.
        stop: int
            Index of the last frame for the buffer.
        """
        if start < self.offset or stop > self.offset + self.buffer.shape[0]:
            offset, size = self._read_indices(start, stop)
            r_offset, r_size = self._recycle_buffer(offset, size)
            self.offset = offset
            # load buffer content from file, this is backend specific:
            self._load_buffer(r_offset, r_size)

    def _read_indices(self, start, stop):
        """Compute position and size for next read from file.

        This takes buffersize and backsize into account.

        Parameters
        ----------
        start: int
            Index of the first requested frame.
        stop: int
            Index of the last requested frame.

        Returns
        -------
        offset: int
           Frame index for the first frame in the buffer.
        size: int
           Number of frames the buffer should hold.
        """
        offset = start
        size = stop-start
        if size < self.buffersize:
            back = self.backsize
            if self.buffersize - size < back:
                back = self.buffersize - size
            offset -= back
            size = self.buffersize
            if offset < 0:
                offset = 0
            if offset + size > self.frames:
                offset = self.frames - size
                if offset < 0:
                    offset = 0
                    size = self.frames - offset
        if self.verbose > 2:
            print('  request %6d frames at %d-%d' % (size, offset, offset+size))
        return offset, size

    def _recycle_buffer(self, offset, size):
        """Recycle buffer contents and return indices for data to be loaded from file.

        Move already existing parts of the buffer to their new position (as
        returned by _read_indices() ) and return position and size of
        data chunk that still needs to be loaded from file.

        Parameters
        ----------
        offset: int
           Frame index for the first frame in the buffer.
        size: int
           Number of frames the buffer should hold.

        Returns
        -------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        """
        def allocate_buffer(size):
            """Make sure the buffer has the right size."""
            if size != self.buffer.shape[0]:
                self.buffer = np.empty((size, self.channels))

        r_offset = offset
        r_size = size
        if ( offset >= self.offset and
             offset < self.offset + self.buffer.shape[0] ):
            i = self.offset + self.buffer.shape[0] - offset
            n = i
            if n > size:
                n = size
            m = self.buffer.shape[0]
            buffer = self.buffer[-i:m-i+n,:]
            allocate_buffer(size)
            self.buffer[:n,:] = buffer
            r_offset += n
            r_size -= n
            if self.verbose > 2:
                print('  recycle %6d frames from %d-%d of the old %d-sized buffer to the front at %d-%d (%d-%d in buffer)'
                       % (n, self.offset+m-i, self.offset+m-i+n, m, offset, offset+n, 0, n))
        elif ( offset + size > self.offset and
            offset + size <= self.offset + self.buffer.shape[0] ):
            n = offset + size - self.offset
            m = self.buffer.shape[0]
            buffer = self.buffer[:n,:]
            allocate_buffer(size)
            self.buffer[-n:,:] = buffer
            r_size -= n
            if self.verbose > 2:
                print('  recycle %6d frames from %d-%d of the old %d-sized buffer to the end at %d-%d (%d-%d in buffer)'
                       % (n, self.offset, self.offset+n, m, offset+size-n, offset+size, size-n, size))
        else:
            allocate_buffer(size)
        return r_offset, r_size

    
    # wave interface:        
    def open_wave(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the wave module.

        Note: we assume that setpos() and tell() use integer numbers!

        Parameters
        ----------
        filepath: string
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If >0 show detailed error/warning messages.

        Raises
        ------
        ImportError
            The wave module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print('open_wave(filepath) with filepath=%s' % filepath)
        if not audio_modules['wave']:
            self.samplerate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_wave()
        self.sf = wave.open(filepath, 'r')
        self.samplerate = float(self.sf.getframerate())
        sampwidth = self.sf.getsampwidth()
        if sampwidth == 1:
            self.dtype = 'u1'
        else:
            self.dtype = 'i%d' % sampwidth
        self.factor = 1.0/(2.0**(sampwidth*8-1))
        self.channels = self.sf.getnchannels()
        self.frames = self.sf.getnframes()
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_wave
        self._load_buffer = self._load_buffer_wave
        # read 1 frame to determine the unit of the position values:
        self.p0 = self.sf.tell()
        self.sf.readframes(1)
        self.pfac = self.sf.tell() - self.p0
        self.sf.setpos(self.p0)
        return self

    def _close_wave(self):
        """Close the audio file using the wave module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _load_buffer_wave(self, r_offset, r_size):
        """Load new data from file using the wave module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        """
        self.sf.setpos(r_offset*self.pfac + self.p0)
        buffer = self.sf.readframes(r_size)
        buffer = np.frombuffer(buffer, dtype=self.dtype).reshape((-1, self.channels))
        if self.dtype[0] == 'u':
            self.buffer[r_offset-self.offset:r_offset+r_size-self.offset,:] = buffer * self.factor - 1.0
        else:
            self.buffer[r_offset-self.offset:r_offset+r_size-self.offset,:] = buffer * self.factor
        if self.verbose > 1:
            print('  loaded %6d frames at %d' % (r_size, r_offset))
        

    # ewave interface:        
    def open_ewave(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the ewave module.

        Parameters
        ----------
        filepath: string
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If >0 show detailed error/warning messages.

        Raises
        ------
        ImportError
            The ewave module is not installed.
        """
        self.verbose = verbose
        if self.verbose > 0:
            print('open_ewave(filepath) with filepath=%s' % filepath)
        if not audio_modules['ewave']:
            self.samplerate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_ewave()
        self.sf = ewave.open(filepath, 'r')
        self.samplerate = float(self.sf.sampling_rate)
        self.channels = self.sf.nchannels
        self.frames = self.sf.nframes
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_ewave
        self._load_buffer = self._load_buffer_ewave
        return self

    def _close_ewave(self):
        """Close the audio file using the ewave module. """
        if self.sf is not None:
            del self.sf
            self.sf = None

    def _load_buffer_ewave(self, r_offset, r_size):
        """Load new data from file using the wave module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        """
        buffer = self.sf.read(frames=r_size, offset=r_offset, memmap='r')
        buffer = ewave.rescale(buffer, 'float')
        if len(buffer.shape) == 1:
            buffer = np.reshape(buffer,(-1, 1))
        self.buffer[r_offset-self.offset:r_offset+r_size-self.offset,:] = buffer
        if self.verbose > 1:
            print('  loaded %d frames from %d up to %d'
                  % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

            
    # soundfile interface:        
    def open_soundfile(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the SoundFile module.

        Parameters
        ----------
        filepath: string
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If >0 show detailed error/warning messages.

        Raises
        ------
        ImportError
            The SoundFile module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print('open_soundfile(filepath) with filepath=%s' % filepath)
        if not audio_modules['soundfile']:
            self.samplerate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_soundfile()
        self.sf = soundfile.SoundFile(filepath, 'r')
        self.samplerate = float(self.sf.samplerate)
        self.channels = self.sf.channels
        self.frames = 0
        if self.sf.seekable():
            self.frames = self.sf.seek(0, soundfile.SEEK_END)
            self.sf.seek(0, soundfile.SEEK_SET)
        # TODO: if not seekable, we cannot handle that file!
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_soundfile
        self._load_buffer = self._load_buffer_soundfile
        return self

    def _close_soundfile(self):
        """Close the audio file using the SoundFile module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _load_buffer_soundfile(self, r_offset, r_size):
        """Load new data from file using the wave module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        """
        self.sf.seek(r_offset, soundfile.SEEK_SET)
        self.buffer[r_offset-self.offset:r_offset+r_size-self.offset,:] = self.sf.read(r_size, always_2d=True)
        if self.verbose > 1:
            print('  loaded %d frames from %d up to %d'
                  % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

            
    # wavefile interface:        
    def open_wavefile(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the wavefile module.

        Parameters
        ----------
        filepath: string
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If >0 show detailed error/warning messages.

        Raises
        ------
        ImportError
            The wavefile module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print('open_wavefile(filepath) with filepath=%s' % filepath)
        if not audio_modules['wavefile']:
            self.samplerate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_wavefile()
        self.sf = wavefile.WaveReader(filepath)
        self.samplerate = float(self.sf.samplerate)
        self.channels = self.sf.channels
        self.frames = self.sf.frames
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_wavefile
        self._load_buffer = self._load_buffer_wavefile
        return self

    def _close_wavefile(self):
        """Close the audio file using the wavefile module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _load_buffer_wavefile(self, r_offset, r_size):
        """Load new data from file using the wave module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        """
        self.sf.seek(r_offset, wavefile.Seek.SET)
        buffer = self.sf.buffer(r_size, dtype=self.buffer.dtype)
        self.sf.read(buffer)
        self.buffer[r_offset-self.offset:r_offset+r_size-self.offset,:] = buffer.T
        if self.verbose > 1:
            print('  loaded %d frames from %d up to %d'
                  % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

            
    # audioread interface:        
    def open_audioread(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the audioread module.

        Note, that audioread can only read forward, therefore random and
        backward access is really slow.

        Parameters
        ----------
        filepath: string
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If >0 show detailed error/warning messages.

        Raises
        ------
        ImportError
            The audioread module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print('open_audio_read(filepath) with filepath=%s' % filepath)
        if not audio_modules['audioread']:
            self.samplerate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_audioread()
        self.sf = audioread.audio_open(filepath)
        self.samplerate = float(self.sf.samplerate)
        self.channels = self.sf.channels
        self.frames = int(np.ceil(self.samplerate*self.sf.duration))
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.read_buffer = np.zeros((0,0))
        self.read_offset = 0
        self.close = self._close_audioread
        self._load_buffer = self._load_buffer_audioread
        self.filepath = filepath
        self.sf_iter = self.sf.__iter__()
        return self

    def _close_audioread(self):
        """Close the audio file using the audioread module. """
        if self.sf is not None:
            self.sf.__exit__(None, None, None)
            self.sf = None

    def _load_buffer_audioread(self, r_offset, r_size):
        """Load new data from file using the wave module.

        audioread can only iterate through a file once and in blocksizes that are
        given by audioread. Therefore we keep yet another buffer: `self.read_buffer`
        at file offset `self.read_offset` containing whatever audioread returned.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        """
        if ( self.read_offset + self.read_buffer.shape[0] >= r_offset + r_size
             and self.read_offset < r_offset + r_size ):
            # read_buffer overlaps at the end of the requested interval:
            i = 0
            n = r_offset + r_size - self.read_offset
            if n > r_size:
                i += n - r_size
                n = r_size
            self.buffer[self.read_offset+i-self.offset:self.read_offset+i-self.offset+n,:] = self.read_buffer[i:i+n,:] / (2.0**15-1.0)
            if self.verbose > 2:
                print('  recycle %6d frames from the front of the read buffer at %d-%d (%d-%d in buffer)'
                       % (n, self.read_offset, self.read_offset+n, self.read_offset-self.offset, self.read_offset-self.offset+n))
            r_size -= n
            if r_size <= 0:
                return
        # go back to beginning of file:
        if r_offset < self.read_offset:
            if self.verbose > 2:
                print('  rewind')
            self._close_audioread()
            self.sf = audioread.audio_open(self.filepath)
            self.sf_iter = self.sf.__iter__()
            self.read_buffer = np.zeros((0,0))
            self.read_offset = 0
        # read to position:
        while self.read_offset + self.read_buffer.shape[0] < r_offset:
            self.read_offset += self.read_buffer.shape[0]
            try:
                if hasattr(self.sf_iter, 'next'):
                    buffer = self.sf_iter.next()
                else:
                    buffer = next(self.sf_iter)
            except StopIteration:
                self.read_buffer = np.zeros((0,0))
                self.buffer[r_offset-self.offset:,:] = 0.0
                if self.verbose > 1:
                    print('  caught StopIteration, padded buffer with %d zeros' % r_size)
                break
            self.read_buffer = np.frombuffer(buffer, dtype='<i2').reshape(-1, self.channels)
            if self.verbose > 2:
                print('  read forward by %d frames' % self.read_buffer.shape[0])
        # recycle file data:
        if ( self.read_offset + self.read_buffer.shape[0] > r_offset
             and self.read_offset <= r_offset ):
            i = r_offset - self.read_offset
            n = self.read_offset + self.read_buffer.shape[0] - r_offset
            if n > r_size:
                n = r_size
            self.buffer[r_offset - self.offset:r_offset - self.offset + n,:] = self.read_buffer[i:i+n,:] / (2.0**15-1.0)
            if self.verbose > 2:
                print('  recycle %6d frames from the end of the read buffer at %d-%d to %d-%d (%d-%d in buffer)'
                       % (n, self.read_offset, self.read_offset + self.read_buffer.shape[0],
                          r_offset, r_offset+n, r_offset-self.offset, r_offset+n-self.offset))
            r_offset += n
            r_size -= n
        # read data:
        if self.verbose > 2 and r_size > 0:
            print('  read    %6d frames at %d-%d (%d-%d in buffer)'
                   % (r_size, r_offset, r_offset+r_size, r_offset-self.offset, r_offset+r_size-self.offset))
        while r_size > 0:
            self.read_offset += self.read_buffer.shape[0]
            try:
                if hasattr(self.sf_iter, 'next'):
                    buffer = self.sf_iter.next()
                else:
                    buffer = next(self.sf_iter)
            except StopIteration:
                self.read_buffer = np.zeros((0,0))
                self.buffer[r_offset-self.offset:,:] = 0.0
                if self.verbose > 1:
                    print('  caught StopIteration, padded buffer with %d zeros' % r_size)
                break
            self.read_buffer = np.frombuffer(buffer, dtype='<i2').reshape(-1, self.channels)
            n = self.read_buffer.shape[0]
            if n > r_size:
                n = r_size
            if n > 0:
                self.buffer[r_offset-self.offset:r_offset-self.offset+n,:] = self.read_buffer[:n,:] / (2.0**15-1.0)
                if self.verbose > 2:
                    print('    read  %6d frames to %d-%d (%d-%d in buffer)'
                          % (n, r_offset, r_offset+n, r_offset-self.offset, r_offset+n-self.offset))
                r_offset += n
                r_size -= n
        if self.verbose > 1:
            print('  loaded  %d frames at %d-%d'
                  % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

                                
    def open(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading.

        Parameters
        ----------
        filepath: string
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If >0 show detailed error/warning messages.

        Raises
        ------
        ValueError
            Empty `filepath`.
        FileNotFoundError
            `filepath` is not an existing file.
        EOFError
            File size of `filepath` is zero.
        IOError
            Failed to load data.
        """
        self.buffer = np.array([])
        self.samplerate = 0.0
        if len(filepath) == 0:
            raise ValueError('input argument filepath is empty string!')
        if not os.path.isfile(filepath):
            raise FileNotFoundError('file "%s" not found' % filepath)
        if os.path.getsize(filepath) <= 0:
            raise EOFError('file "%s" is empty (size=0)!' % filepath)
        # list of implemented open functions:
        audio_open = [
            ['soundfile', self.open_soundfile],
            ['audioread', self.open_audioread],
            ['wave', self.open_wave],
            ['wavefile', self.open_wavefile],
            ['ewave', self.open_ewave]
            ]
        # open an audio file by trying various modules:
        success = False
        not_installed = []
        for lib, open_file in audio_open:
            if not audio_modules[lib]:
                if verbose > 1:
                    print('failed to load data from file "%s" using %s module' %
                          (filepath, lib))
                not_installed.append(lib)
                continue
            try:
                open_file(filepath, buffersize, backsize, verbose-1)
                if self.frames > 0:
                    success = True
                    if verbose > 0:
                        print('opened audio file "%s" using %s' % (filepath, lib))
                        if verbose > 1:
                            print('  sampling rate: %g Hz' % self.samplerate)
                            print('  data values  : %d' % self.frames)
                    break
            except Exception as e:
                    pass
        if not success:
            need_install = ""
            if len(not_installed) > 0:
                need_install = " You may need to install one of the " + \
                  ', '.join(not_installed) + " packages."
            raise IOError('failed to load data from file "%s".%s' %
                          (filepath, need_install))
        return self

    
def demo(file_path, plot):
    """Demo of the audioloader functions.

    Parameters
    ----------
    file_path: string
        File path of an audio file.
    plot: bool
        If True also plot the loaded data.
    """
    print('')
    print("try load_audio:")
    full_data, rate = load_audio(file_path, 1)
    if plot:
        plt.plot(np.arange(len(full_data))/rate, full_data[:,0])
        plt.show()

    if audio_modules['soundfile'] and audio_modules['audioread']:
        print('')
        print("cross check:")
        data1, rate1 = load_soundfile(file_path)
        data2, rate2 = load_audioread(file_path)
        n = min((len(data1), len(data2)))
        print("rms difference is %g" % np.std(data1[:n]-data2[:n]))
        if plot:
            plt.plot(np.arange(len(data1))/rate1, data1[:,0])
            plt.plot(np.arange(len(data2))/rate2, data2[:,0])
            plt.show()
    
    print('')
    print("try AudioLoader:")
    with AudioLoader(file_path, 4.0, 1.0, 1) as data:
        print('samplerate: %g' % data.samplerate)
        print('channels: %d %d' % (data.channels, data.shape[1]))
        print('frames: %d %d' % (len(data), data.shape[0]))
        nframes = int(1.5*data.samplerate)
        # check access:
        print('check random single frame access')
        for inx in np.random.randint(0, len(data), 1000):
            if np.any(np.abs(full_data[inx] - data[inx]) > 2.0**(-14)):
                print('single random frame access failed', inx, full_data[inx], data[inx])
        print('check random frame slice access')
        for inx in np.random.randint(0, len(data)-nframes, 1000):
            if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > 2.0**(-14)):
                print('random frame slice access failed', inx)
        print('check frame slice access forward')
        for inx in range(0, len(data)-nframes, 10):
            if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > 2.0**(-14)):
                print('frame slice access forward failed', inx)
        print('check frame slice access backward')
        for inx in range(len(data)-nframes, 0, -10):
            if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > 2.0**(-14)):
                print('frame slice access backward failed', inx)
        # forward:
        for i in range(0, len(data), nframes):
            print('forward %d-%d' % (i, i+nframes))
            x = data[i:i+nframes,0]
            if plot:
                plt.plot((i+np.arange(len(x)))/rate, x)
                plt.show()
        # and backwards:
        for i in reversed(range(0, len(data), nframes)):
            print('backward %d-%d' % (i, i+nframes))
            x = data[i:i+nframes,0]
            if plot:
                plt.plot((i+np.arange(len(x)))/rate, x)
                plt.show()


def main(args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv
    """
    print("Checking audioloader module ...")

    help = False
    plot = False
    file_path = None
    mod = False
    for arg in args[1:]:
        if mod:
            if not select_module(arg):
                print('can not select module %s that is not installed' % arg)
                return
            mod = False
        elif arg == '-h':
            help = True
            break
        elif arg == '-p':
            plot = True
        elif arg == '-m':
            mod = True
        else:
            file_path = arg
            break

    if help:
        print('')
        print('Usage:')
        print('  python -m audioio.audioloader [-m <module>] [-p] <audio/file.wav>')
        print('  -m: audio module to be used')
        print('  -p: plot loaded data')
        return

    if plot:
        import matplotlib.pyplot as plt

    demo(file_path, plot)


if __name__ == "__main__":
    import sys
    main(sys.argv)

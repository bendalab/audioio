"""Loading data, metadata, and markers from audio files.

- `load_audio()`: load a whole audio file at once.
- `metadata()`: read metadata of an audio file.
- `markers()`: read markers of an audio file.
- class `AudioLoader`: read data from audio files in chunks.

The read in data are always numpy arrays of floats ranging between -1 and 1.
The arrays are 2-D ndarrays with first axis time and second axis channel,
even for single channel data.

If an audio file cannot be loaded, you might need to install
additional packages.  See
[installation](https://bendalab.github.io/audioio/installation) for
further instructions.

For a demo run the module as:
```
python -m src.audioio.audioloader audiofile.wav
```
"""
 
import sys
import warnings
import os.path
import numpy as np
from .audiomodules import *
from .bufferedarray import BufferedArray
from .riffmetadata import metadata_riff, markers_riff
from .audiometadata import update_gain, add_unwrap
from .audiotools import unwrap


def load_wave(filepath):
    """Load wav file using the wave module from pythons standard libray.
    
    Documentation
    -------------
    https://docs.python.org/3.8/library/wave.html

    Parameters
    ----------
    filepath: str
        The full path and name of the file to load.

    Returns
    -------
    data: ndarray
        All data traces as an 2-D ndarray, first dimension is time, second is channel
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
    buffer = wf.readframes(nframes)
    factor = 2.0**(sampwidth*8-1)
    if sampwidth == 1:
        dtype = 'u1'
        buffer = np.frombuffer(buffer, dtype=dtype).reshape(-1, nchannels)
        data = buffer.astype('d')/factor - 1.0
    else:
        dtype = f'i{sampwidth}' 
        buffer = np.frombuffer(buffer, dtype=dtype).reshape(-1, nchannels)
        data = buffer.astype('d')/factor
    wf.close()
    return data, float(rate)

    
def load_ewave(filepath):
    """Load wav file using ewave module.

    Documentation
    -------------
    https://github.com/melizalab/py-ewave

    Parameters
    ----------
    filepath: str
        The full path and name of the file to load.

    Returns
    -------
    data: ndarray
        All data traces as an 2-D ndarray, first dimension is time, second is channel.
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

    
def load_wavfile(filepath):
    """Load wav file using scipy.io.wavfile.

    Documentation
    -------------
    http://docs.scipy.org/doc/scipy/reference/io.html
    Does not support blocked read.
    
    Parameters
    ----------
    filepath: str
        The full path and name of the file to load.

    Returns
    -------
    data: ndarray
        All data traces as an 2-D ndarray, first dimension is time, second is channel.
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

    warnings.filterwarnings("ignore")
    rate, data = wavfile.read(filepath)
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


def load_soundfile(filepath):
    """Load audio file using SoundFile (based on libsndfile).

    Documentation
    -------------
    http://pysoundfile.readthedocs.org
    http://www.mega-nerd.com/libsndfile

    Parameters
    ----------
    filepath: str
        The full path and name of the file to load.

    Returns
    -------
    data: ndarray
        All data traces as an 2-D ndarray, first dimension is time, second is channel.
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


def load_wavefile(filepath):
    """Load audio file using wavefile (based on libsndfile).

    Documentation
    -------------
    https://github.com/vokimon/python-wavefile

    Parameters
    ----------
    filepath: str
        The full path and name of the file to load.

    Returns
    -------
    data: ndarray
        All data traces as an 2-D ndarray, first dimension is time, second is channel.
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


def load_audioread(filepath):
    """Load audio file using audioread.

    Documentation
    -------------
    https://github.com/beetbox/audioread

    Parameters
    ----------
    filepath: str
        The full path and name of the file to load.

    Returns
    -------
    data: ndarray
        All data traces as an 2-D ndarray, first dimension is time, second is channel.
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
    ('wave', load_wave),
    ('wavefile', load_wavefile),
    ('ewave', load_ewave),
    ('scipy.io.wavfile', load_wavfile),
    ('audioread', load_audioread),
    )
"""List of implemented load() functions.

Each element of the list is a tuple with the module's name and its
load() function.

"""    


def load_audio(filepath, verbose=0):
    """Call this function to load all channels of audio data from a file.
    
    This function tries different python modules to load the audio file.

    Parameters
    ----------
    filepath: str
        The full path and name of the file to load.
    verbose: int
        If larger than zero show detailed error/warning messages.

    Returns
    -------
    data: ndarray
        All data traces as an 2-D ndarray, even for single channel data.
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

    Examples
    --------
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
        raise FileNotFoundError(f'file "{filepath}" not found')
    if os.path.getsize(filepath) <= 0:
        raise EOFError(f'file "{filepath}" is empty (size=0)!')

    # load an audio file by trying various modules:
    not_installed = []
    errors = [f'failed to load data from file "{filepath}":']
    for lib, load_file in audio_loader_funcs:
        if not audio_modules[lib]:
            if verbose > 1:
                print(f'unable to load data from file "{filepath}" using {lib} module: module not available')
            not_installed.append(lib)
            continue
        try:
            data, rate = load_file(filepath)
            if len(data) > 0:
                if verbose > 0:
                    print(f'loaded data from file "{filepath}" using {lib} module')
                    if verbose > 1:
                        print(f'  sampling rate: {rate:g} Hz')
                        print(f'  channels     : {data.shape[1]}')
                        print(f'  frames       : {len(data)}')
                return data, rate
        except Exception as e:
            errors.append(f'  {lib} failed: {str(e)}')
            if verbose > 1:
                print(errors[-1])
    if len(not_installed) > 0:
        errors.append('\n  You may need to install one of the ' + \
          ', '.join(not_installed) + ' packages.')
    raise IOError('\n'.join(errors))
    return np.zeros(0), 0.0


def metadata(filepath, store_empty=False):
    """Read metadata of an audio file.

    Parameters
    ----------
    filepath: str or file handle
        The audio file from which to read metadata.
    store_empty: bool
        If `False` do not return meta data with empty values.

    Returns
    -------
    meta_data: nested dict
        Meta data contained in the audio file.  Keys of the nested
        dictionaries are always strings.  If the corresponding values
        are dictionaries, then the key is the section name of the
        metadata contained in the dictionary. All other types of
        values are values for the respective key. In particular they
        are strings. But other types like for example ints or floats
        are also allowed.  See `audioio.audiometadata` module for
        available functions to work with such metadata.

    Examples
    --------
    ```
    from audioio import metadata, print_metadata
    md = metadata('data.wav')
    print_metadata(md)
    ```

    """
    try:
        return metadata_riff(filepath, store_empty)
    except ValueError: # not a RIFF file
        return {}


def markers(filepath):
    """ Read markers of an audio file.

    See `audioio.audiomarkers` module for available functions
    to work with markers.

    Parameters
    ----------
    filepath: str or file handle
        The audio file.

    Returns
    -------
    locs: 2-D ndarray of int
        Marker positions (first column) and spans (second column)
        for each marker (rows).
    labels: 2-D ndarray of string objects
        Labels (first column) and texts (second column)
        for each marker (rows).

    Examples
    --------
    ```
    from audioio import markers, print_markers
    locs, labels = markers('data.wav')
    print_markers(locs, labels)
    ```
    """
    try:
        return markers_riff(filepath)
    except ValueError: # not a RIFF file
        return np.zeros((0, 2), dtype=int), np.zeros((0, 2), dtype=object)

    
class AudioLoader(BufferedArray):
    """Buffered reading of audio data for random access of the data in the file.
    
    The class allows for reading very large audio files that do not
    fit into memory.
    An AudioLoader instance can be used like a huge read-only numpy array, i.e.
    ```
    data = AudioLoader('path/to/audio/file.wav')
    x = data[10000:20000,0]
    ```
    The first index specifies the frame, the second one the channel.

    Behind the scenes, `AudioLoader` tries to open the audio file with
    all available audio modules until it succeeds (first line). It
    then reads data from the file as necessary for the requested data
    (second line). Accesing the content of the audio files via a
    buffer that holds only a part of the data is managed by the
    `BufferedArray` class.

    Reading sequentially through the file is always possible. Some
    modules, however, (e.g. audioread, needed for mp3 files) can only
    read forward. If previous data are requested, then the file is read
    from the beginning again. This slows down access to previous data
    considerably. Use the `backsize` argument of the open function to
    make sure some data are loaded into the buffer before the requested
    frame. Then a subsequent access to the data within `backsize` seconds
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
            f, t, Sxx = spectrogram(x, fs=data.rate,
                                    nperseg=nfft, noverlap=nfft//2)
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

    Classes inheriting AudioLoader just need to implement
    ```
    self.load_audio_buffer(offset, nsamples, pbuffer)
    ```
    This function needs to load the supplied `pbuffer` with
    `nframes` frames of data starting at frame `offset`.

    In the constructor or some kind of opening function, you need to
    set some member variables, as described for `BufferedArray`.
    
    Parameters
    ----------
    filepath: str
        Name of the file.
    buffersize: float
        Size of internal buffer in seconds.
    backsize: float
        Part of the buffer to be loaded before the requested start index in seconds.
    verbose: int
        If larger than zero show detailed error/warning messages.
    store_empty: bool
        If `False` do not return meta data with empty values.

    Attributes
    ----------
    filepath: str
        Path and name of the file.
    rate: float
        The sampling rate of the data in seconds.
    channels: int
        The number of channels.
    frames: int
        The number of frames in the file. Same as `len()`.
    format: str or None
        Format of the audio file.
    encoding: str or None
        Encoding/subtype of the audio file.
    shape: tuple
        Frames and channels of the data.
    ndim: int
        Number of dimensions: always 2 (frames and channels).
    offset: int
        Index of first frame in the current buffer.
    buffer: ndarray of floats
        The curently available data from the file.
    ampl_min: float
        Minimum amplitude the file format supports.
        Always -1.0 for audio data.
    ampl_max: float
        Maximum amplitude the file format supports.
        Always +1.0 for audio data.

    Methods
    -------
    - `len()`: Number of frames.
    - `open()`: Open an audio file by trying available audio modules.
    - `open_*()`: Open an audio file with the respective audio module.
    - `__getitem__`: Access data of the audio file.
    - `update_buffer()`: Update the internal buffer for a range of frames.
    - `blocks()`: Generator for blockwise processing of AudioLoader data.
    - `format_dict()`: technical infos about how the data are stored.
    - `metadata()`: Metadata stored along with the audio data.
    - `markers()`: Markers stored along with the audio data.
    - `set_unwrap()`: Set parameters for unwrapping clipped data.
    - `close()`: Close the file.

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
    
    def __init__(self, filepath=None, buffersize=10.0, backsize=0.0,
                 verbose=0, **meta_kwargs):
        super().__init__(verbose)
        self.format = None
        self.encoding = None
        self._metadata = None
        self._locs = None
        self._labels = None
        self._load_metadata = metadata
        self._load_markers = markers
        self._metadata_kwargs = meta_kwargs
        self.filepath = None
        self.sf = None
        self.close = self._close
        self.load_buffer = self._load_buffer_unwrap
        self.ampl_min = -1.0
        self.ampl_max = +1.0
        self.unwrap = False
        self.unwrap_thresh = 0.0
        self.unwrap_clips = False
        self.unwrap_ampl = 1.0
        self.unwrap_downscale = True
        if filepath is not None:
            self.open(filepath, buffersize, backsize, verbose)
            
    numpy_encodings = {np.dtype(np.int64): 'PCM_64',
                       np.dtype(np.int32): 'PCM_32',
                       np.dtype(np.int16): 'PCM_16',
                       np.dtype(np.single): 'FLOAT',
                       np.dtype(np.double): 'DOUBLE',
                       np.dtype('>f4'): 'FLOAT',
                       np.dtype('>f8'): 'DOUBLE'}
    """ Map numpy dtypes to encodings.
    """

    def _close(self):
        pass

    def __del__(self):
        self.close()

    def format_dict(self):
        """ Technical infos about how the data are stored in the file.

        Returns
        -------
        fmt: dict
            Dictionary with filepath, format, encoding, samplingrate,
            channels, frames, and duration of the audio file as strings.

        """
        fmt = dict(filepath=self.filepath)
        if self.format is not None:
            fmt['format'] = self.format
        if self.encoding is not None:
            fmt['encoding'] = self.encoding
        fmt.update(dict(samplingrate=f'{self.rate:.0f}Hz',
                        channels=self.channels,
                        frames=self.frames,
                        duration=f'{self.frames/self.rate:.3f}s'))
        return fmt
        
    def metadata(self):
        """Metadata of the audio file.

        Parameters
        ----------
        store_empty: bool
            If `False` do not add meta data with empty values.

        Returns
        -------
        meta_data: nested dict

            Meta data contained in the audio file.  Keys of the nested
            dictionaries are always strings.  If the corresponding
            values are dictionaries, then the key is the section name
            of the metadata contained in the dictionary. All other
            types of values are values for the respective key. In
            particular they are strings. But other types like for
            example ints or floats are also allowed.  See
            `audioio.audiometadata` module for available functions to
            work with such metadata.

        """
        if self._metadata is None:
            if self._load_metadata is None:
                self._metadata = {}
            else:
                self._metadata = self._load_metadata(self.filepath,
                                                     **self._metadata_kwargs)
        return self._metadata

    def markers(self):
        """Read markers of the audio file.

        See `audioio.audiomarkers` module for available functions
        to work with markers.

        Returns
        -------
        locs: 2-D ndarray of int
            Marker positions (first column) and spans (second column)
            for each marker (rows).
        labels: 2-D ndarray of str objects
            Labels (first column) and texts (second column)
            for each marker (rows).
        """
        if self._locs is None:
            if self._load_markers is None:
                self._locs = np.zeros((0, 2), dtype=int)
                self._labels = np.zeros((0, 2), dtype=object)
            else:
                self._locs, self._labels = self._load_markers(self.filepath)
        return self._locs, self._labels 

    def set_unwrap(self, thresh, clips=False, down_scale=True, unit=''):
        """Set parameters for unwrapping clipped data.

        See unwrap() function from the audioio package.

        Parameters
        ----------
        thresh: float
            Threshold for detecting wrapped data relative to self.unwrap_ampl
            which is initially set to self.ampl_max.
            If zero, do not unwrap.
        clips: bool
            If True, then clip the unwrapped data properly.
            Otherwise, unwrap the data and double the
            minimum and maximum data range
            (self.ampl_min and self.ampl_max).
        down_scale: bool
            If not `clip`, then downscale the signal by a factor of two,
            in order to keep the range between -1 and 1.
        unit: str
            Unit of the data.
        """
        self.unwrap_ampl = self.ampl_max
        self.unwrap_thresh = thresh
        self.unwrap_clips = clips
        self.unwrap_down_scale = down_scale
        self.unwrap = thresh > 1e-3
        if self.unwrap:
            if self.unwrap_clips:
                add_unwrap(self.metadata(),
                           self.unwrap_thresh*self.unwrap_ampl,
                           self.unwrap_ampl, unit)
            elif down_scale:
                update_gain(self.metadata(), 0.5)
                add_unwrap(self.metadata(),
                           0.5*self.unwrap_thresh*self.unwrap_ampl,
                           0.0, unit)
            else:
                self.ampl_min *= 2
                self.ampl_max *= 2
                add_unwrap(self.metadata(),
                           self.unwrap_thresh*self.unwrap_ampl,
                           0.0, unit)

    def _load_buffer_unwrap(self, r_offset, r_size, pbuffer):
        """Load new data and unwrap it.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        pbuffer: ndarray
           Buffer where to store the loaded data.
        """
        self.load_audio_buffer(r_offset, r_size, pbuffer)
        if self.unwrap:
            # TODO: handle edge effects!
            unwrap(pbuffer, self.unwrap_thresh, self.unwrap_ampl)
            if self.unwrap_clips:
                pbuffer[pbuffer > self.ampl_max] = self.ampl_max
                pbuffer[pbuffer < self.ampl_min] = self.ampl_min
            elif self.unwrap_down_scale:
                pbuffer *= 0.5
                
                
    # wave interface:        
    def open_wave(self, filepath, buffersize=10.0, backsize=0.0,
                  verbose=0):
        """Open audio file for reading using the wave module.

        Note: we assume that setpos() and tell() use integer numbers!

        Parameters
        ----------
        filepath: str
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If larger than zero show detailed error/warning messages.

        Raises
        ------
        ImportError
            The wave module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print(f'open_wave(filepath) with filepath={filepath}')
        if not audio_modules['wave']:
            self.rate = 0.0
            self.channels = 0
            self.frames = 0
            self.size = 0
            self.shape = (0, 0)
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_wave()
        self.sf = wave.open(filepath, 'r')
        self.filepath = filepath
        self.rate = float(self.sf.getframerate())
        self.format = 'WAV'
        sampwidth = self.sf.getsampwidth()
        if sampwidth == 1:
            self.dtype = 'u1'
            self.encoding = 'PCM_U8'
        else:
            self.dtype = f'i{sampwidth}' 
            self.encoding = f'PCM_{sampwidth*8}'
        self.factor = 1.0/(2.0**(sampwidth*8-1))
        self.channels = self.sf.getnchannels()
        self.frames = self.sf.getnframes()
        self.shape = (self.frames, self.channels)
        self.size = self.frames * self.channels
        self.bufferframes = int(buffersize*self.rate)
        self.backframes = int(backsize*self.rate)
        self.init_buffer()
        self.close = self._close_wave
        self.load_audio_buffer = self._load_buffer_wave
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

    def _load_buffer_wave(self, r_offset, r_size, buffer):
        """Load new data from file using the wave module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        buffer: ndarray
           Buffer where to store the loaded data.
        """
        self.sf.setpos(r_offset*self.pfac + self.p0)
        fbuffer = self.sf.readframes(r_size)
        fbuffer = np.frombuffer(fbuffer, dtype=self.dtype).reshape((-1, self.channels))
        if self.dtype[0] == 'u':
            buffer[:, :] = fbuffer * self.factor - 1.0
        else:
            buffer[:, :] = fbuffer * self.factor


    # ewave interface:        
    def open_ewave(self, filepath, buffersize=10.0, backsize=0.0,
                   verbose=0):
        """Open audio file for reading using the ewave module.

        Parameters
        ----------
        filepath: str
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If larger than zero show detailed error/warning messages.

        Raises
        ------
        ImportError
            The ewave module is not installed.
        """
        self.verbose = verbose
        if self.verbose > 0:
            print(f'open_ewave(filepath) with filepath={filepath}')
        if not audio_modules['ewave']:
            self.rate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.size = 0
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_ewave()
        self.sf = ewave.open(filepath, 'r')
        self.filepath = filepath
        self.rate = float(self.sf.sampling_rate)
        self.channels = self.sf.nchannels
        self.frames = self.sf.nframes
        self.shape = (self.frames, self.channels)
        self.size = self.frames * self.channels
        self.format = 'WAV' # or WAVEX?
        self.encoding = self.numpy_encodings[self.sf.dtype]
        self.bufferframes = int(buffersize*self.rate)
        self.backframes = int(backsize*self.rate)
        self.init_buffer()
        self.close = self._close_ewave
        self.load_audio_buffer = self._load_buffer_ewave
        return self

    def _close_ewave(self):
        """Close the audio file using the ewave module. """
        if self.sf is not None:
            del self.sf
            self.sf = None

    def _load_buffer_ewave(self, r_offset, r_size, buffer):
        """Load new data from file using the ewave module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        buffer: ndarray
           Buffer where to store the loaded data.
        """
        fbuffer = self.sf.read(frames=r_size, offset=r_offset, memmap='r')
        fbuffer = ewave.rescale(fbuffer, 'float')
        if len(fbuffer.shape) == 1:
            fbuffer = np.reshape(fbuffer,(-1, 1))
        buffer[:,:] = fbuffer

        
    # soundfile interface:        
    def open_soundfile(self, filepath, buffersize=10.0, backsize=0.0,
                       verbose=0):
        """Open audio file for reading using the SoundFile module.

        Parameters
        ----------
        filepath: str
            Name of the file.
        bufferframes: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If larger than zero show detailed error/warning messages.

        Raises
        ------
        ImportError
            The SoundFile module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print(f'open_soundfile(filepath) with filepath={filepath}')
        if not audio_modules['soundfile']:
            self.rate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.size = 0
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_soundfile()
        self.sf = soundfile.SoundFile(filepath, 'r')
        self.filepath = filepath
        self.rate = float(self.sf.samplerate)
        self.channels = self.sf.channels
        self.frames = 0
        self.size = 0
        if self.sf.seekable():
            self.frames = self.sf.seek(0, soundfile.SEEK_END)
            self.sf.seek(0, soundfile.SEEK_SET)
        # TODO: if not seekable, we cannot handle that file!
        self.shape = (self.frames, self.channels)
        self.size = self.frames * self.channels
        self.format = self.sf.format
        self.encoding = self.sf.subtype
        self.bufferframes = int(buffersize*self.rate)
        self.backframes = int(backsize*self.rate)
        self.init_buffer()
        self.close = self._close_soundfile
        self.load_audio_buffer = self._load_buffer_soundfile
        return self

    def _close_soundfile(self):
        """Close the audio file using the SoundFile module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _load_buffer_soundfile(self, r_offset, r_size, buffer):
        """Load new data from file using the SoundFile module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        buffer: ndarray
           Buffer where to store the loaded data.
        """
        self.sf.seek(r_offset, soundfile.SEEK_SET)
        buffer[:, :] = self.sf.read(r_size, always_2d=True)

        
    # wavefile interface:        
    def open_wavefile(self, filepath, buffersize=10.0, backsize=0.0,
                      verbose=0):
        """Open audio file for reading using the wavefile module.

        Parameters
        ----------
        filepath: str
            Name of the file.
        bufferframes: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If larger than zero show detailed error/warning messages.

        Raises
        ------
        ImportError
            The wavefile module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print(f'open_wavefile(filepath) with filepath={filepath}')
        if not audio_modules['wavefile']:
            self.rate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.size = 0
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_wavefile()
        self.sf = wavefile.WaveReader(filepath)
        self.filepath = filepath
        self.rate = float(self.sf.samplerate)
        self.channels = self.sf.channels
        self.frames = self.sf.frames
        self.shape = (self.frames, self.channels)
        self.size = self.frames * self.channels
        # get format and encoding:
        for attr in dir(wavefile.Format):
            v = getattr(wavefile.Format, attr)
            if isinstance(v, int):
                if v & wavefile.Format.TYPEMASK > 0 and \
                   (self.sf.format & wavefile.Format.TYPEMASK) == v:
                    self.format = attr
                if v & wavefile.Format.SUBMASK > 0 and \
                   (self.sf.format & wavefile.Format.SUBMASK) == v:
                    self.encoding = attr
        # init buffer:
        self.bufferframes = int(buffersize*self.rate)
        self.backframes = int(backsize*self.rate)
        self.init_buffer()
        self.close = self._close_wavefile
        self.load_audio_buffer = self._load_buffer_wavefile
        return self

    def _close_wavefile(self):
        """Close the audio file using the wavefile module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _load_buffer_wavefile(self, r_offset, r_size, buffer):
        """Load new data from file using the wavefile module.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        buffer: ndarray
           Buffer where to store the loaded data.
        """
        self.sf.seek(r_offset, wavefile.Seek.SET)
        fbuffer = self.sf.buffer(r_size, dtype=self.buffer.dtype)
        self.sf.read(fbuffer)
        buffer[:,:] = fbuffer.T

            
    # audioread interface:        
    def open_audioread(self, filepath, buffersize=10.0, backsize=0.0,
                       verbose=0):
        """Open audio file for reading using the audioread module.

        Note, that audioread can only read forward, therefore random and
        backward access is really slow.

        Parameters
        ----------
        filepath: str
            Name of the file.
        bufferframes: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If larger than zero show detailed error/warning messages.

        Raises
        ------
        ImportError
            The audioread module is not installed
        """
        self.verbose = verbose
        if self.verbose > 0:
            print(f'open_audioread(filepath) with filepath={filepath}')
        if not audio_modules['audioread']:
            self.rate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.size = 0
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_audioread()
        self.sf = audioread.audio_open(filepath)
        self.filepath = filepath
        self.rate = float(self.sf.samplerate)
        self.channels = self.sf.channels
        self.frames = int(np.ceil(self.rate*self.sf.duration))
        self.shape = (self.frames, self.channels)
        self.size = self.frames * self.channels
        self.bufferframes = int(buffersize*self.rate)
        self.backframes = int(backsize*self.rate)
        self.init_buffer()
        self.read_buffer = np.zeros((0,0))
        self.read_offset = 0
        self.close = self._close_audioread
        self.load_audio_buffer = self._load_buffer_audioread
        self.filepath = filepath
        self.sf_iter = self.sf.__iter__()
        return self

    def _close_audioread(self):
        """Close the audio file using the audioread module. """
        if self.sf is not None:
            self.sf.__exit__(None, None, None)
            self.sf = None

    def _load_buffer_audioread(self, r_offset, r_size, buffer):
        """Load new data from file using the audioread module.

        audioread can only iterate through a file once and in blocksizes that are
        given by audioread. Therefore we keep yet another buffer: `self.read_buffer`
        at file offset `self.read_offset` containing whatever audioread returned.

        Parameters
        ----------
        r_offset: int
           First frame to be read from file.
        r_size: int
           Number of frames to be read from file.
        buffer: ndarray
           Buffer where to store the loaded data.
        """
        b_offset = 0
        if ( self.read_offset + self.read_buffer.shape[0] >= r_offset + r_size
             and self.read_offset < r_offset + r_size ):
            # read_buffer overlaps at the end of the requested interval:
            i = 0
            n = r_offset + r_size - self.read_offset
            if n > r_size:
                i += n - r_size
                n = r_size
            buffer[self.read_offset+i-r_offset:self.read_offset+i+n-r_offset,:] = self.read_buffer[i:i+n,:] / (2.0**15-1.0)
            if self.verbose > 2:
                print(f'  recycle {n:6d} frames from the front of the read buffer at {self.read_offset}-{self.read_offset+n} ({self.read_offset-self.offset}-{self.read_offset-self.offset+n} in buffer)')
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
                    fbuffer = self.sf_iter.next()
                else:
                    fbuffer = next(self.sf_iter)
            except StopIteration:
                self.read_buffer = np.zeros((0,0))
                buffer[:,:] = 0.0
                if self.verbose > 1:
                    print(f'  caught StopIteration, padded buffer with {r_size} zeros')
                break
            self.read_buffer = np.frombuffer(fbuffer, dtype='<i2').reshape(-1, self.channels)
            if self.verbose > 2:
                print(f'  read forward by {self.read_buffer.shape[0]} frames')
        # recycle file data:
        if ( self.read_offset + self.read_buffer.shape[0] > r_offset
             and self.read_offset <= r_offset ):
            i = r_offset - self.read_offset
            n = self.read_offset + self.read_buffer.shape[0] - r_offset
            if n > r_size:
                n = r_size
            buffer[:n,:] = self.read_buffer[i:i+n,:] / (2.0**15-1.0)
            if self.verbose > 2:
                print(f'  recycle {n:6d} frames from the end of the read buffer at {self.read_offset}-{self.read_offset + self.read_buffer.shape[0]} to {r_offset}-{r_offset+n} ({r_offset-self.offset}-{r_offset+n-self.offset} in buffer)')
            b_offset += n
            r_offset += n
            r_size -= n
        # read data:
        if self.verbose > 2 and r_size > 0:
            print(f'  read    {r_size:6d} frames at {r_offset}-{r_offset+r_size} ({r_offset-self.offset}-{r_offset+r_size-self.offset} in buffer)')
        while r_size > 0:
            self.read_offset += self.read_buffer.shape[0]
            try:
                if hasattr(self.sf_iter, 'next'):
                    fbuffer = self.sf_iter.next()
                else:
                    fbuffer = next(self.sf_iter)
            except StopIteration:
                self.read_buffer = np.zeros((0,0))
                buffer[b_offset:,:] = 0.0
                if self.verbose > 1:
                    print(f'  caught StopIteration, padded buffer with {r_size} zeros')
                break
            self.read_buffer = np.frombuffer(fbuffer, dtype='<i2').reshape(-1, self.channels)
            n = self.read_buffer.shape[0]
            if n > r_size:
                n = r_size
            if n > 0:
                buffer[b_offset:b_offset+n,:] = self.read_buffer[:n,:] / (2.0**15-1.0)
                if self.verbose > 2:
                    print(f'    read  {n:6d} frames to {r_offset}-{r_offset+n} ({r_offset-self.offset}-{r_offset+n-self.offset} in buffer)')
                b_offset += n
                r_offset += n
                r_size -= n

                                
    def open(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading.

        Parameters
        ----------
        filepath: str
            Name of the file.
        buffersize: float
            Size of internal buffer in seconds.
        backsize: float
            Part of the buffer to be loaded before the requested start index in seconds.
        verbose: int
            If larger than zero show detailed error/warning messages.

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
        self.rate = 0.0
        if not filepath:
            raise ValueError('input argument filepath is empty string!')
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f'file "{filepath}" not found')
        if os.path.getsize(filepath) <= 0:
            raise EOFError(f'file "{filepath}" is empty (size=0)!')
        # list of implemented open functions:
        audio_open_funcs = (
            ('soundfile', self.open_soundfile),
            ('wave', self.open_wave),
            ('wavefile', self.open_wavefile),
            ('ewave', self.open_ewave),
            ('audioread', self.open_audioread),
            )
        # open an audio file by trying various modules:
        not_installed = []
        errors = [f'failed to load data from file "{filepath}":']
        for lib, open_file in audio_open_funcs:
            if not audio_modules[lib]:
                if verbose > 1:
                    print(f'unable to load data from file "{filepath}" using {lib} module: module not available')
                not_installed.append(lib)
                continue
            try:
                open_file(filepath, buffersize, backsize, verbose-1)
                if self.frames > 0:
                    if verbose > 0:
                        print(f'opened audio file "{filepath}" using {lib}')
                        if verbose > 1:
                            if self.format is not None:
                                print(f'  format       : {self.format}')
                            if self.encoding is not None:
                                print(f'  encoding     : {self.encoding}')
                            print(f'  sampling rate: {self.rate} Hz')
                            print(f'  channels     : {self.channels}')
                            print(f'  frames       : {self.frames}')
                    return self
            except Exception as e:
                errors.append(f'  {lib} failed: {str(e)}')
                if verbose > 1:
                    print(errors[-1])
        if len(not_installed) > 0:
            errors.append('\n  You may need to install one of the ' + \
              ', '.join(not_installed) + ' packages.')
        raise IOError('\n'.join(errors))
        return self

    
def demo(file_path, plot):
    """Demo of the audioloader functions.

    Parameters
    ----------
    file_path: str
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
        print(f"rms difference is {np.std(data1[:n]-data2[:n])}")
        if plot:
            plt.plot(np.arange(len(data1))/rate1, data1[:,0])
            plt.plot(np.arange(len(data2))/rate2, data2[:,0])
            plt.show()
    
    print('')
    print("try AudioLoader:")
    with AudioLoader(file_path, 4.0, 1.0, verbose=1) as data:
        print(f'samplerate: {data.rate:0f}Hz')
        print(f'channels: {data.channels} {data.shape[1]}')
        print(f'frames: {len(data)} {data.shape[0]}')
        nframes = int(1.5*data.rate)
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
            print(f'forward {i}-{i+nframes}')
            x = data[i:i+nframes,0]
            if plot:
                plt.plot((i+np.arange(len(x)))/rate, x)
                plt.show()
        # and backwards:
        for i in reversed(range(0, len(data), nframes)):
            print(f'backward {i}-{i+nframes}')
            x = data[i:i+nframes,0]
            if plot:
                plt.plot((i+np.arange(len(x)))/rate, x)
                plt.show()


def main(*args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of str
        Command line arguments as provided by sys.argv[1:]
    """
    print("Checking audioloader module ...")

    help = False
    plot = False
    file_path = None
    mod = False
    for arg in args:
        if mod:
            if not select_module(arg):
                print(f'can not select module {arg} that is not installed')
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
        print('  python -m src.audioio.audioloader [-m <module>] [-p] <audio/file.wav>')
        print('  -m: audio module to be used')
        print('  -p: plot loaded data')
        return

    if plot:
        import matplotlib.pyplot as plt

    demo(file_path, plot)


if __name__ == "__main__":
    main(*sys.argv[1:])

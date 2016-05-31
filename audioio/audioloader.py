"""
Functions for loading data from audio files.

data, samplingrate = load_audio('audio/file.wav')
Loads the whole file by trying different modules until it succeeds to load the data.

data = AudioLoader('audio/file.wav', 60.0)
or
with open_audio('audio/file.wav', 60.0) as data:
Create an AudioLoader object that loads chuncks of 60 seconds long data on demand.
data can be used like a read-only numpy array.

list_modules() and available_modules() let you query which audio modules
are installed and available.
For further information and installing instructions of missing modules,
see the documentation of the respective load_*() functions.

For an overview on available python modules see
http://nbviewer.jupyter.org/github/mgeier/python-audio/blob/master/audio-files/index.ipynb
"""
 
import warnings
import os.path
import numpy as np


# probe for available audio modules:
audio_modules = {}

try:
    import wave
    audio_modules['wave'] = True
except ImportError:
    audio_modules['wave'] = False

try:
    import ewave
    audio_modules['ewave'] = True
except ImportError:
    audio_modules['ewave'] = False

try:
    from scipy.io import wavfile
    audio_modules['scipy.io.wavfile'] = True
except ImportError:
    audio_modules['scipy.io.wavfile'] = False

try:
    import soundfile
    audio_modules['soundfile'] = True
except ImportError:
    audio_modules['soundfile'] = False

try:
    import wavefile
    audio_modules['wavefile'] = True
except ImportError:
    audio_modules['wavefile'] = False

try:
    import scikits.audiolab as audiolab
    audio_modules['scikits.audiolab'] = True
except ImportError:
    audio_modules['scikits.audiolab'] = False
        
try:
    import audioread
    audio_modules['audioread'] = True
except ImportError:
    audio_modules['audioread'] = False


def available_modules():
    """Returns:
         mods (list): list of installed audio modules.
    """
    mods = []
    for module, available in audio_modules.items():
        if available:
            mods.append(module)
    return mods


def list_modules():
    """Print list of all modules the audioloader module is able to use
    and whether they are installed or not.
    """
    for module, available in audio_modules.items():
        if available:
            print('%-16s is     installed' % module)
        else:
            print('%-16s is not installed' % module)


def load_wave(filepath, verbose=0):
    """
    Load wav file using the wave module from pythons standard libray.
    
    Documentation:
        https://docs.python.org/2/library/wave.html

    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages
                       if 2 print information about soundfile

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz

    Exceptions:
        ImportError: if the wave module is not installed
        *: if loading of the data failed
    """
    if not audio_modules['wave']:
        raise ImportError

    wf = wave.open(filepath, 'r')   # 'with' is not supported by wave
    (nchannels, sampwidth, rate, nframes, comptype, compname) = wf.getparams()
    if verbose > 1:
        print('channels       : %d' % nchannels)
        print('bytes          : %d' % sampwidth)
        print('sampling rate  : %g' % rate)
        print('frames         : %d' % nframes)
        print('compression type: %s' % comptype)
        print('compression name: %s' % compname)
    buffer = wf.readframes(nframes)
    format = 'i%d' % sampwidth
    data = np.fromstring(buffer, dtype=format).reshape(-1, nchannels)  # read data
    wf.close()
    data /= 2.0**(sampwidth*8-1)
    if len(data.shape) == 1:
        data = np.reshape(data,(-1, 1))
    return data, float(rate)

    
def load_ewave(filepath, verbose=0):
    """
    Load wav file using ewave module.

    Documentation:
        https://github.com/melizalab/py-ewave
        
    Installation:
        git clone https://github.com/melizalab/py-ewave
        python setup.py build
        sudo python setup.py install

    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages (not used)

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz

    Exceptions:
        ImportError: if the ewave module is not installed
        *: if loading of the data failed
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
    """
    Load wav file using scipy.io.wavfile.

    Documentation:
        http://docs.scipy.org/doc/scipy/reference/io.html
        Does not support blocked read.
    
    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz

    Exceptions:
        ImportError: if the scipy.io module is not installed
        *: if loading of the data failed
    """
    if not audio_modules['scipy.io.wavfile']:
        raise ImportError

    if verbose < 2:
        warnings.filterwarnings("ignore")
    rate, data = wavfile.read(filepath)
    if verbose < 2:
        warnings.filterwarnings("always")
    data = data / 2.0**15
    if len(data.shape) == 1:
        data = np.reshape(data,(-1, 1))
    return data, float(rate)
        

def load_soundfile(filepath, verbose=0):
    """
    Load audio file using pysoundfile (based on libsndfile).

    Documentation:
        http://pysoundfile.readthedocs.org
        http://www.mega-nerd.com/libsndfile
        
    Installation:
        sudo apt-get install libsndfile1 libsndfile1-dev libffi-dev
        sudo pip install pysoundfile

    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages (not used)

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz

    Exceptions:
        ImportError: if the soundfile module is not installed
        *: if loading of the data failed
    """
    if not audio_modules['soundfile']:
        raise ImportError

    data = np.array([])
    rate = 0.0
    with soundfile.SoundFile(filepath, 'r') as sf:
        rate = sf.samplerate
        data = sf.read(always_2d=True)
    return data, float(rate)


def load_wavefile(filepath, verbose=0):
    """
    Load audio file using wavefile (based on libsndfile).

    Documentation:
        https://github.com/vokimon/python-wavefile

    Installation:
        sudo apt-get install libsndfile1
        sudo pip install wavefile

    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages (not used)

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz

    Exceptions:
        ImportError: if the wavefile module is not installed
        *: if loading of the data failed
    """
    if not audio_modules['wavefile']:
        raise ImportError

    rate, data = wavefile.load(filepath)
    return data.T, float(rate)


def load_audiolab(filepath, verbose=0):
    """
    Load audio file using scikits.audiolab (based on libsndfile).

    Documentation:
        http://cournape.github.io/audiolab/
        https://github.com/cournape/audiolab
                
    Installation:
        sudo apt-get install libsndfile1
        sudo pip install scikits.audiolab

    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages (not used)

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz

    Exceptions:
        ImportError: if the scikits.audiolab module is not installed
        *: if loading of the data failed
    """
    if not audio_modules['scikits.audiolab']:
        raise ImportError

    af = audiolab.Sndfile(filepath, 'r')
    rate = af.samplerate
    data = af.read_frames(af.nframes)
    if len(data.shape) == 1:
        data = np.reshape(data,(-1, 1))
    return data, float(rate)


def load_audioread(filepath, verbose=0):
    """
    Load audio file using audioread.

    Documentation:
        https://github.com/sampsyo/audioread

    Installation:
        sudo apt-get install libav-tools python-audioread
        
    audioread is not available in python x,y.

    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages (not used)

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz

    Exceptions:
        ImportError: if the audioread module is not installed
        *: if loading of the data failed
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
            fulldata = np.fromstring(buffer, dtype='<i2').reshape(-1, af.channels)
            n = fulldata.shape[0]
            if index+n > len(data):
                n = len(data) - index
            if n > 0:
                data[index:index+n,:] = fulldata[:n,:]
                index += n
            else:
                break
    return data/2.0**15, float(rate)


# list of implemented load functions:
audio_loader = [
    ['soundfile', load_soundfile],
    ['audioread', load_audioread],
    ['wave', load_wave],
    ['wavefile', load_wavefile],
    ['scikits.audiolab', load_audiolab],
    ['ewave', load_ewave],
    ['scipy.io.wavfile', load_wavfile]
    ]

def load_audio(filepath, verbose=0):
    """
    Call this function to load all channels of audio data from a file.
    This function tries different python modules to load the audio file.

    Args:
        filepath (string): the full path and name of the file to load
        verbose (int): if >0 show detailed error/warning messages

    Returns:
        data (array): all data traces as an 2-D numpy array,
                      first dimension is time, second is channel
        rate (float): the sampling rate of the data in Hz
    """
    # check values:
    rate = 0.0
    data = np.zeros((0, 0))
    if len(filepath) == 0:
        warnings.warn('input argument filepath is empty string!')
        return data, rate
    if not os.path.isfile(filepath):
        warnings.warn('input argument filepath=%s does not indicate an existing file!' % filepath)
        return data, rate
    if os.path.getsize(filepath) <= 0:
        warnings.warn('load_audio(): input argument filepath=%s indicates file of size 0!' % filepath)
        return data, rate

    # load an audio file by trying various modules:
    for lib, load_file in audio_loader:
        if not audio_modules[lib]:
            continue
        try:
            data, rate = load_file(filepath, verbose)
            if len(data) > 0:
                if verbose > 0:
                    print('loaded data from file "%s" using %s:' %
                          (filepath, lib))
                    print('  sampling rate: %g Hz' % rate)
                    print('  data values : %d' % len(data))
                break
        except:
            warnings.warn('failed to load data from file "%s" with %s' % (filepath, lib))
    return data, rate


class AudioLoader(object):
    """Buffered reading of audio data for random access of the data in the file.
    This allows for reading very large audio files that  do not fit into memory.
    An AudioLoader instance can be used like a huge read-only numpy array, i.e.

        data = AudioLoader('path/to/audio/file.wav')
        x = data[10000:20000,0]

    The first index specifies the frame, the second one the channel.

    Behind the scenes AudioLoader tries to open the audio file with all available
    audio modules until it succeeds (first line). It then reads data from the file
    as necessary for the requested data (second line).

    Reading sequentially through the file is always possible. Some modules, however,
    (e.g. audioread, needed for mp3 files) can only read forward. If previous data
    are requested, then the file is read from the beginning. This slows down access
    to previous data considerably. Use the backsize argument to the open functions to
    make sure some data are loaded before the requested frame. Then a subsequent access
    to the data within backsize seconds before that frame can still be handled without
    the need to reread the file from the beginning.

    Usage:

        import audioloader as al
        with al.open_audio(filepath, 60.0, 10.0) as data:
            # do something with the content of the file:
            x = data[0:10000]
            y = data[10000:20000]
            z = x + y

    For using a specific module:
    
        data = al.AudioLoader()
        with data.open_audioread(filepath, 60.0, 10.0):
            # do something ...

    Normal open and close:

        data = al.AudioLoader(filepath, 60.0)
        x = data[:,:]  # read the whole file
        data.close()
        
    that is the same as:

        data = al.AudioLoader()
        data.open(filepath, 60.0)

    or for a specific module:

        data = al.AudioLoader()
        data.open_soundfile(filepath, 60.0)

    See output of
    
        al.list_modules()

    for supported and available modules.
    

    Member variables:
      samplerate (float): the sampling rate of the data in seconds.
      channels (int): the number of channels.
      frames (int): the number of frames in the file.
      shape (tuple): frames and channels of the data.

    Some member functions:
      len(): the number of frames
      open(): open an audio file by trying available audio modules.
      open_*(): open an audio file with the respective audio module.
      close(): close the file.
    """
    
    def __init__(self, filepath=None, buffersize=10.0, backsize=0.0, verbose=0):
        """Initialize the AudioLoader instance. If filepath is not None open the file.

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
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
        
    def __exit__(self, type, value, tb):
        self.__del__()
        return value
        
    def __len__(self):
        return self.frames

    def __getitem__(self, key):
        if hasattr(key, '__len__'):
            index = key[0]
        else:
            index = key
        if isinstance(index, slice):
            start = index.start
            stop = index.stop
            step = index.step
            if start is None:
                start=0
            if start < 0:
                start += len(self)
            if stop is None:
                stop = len(self)
            if stop < 0:
                stop += len(self)
            if stop > self.frames:
                stop = self.frames
            if step is None:
                step = 1
            self._update_buffer(start, stop)
            newindex = slice(start-self.offset, stop-self.offset, step)
        else:
            if index > self.frames:
                raise IndexError
            self._update_buffer(index, index+1)
            newindex = index-self.offset
        if hasattr(key, '__len__'):
            newkey = (newindex,) + key[1:]
            return self.buffer[newkey]
        else:
            return self.buffer[newindex]
        return 0

    def _read_indices(self, start, stop):
        """ Compute position and size for next read from file. """ 
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
        if self.verbose > 1:
            print('  request %6d frames at %d-%d' % (size, offset, offset+size))
        return offset, size

    def _init_buffer(self):
        """Allocate a buffer of size zero."""
        self.buffer = np.empty((0, self.channels))

    def _allocate_buffer(self, size):
        """Make sure the buffer has the right size."""
        if size != self.buffer.shape[0]:
            self.buffer = np.empty((size, self.channels))

    def _recycle_buffer(self, offset, size):
        """Move already existing parts of the buffer to their new position (as
        returned by _read_indices() ) and return position and size of
        data chunk that still needs to be loaded from file.
        """
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
            self._allocate_buffer(size)
            self.buffer[:n,:] = buffer
            r_offset += n
            r_size -= n
            if self.verbose > 1:
                print('  recycle %6d frames from %d-%d of the old %d-sized buffer to the front at %d-%d (%d-%d in buffer)'
                       % (n, self.offset+m-i, self.offset+m-i+n, m, offset, offset+n, 0, n))
        elif ( offset + size > self.offset and
            offset + size <= self.offset + self.buffer.shape[0] ):
            n = offset + size - self.offset
            m = self.buffer.shape[0]
            buffer = self.buffer[:n,:]
            self._allocate_buffer(size)
            buffer[-n:,:] = buffer
            r_size -= n
            if self.verbose > 1:
                print('  recycle %6d frames from %d-%d of the old %d-sized buffer to the end at %d-%d (%d-%d in buffer)'
                       % (n, self.offset, self.offset+n, m, offset+size-n, offset+size, size-n, size))
        else:
            self._allocate_buffer(size)
        return r_offset, r_size

    
    # wave interface:        
    def open_wave(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the wave module.

        Note: we assume that setpos() and tell() use integer numbers!

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
        self.verbose = verbose
        if self.verbose > 1:
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
        self.samplerate = self.sf.getframerate()
        self.format = 'i%d' % self.sf.getsampwidth()
        self.factor = 1.0/2.0**(self.sf.getsampwidth()*8-1)
        self.channels = self.sf.getnchannels()
        self.frames = self.sf.getnframes()
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_wave
        self._update_buffer = self._update_buffer_wave
        # read 1 frame to determine the unit of the position values:
        self.p0 = self.sf.tell()
        self.sf.readframes(1)
        self.pfac = self.sf.tell() - self.p0
        self.sf.setpos(self.p0)
        return self

    def _close_wave(self):
        """ Close the audio file using the wave module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _update_buffer_wave(self, start, stop):
        """Make sure that the buffer contains the data between
        start and stop using the wave module.
        """
        if start < self.offset or stop > self.offset + self.buffer.shape[0]:
            offset, size = self._read_indices(start, stop)
            r_offset, r_size = self._recycle_buffer(offset, size)
            # read buffer:
            self.sf.setpos(r_offset*self.pfac + self.p0)
            buffer = self.sf.readframes(r_size)
            buffer = np.fromstring(buffer, dtype=self.format).reshape((-1, self.channels))
            self.buffer[r_offset-offset:r_offset+r_size-offset,:] = buffer * self.factor
            self.offset = offset
            if self.verbose > 1:
                print('  read %6d frames at %d' % (r_size, r_offset))
            if self.verbose > 0:
                print('  loaded %d frames from %d up to %d'
                      % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))
        

    # ewave interface:        
    def open_ewave(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the ewave module.

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
        self.verbose = verbose
        if self.verbose > 1:
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
        self.samplerate = self.sf.sampling_rate
        self.channels = self.sf.nchannels
        self.frames = self.sf.nframes
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_ewave
        self._update_buffer = self._update_buffer_ewave
        return self

    def _close_ewave(self):
        """ Close the audio file using the ewave module. """
        if self.sf is not None:
            del self.sf
            self.sf = None

    def _update_buffer_ewave(self, start, stop):
        """Make sure that the buffer contains the data between
        start and stop using the ewave module.
        """
        if start < self.offset or stop > self.offset + self.buffer.shape[0]:
            offset, size = self._read_indices(start, stop)
            r_offset, r_size = self._recycle_buffer(offset, size)
            # read buffer:
            buffer = self.sf.read(frames=r_size, offset=r_offset, memmap='r')
            buffer = ewave.rescale(buffer, 'float')
            if len(buffer.shape) == 1:
                buffer = np.reshape(buffer,(-1, 1))
            self.buffer[r_offset-offset:r_offset+r_size-offset,:] = buffer
            self.offset = offset
            if self.verbose > 0:
                print('  loaded %d frames from %d up to %d'
                      % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

            
    # pysoundfile interface:        
    def open_soundfile(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the pysoundfile module.

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
        self.verbose = verbose
        if self.verbose > 1:
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
        self.samplerate = self.sf.samplerate
        self.channels = self.sf.channels
        self.frames = 0
        if self.sf.seekable():
            self.frames = self.sf.seek(0, soundfile.SEEK_END)
            self.sf.seek(0, soundfile.SEEK_SET)
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_soundfile
        self._update_buffer = self._update_buffer_soundfile
        return self

    def _close_soundfile(self):
        """ Close the audio file using the pysoundfile module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _update_buffer_soundfile(self, start, stop):
        """Make sure that the buffer contains the data between
        start and stop using the pysoundfile module.
        """
        if start < self.offset or stop > self.offset + self.buffer.shape[0]:
            offset, size = self._read_indices(start, stop)
            r_offset, r_size = self._recycle_buffer(offset, size)
            self.sf.seek(r_offset, soundfile.SEEK_SET)
            self.buffer[r_offset-offset:r_offset+r_size-offset,:] = self.sf.read(r_size, always_2d=True)
            self.offset = offset
            if self.verbose > 0:
                print('  loaded %d frames from %d up to %d'
                      % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

            
    # wavefile interface:        
    def open_wavefile(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the wavefile module.

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
        self.verbose = verbose
        if self.verbose > 1:
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
        self.samplerate = self.sf.samplerate
        self.channels = self.sf.channels
        self.frames = self.sf.frames
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_wavefile
        self._update_buffer = self._update_buffer_wavefile
        return self

    def _close_wavefile(self):
        """ Close the audio file using the wavefile module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _update_buffer_wavefile(self, start, stop):
        """Make sure that the buffer contains the data between
        start and stop using the wavefile module.
        """
        if start < self.offset or stop > self.offset + self.buffer.shape[0]:
            offset, size = self._read_indices(start, stop)
            r_offset, r_size = self._recycle_buffer(offset, size)
            self.sf.seek(r_offset, wavefile.Seek.SET)
            buffer = self.sf.buffer(r_size, dtype=self.buffer.dtype)
            self.sf.read(buffer)
            self.buffer[r_offset-offset:r_offset+r_size-offset,:] = buffer.T
            self.offset = offset
            if self.verbose > 0:
                print('  loaded %d frames from %d up to %d'
                      % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

            
    # scikits.audiolab interface:        
    def open_audiolab(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the scikits.audiolab module.

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
        self.verbose = verbose
        if self.verbose > 1:
            print('open_audiolab(filepath) with filepath=%s' % filepath)
        if not audio_modules['scikits.audiolab']:
            self.samplerate = 0.0
            self.channels = 0
            self.frames = 0
            self.shape = (0, 0)
            self.offset = 0
            raise ImportError
        if self.sf is not None:
            self._close_audiolab()
        self.sf = audiolab.Sndfile(filepath, 'r')
        self.samplerate = self.sf.samplerate
        self.channels = self.sf.channels
        self.frames = int(self.sf.nframes)
        self.shape = (self.frames, self.channels)
        self.buffersize = int(buffersize*self.samplerate)
        self.backsize = int(backsize*self.samplerate)
        self._init_buffer()
        self.offset = 0
        self.close = self._close_audiolab
        self._update_buffer = self._update_buffer_audiolab
        return self

    def _close_audiolab(self):
        """ Close the audio file using the scikits.audiolab module. """
        if self.sf is not None:
            self.sf.close()
            self.sf = None

    def _update_buffer_audiolab(self, start, stop):
        """Make sure that the buffer contains the data between
        start and stop using the scikits.audiolab module.
        """
        if start < self.offset or stop > self.offset + self.buffer.shape[0]:
            offset, size = self._read_indices(start, stop)
            r_offset, r_size = self._recycle_buffer(offset, size)
            self.sf.seek(r_offset)  # undocumented ...
            buffer = self.sf.read_frames(nframes=r_size, dtype=self.buffer.dtype)
            if len(buffer.shape) == 1:
                buffer = np.reshape(buffer,(-1, 1))
            self.buffer[r_offset-offset:r_offset+r_size-offset,:] = buffer
            self.offset = offset
            if self.verbose > 0:
                print('  loaded %d frames from %d up to %d'
                      % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))
                
            
    # audioread interface:        
    def open_audioread(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading using the audioread module.

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
        self.verbose = verbose
        if self.verbose > 1:
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
        self.samplerate = self.sf.samplerate
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
        self._update_buffer = self._update_buffer_audioread
        self.filepath = filepath
        self.sf_iter = self.sf.__iter__()
        return self

    def _close_audioread(self):
        """ Close the audio file using the audioread module. """
        if self.sf is not None:
            self.sf.__exit__(None, None, None)
            self.sf = None

    def _update_buffer_audioread(self, start, stop):
        """Make sure that the buffer contains the data between
        start and stop using the audioread module.

        audioread can only iterate through a file once.
        """
        if start < self.offset or stop > self.offset + self.buffer.shape[0]:
            offset, size = self._read_indices(start, stop)
            r_offset, r_size = self._recycle_buffer(offset, size)
            # recycle file data:
            if ( self.read_offset + self.read_buffer.shape[0] >= r_offset + r_size
                 and self.read_offset < r_offset + r_size ):
                n = r_offset + r_size - self.read_offset
                self.buffer[self.read_offset-offset:self.read_offset-offset+n,:] = self.read_buffer[:n,:] / 2.0**15
                if self.verbose > 1:
                    print('  recycle %6d frames from the front of the read buffer to %d-%d (%d-%d in buffer)'
                           % (n, self.read_offset, self.read_offset+n, self.read_offset-offset, self.read_offset-offset+n))
                r_size -= n
            # go back to beginning of file:
            if r_offset < self.read_offset:
                if self.verbose > 1:
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
                    buffer = self.sf_iter.next()
                except StopIteration:
                    self.read_buffer = np.zeros((0,0))
                    self.buffer[r_offset-offset:,:] = 0.0
                    if self.verbose > 1:
                        print('  caught StopIteration, padded buffer with %d zeros' % r_size)
                    break
                self.read_buffer = np.fromstring(buffer, dtype='<i2').reshape(-1, self.channels)
                if self.verbose > 2:
                    print('  read forward by %d frames' % self.read_buffer.shape[0])
            # recycle file data:
            if ( self.read_offset + self.read_buffer.shape[0] > r_offset
                 and self.read_offset <= r_offset ):
                n = self.read_offset + self.read_buffer.shape[0] - r_offset
                if n > r_size:
                    n = r_size
                self.buffer[r_offset - offset:r_offset - offset + n,:] = self.read_buffer[-n:,:] / 2.0**15
                if self.verbose > 1:
                    print('  recycle %6d frames from the end of the read buffer at %d-%d to %d-%d (%d-%d in buffer)'
                           % (n, self.read_offset, self.read_offset + self.read_buffer.shape[0],
                              r_offset, r_offset+n, r_offset-offset, r_offset+n-offset))
                r_offset += n
                r_size -= n
            # read data:
            if self.verbose > 1 and r_size > 0:
                print('  read    %6d frames at %d-%d (%d-%d in buffer)'
                       % (r_size, r_offset, r_offset+r_size, r_offset-offset, r_offset+r_size-offset))
            while r_size > 0:
                self.read_offset += self.read_buffer.shape[0]
                try:
                    buffer = self.sf_iter.next()
                except StopIteration:
                    self.read_buffer = np.zeros((0,0))
                    self.buffer[r_offset-offset:,:] = 0.0
                    if self.verbose > 1:
                        print('  caught StopIteration, padded buffer with %d zeros' % r_size)
                    break
                self.read_buffer = np.fromstring(buffer, dtype='<i2').reshape(-1, self.channels)
                n = self.read_buffer.shape[0]
                if n > r_size:
                    n = r_size
                if n > 0:
                    self.buffer[r_offset-offset:r_offset+n-offset,:] = self.read_buffer[:n,:] / 2.0**15
                    if self.verbose > 2:
                        print('    read  %6d frames to %d-%d (%d-%d in buffer)'
                              % (n, r_offset, r_offset+n, r_offset-offset, r_offset+n-offset))
                    r_offset += n
                    r_size -= n
            self.offset = offset
            if self.verbose > 0:
                print('  loaded  %d frames at %d-%d'
                      % (self.buffer.shape[0], self.offset, self.offset+self.buffer.shape[0]))

                                
    def open(self, filepath, buffersize=10.0, backsize=0.0, verbose=0):
        """Open audio file for reading.

        Args:
          filepath (string): name of the file
          buffersize (float): size of internal buffer in seconds
          backsize (float): part of the buffer to be loaded before the requested start index in seconds
          verbose (int): if >0 show detailed error/warning messages
        """
        if len(filepath) == 0:
            warnings.warn('input argument filepath is empty string!')
            return data, rate
        if not os.path.isfile(filepath):
            warnings.warn('input argument filepath=%s does not indicate an existing file!' % filepath)
            return data, rate
        if os.path.getsize(filepath) <= 0:
            warnings.warn('load_audio(): input argument filepath=%s indicates file of size 0!' % filepath)
            return data, rate
        # list of implemented open functions:
        audio_open = [
            ['soundfile', self.open_soundfile],
            ['audioread', self.open_audioread],
            ['wave', self.open_wave],
            ['wavefile', self.open_wavefile],
            ['scikits.audiolab', self.open_audiolab],
            ['ewave', self.open_ewave]
            ]
        # open an audio file by trying various modules:
        for lib, open_file in audio_open:
            if not audio_modules[lib]:
                continue
            try:
                open_file(filepath, buffersize, backsize, verbose)
                if self.verbose > 0:
                    print('opened audio file "%s" using %s:' %
                          (filepath, lib))
                    print('  sampling rate: %g Hz' % self.samplerate)
                    print('  data values : %d' % self.frames)
                break
            except:
                warnings.warn('failed to open audio file "%s" with %s' % (filepath, lib))
        return self


open_audio = AudioLoader
                

if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt

    print("Checking audioloader module ...")
    print('')
    print('Usage:')
    print('  python audioloader.py [-p] <audiofile>')
    print('  -p: plot data')
    print('')
    list_modules()
    print('')
    print('available modules:')
    print('  %s' % '\n  '.join(available_modules()))

    plot = False
    if len(sys.argv) > 1 and sys.argv[1] == '-p':
        plot = True
        
    filepath = sys.argv[-1]
    print('')
    print("try load_audio:")
    data, rate = load_audio(filepath, 2)
    if plot:
        plt.plot(np.arange(len(data))/rate, data[:,0])
        plt.show()
    print('')
    for lib, load_file in audio_loader:
        if not audio_modules[lib]:
            continue
        try:
            data, rate = load_file(filepath, 1)
            print('loaded data from file "%s" with %s' %
                    (filepath, lib))
        except:
            print('failed to load data from file "%s" with %s' %
                  (filepath, lib))
    print('')

    print("try AudioLoader:")
    print('')
    #data = AudioLoader()
    #data.open_audioread(filepath, 2.0, 1.0, 2)
    #data = AudioLoader(filepath, 8.0, 3.0, 2)
    #with data.open_soundfile(filepath, 2.0, 1.0, 2):
    with open_audio(filepath, 2.0, 1.0, 1) as data:
        print('samplerate: %g' % data.samplerate)
        print('channels: %d %d' % (data.channels, data.shape[1]))
        print('frames: %d %d' % (len(data), data.shape[0]))
        nframes = int(1.0*data.samplerate)
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
    #data.close()

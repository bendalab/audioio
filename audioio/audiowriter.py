"""
Writing numpy arrays of floats to audio files.

- `write_audio()`: write audio data to file.
- `available_formats()`: audio file formats supported by any of the installed audio modules.
- `available_encodings()`: encodings of an audio file format supported by any of the installed audio modules.

The data to be written are 1-D or 2-D numpy arrays of floats ranging between -1 and 1
with first axis time and second axis channel.

For support of more audio formats, you might need to install additional packages.
See [installation](https://bendalab.github.io/audioio/installation)
for further instructions.

For a demo, run the script as:
```
python -m audioio.audiowriter
```
"""
 
import numpy as np
from .audiomodules import *


def formats_wave():
    """Audio file formats supported by the wave module.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    if not audio_modules['wave']:
        return []
    else:
        return ['WAV']


def encodings_wave(format):
    """Encodings of an audio file format supported by the wave module.

    Parameters
    ----------
    format: str
        The file format.

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    if not audio_modules['wave']:
        return []
    elif format.upper() != 'WAV':
        return []
    else:
        return ['PCM_32', 'PCM_16', 'PCM_U8']


def write_wave(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the wave module from pythons standard libray.
    
    Documentation
    -------------
    https://docs.python.org/3.8/library/wave.html

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format, only 'WAV' is supported.
    encoding: string or None
        Encoding of the data: 'PCM_32', 'PCM_16', or 'PCM_U8'
        If None or empty string use 'PCM_16'.

    Raises
    ------
    ImportError
        The wave module is not installed.
    *
        Writing of the data failed.
    ValueError
        File format or encoding not supported.
    """
    if not audio_modules['wave']:
        raise ImportError

    if format and format.upper() != 'WAV':
        raise ValueError('file format %s not supported by wave module' % format)

    wave_encodings = {'PCM_32': [4, 'i4'],
                      'PCM_16': [2, 'i2'],
                      'PCM_U8': [1, 'u1'] }
    if encoding is None:
        encoding = ''
    if len(encoding) == 0:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if not encoding in wave_encodings:
        raise ValueError('file encoding %s not supported by wave module' % encoding)
    sampwidth = wave_encodings[encoding][0]
    dtype = wave_encodings[encoding][1]

    wf = wave.open(filepath, 'w')   # 'with' is not supported by wave
    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]
    wf.setnchannels(channels)
    wf.setnframes(len(data))
    wf.setframerate(int(samplerate))
    wf.setsampwidth(sampwidth)
    factor = 2**(sampwidth*8-1)
    if sampwidth == 1:
        buffer = np.floor((data+1.0) * factor).astype(dtype)
        buffer[data >= 1.0] = 2*factor - 1
    else:
        buffer = np.floor(data * factor).astype(dtype)
        buffer[data >= 1.0] = factor - 1
    try:
        wf.writeframes(buffer.tobytes())
    except AttributeError: 
        wf.writeframes(buffer.tostring())
    wf.close()


def formats_ewave():
    """Audio file formats supported by the ewave module.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    if not audio_modules['ewave']:
        return []
    else:
        return ['WAV', 'WAVEX']


def encodings_ewave(format):
    """Encodings of an audio file format supported by the ewave module.

    Parameters
    ----------
    format: str
        The file format.

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    if not audio_modules['ewave']:
        return []
    elif format.upper() != 'WAV' and format.upper() != 'WAVEX':
        return []
    else:
        return ['PCM_64', 'PCM_32', 'PCM_16', 'FLOAT', 'DOUBLE']


def write_ewave(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the ewave module from pythons standard libray.

    Documentation
    -------------
    https://github.com/melizalab/py-ewave

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format, only 'WAV' and 'WAVEX' are supported.
    encoding: string or None
        Encoding of the data: 'PCM_64', 'PCM_32', PCM_16', 'FLOAT', 'DOUBLE'
        If None or empty string use 'PCM_16'.

    Raises
    ------
    ImportError
        The ewave module is not installed.
    *
        Writing of the data failed.
    ValueError
        File format or encoding not supported.
    """
    if not audio_modules['ewave']:
        raise ImportError

    if format and format.upper() != 'WAV' and format.upper() != 'WAVEX':
        raise ValueError('file format %s not supported by ewave module' % format)

    ewave_encodings = {'PCM_64': 'l',
                       'PCM_32': 'i',
                       'PCM_16': 'h',
                       'FLOAT': 'f',
                       'DOUBLE': 'd' }
    if encoding == '':
        encoding = None
    if encoding is None:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if not encoding in ewave_encodings:
        raise ValueError('file encoding %s not supported by ewave module' % encoding)

    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]

    with ewave.open(filepath, 'w', sampling_rate=int(samplerate),
                    dtype=ewave_encodings[encoding], nchannels=channels) as wf:
        wf.write(data, scale=True)


def formats_wavfile():
    """Audio file formats supported by the scipy.io.wavfile module.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    if not audio_modules['scipy.io.wavfile']:
        return []
    else:
        return ['WAV']


def encodings_wavfile(format):
    """Encodings of an audio file format supported by the scipy.io.wavfile module.

    Parameters
    ----------
    format: str
        The file format.

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    if not audio_modules['scipy.io.wavfile']:
        return []
    elif format.upper() != 'WAV':
        return []
    else:
        return ['PCM_U8', 'PCM_16', 'PCM_32', 'PCM_64', 'FLOAT', 'DOUBLE']


def write_wavfile(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the scipy.io.wavfile module.
    
    Documentation
    -------------
    http://docs.scipy.org/doc/scipy/reference/io.html

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format, only 'WAV' is supported.
    encoding: string or None
        Encoding of the data: 'PCM_64', 'PCM_32', PCM_16', 'PCM_U8', 'FLOAT', 'DOUBLE'
        If None or empty string use 'PCM_16'.

    Raises
    ------
    ImportError
        The wavfile module is not installed.
    ValueError
        File format or encoding not supported.
    *
        Writing of the data failed.
    """
    if not audio_modules['scipy.io.wavfile']:
        raise ImportError

    if format and format.upper() != 'WAV':
        raise ValueError('file format %s not supported by scipy.io.wavfile module' % format)

    wave_encodings = {'PCM_U8': [1, 'u1'],
                      'PCM_16': [2, 'i2'],
                      'PCM_32': [4, 'i4'],
                      'PCM_64': [8, 'i8'],
                      'FLOAT': [4, 'f'],
                      'DOUBLE': [8, 'd']}
    if encoding == '':
        encoding = None
    if encoding is None:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if not encoding in wave_encodings:
        raise ValueError('file encoding %s not supported by scipy.io.wavfile module' % encoding)
    sampwidth = wave_encodings[encoding][0]
    dtype = wave_encodings[encoding][1]
    if sampwidth == 1:
        factor = 2**(sampwidth*8-1)
        buffer = np.floor((data+1.0) * factor).astype(dtype)
        buffer[data >= 1.0] = 2*factor - 1
    elif dtype[0] == 'i':
        factor = 2**(sampwidth*8-1)
        buffer = np.floor(data * factor).astype(dtype)
        buffer[data >= 1.0] = factor - 1
    else:
        buffer = data.astype(dtype, copy=False)
    wavfile.write(filepath, int(samplerate), buffer)


def formats_soundfile():
    """Audio file formats supported by the SoundFile module.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    if not audio_modules['soundfile']:
        return []
    else:
        return sorted(list(soundfile.available_formats()))


def encodings_soundfile(format):
    """Encodings of an audio file format supported by the SoundFile module.

    Parameters
    ----------
    format: str
        The file format.

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    if not audio_modules['soundfile']:
        return []
    else:
        return sorted(list(soundfile.available_subtypes(format)))


def write_soundfile(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the SoundFile module (based on libsndfile).
    
    Documentation
    -------------
    http://pysoundfile.readthedocs.org

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format.
    encoding: string or None
        Encoding of the data.
        If None or empty string use 'PCM_16'.

    Raises
    ------
    ImportError
        The SoundFile module is not installed.
    *
        Writing of the data failed.
    """
    if not audio_modules['soundfile']:
        raise ImportError

    if format is not None:
        if len(format) == 0:
            format = None
        else:
            format = format.upper()

    if encoding == '':
        encoding = None
    if encoding is None:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    soundfile.write(filepath, data, int(samplerate), format=format, subtype=encoding)


def formats_wavefile():
    """Audio file formats supported by the wavefile module.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    if not audio_modules['wavefile']:
        return []
    formats = []
    for attr in dir(wavefile.Format):
        v = getattr(wavefile.Format, attr)
        if ( isinstance(v, int)
             and v & wavefile.Format.TYPEMASK > 0
             and v != wavefile.Format.TYPEMASK ):
            formats.append(attr)
    return sorted(formats)


def encodings_wavefile(format):
    """Encodings supported by the wavefile module.

    Parameters
    ----------
    format: str
        The file format (ignored).

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    if not audio_modules['wavefile']:
        return []
    if not format.upper() in formats_wavefile():
        return []
    encodings = []
    for attr in dir(wavefile.Format):
        v = getattr(wavefile.Format, attr)
        if ( isinstance(v, int)
             and v & wavefile.Format.SUBMASK > 0
             and v != wavefile.Format.SUBMASK ):
            encodings.append(attr)
    return sorted(encodings)

    
def write_wavefile(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the wavefile module (based on libsndfile).
    
    Documentation
    -------------
    https://github.com/vokimon/python-wavefile

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format as in wavefile.Format.
    encoding: string or None
        Encoding of the data as in wavefile.Format.
        If None or empty string use 'PCM_16'.

    Raises
    ------
    ImportError
        The wavefile module is not installed.
    ValueError
        File format or encoding not supported.
    *
        Writing of the data failed.
    """
    if not audio_modules['wavefile']:
        raise ImportError

    if format is None:
        format = ''
    if len(format) == 0:
        format = filepath.split('.')[-1]
        # TODO: we need a mapping from file extensions to formats and default encoding!
    format = format.upper()
    try:
        format_value = getattr(wavefile.Format, format)
    except AttributeError:
        raise ValueError('file format %s not supported by wavefile module' % format)

    if encoding is None:
        encoding = ''
    if len(encoding) == 0:
        encodings = encodings_wavefile(format)
        if 'PCM_16' in encodings:
            encoding = 'PCM_16'
        else:
            encoding = encodings[0]
    encoding = encoding.upper()
    try:
        encoding_value = getattr(wavefile.Format, encoding)
    except AttributeError:
        raise ValueError('file encoding %s not supported by wavefile module' % encoding)
        
    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]
    else:
        data = data.reshape((-1, 1))
    with wavefile.WaveWriter(filepath, channels=channels, samplerate=int(samplerate),
                             format=format_value|encoding_value) as w:
        w.write(data.T)


audio_formats_funcs = (
    ('soundfile', formats_soundfile),
    ('wavefile', formats_wavefile),
    ('wave', formats_wave),
    ('ewave', formats_ewave),
    ('scipy.io.wavfile', formats_wavfile)
    )
""" List of implemented formats functions.

Each element of the list is a tuple with the module's name and the formats function.
"""


def available_formats():
    """Audio file formats supported by any of the installed audio modules.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    formats = set()
    for module, formats_func in audio_formats_funcs:
        formats |= set(formats_func())
    return sorted(list(formats))


audio_encodings_funcs = (
    ('soundfile', encodings_soundfile),
    ('wavefile', encodings_wavefile),
    ('wave', encodings_wave),
    ('ewave', encodings_ewave),
    ('scipy.io.wavfile', encodings_wavfile)
    )
""" List of implemented encodings functions.

Each element of the list is a tuple with the module's name and the encodings function.
"""


def available_encodings(format):
    """Encodings of an audio file format supported by any of the installed audio modules.

    Parameters
    ----------
    format: str
        The file format.

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    got_sndfile = False
    encodings = set()
    for module, encodings_func in audio_encodings_funcs:
        if got_sndfile and module == 'scipy.io.wavfile':
            continue
        encs = encodings_func(format)
        encodings |= set(encs)
        if module in ['soundfile', 'wavefile'] and len(encs) > 0:
            got_sndfile = True
    return sorted(list(encodings))


audio_writer_funcs = (
    ('soundfile', write_soundfile),
    ('wavefile', write_wavefile),
    ('wave', write_wave),
    ('ewave', write_ewave),
    ('scipy.io.wavfile', write_wavfile)
    )
""" List of implemented write functions.

Each element of the list is a tuple with the module's name and the write function.
"""


def write_audio(filepath, data, samplerate, format=None, encoding=None, verbose=0):
    """
    Write audio data to file.

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format. If None deduce file format from filepath.
        See `available_formats()` for possible values.
    encoding: string or None
        Encoding of the data. See `available_encodings()` for possible values.
        If None or empty string use 'PCM_16'.
    verbose: int
        If >0 show detailed error/warning messages.

    Raises
    ------
    ValueError
        `filepath` is empty string.
    IOError
        Writing of the data failed.

    Example
    -------
    ```
    import numpy as np
    from audioio import write_audio
    
    samplerate = 28000.0
    freq = 800.0
    time = np.arange(0.0, 1.0, 1/samplerate) # one second
    data = np.sin(2.0*np.p*freq*time)        # 800Hz sine wave
    write_audio('audio/file.wav', data, samplerate)
    ```
    """

    if len(filepath) == 0:
        raise ValueError('input argument filepath is empty string!')

    # write audio file by trying available modules:
    success = False
    for lib, write_file in audio_writer_funcs:
        if not audio_modules[lib]:
            continue
        try:
            write_file(filepath, data, samplerate, format, encoding)
            success = True
            if verbose > 0:
                print('wrote data to file "%s" using %s module' %
                      (filepath, lib))
                if verbose > 1:
                    print('  sampling rate: %g Hz' % samplerate)
                    print('  channels     : %d' % (data.shape[1] if len(data.shape) > 1 else 1))
                    print('  frames       : %d' % len(data))
            break
        except Exception as e:
            pass
    if not success:
        raise IOError('failed to write data to file "%s"' % filepath)


def demo(file_path, encoding=''):
    """ Demo of the audiowriter functions.

    Parameters
    ----------
    file_path: string
        File path of an audio file.
    encoding: string
        Encoding to be used.
    """
    print('')
    print('generate data ...')
    samplerate = 44100.0
    t = np.arange(0.0, 2.0, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t)
        
    print("write_audio(%s) ..." % file_path)
    write_audio(file_path, data, samplerate, encoding=encoding, verbose=2)

    print('done.')
    

def main(args):
    """ Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv
    """
    print("Checking audiowriter module ...")

    help = False
    file_path = None
    encoding = ''
    mod = False
    for arg in args[1:]:
        if mod:
            select_module(arg)
            mod = False
        elif arg == '-h':
            help = True
            break
        elif arg == '-m':
            mod = True
        elif file_path is None:
            file_path = arg
        else:
            encoding = arg
            break
    if file_path is None:
        file_path = 'test.wav'

    if help:
        print('')
        print('Usage:')
        print('  python -m audioio.audiowriter [-m module] [<filename>] [<encoding>]')
        return

    demo(file_path, encoding)


if __name__ == "__main__":
    import sys
    main(sys.argv)

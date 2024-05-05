"""Write numpy arrays of floats to audio files.

- `write_audio()`: write audio data to file.
- `available_formats()`: audio file formats supported by any of the installed audio modules.
- `available_encodings()`: encodings of an audio file format supported by any of the installed audio modules.
- `format_from_extension()`: deduce audio file format from file extension.

The data to be written are 1-D or 2-D numpy arrays of floats ranging
between -1 and 1 with first axis time and (optional) second axis channel.

For support of more audio formats, you might need to install
additional packages.
See [installation](https://bendalab.github.io/audioio/installation)
for further instructions.

For a demo, run the script as:
```
python -m src.audioio.audiowriter
```

"""

import os
import sys
import subprocess
import numpy as np
from .audiomodules import *
from .riffmetadata import write_wave as audioio_write_wave
from .riffmetadata import append_riff


def format_from_extension(filepath):
    """Deduce audio file format from file extension.

    Parameters
    ----------
    filepath: string
        Name of the audio file.

    Returns
    -------
    format: string
        Audio format deduced from file extension.
    """
    if not filepath:
        return None
    ext = os.path.splitext(filepath)[1]
    if not ext:
        return None
    if ext[0] == '.':
        ext = ext[1:]
    if not ext:
        return None
    ext = ext.upper()
    if ext == 'WAVE':
        return 'WAV'
    ext = ext.replace('MPEG' , 'MP')
    return ext


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


def write_wave(filepath, data, rate, metadata=None, locs=None,
               labels=None, format=None, encoding=None,
               marker_hint='cue'):
    """Write audio data using the wave module from pythons standard libray.
    
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
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    format: string or None
        File format, only 'WAV' is supported.
    encoding: string or None
        Encoding of the data: 'PCM_32', 'PCM_16', or 'PCM_U8'.
        If None or empty string use 'PCM_16'.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

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
    if not filepath:
        raise ValueError('no file specified!')

    if not format:
        format = format_from_extension(filepath)
    if format and format.upper() != 'WAV':
        raise ValueError('file format %s not supported by wave module' % format)

    wave_encodings = {'PCM_32': [4, 'i4'],
                      'PCM_16': [2, 'i2'],
                      'PCM_U8': [1, 'u1'] }
    if not encoding:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if encoding not in wave_encodings:
        raise ValueError('file encoding %s not supported by wave module' % encoding)
    sampwidth = wave_encodings[encoding][0]
    dtype = wave_encodings[encoding][1]

    wf = wave.open(filepath, 'w')   # 'with' is not supported by wave
    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]
    wf.setnchannels(channels)
    wf.setnframes(len(data))
    wf.setframerate(int(rate))
    wf.setsampwidth(sampwidth)
    factor = 2**(sampwidth*8-1)
    if sampwidth == 1:
        buffer = np.floor((data+1.0) * factor).astype(dtype)
        buffer[data >= 1.0] = 2*factor - 1
    else:
        buffer = np.floor(data * factor).astype(dtype)
        buffer[data >= 1.0] = factor - 1
    wf.writeframes(buffer.tobytes())
    wf.close()
    append_riff(filepath, metadata, locs, labels, rate, marker_hint)


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


def write_ewave(filepath, data, rate, metadata=None, locs=None,
                labels=None, format=None, encoding=None,
                marker_hint='cue'):
    """Write audio data using the ewave module from pythons standard libray.

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
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    format: string or None
        File format, only 'WAV' and 'WAVEX' are supported.
    encoding: string or None
        Encoding of the data: 'PCM_64', 'PCM_32', PCM_16', 'FLOAT', 'DOUBLE'
        If None or empty string use 'PCM_16'.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

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
    if not filepath:
        raise ValueError('no file specified!')

    if not format:
        format = format_from_extension(filepath)
    if format and format.upper() != 'WAV' and format.upper() != 'WAVEX':
        raise ValueError('file format %s not supported by ewave module' % format)

    ewave_encodings = {'PCM_64': 'l',
                       'PCM_32': 'i',
                       'PCM_16': 'h',
                       'FLOAT': 'f',
                       'DOUBLE': 'd' }
    if not encoding:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if encoding not in ewave_encodings:
        raise ValueError('file encoding %s not supported by ewave module' % encoding)

    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]

    with ewave.open(filepath, 'w', sampling_rate=int(rate),
                    dtype=ewave_encodings[encoding], nchannels=channels) as wf:
        wf.write(data, scale=True)
    append_riff(filepath, metadata, locs, labels, rate, marker_hint)


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


def write_wavfile(filepath, data, rate, metadata=None, locs=None,
                  labels=None, format=None, encoding=None,
                  marker_hint='cue'):
    """Write audio data using the scipy.io.wavfile module.
    
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
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    format: string or None
        File format, only 'WAV' is supported.
    encoding: string or None
        Encoding of the data: 'PCM_64', 'PCM_32', PCM_16', 'PCM_U8', 'FLOAT', 'DOUBLE'
        If None or empty string use 'PCM_16'.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

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
    if not filepath:
        raise ValueError('no file specified!')

    if not format:
        format = format_from_extension(filepath)
    if format and format.upper() != 'WAV':
        raise ValueError('file format %s not supported by scipy.io.wavfile module' % format)

    wave_encodings = {'PCM_U8': [1, 'u1'],
                      'PCM_16': [2, 'i2'],
                      'PCM_32': [4, 'i4'],
                      'PCM_64': [8, 'i8'],
                      'FLOAT': [4, 'f'],
                      'DOUBLE': [8, 'd']}
    if not encoding:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if encoding not in wave_encodings:
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
    wavfile.write(filepath, int(rate), buffer)
    append_riff(filepath, metadata, locs, labels, rate, marker_hint)


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


def write_soundfile(filepath, data, rate, metadata=None, locs=None,
                    labels=None, format=None, encoding=None,
                    marker_hint='cue'):
    """Write audio data using the SoundFile module (based on libsndfile).
    
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
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    format: string or None
        File format.
    encoding: string or None
        Encoding of the data.
        If None or empty string use 'PCM_16'.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

    Raises
    ------
    ImportError
        The SoundFile module is not installed.
    *
        Writing of the data failed.
    """
    if not audio_modules['soundfile']:
        raise ImportError
    if not filepath:
        raise ValueError('no file specified!')

    if not format:
        format = format_from_extension(filepath)
    if format:
        format = format.upper()

    if not encoding:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    
    soundfile.write(filepath, data, int(rate), format=format,
                    subtype=encoding)
    try:
        append_riff(filepath, metadata, locs, labels, rate, marker_hint)
    except ValueError:
        pass


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

    
def write_wavefile(filepath, data, rate, metadata=None, locs=None,
                   labels=None, format=None, encoding=None,
                   marker_hint='cue'):
    """Write audio data using the wavefile module (based on libsndfile).
    
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
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    format: string or None
        File format as in wavefile.Format.
    encoding: string or None
        Encoding of the data as in wavefile.Format.
        If None or empty string use 'PCM_16'.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

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
    if not filepath:
        raise ValueError('no file specified!')

    if not format:
        format = format_from_extension(filepath)
    format = format.upper()
    try:
        format_value = getattr(wavefile.Format, format)
    except AttributeError:
        raise ValueError('file format %s not supported by wavefile module' % format)

    if not encoding:
        encodings = encodings_wavefile(format)
        encoding = encodings[0]
        if 'PCM_16' in encodings:
            encoding = 'PCM_16'
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
    with wavefile.WaveWriter(filepath, channels=channels,
                             samplerate=int(rate),
                             format=format_value|encoding_value) as w:
        w.write(data.T)
    try:
        append_riff(filepath, metadata, locs, labels, rate, marker_hint)
    except ValueError:
        pass


def formats_pydub():
    """Audio file formats supported by the Pydub module.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    if not audio_modules['pydub']:
        return []
    formats = []
    command = [pydub.AudioSegment.converter, '-formats']
    with open(os.devnull, 'rb') as devnull:
        p = subprocess.Popen(command, stdin=devnull, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, universal_newlines=True)
        skip = True
        for line in p.communicate()[0].split('\n'):
            if '--' in line[:3]:
                skip = False
                continue
            if skip:
                continue
            cols = line.split()
            if len(cols) > 2 and 'E' in cols[0]:
                formats.append(cols[1].upper())
    return formats

def encodings_pydub(format):
    """Encodings of an audio file format supported by the Pydub module.

    Parameters
    ----------
    format: str
        The file format.

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    pydub_encodings = {'pcm_s16le': 'PCM_16',
                       'pcm_s24le': 'PCM_24',
                       'pcm_s32le': 'PCM_32',
                       'pcm_f32le': 'FLOAT',
                       'pcm_f64le': 'DOUBLE',
                       }    
    if not audio_modules['pydub']:
        return []
    if format.upper() not in formats_pydub():
        return []
    encodings = []
    command = [pydub.AudioSegment.converter, '-encoders']
    with open(os.devnull, 'rb') as devnull:
        p = subprocess.Popen(command, stdin=devnull, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, universal_newlines=True)
        skip = True
        for line in p.communicate()[0].split('\n'):
            if '--' in line[:3]:
                skip = False
                continue
            if skip:
                continue
            cols = line.split()
            if len(cols) > 2 and cols[0][0] == 'A':
                encoding = cols[1]
                if encoding in pydub_encodings:
                    encoding = pydub_encodings[encoding]
                encodings.append(encoding.upper())
    return encodings

def write_pydub(filepath, data, rate, metadata=None, locs=None,
                labels=None, format=None, encoding=None,
                marker_hint='cue'):
    """Write audio data using the Pydub module.
    
    Documentation
    -------------
    https://github.com/jiaaro/pydub

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    format: string or None
        File format, everything ffmpeg or avtools are supporting.
    encoding: string or None
        Encoding of the data.
        If None or empty string use 'PCM_16'.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.

    Raises
    ------
    ImportError
        The Pydub module is not installed.
    *
        Writing of the data failed.
    ValueError
        File format or encoding not supported.
    """
    if not audio_modules['pydub']:
        raise ImportError
    if not filepath:
        raise ValueError('no file specified!')

    if not format:
        format = format_from_extension(filepath)
    if format and format.upper() not in formats_pydub():
        raise ValueError('file format %s not supported by Pydub module' % format)

    pydub_encodings = {'PCM_16': 'pcm_s16le',
                       'PCM_24': 'pcm_s24le',
                       'PCM_32': 'pcm_s32le',
                       'DOUBLE': 'pcm_f32le',
                       'FLOAT': 'pcm_f64le',
                       }    
    if encoding:
        encoding = encoding.upper()
        if encoding in pydub_encodings:
            encoding = pydub_encodings[encoding]
        if encoding not in encodings_pydub(format):
            raise ValueError('file encoding %s not supported by Pydub module' % encoding)
        encoding = encoding.lower()
    else:
        encoding = None
        
    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]
    int_data = (data*(2**31-1)).astype(np.int32)
    sound = pydub.AudioSegment(int_data.ravel(), sample_width=4,
                               frame_rate=rate, channels=channels)
    sound.export(filepath, format=format.lower(), codec=encoding)
    try:
        append_riff(filepath, metadata, locs, labels, rate, marker_hint)
    except ValueError:
        pass
    

audio_formats_funcs = (
    ('soundfile', formats_soundfile),
    ('wavefile', formats_wavefile),
    ('wave', formats_wave),
    ('ewave', formats_ewave),
    ('scipy.io.wavfile', formats_wavfile),
    ('pydub', formats_pydub)
    )
""" List of implemented formats() functions.

Each element of the list is a tuple with the module's name and the formats() function.
"""


def available_formats():
    """Audio file formats supported by any of the installed audio modules.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.

    Examples
    --------
    ```
    >>> from audioio import available_formats
    >>> f = available_formats()
    >>> printf(f)
    ['3G2', '3GP', 'A64', 'AC3', 'ADTS', 'ADX', 'AIFF', ...,  'WAV', 'WAVEX', 'WEBM', 'WEBM_CHUNK', 'WEBM_DASH_MANIFEST', 'WEBP', 'WEBVTT', 'WTV', 'WV', 'WVE', 'XI', 'XV', 'YUV4MPEGPIPE']
    ```
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
    ('scipy.io.wavfile', encodings_wavfile),
    ('pydub', encodings_pydub)
    )
""" List of implemented encodings() functions.

Each element of the list is a tuple with the module's name and the encodings() function.
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

    Example
    -------
    ```
    >>> from audioio import available_encodings
    >>> e = available_encodings('WAV')
    >>> printf(e)
    ['ALAW', 'DOUBLE', 'FLOAT', 'G721_32', 'GSM610', 'IMA_ADPCM', 'MS_ADPCM', 'PCM_16', 'PCM_24', 'PCM_32', 'PCM_U8', 'ULAW']
    ```
    """
    for module, encodings_func in audio_encodings_funcs:
        encs = encodings_func(format)
        if len(encs) > 0:
            return encs
    return []


audio_writer_funcs = (
    ('soundfile', write_soundfile),
    ('wavefile', write_wavefile),
    ('wave', write_wave),
    ('ewave', write_ewave),
    ('scipy.io.wavfile', write_wavfile),
    ('pydub', write_pydub)
    )
""" List of implemented write() functions.

Each element of the list is a tuple with the module's name and the write() function.
"""


def write_audio(filepath, data, rate, metadata=None, locs=None,
                labels=None, format=None, encoding=None,
                marker_hint='cue', verbose=0):
    """Write audio data, metadata, and marker to file.

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1-D or 2-D array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    rate: float
        Sampling rate of the data in Hertz.
    metadata: None or nested dict
        Metadata as key-value pairs. Values can be strings, integers,
        or dictionaries.
    locs: None or 1-D or 2-D array of ints
        Marker positions (first column) and spans (optional second column)
        for each marker (rows).
    labels: None or 2-D array of string objects
        Labels (first column) and texts (optional second column)
        for each marker (rows).
    format: string or None
        File format. If None deduce file format from filepath.
        See `available_formats()` for possible values.
    encoding: string or None
        Encoding of the data. See `available_encodings()` for possible values.
        If None or empty string use 'PCM_16'.
    marker_hint: str
        - 'cue': store markers in cue and and adtl chunks.
        - 'lbl': store markers in avisoft lbl chunk.
    verbose: int
        If >0 show detailed error/warning messages.

    Raises
    ------
    ValueError
        `filepath` is empty string.
    IOError
        Writing of the data failed.

    Examples
    --------
    ```
    import numpy as np
    from audioio import write_audio
    
    rate = 28000.0
    freq = 800.0
    time = np.arange(0.0, 1.0, 1/rate) # one second
    data = np.sin(2.0*np.p*freq*time)        # 800Hz sine wave
    md = dict(Artist='underscore_')          # metadata

    write_audio('audio/file.wav', data, rate, md)
    ```
    """
    if not filepath:
        raise ValueError('no file specified!')

    # write audio with metadata and markers:
    if not format:
        format = format_from_extension(filepath)
    if format == 'WAV' and (metadata is not None or locs is not None):
        try:
            audioio_write_wave(filepath, data, rate, metadata,
                               locs, labels, encoding, marker_hint)
            return
        except ValueError:
            pass
    # write audio file by trying available modules:
    errors = [f'failed to write data to file "{filepath}":']
    for lib, write_file in audio_writer_funcs:
        if not audio_modules[lib]:
            continue
        try:
            write_file(filepath, data, rate, metadata, locs,
                       labels, format, encoding, marker_hint)
            success = True
            if verbose > 0:
                print('wrote data to file "%s" using %s module' %
                      (filepath, lib))
                if verbose > 1:
                    print('  sampling rate: %g Hz' % rate)
                    print('  channels     : %d' % (data.shape[1] if len(data.shape) > 1 else 1))
                    print('  frames       : %d' % len(data))
            return
        except Exception as e:
            errors.append(f'  {lib} failed: {str(e)}')
    raise IOError('\n'.join(errors))


def demo(file_path, channels=2, encoding=''):
    """Demo of the audiowriter functions.

    Parameters
    ----------
    file_path: string
        File path of an audio file.
    encoding: string
        Encoding to be used.
    """
    print('generate data ...')
    rate = 44100.0
    t = np.arange(0.0, 1.0, 1.0/rate)
    data = np.zeros((len(t), channels))
    for c in range(channels):
        data[:,c] = np.sin(2.0*np.pi*(440.0+c*8.0)*t)
        
    print("write_audio(%s) ..." % file_path)
    write_audio(file_path, data, rate, encoding=encoding, verbose=2)

    print('done.')
    

def main(*args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv[1:]
    """
    help = False
    file_path = None
    encoding = ''
    mod = False
    nchan = False
    channels = 2
    for arg in args:
        if mod:
            select_module(arg)
            mod = False
        elif nchan:
            channels = int(arg)
            nchan = False
        elif arg == '-h':
            help = True
            break
        elif arg == '-m':
            mod = True
        elif arg == '-n':
            nchan = True
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
        print('  python -m src.audioio.audiowriter [-m module] [-n channels] [<filename>] [<encoding>]')
        return

    demo(file_path, channels=channels, encoding=encoding)


if __name__ == "__main__":
    main(*sys.argv[1:])

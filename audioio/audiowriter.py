"""
Functions for writing numpy arrays of floats to audio files.

```
write_audio('audio/file.wav', data, samplerate)
```
Writes the whole file at once with an installed audio module that
supports the requested file format.

```
available_formats()
available_encodings()
```
return lists of supported formats and encodings.

We recommend pysoundfile for best results:
Installation:
```
sudo apt-get install libsndfile1 libsndfile1-dev libffi-dev
sudo pip install pysoundfile
```

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
    https://docs.python.org/2/library/wave.html

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1d- or 2d-array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format, only 'WAV' is supported.
    encoding: string or None
        Encoding of the data: 'PCM_32', PCM_16', or 'PCM_U8'

    Raises
    ------
    ImportError: The wave module is not installed.
    *: Writing of the data failed.
    ValueError: File format or encoding not supported.
    """
    if not audio_modules['wave']:
        raise ImportError

    if format is not None and format.upper() != 'WAV':
        raise ValueError('file format %s not supported by wave-module' % format)
        return

    wave_encodings = {'PCM_32': [4, 'i4'],
                      'PCM_16': [2, 'i2'],
                      'PCM_U8': [1, 'u1'] }
    if encoding is None:
        encoding = ''
    if len(encoding) == 0:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if not encoding in wave_encodings:
        raise ValueError('file encoding %s not supported by wave-module' % encoding)
        return
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
    data: 1d- or 2d-array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format, only 'WAV' is supported.
    encoding: string or None
        Encoding of the data: 'PCM_64', 'PCM_32', PCM_16', 'FLOAT', 'DOUBLE'

    Raises
    ------
    ImportError: The ewave module is not installed.
    *: Writing of the data failed.
    ValueError: File format or encoding not supported.
    """
    if not audio_modules['ewave']:
        raise ImportError

    if format is not None and format.upper() != 'WAV' and format.upper() != 'WAVEX':
        raise ValueError('file format %s not supported by ewave-module' % format)
        return

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
        raise ValueError('file encoding %s not supported by ewave-module' % encoding)
        return

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
    data: 1d- or 2d-array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format, only 'WAV' is supported.
    encoding: string or None
        Encoding of the data: PCM_16

    Raises
    ------
    ImportError: The wavfile module is not installed.
    *: Writing of the data failed.
    ValueError: File format or encoding not supported.
    """
    if not audio_modules['scipy.io.wavfile']:
        raise ImportError

    if format is not None and format.upper() != 'WAV':
        raise ValueError('file format %s not supported by scipy.io.wavfile-module' % format)
        return

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
        raise ValueError('file encoding %s not supported by scipy.io.wavfile-module' % encoding)
        return
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
    """Audio file formats supported by the pysoundfile module.

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
    """Encodings of an audio file format supported by the pysoundfile module.

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
    Write audio data using the pysoundfile module (based on libsndfile).
    
    Documentation
    -------------
    http://pysoundfile.readthedocs.org

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1d- or 2d-array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format.
    encoding: string or None
        Encoding of the data.

    Raises
    ------
    ImportError: The pysoundfile module is not installed.
    *: Writing of the data failed.
    """
    if not audio_modules['soundfile']:
        raise ImportError

    if format is not None:
        format = format.upper()

    if encoding == '':
        encoding = None
    if encoding is not None:
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
    data: 1d- or 2d-array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format as in wavefile.Format.
    encoding: string or None
        Encoding of the data as in wavefile.Format.

    Raises
    ------
    ImportError: The wavefile module is not installed.
    *: Writing of the data failed.
    """
    if not audio_modules['wavefile']:
        raise ImportError

    if format is None:
        format = ''
    if len(format) == 0:
        format = filepath.split('.')[-1]
        # TODO: we need a mapping from file extensions to formats and default encoding!
    format = format.upper()
    format_value = getattr(wavefile.Format, format)

    if encoding is None:
        encoding = ''
    if len(encoding) == 0:
        encodings = encodings_wavefile(format)
        # TODO: better default settings!
        if 'PCM_16' in encodings:
            encoding = 'PCM_16'
        else:
            encoding = encodings[0]
    encoding = encoding.upper()
    encoding_value = getattr(wavefile.Format, encoding)
        
    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]
    with wavefile.WaveWriter(filepath, channels=channels, samplerate=int(samplerate),
                             format=format_value|encoding_value) as w:
        w.write(data.T)


def formats_audiolab():
    """Audio file formats supported by the scikits.audiolab module.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    if not audio_modules['scikits.audiolab']:
        return []
    formats = [f.upper() for f in audiolab.available_file_formats()]
    return sorted(formats)

def encodings_audiolab(format):
    """Encodings of an audio file format supported by the scikits.audiolab module.

    Parameters
    ----------
    format: str
        The file format.

    Returns
    -------
    encodings: list of strings
        List of supported encodings as strings.
    """
    if not audio_modules['scikits.audiolab']:
        return []
    try:
        encodings = []
        for encoding in audiolab.available_encodings(format.lower()):
            if encoding[0:3] == 'pcm':
                encoding = 'pcm_' + encoding[3:]
            if encoding == 'float32': encoding = 'float'
            if encoding == 'float64': encoding = 'double'
            encodings.append(encoding.upper())
        return sorted(encodings)
    except ValueError:
        return []

def write_audiolab(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the scikits.audiolab module (based on libsndfile).

    Documentation
    -------------
    http://cournape.github.io/audiolab/
    https://github.com/cournape/audiolab

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1d- or 2d-array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format like the SF_FORMAT_ constants of libsndfile.
    encoding: string or None
        Encoding of the data like the SF_FORMAT_ constants of libsndfile.

    Raises
    ------
    ImportError: The scikits.audiolab module is not installed.
    *: Writing of the data failed.
    """
    if not audio_modules['scikits.audiolab']:
        raise ImportError

    if format is None:
        format = ''
    if len(format) == 0:
        format = filepath.split('.')[-1].lower()
        # TODO: we need a mapping from file extensions to formats and default encoding!
    format = format.lower()

    if encoding is None:
        encoding = ''
    if len(encoding) == 0:
        encodings = encodings_audiolab(format)
        # TODO: better default settings!
        if 'PCM_16' in encodings:
            encoding = 'PCM_16'
        else:
            encoding = encodings[0]
    encoding = encoding.lower()
    encoding = encoding.replace('pcm_', 'pcm')
    if encoding == 'float': encoding = 'float32'
    if encoding == 'double': encoding = 'float64'
        
    channels = 1
    if len(data.shape) > 1:
        channels = data.shape[1]

    af = audiolab.Sndfile(filepath, 'w', format=audiolab.Format(format, encoding),
                          channels=channels, samplerate=int(samplerate))
    af.write_frames(data)
    af.close()


def available_formats():
    """Audio file formats supported by any of the installed audio modules.

    Returns
    -------
    formats: list of strings
        List of supported file formats as strings.
    """
    audio_formats = [formats_wave, formats_ewave, formats_wavfile,
                     formats_soundfile, formats_wavefile, formats_audiolab]
    formats = set()
    for formats_func in audio_formats:
        formats |= set(formats_func())
    return sorted(list(formats))

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
    audio_encodings = [encodings_wave, encodings_ewave, encodings_wavfile,
                        encodings_soundfile, encodings_audiolab, encodings_wavefile]
    first_sndfilelib_inx = 3
    wavefile_inx = 5
    got_sndfile = False
    encodings = set()
    for e_inx, encodings_func in enumerate(audio_encodings):
        if e_inx == wavefile_inx and got_sndfile:
            continue
        encs = encodings_func(format)
        if e_inx >= first_sndfilelib_inx and len(encs) > 0:
            got_sndfile = True
        encodings |= set(encs)
    return sorted(list(encodings))

def write_audio(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data to file.

    Parameters
    ----------
    filepath: string
        Full path and name of the file to write.
    data: 1d- or 2d-array of floats
        Array with the data (first index time, second index channel,
        values within -1.0 and 1.0).
    samplerate: float
        Sampling rate of the data in Hertz.
    format: string or None
        File format.
    encoding: string or None
        Encoding of the data.

    Raises
    ------
    ValueError: `filepath` is empty string.
    IOError: Writing of the data failed.
    """

    audio_writer = [
        ['soundfile', write_soundfile],
        ['scikits.audiolab', write_audiolab],
        ['wavefile', write_wavefile],
        ['wave', write_wave],
        ['ewave', write_ewave],
        ['scipy.io.wavfile', write_wavfile]
        ]

    if len(filepath) == 0:
        raise ValueError('input argument filepath is empty string!')

    # write audio file by trying available modules:
    success = False
    for lib, write_file in audio_writer:
        if not audio_modules[lib]:
            continue
        try:
            write_file(filepath, data, samplerate, format, encoding)
            success = True
            break
        except Exception as e:
            pass
    if not success:
        raise IOError('failed to write data to file "%s"' % filepath)


if __name__ == "__main__":
    import sys
    import numpy as np

    print("Checking audiowriter module ...")
    print('')
    print('Usage:')
    print('  python audiowriter.py <filename> <encoding>')

    filepath = 'test.wav'
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    encoding = ''
    if len(sys.argv) > 2:
        encoding = sys.argv[2]

    samplerate = 44100.0
    t = np.arange(int(2*samplerate))/samplerate
    data = np.sin(2.0*np.pi*880.0*t)
        
    print('')
    print("write_audio(%s) ..." % filepath)
    write_audio(filepath, data, samplerate, encoding=encoding)

    print('done.')
    


"""
Functions for writing audio data to files.

write_audio('audio/file.wav', data, samplerate)

Writes the whole file at once with an installed audio module that
supports the requested file format.
"""
 
import warnings
from audiomodules import *


def write_wave(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the wave module from pythons standard libray.
    
    Documentation:
        https://docs.python.org/2/library/wave.html

    Args:
        filepath (string): Full path and name of the file to write.
        data (array): 1d- or 2d-array with the data (first index time, second index channel,
                      floats within -1.0 and 1.0 .
        samplerate (float): Sampling rate of the data in Hertz.
        format (string or None): File format, only 'WAV' is supported.
        encoding (string or None): Encoding of the data:
                                   'PCM_32', PCM_24', PCM_16', or 'PCM_U8'

    Exceptions:
        ImportError: if the wave module is not installed
        *: if writing of the data failed
    """
    if not audio_modules['wave']:
        raise ImportError

    if format is not None and format.upper() != 'WAV':
        warnings.warn('file format %s not supported by wave-module' % format)
        return

    wave_encodings = {'PCM_32': [4, 'i4'],
                      'PCM_16': [2, 'i2'],
                      'PCM_U8': [1, 'u1'] }
    if encoding == '':
        encoding = None
    if encoding is None:
        encoding = 'PCM_16'
    encoding = encoding.upper()
    if not encoding in wave_encodings:
        warnings.warn('file encoding %s not supported by wave-module' % format)
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
    if sampwidth == 1:
        buffer = np.array((data+1.0)*128, dtype=dtype)
    else:
        buffer = np.array(data*(2**(sampwidth*8-1)-1), dtype=dtype)
    wf.writeframes(buffer.tostring())
    wf.close()

def write_soundfile(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data using the pysoundfile module.
    
    Documentation:
        http://pysoundfile.readthedocs.org

    Args:
        filepath (string): Full path and name of the file to write.
        data (array): 1d- or 2d-array with the data (first index time, second index channel,
                      floats within -1.0 and 1.0 .
        samplerate (float): Sampling rate of the data in Hertz.
        format (string or None): File format.
        encoding (string or None): Encoding of the data.

    Exceptions:
        ImportError: if the wave module is not installed
        *: if writing of the data failed
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
    
def write_audio(filepath, data, samplerate, format=None, encoding=None):
    """
    Write audio data to file.

    Args:
        filepath (string): Full path and name of the file to write.
        data (array): 1d- or 2d-array with the data (first index time, second index channel,
                      floats within -1.0 and 1.0 .
        samplerate (float): Sampling rate of the data in Hertz.
        format (string or None): File format.
        encoding (string or None): Encoding of the data.
    """

    audio_writer = [
        ['soundfile', write_soundfile],
        ['wave', write_wave],
        ]

    if len(filepath) == 0:
        warnings.warn('input argument filepath is empty string!')

    # write audio file by trying available modules:
    for lib, write_file in audio_writer:
        if not audio_modules[lib]:
            continue
        try:
            write_file(filepath, data, samplerate, format, encoding)
            break
        except:
            warnings.warn('failed to write data to file "%s" with %s' % (filepath, lib))

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
    


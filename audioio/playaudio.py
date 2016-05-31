"""
Audio output

See also:
https://wiki.python.org/moin/Audio/
https://docs.python.org/3/library/mm.html

and ossaudiodev at the bottom of this file.
"""

import os
import numpy as np
import pyaudio


def open():
    """
    Initializes audio output.

    Returns:
        audio: a handle for subsequent calls of play() and close_audio()
    """
    oldstderr = os.dup(2)
    os.close(2)
    tmpfile = 'tmpfile.tmp'
    os.open(tmpfile, os.O_WRONLY | os.O_CREAT)
    audio = pyaudio.PyAudio()
    os.close(2)
    os.dup(oldstderr)
    os.close(oldstderr)
    os.remove(tmpfile)
    return audio


def close(audio):
    """
    Close audio output.

    Args:
        audio: the handle returned by init_audio()
    """
    audio.terminate()           

    
def play(audio, data, rate):
    """
    Play audio data.

    Args:
        audio: the handle returned by init_audio()
        data (array): the data to be played
        rate (float): the sampling rate in Hertz
    """
    # print 'play'
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=int(rate), output=True)
    rawdata = data - np.mean(data)
    rawdata /= np.max(rawdata)*2.0
    ## nr = int(np.round(0.1*rate))
    ## if len(rawdata) > 2*nr :
    ##     for k in xrange(nr) :
    ##         rawdata[k] *= float(k)/nr
    ##         rawdata[len(rawdata)-k-1] *= float(k)/nr
    # somehow more than twice as many data are needed:
    rawdata = np.hstack((rawdata, np.zeros(11*len(rawdata)/10)))
    ad = np.array(np.round(2.0**15*rawdata)).astype('i2')
    stream.write(ad)
    stream.stop_stream()
    stream.close()

    
def play_tone(audio, frequency, duration, rate):
    """
    Play a tone of a given frequency and duration.

    Args:
        audio: the handle returned by init_audio()
        frequency (float): the frequency of the tone in Hertz
        duration (float): the duration of the tone in seconds
        rate (float): the sampling rate in Hertz
    """
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=rate, output=True)
    time = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*frequency*time)
    nr = int(np.round(0.1*rate))
    for k in xrange(nr) :
        data[k] *= float(k)/float(nr)
        data[len(data)-k-1] *= float(k)/float(nr)
    ## somehow more than twice as many data are needed:
    data = np.hstack((data, np.zeros(11*len(data)/10)))
    ad = np.array(np.round(2.0**14*data)).astype('i2')
    stream.write(ad)
    stream.stop_stream()
    stream.close()

    
"""
    Alternative:
    OSS audio module:
    https://docs.python.org/2/library/ossaudiodev.html
    
import numpy as np
import ossaudiodev

rate = 44000.0
time = np.arange(0.0, 2.0, 1/rate)
data = np.sin(2.0*np.pi*440.0*time)
adata = np.array(np.int16(data*2**14), dtype=np.int16)

ad = ossaudiodev.open('w')
ad.setfmt(ossaudiodev.AFMT_S16_LE)
ad.channels(1)
ad.speed(int(rate))
ad.writeall(adata)
ad.close()
"""

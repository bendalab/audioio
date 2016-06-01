"""
Play numpy arrays as audio.

See also:
https://wiki.python.org/moin/Audio/
https://docs.python.org/3/library/mm.html

and winsound at the bottom of this file.
"""

import os
import numpy as np
import pyaudio
import ossaudiodev


handle = None


class PlayAudio(object):
    
    def __init__(self):
        self.handle = None
        self.close = self._close
        self._do_play = self._play
        self.open()

    def _close(self):
        pass

    def _play(self):
        pass

    def play(self, data, rate):
        """Play audio data.

        Args:
            data (array): the data to be played
            rate (float): the sampling rate in Hertz
        """
        if self.handle is None:
            self.open()
        self._do_play(data, rate)

    def beep(self, duration, frequency, rate=44100.0, ramp=0.1):
        """Play a tone of a given duration and frequency.

        Args:
            duration (float): the duration of the tone in seconds
            frequency (float): the frequency of the tone in Hertz
            rate (float): the sampling rate in Hertz
            ramp (float): ramp time in seconds
        """
        # sine wave:
        time = np.arange(0.0, duration, 1.0/rate)
        data = np.sin(2.0*np.pi*frequency*time)
        # ramp:
        nr = int(np.round(ramp*rate))
        for k in xrange(nr) :
            data[k] *= float(k)/float(nr)
            data[len(data)-k-1] *= float(k)/float(nr)
        # play:
        self.play(data, rate)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self
        
    def __exit__(self, type, value, tb):
        self.__del__()
        return value
        
    def open_pyaudio(self):
        """Initialize audio output via pyaudio module.

        Documentation:

        Installation:
          sudo apt-get install libportaudio2 python-pyaudio
        """
        oldstderr = os.dup(2)
        os.close(2)
        tmpfile = 'tmpfile.tmp'
        os.open(tmpfile, os.O_WRONLY | os.O_CREAT)
        self.handle = pyaudio.PyAudio()
        os.close(2)
        os.dup(oldstderr)
        os.close(oldstderr)
        os.remove(tmpfile)
        self._do_play = self._play_pyaudio
        self.close = self._close_pyaudio
    
    def _play_pyaudio(self, data, rate):
        """
        Play audio data using the pyaudio module.

        Args:
            data (array): the data to be played
            rate (float): the sampling rate in Hertz
        """
        stream = self.handle.open(format=pyaudio.paInt16, channels=1,
                                  rate=int(rate), output=True)
        rawdata = data - np.mean(data)
        rawdata /= np.max(rawdata)*2.0
        # somehow more than twice as many data are needed:
        rawdata = np.hstack((rawdata, np.zeros(11*len(rawdata)/10)))
        ad = np.array(np.round(2.0**15*rawdata)).astype('i2')
        stream.write(ad)
        stream.stop_stream()
        stream.close()

    def _close_pyaudio(self):
        """Close audio output using pyaudio module. """
        self.handle.terminate()           

        
    def open_ossaudiodev(self):
        """Initialize audio output via ossaudiodev module.

        The OSS audio module is part of the python standard library.

        Documentation:
          https://docs.python.org/2/library/ossaudiodev.html

        Installation:
          The ossaudiodev module needs an oss /dev/dsp device file.
          Enable an oss emulation via alsa by installing
          sudo apt-get install osspd
        """
        self.handle = True
        self._do_play = self._play_ossaudiodev
        self.close = self._close_ossaudiodev
    
    def _play_ossaudiodev(self, data, rate):
        """
        Play audio data using the ossaudiodev module.

        Args:
            data (array): the data to be played
            rate (float): the sampling rate in Hertz
        """
        ad = ossaudiodev.open('w')
        ad.setfmt(ossaudiodev.AFMT_S16_LE)
        ad.channels(1)
        ad.speed(int(rate))
        rawdata = data - np.mean(data)
        rawdata /= np.max(rawdata)*2.0
        rawdata = np.array(np.round(2.0**15*rawdata)).astype('i2')
        ad.writeall(rawdata)
        ad.close()

    def _close_ossaudiodev(self):
        """Close audio output using ossaudiodev module. """
        self.handle = None

    def open(self):
        """Initialize the audio module."""
        self.open_pyaudio()
        #self.open_ossaudiodev()


open_audio = PlayAudio
                

def play(data, rate):
    """Play audio data.

    Args:
        data (array): the data to be played
        rate (float): the sampling rate in Hertz
    """
    global handle
    if handle is None:
        handle = PlayAudio()
    handle.play(data, rate)

    
def beep(duration, frequency, rate=44100.0, ramp=0.1):
    """
    Play a tone of a given duration and frequency.

    Args:
        duration (float): the duration of the tone in seconds
        frequency (float): the frequency of the tone in Hertz
        rate (float): the sampling rate in Hertz
        ramp (float): ramp time in seconds
    """
    global handle
    if handle is None:
        handle = PlayAudio()
    handle.beep(duration, frequency, rate, ramp)

    
"""
    Alternative:
    OSS audio module:
    https://docs.python.org/2/library/ossaudiodev.html
    
import numpy as np

rate = 44000.0
time = np.arange(0.0, 2.0, 1/rate)
data = np.sin(2.0*np.pi*440.0*time)
adata = np.array(np.int16(data*2**14), dtype=np.int16)

"""

"""
from:
winsound: https://mail.python.org/pipermail/tutor/2012-September/091529.html

this has also information on usage of pyaudio

    import wave
    import winsound
    from cStringIO import StringIO

    def get_wave(data):
        f = StringIO()
        w = wave.open(f, 'w')
        w.setnchannels(1) # mono
        w.setsampwidth(2) # 2 bytes
        w.setframerate(48000) # samples/second
        w.writeframes(data)
        return f.getvalue()


Then play the sound like this (_untested_):


    wave_data = get_wave(data)
    windsound.PlaySound(wave_data, winsound.SND_MEMORY)
"""



if __name__ == "__main__":
    audio = PlayAudio()
    audio.beep(1.0, 440.0)
    audio.close()
    
    with open_audio() as audio:
        audio.beep(1.0, 440.0*2.0**(1.0/12.0))

    beep(1.0, 440.0*2.0**(2.0/12.0))
            

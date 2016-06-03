"""
Play numpy arrays as audio.

Globally defined functions

play(data, rate)
beep(duration, frequeny)

use a global instance of PlayAudio.

Alternatively you may use the PlayAudio class directly, like this:

with open_audio_player() as audio:
    audio.beep(1.0, 440.0)

or without context management:

audio = PlayAudio()
audio.beep(1.0, 440.0)
audio.close()


See also:
https://wiki.python.org/moin/Audio/
https://docs.python.org/3/library/mm.html
"""

import os
import time
import numpy as np
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from audiomodules import *


# default audio device handler:
handle = None


class PlayAudio(object):
    
    def __init__(self):
        """Initialize module for playing audio."""
        self.handle = None
        self.close = self._close
        self._do_play = self._play
        self.open()

    def _close(self):
        """Terminate module for playing audio."""
        pass

    def _play(self, data, rate, scale=None):
        """Default implementation of playing sound: does nothing."""
        pass

    def play(self, data, rate, scale=None):
        """Play audio data.

        Args:
            data (array): the data to be played, either 1-D array for single channel output,
                          or 2-day array with first axis time and second axis channel 
            rate (float): the sampling rate in Hertz
            scale (float): multiply data with scale before playing.
                           If None scale it to the maximum value, if 1.0 do not scale.
        """
        if self.handle is None:
            self.open()
        self._do_play(data, rate, scale)

    def beep(self, duration, frequency, amplitude=1.0, rate=44100.0, ramp=0.1):
        """Play a tone of a given duration and frequency.

        Args:
            duration (float): the duration of the tone in seconds
            frequency (float): the frequency of the tone in Hertz
            amplitude (float): the ampliude of the tone from 0.0 to 1.0
            rate (float): the sampling rate in Hertz
            ramp (float): ramp time in seconds
        """
        # sine wave:
        time = np.arange(0.0, duration, 1.0/rate)
        data = amplitude*np.sin(2.0*np.pi*frequency*time)
        # ramp:
        nr = int(np.round(ramp*rate))
        for k in range(nr) :
            data[k] *= float(k)/float(nr)
            data[len(data)-k-1] *= float(k)/float(nr)
        # play:
        self.play(data, rate, scale=1.0)

    def __del__(self):
        """Terminate the audio module."""
        self.close()

    def __enter__(self):
        return self
        
    def __exit__(self, type, value, tb):
        self.__del__()
        return value
        
    def open_pyaudio(self):
        """Initialize audio output via pyaudio module.

        Documentation:
        see also:
          https://mail.python.org/pipermail/tutor/2012-September/091529.html

        Installation:
          sudo apt-get install libportaudio2 python-pyaudio
        """
        if not audio_modules['pyaudio']:
            raise ImportError
        oldstderr = os.dup(2)
        os.close(2)
        tmpfile = 'tmpfile.tmp'
        os.open(tmpfile, os.O_WRONLY | os.O_CREAT)
        self.handle = pyaudio.PyAudio()
        self.stream = None
        os.close(2)
        os.dup(oldstderr)
        os.close(oldstderr)
        os.remove(tmpfile)
        self.index = 0
        self.data = None
        self._do_play = self._play_pyaudio
        self.close = self._close_pyaudio
        return self

    def _callback_pyaudio(self, in_data, frame_count, time_info, status):
        """Callback for pyaudio for supplying output with data."""
        if self.index < len(self.data):
            n = frame_count*self.channels
            out_data = self.data[self.index:self.index+n].tostring()
            self.index += n
            return (out_data, pyaudio.paContinue)
        else:
            return (None, pyaudio.paComplete)
    
    def _play_pyaudio(self, data, rate, scale=None):
        """Play audio data using the pyaudio module.

        Args:
            data (array): the data to be played, either 1-D array for single channel output,
                          or 2-day array with first axis time and second axis channel 
            rate (float): the sampling rate in Hertz
            scale (float): multiply data with scale before playing.
                           If None scale it to the maximum value, if 1.0 do not scale.
        """
        # data:
        self.channels = 1
        if len(data.shape) > 1:
            self.channels = data.shape[1]
        rawdata = data - np.mean(data, axis=0)
        if scale is None:
            scale = 1.0/np.max(rawdata)
        rawdata *= scale
        self.data = np.array(np.round((2.0**15-1.0)*rawdata)).ravel().astype('i2')
        self.index = 0
        # play:
        self.stream = self.handle.open(format=pyaudio.paInt16, channels=self.channels,
                                       rate=int(rate), output=True,
                                       stream_callback=self._callback_pyaudio)
        self.stream.start_stream()
        while self.stream.is_active():
            time.sleep(0.01)
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        
    def _close_pyaudio(self):
        """Terminate pyaudio module. """
        if self.stream is not None:
            self.stream.close()
        self.stream = None
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
        if not audio_modules['ossaudiodev']:
            raise ImportError
        self.handle = True
        self.osshandle = None
        self._do_play = self._play_ossaudiodev
        self.close = self._close_ossaudiodev
        return self
    
    def _play_ossaudiodev(self, data, rate, scale=None):
        """
        Play audio data using the ossaudiodev module.

        Args:
            data (array): the data to be played, either 1-D array for single channel output,
                          or 2-day array with first axis time and second axis channel 
            rate (float): the sampling rate in Hertz
            scale (float): multiply data with scale before playing.
                           If None scale it to the maximum value, if 1.0 do not scale.
        """
        channels = 1
        if len(data.shape) > 1:
            channels = data.shape[1]
        self.osshandle = ossaudiodev.open('w')
        self.osshandle.setfmt(ossaudiodev.AFMT_S16_LE)
        self.osshandle.channels(channels)
        self.osshandle.speed(int(rate))
        rawdata = data - np.mean(data, axis=0)
        if scale is None:
            scale = 1.0/np.max(rawdata)
        rawdata *= scale
        rawdata = np.array(np.round((2.0**15-1.0)*rawdata)).astype('i2')
        self.osshandle.writeall(rawdata)
        self.osshandle.close()
        self.osshandle = None

    def _close_ossaudiodev(self):
        """Close audio output using ossaudiodev module. """
        self.handle = None
        if self.osshandle is not None:
            self.osshandle.close()
        self.osshandle = None

        
    def open_winsound(self):
        """Initialize audio output via winsound module.

        The winsound module is part of the python standard library.

        Documentation:
          https://mail.python.org/pipermail/tutor/2012-September/091529.html
        """
        if not audio_modules['winsound'] or not not audio_modules['wave']:
            raise ImportError
        self.handle = True
        self._do_play = self._play_winsound
        self.close = self._close_winsound
        return self
    
    def _play_winsound(self, data, rate, scale=None):
        """
        Play audio data using the winsound module.

        Args:
            data (array): the data to be played, either 1-D array for single channel output,
                          or 2-day array with first axis time and second axis channel 
            rate (float): the sampling rate in Hertz
            scale (float): multiply data with scale before playing.
                           If None scale it to the maximum value, if 1.0 do not scale.
        """
        channels = 1
        if len(data.shape) > 1:
            channels = data.shape[1]
        rawdata = data - np.mean(data, axis=0)
        if scale is None:
            scale = 1.0/np.max(rawdata)
        rawdata *= scale
        rawdata = np.array(np.round((2.0**15-1.0)*rawdata)).astype('i2')
        # write data as wav file to memory:
        # TODO: check this code!!!
        f = StringIO()
        w = wave.open(f, 'w')
        w.setnchannels(channels)
        w.setsampwidth(2) # 2 bytes
        w.setframerate(int(rate))
        # TODO: how does this handle 2-d arrays?
        w.writeframes(rawdata)
        # play file:
        winsound.PlaySound(f.getvalue(), winsound.SND_MEMORY)
        
    def _close_winsound(self):
        """Close audio output using winsound module. """
        self.handle = None


    def open(self):
        """Initialize the audio module with the best module available."""
        # list of implemented play functions:
        audio_open = [
            ['pyaudio', self.open_pyaudio],
            ['ossaudiodev', self.open_ossaudiodev],
            ['winsound', self.open_winsound]
            ]
        # open audio device by trying various modules:
        for lib, open_device in audio_open:
            if not audio_modules[lib]:
                continue
            try:
                open_device()
                break
            except:
                warnings.warn('failed to open audio module %s' % lib)
        return self


open_audio_player = PlayAudio
                

def play(data, rate, scale=None):
    """Play audio data.

    Create an PlayAudio instance on the globale variable handle.

    Args:
        data (array): the data to be played, either 1-D array for single channel output,
                      or 2-day array with first axis time and second axis channel 
        rate (float): the sampling rate in Hertz
    """
    global handle
    if handle is None:
        handle = PlayAudio()
    handle.play(data, rate, scale)

    
def beep(duration, frequency, amplitude=1.0, rate=44100.0, ramp=0.1):
    """
    Play a tone of a given duration and frequency.

    Create an PlayAudio instance on the globale variable handle.

    Args:
        duration (float): the duration of the tone in seconds
        frequency (float): the frequency of the tone in Hertz
        amplitude (float): the ampliude of the tone from 0.0 to 1.0
        rate (float): the sampling rate in Hertz
        ramp (float): ramp time in seconds
    """
    global handle
    if handle is None:
        handle = PlayAudio()
    handle.beep(duration, frequency, amplitude, rate, ramp)

    
if __name__ == "__main__":

    print('play mono beep 1')
    audio = PlayAudio()
    audio.beep(1.0, 440.0, 0.25)
    audio.close()
    
    print('play mono beep 2')
    with open_audio_player() as audio:
        audio.beep(1.0, 440.0*2.0**(1.0/12.0), 0.75)

    print('play mono beep 3')
    beep(1.0, 440.0*2.0**(2.0/12.0))
            
    print('play stereo beep')
    duration = 1.0
    rate = 44100.0
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.zeros((len(t),2))
    data[:,0] = np.sin(2.0*np.pi*440.0*t)
    data[:,1] = 0.25*np.sin(2.0*np.pi*700.0*t)
    play(data, rate)

"""
Play numpy arrays as audio.

The globally defined functions

play(data, rate)
beep(duration, frequeny)

use a global instance of the PlayAudio class.

Alternatively you may use the PlayAudio class directly, like this:

with open_audio_player() as audio:
    audio.beep(1.0, 440.0)

or without context management:

audio = PlayAudio()
audio.beep(1.0, 'a4')
audio.close()

The note2freq() function converts a musical note, like 'f#4',
to the appropriate frequency.
The beep() functions also accept notes for the frequency argument,
and use note2freq() to get the right frequency.

Data can be multiplied with a squared-sine for fading in and out with
fade_in(), fade_out(), and fade().

See also:
https://wiki.python.org/moin/Audio/
https://docs.python.org/3/library/mm.html
"""

import os
import warnings
import time
import numpy as np
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from multiprocessing import Process
from audiomodules import *


# default audio device handler:
handle = None


def note2freq(note, a4freq=440.0):
    """Converts textual note to the corresponding frequency.

    Args:
      note (string): a musical note like 'a4', 'f#3', 'eb5'.
                     The first character is the note, it can be
                     'a', 'b', 'c', 'd', 'e', 'f', or 'g'.
                     The optional second character is either a 'b'
                     or a '#' to decrease or increase by half a note.
                     The last character specifies the octave.
                     'a4' is defined by a4freq.
      a4freq (float): the frequency of a4.

    Returns:
      freq (float): the frequency of the note in Hertz.
    """
    freq = a4freq
    tone = 0
    octave = 4
    if not isinstance(note, str) or len(note) == 0:
        warnings.warn('no note specified')
        return freq
    if note[0] < 'a' or note[0] > 'g':
        warnings.warn('invalid note %s' % note[0])
        return freq
    # note:
    index = 0
    tonemap = [0, 2, 3, 5, 7, 8, 10]
    tone = tonemap[ord(note[index]) - ord('a')]
    index += 1
    # flat or sharp:
    if index < len(note):
        if note[index] == 'b':
            tone -= 1
            index += 1
        elif note[index] == '#':
            tone += 1
            index += 1
    # octave:
    if index < len(note) and note[index] >= '0' and note[index] <= '9':
        octave = ord(note[index]) - ord('0')
    if tone >= 3:
        octave -= 1
    tone += 12*(octave-4)
    # frequency:
    freq = a4freq * 2.0**(tone/12.0)
    return freq


def fade_in(data, rate, fadetime):
    """
    Fade the signal in.

    The first fadetime seconds of the data are multiplied with a squared sine.
    
    Args:
      data (array): the data to be faded in, either 1-D array for single channel output,
                    or 2-day array with first axis time and second axis channel 
      rate (float): the sampling rate in Hertz
      fadetime (float): time for fading in and out in seconds
    """
    nr = int(np.round(fadetime*rate))
    for k in range(nr) :
        data[k] *= np.sin(0.5*np.pi*float(k)/float(nr))**2.0

        
def fade_out(data, rate, fadetime):
    """
    Fade the signal out.

    The last fadetime seconds of the data are multiplied with a squared sine.
    
    Args:
      data (array): the data to be faded out, either 1-D array for single channel output,
                    or 2-day array with first axis time and second axis channel 
      rate (float): the sampling rate in Hertz
      fadetime (float): time for fading in and out in seconds
    """
    nr = int(np.round(fadetime*rate))
    for k in range(nr) :
        data[len(data)-k-1] *= np.sin(0.5*np.pi*float(k)/float(nr))**2.0


def fade(data, rate, fadetime):
    """
    Fade the signal in and out.

    The first and last fadetime seconds of the data are multiplied with a squared sine.
        
    Args:
      data (array): the data to be faded, either 1-D array for single channel output,
                    or 2-day array with first axis time and second axis channel 
      rate (float): the sampling rate in Hertz
      fadetime (float): time for fading in and out in seconds
    """
    fade_in(data, rate, fadetime)
    fade_out(data, rate, fadetime)


class PlayAudio(object):
    
    def __init__(self):
        """Initialize module for playing audio."""
        self.handle = None
        self._do_play = self._play
        self.close = self._close
        self.stop = self._stop
        self.open()

    def _close(self):
        """Terminate module for playing audio."""
        pass

    def _stop(self):
        """Stop playing."""
        pass

    def _play(self, blocking=True):
        """Default implementation of playing a sound: does nothing."""
        pass

    def play(self, data, rate, scale=None, blocking=True):
        """Play audio data.

        Args:
            data (array): the data to be played, either 1-D array for single channel output,
                          or 2-day array with first axis time and second axis channel 
            rate (float): the sampling rate in Hertz
            scale (float): multiply data with scale before playing.
                           If None scale it to the maximum value, if 1.0 do not scale.
            blocking (boolean): if False do not block. 
        """
        if self.handle is None:
            self.open()
        else:
            self.stop()
        self.rate = rate
        self.channels = 1
        if len(data.shape) > 1:
            self.channels = data.shape[1]
        # convert data:
        rawdata = data - np.mean(data, axis=0)
        if scale is None:
            maxd = np.abs(np.max(rawdata))
            mind = np.abs(np.min(rawdata))
            scale = 1.0/max((mind, maxd))
        rawdata *= scale
        self.data = np.array(rawdata*(2**15-1), dtype='i2')
        self.index = 0
        self._do_play(blocking)

    def beep(self, duration, frequency, amplitude=1.0, rate=44100.0,
             fadetime=0.05, blocking=True):
        """Play a pure tone of a given duration and frequency.

        Args:
            duration (float): the duration of the tone in seconds
            frequency (float): the frequency of the tone in Hertz
            frequency (string): a musical note like 'f#5'.
                                See note2freq() for details
            amplitude (float): the ampliude of the tone from 0.0 to 1.0
            rate (float): the sampling rate in Hertz
            fadetime (float): time for fading in and out in seconds
            blocking (boolean): if False do not block. 
        """
        # frequency
        if isinstance(frequency, str):
            frequency = note2freq(frequency)
        # sine wave:
        time = np.arange(0.0, duration, 1.0/rate)
        data = amplitude*np.sin(2.0*np.pi*frequency*time)
        # fade in and out:
        fade(data, rate, fadetime)
        ## final click for testing:
        #data = np.hstack((data, np.sin(2.0*np.pi*1000.0*time[0:int(np.ceil(4.0*rate/1000.0))])))
        # play:
        self.play(data, rate, scale=1.0, blocking=blocking)

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
        self.stop = self._stop_pyaudio
        return self

    def _callback_pyaudio(self, in_data, frames, time_info, status):
        """Callback for pyaudio for supplying output with data."""
        flag = pyaudio.paContinue
        if not self.run:
            flag = pyaudio.paComplete
        if self.index < len(self.data):
            out_data = self.data[self.index:self.index+frames]
            self.index += len(out_data)
            # zero padding:
            if len(out_data) < frames:
                if len(self.data.shape) > 1:
                    out_data = np.vstack((out_data,
                      np.zeros((frames-len(out_data), self.channels), dtype='i2')))
                else:
                    out_data = np.hstack((out_data, np.zeros(frames-len(out_data), dtype='i2')))
            return (out_data, flag)
        else:
            # we need to play more to make sure everything is played!
            # This is because of an ALSA bug and might be fixed in newer versions,
            # see http://music.columbia.edu/pipermail/portaudio/2012-May/013959.html
            out_data = np.zeros(frames*self.channels, dtype='i2')
            self.index += frames
            latency = int(self.stream.get_output_latency()*self.rate)
            if self.index >= len(self.data) + 2*latency:
                flag = pyaudio.paComplete
            return (out_data, flag)

    def _stop_pyaudio(self):
        if self.stream is not None:
            if self.stream.is_active():
                # fade out:
                fadetime = 0.1
                nr = int(np.round(fadetime*self.rate))
                index = self.index+nr
                if nr > len(self.data) - index:
                    nr = len(self.data) - index
                else:
                    self.data[index+nr:] = 0
                if nr > 0:
                    for k in range(nr) :
                        self.data[index+(nr-k-1)] *= np.sin(0.5*np.pi*float(k)/float(nr))**2.0
                time.sleep(2*fadetime)
            if self.stream.is_active():
                self.run = False
                while self.stream.is_active():
                    time.sleep(0.01)
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def _play_pyaudio(self, blocking=True):
        """Play audio data using the pyaudio module.

        Args:
            blocking (boolean): if False do not block. 
        """
        # play:
        self.stream = self.handle.open(format=pyaudio.paInt16, channels=self.channels,
                                       rate=int(self.rate), output=True,
                                       stream_callback=self._callback_pyaudio)
        self.run = True
        self.stream.start_stream()
        if blocking:
            while self.stream.is_active():
                time.sleep(0.01)
            self.run = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
    def _close_pyaudio(self):
        """Terminate pyaudio module."""
        print('close')
        self._stop_pyaudio()
        self.handle.terminate()           
        self._do_play = self._play
        self.stop = self._stop

        
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
        self.run = False
        self.play_thread = None
        self._do_play = self._play_ossaudiodev
        self.close = self._close_ossaudiodev
        self.stop = self._stop_ossaudiodev
        return self

    def _stop_ossaudiodev(self):
        if self.osshandle is not None:
            self.run = False
            self.osshandle.reset()
            if self.play_thread is not None:
                if self.play_thread.is_alive():
                    self.play_thread.join()
                self.play_thread = None
            self.osshandle.close()
            self.osshandle = None

    def _run_play_ossaudiodev(self):
        self.osshandle.writeall(self.data)
        if self.run:
            time.sleep(0.5)
            self.osshandle.close()
            self.osshandle = None
            self.run = False
        
    def _play_ossaudiodev(self, blocking=True):
        """
        Play audio data using the ossaudiodev module.

        Args:
            blocking (boolean): if False do not block. 
        """
        self.osshandle = ossaudiodev.open('w')
        self.osshandle.setfmt(ossaudiodev.AFMT_S16_LE)
        self.osshandle.channels(self.channels)
        self.osshandle.speed(int(self.rate))
        if blocking:
            self.run = True
            self.osshandle.writeall(self.data)
            time.sleep(0.5)
            self.osshandle.close()
            self.run = False
            self.osshandle = None
        else:
            self.play_thread = Process(target=self._run_play_ossaudiodev)
            self.run = True
            self.play_thread.start()

    def _close_ossaudiodev(self):
        """Close audio output using ossaudiodev module. """
        self._stop_ossaudiodev()
        self.handle = None
        self._do_play = self._play
        self.stop = self._stop

        
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
        self.stop = self._stop
        return self
    
    def _play_winsound(self, blocking=True):
        """
        Play audio data using the winsound module.

        Args:
            blocking (boolean): ignored. Non-blocking is not supported.
        """
        # write data as wav file to memory:
        # TODO: check this code!!!
        f = StringIO()
        w = wave.open(f, 'w')
        w.setnchannels(self.channels)
        w.setsampwidth(2) # 2 byte integers
        w.setframerate(int(self.rate))
        w.setnframes(len(self.data))
        # TODO: how does this handle 2-d arrays?
        w.writeframesraw(self.data.tostring())
        w.close() # TODO: close here or after PlaySound?
        # play file:
        winsound.PlaySound(f.getvalue(), winsound.SND_MEMORY)
        
    def _close_winsound(self):
        """Close audio output using winsound module. """
        self.handle = None
        self._do_play = self._play
        self.stop = self._stop


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
                

def play(data, rate, scale=None, blocking=True):
    """Play audio data.

    Create an PlayAudio instance on the globale variable handle.

    Args:
        data (array): the data to be played, either 1-D array for single channel output,
                      or 2-day array with first axis time and second axis channel 
        rate (float): the sampling rate in Hertz
        blocking (boolean): if False do not block. 
    """
    global handle
    if handle is None:
        handle = PlayAudio()
    handle.play(data, rate, scale, blocking)

    
def beep(duration, frequency, amplitude=1.0, rate=44100.0,
         fadetime=0.05, blocking=True):
    """
    Play a tone of a given duration and frequency.

    Create an PlayAudio instance on the globale variable handle.

    Args:
        duration (float): the duration of the tone in seconds
        frequency (float): the frequency of the tone in Hertz
        frequency (string): a musical note like 'f#5'.
                            See note2freq() for details
        amplitude (float): the ampliude of the tone from 0.0 to 1.0
        rate (float): the sampling rate in Hertz
        fadetime (float): time for fading in and out in seconds
        blocking (boolean): if False do not block. 
    """
    global handle
    if handle is None:
        handle = PlayAudio()
    handle.beep(duration, frequency, amplitude, rate, fadetime, blocking)

    
if __name__ == "__main__":

    disable_module('pyaudio')
    print('play mono beep 1')
    audio = PlayAudio()
    audio.beep(1.0, 440.0)
    audio.close()
    
    print('play mono beep 2')
    with open_audio_player() as audio:
        audio.beep(1.0, 'b4', 0.75, blocking=False)
        print('  done')
        time.sleep(0.3)
    time.sleep(0.5)

    print('play mono beep 3')
    beep(1.0, 'c5', 0.25, blocking=False)
    print('  done')
    time.sleep(0.3)
            
    print('play stereo beep')
    duration = 1.0
    rate = 44100.0
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.zeros((len(t),2))
    data[:,0] = np.sin(2.0*np.pi*note2freq('a4')*t)
    data[:,1] = 0.25*np.sin(2.0*np.pi*note2freq('e5')*t)
    fade(data, rate, 0.1)
    play(data, rate)

    print('play notes')
    o = 3
    for oo in range(3):
        for t in range(7):
            if t == 2:
                o += 1
            tone = '%s%d' % (chr(ord('a')+t), o)
            print('%s %6.1f Hz' % (tone, note2freq(tone)))
            beep(0.5, tone)
    

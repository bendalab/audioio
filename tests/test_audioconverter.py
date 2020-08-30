from nose.tools import assert_equal, assert_greater, assert_greater_equal, assert_less, assert_raises, nottest
import os
import numpy as np
import audioio.audiowriter as aw
import audioio.audioconverter as ac


def write_audio_file(filename):
    samplerate = 44100.0
    duration = 10.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    encoding = 'PCM_16'
    aw.write_wave(filename, data, samplerate, encoding=encoding)


def test_main():
    filename = 'test.wav'
    destfile = 'test2'
    write_audio_file(filename)
    assert_raises(SystemExit, ac.main, ['-h'])
    assert_raises(SystemExit, ac.main, ['--help'])
    assert_raises(SystemExit, ac.main, ['--version'])
    ac.main(['-l'])
    ac.main(['-f', 'wav', '-l'])
    ac.main(['-f', 'ogg', '-l'])
    ac.main(['-f', 'wav', '-o', destfile, filename])
    ac.main(['-f', 'wav', '-e', 'float', '-o', destfile, filename])
    ac.main(['-f', 'ogg', '-e', 'vorbis', '-o', destfile, filename])
    ac.main(['-e', 'float', '-o', destfile + '.wav', filename])
    os.remove(filename)
    os.remove(destfile+'.wav')
    os.remove(destfile+'.ogg')

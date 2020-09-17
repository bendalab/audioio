from nose.tools import assert_equal, assert_greater, assert_greater_equal, assert_less, assert_raises
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
    ac.main(['-f', 'wav', '-o', destfile, filename])
    assert_raises(SystemExit, ac.main, ['-f', 'xxx', '-o', destfile, filename])
    ac.main(['-o', destfile, filename])
    ac.main(['-f', 'wav', '-o', destfile, filename])
    ac.main(['-e', 'PCM_32', '-o', destfile + '.wav', filename])
    ac.main(['-f', 'wav', '-e', 'PCM_32', '-o', destfile, '-v', filename])
    if 'FLOAT' in aw.available_encodings('WAV'):
        ac.main(['-f', 'wav', '-e', 'float', '-o', destfile, filename])
        ac.main(['-e', 'float', '-o', destfile + '.wav', filename])
    if 'OGG' in aw.available_formats():
        ac.main(['-f', 'ogg', '-l'])
        ac.main(['-f', 'ogg', '-e', 'vorbis', '-o', destfile, filename])
        ac.main(['-f', 'ogg', '-e', 'vorbis', filename])
        os.remove(destfile+'.ogg')
    assert_raises(SystemExit, ac.main, [filename])
    os.remove(filename)
    os.remove(destfile+'.wav')

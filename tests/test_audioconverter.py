from nose.tools import assert_equal, assert_greater, assert_greater_equal, assert_less, assert_raises
import os
import numpy as np
import audioio.audioloader as al
import audioio.audiowriter as aw
import audioio.audioconverter as ac


def write_audio_file(filename, channels=2, samplerate = 44100):
    duration = 10.0
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    encoding = 'PCM_16'
    aw.write_wave(filename, data, samplerate, encoding=encoding)


def test_main():
    filename = 'test.wav'
    filename1 = 'test1.wav'
    destfile = 'test2'
    write_audio_file(filename)
    assert_raises(SystemExit, ac.main, '-h')
    assert_raises(SystemExit, ac.main, '--help')
    assert_raises(SystemExit, ac.main, '--version')
    ac.main('-l')
    ac.main('-f', 'wav', '-l')
    ac.main('-f', 'wav', '-o', destfile, filename)
    assert_raises(SystemExit, ac.main, 'prog', '-f', 'xxx', '-o', destfile, filename)
    ac.main('-o', destfile, filename)
    ac.main('-f', 'wav', '-o', destfile, filename)
    ac.main('-u', '-f', 'wav', '-o', destfile, filename)
    ac.main('-u', '0.8', '-f', 'wav', '-o', destfile, filename)
    ac.main('-U', '0.8', '-f', 'wav', '-o', destfile, filename)
    ac.main('-e', 'PCM_32', '-o', destfile + '.wav', filename)
    ac.main('-f', 'wav', '-e', 'PCM_32', '-o', destfile, '-v', filename)
    if 'FLOAT' in aw.available_encodings('WAV'):
        ac.main('-f', 'wav', '-e', 'float', '-o', destfile, filename)
        ac.main('-e', 'float', '-o', destfile + '.wav', filename)
    if 'OGG' in aw.available_formats():
        ac.main('-f', 'ogg', '-l')
        ac.main('-f', 'ogg', '-e', 'vorbis', '-o', destfile, filename)
        ac.main('-f', 'ogg', '-e', 'vorbis', filename)
        os.remove(filename.replace('.wav', '.ogg'))
        os.remove(destfile+'.ogg')
    assert_raises(SystemExit, ac.main, '-f', 'xyz123', filename)
    assert_raises(SystemExit, ac.main, filename)
    assert_raises(SystemExit, ac.main)
    write_audio_file(filename1, 4)
    ac.main('-c', '1', '-o', destfile, filename1)
    ac.main('-c', '0-2', '-o', destfile, filename1)
    ac.main('-c', '0-1,3', '-o', destfile, filename1)
    assert_raises(SystemExit, ac.main, '-o', destfile, filename, filename1)
    write_audio_file(filename1, 2, 20000)
    assert_raises(SystemExit, ac.main, '-o', destfile, filename, filename1)
    write_audio_file(filename1)
    ac.main('-o', destfile, filename, filename1)
    xdata, xrate = al.load_audio(filename)
    n = len(xdata)
    xdata, xrate = al.load_audio(filename1)
    n += len(xdata)
    xdata, xrate = al.load_audio(destfile + '.wav')
    assert_equal(len(xdata), n, 'len of merged files')
    os.remove(filename)
    os.remove(filename1)
    os.remove(destfile+'.wav')

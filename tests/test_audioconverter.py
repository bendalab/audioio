import pytest
import os
import shutil
import numpy as np
import audioio.audioloader as al
import audioio.audiowriter as aw
import audioio.audioconverter as ac


def write_audio_file(filename, channels=2, rate = 44100):
    duration = 10.0
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    encoding = 'PCM_16'
    md = dict(Amplifier='Teensy_Amp', Num=42)
    aw.write_wave(filename, data, rate, md, encoding=encoding)


def test_main():
    filename = 'test.wav'
    filename1 = 'test1.wav'
    destfile = 'test2'
    destpath = 'test3'
    os.mkdir(destpath)
    write_audio_file(filename)
    with pytest.raises(SystemExit):
        ac.main()
    with pytest.raises(SystemExit):
        ac.main('-h')
    with pytest.raises(SystemExit):
        ac.main('--help')
    with pytest.raises(SystemExit):
        ac.main('--version')
    ac.main('-l')
    ac.main('-f', 'wav', '-l')
    ac.main('-f', 'wav', '-o', destfile, filename)
    with pytest.raises(SystemExit):
        ac.main('')
    with pytest.raises(SystemExit):
        ac.main('-f', 'xxx', '-l')
    with pytest.raises(SystemExit):
        ac.main('-f', 'xxx', '-o', destfile, filename)
    with pytest.raises(SystemExit):
        ac.main('-o', 'test.xxx', filename)
    with pytest.raises(SystemExit):
        ac.main('-f', 'xyz123', filename)
    with pytest.raises(SystemExit):
        ac.main(filename)
    with pytest.raises(SystemExit):
        ac.main('-o', filename, filename)
    ac.main('-o', destfile + '.wav', filename)
    ac.main('-f', 'wav', '-o', destfile, filename)
    ac.main('-u', '-f', 'wav', '-o', destfile, filename)
    ac.main('-u', '0.8', '-f', 'wav', '-o', destfile, filename)
    ac.main('-U', '0.8', '-f', 'wav', '-o', destfile, filename)
    ac.main('-s', '0.1', '-f', 'wav', '-o', destfile, filename)
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
    ac.main('-a', 'INFO.Artist=John Doe', '-o', destfile + '.wav', filename)
    ac.main('-r', 'Amplifier', '-o', destfile + '.wav', filename)
    write_audio_file(filename)
    write_audio_file(filename1, 4)
    ac.main('-c', '1', '-o', destfile + '.wav', filename1)
    ac.main('-c', '0-2', '-o', destfile + '.wav', filename1)
    ac.main('-c', '0-1,3', '-o', destfile + '.wav', filename1)
    with pytest.raises(SystemExit):
        ac.main('-o', destfile + '.wav', filename, filename1)
    write_audio_file(filename1, 2, 20000)
    with pytest.raises(SystemExit):
        ac.main('-o', destfile + '.wav', filename, filename1)
    write_audio_file(filename1)
    with pytest.raises(SystemExit):
        ac.main('-n', '1', '-o', destfile, filename, filename1)
    ac.main('-n', '1', '-f', 'wav', '-o', destfile, filename, filename1)
    shutil.rmtree(destfile)
    ac.main('-vv', '-o', destfile + '.wav', filename, filename1)
    xdata, xrate = al.load_audio(filename)
    n = len(xdata)
    xdata, xrate = al.load_audio(filename1)
    n += len(xdata)
    xdata, xrate = al.load_audio(destfile + '.wav')
    assert len(xdata) == n, 'len of merged files'
    md1 = al.metadata(filename)
    md1['CodingHistory'] = 'A=PCM,F=44100,W=16,M=stereo,T=test.wav\nA=PCM,F=44100,W=16,M=stereo,T=test2.wav'
    md2 = al.metadata(destfile + '.wav')
    md2['CodingHistory'] = md2['CodingHistory'].replace('\r\n', '\n')
    assert md1 == md2, 'metadata of merged files'
    ac.main('-d', '4', '-o', destfile + '.wav', filename)
    xdata, xrate = al.load_audio(filename)
    ydata, yrate = al.load_audio(destfile + '.wav')
    assert len(ydata) == len(xdata)//4, 'decimation data'
    assert yrate*4 == xrate, 'decimation rate'
    ac.main('-o', 'test{Num}.wav', filename)
    os.remove('test42.wav')
    os.remove(filename)
    os.remove(filename1)
    os.remove(destfile+'.wav')
    shutil.rmtree(destpath)

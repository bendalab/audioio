from nose.tools import assert_true, assert_false, assert_equal, assert_raises
import os
import numpy as np
import audioio.audiowriter as aw
import audioio.audioloader as al
import audioio.audiomodules as am


def write_audio_file(filename, duration=20.0):
    samplerate = 44100.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    encoding = 'PCM_16'
    aw.write_wave(filename, data, samplerate, encoding=encoding)


def test_single_frame():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 20.0)
    tolerance = 2.0**(-15)
    ntests = 500
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print('')
        print('check single frame access for module %s ...' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            assert_false(np.any(np.abs(full_data[0] - data[0]) > tolerance), 'first frame access failed with %s module' % lib)
            assert_false(np.any(np.abs(full_data[-1] - data[-1]) > tolerance), 'last frame access failed with %s module' % lib)
            def access_end(n):
                x = data[len(data)+n]
            for n in range(10):
                assert_raises(IndexError, access_end, n)
            failed = -1
            for inx in np.random.randint(-len(data), len(data), ntests):
                if np.any(np.abs(full_data[inx] - data[inx]) > tolerance):
                    failed = inx
                    break
            assert_true(failed < 0, 'single random frame access failed at index %d with %s module' % (failed, lib))
    os.remove(filename)
    am.enable_module()


def test_slice():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 20.0)
    tolerance = 2.0**(-15)
    ntests = 100
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print('')
        print('random frame slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for n in range(5):
                assert_false(np.any(np.abs(data[:n]-full_data[:n]) > tolerance), 'zero slice up to %d does not match' % n)
            for n in range(1, 5):
                assert_false(np.any(np.abs(data[:50:n]-full_data[:50:n]) > tolerance), 'step slice with step=%d does not match' % n)
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.samplerate)
                failed = -1
                for inx in np.random.randint(0, len(data)-nframes, ntests):
                    if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > tolerance):
                        failed = inx
                        break
                assert_true(failed < 0, 'random frame slice access failed at index %d with nframes=%d and %s module' % (failed, nframes, lib))
    os.remove(filename)
    am.enable_module()


def test_forward():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 40.0)
    tolerance = 2.0**(-15)
    nsteps = 200
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print('')
        print('forward slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.samplerate)
                step = int(len(data)/nsteps)
                failed = -1
                for inx in range(0, len(data)-nframes, step):
                    if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > tolerance):
                        failed = inx
                        break
                assert_true(failed < 0, 'frame slice access forward failed at index %d with nframes=%d and %s module' % (failed, nframes, lib))
    os.remove(filename)
    am.enable_module()


def test_backward():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 40.0)
    tolerance = 2.0**(-15)
    nsteps = 200
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print('')
        print('backward slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.samplerate)
                step = int(len(data)/nsteps)
                failed = -1
                print('  check backward slice access...')
                for inx in range(len(data)-nframes, 0, -step):
                    if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > tolerance):
                        failed = inx
                        break
                assert_true(failed < 0, 'frame slice access backward failed at index %d with nframes=%d and %s module' % (failed, nframes, lib))
    os.remove(filename)
    am.enable_module()


def test_negative():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 40.0)
    tolerance = 2.0**(-15)
    nsteps = 200
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print('')
        print('negative slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.samplerate)
                step = int(len(data)/nsteps)
                failed = -1
                for inx in range(0, len(data)-nframes, step):
                    if np.any(np.abs(full_data[-inx:-inx+nframes] - data[-inx:-inx+nframes]) > tolerance):
                        failed = -inx
                        break
                assert_true(failed < 0, 'frame slice access backward with negative indices failed at index %d with nframes=%d and %s module' % (failed, nframes, lib))
    os.remove(filename)
    am.enable_module()


def test_multiple():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 20.0)
    tolerance = 2.0**(-15)
    ntests = 100
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print('')
        print('multiple indices access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0, 20.0]:
                nframes = int(time*data.samplerate)
                if nframes > 0.9*len(data):
                    nframes = len(data)
                for n in [1, 2, 4, 8, 16]:     # number of indices
                    offs = 0
                    if len(data) > nframes:
                        offs = np.random.randint(len(data)-nframes)
                    failed = -1
                    for k in range(ntests):
                        inx = np.random.randint(0, nframes, n) + offs
                        if np.any(np.abs(full_data[inx] - data[inx]) > tolerance):
                            failed = 1
                            break
                    assert_equal(failed, -1, ('multiple random frame access failed with %s module at indices ' % lib) + str(inx))
    os.remove(filename)
    am.enable_module()


def test_modules():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 1.0)
    for lib, load_file in al.audio_loader_funcs:
        print(lib)
        am.disable_module(lib)
        assert_raises(ImportError, load_file, filename)
        data = al.AudioLoader(verbose=4)
        load_funcs = {
            'soundfile': data.open_soundfile,
            'wavefile': data.open_wavefile,
            'audioread': data.open_audioread,
            'wave': data.open_wave,
            'ewave': data.open_ewave,
            }
        if lib not in load_funcs:
            continue
        assert_raises(ImportError, load_funcs[lib], filename, 10.0, 2.0)
        if am.select_module(lib):
            # check double opening:
            load_funcs[lib](filename)
            load_funcs[lib](filename)
            data.close()
    os.remove(filename)
    am.enable_module()
        

def test_audio_files():
    am.enable_module()
    assert_raises(ValueError, al.load_audio, '')
    assert_raises(FileNotFoundError, al.load_audio, 'xxx.wav')
    assert_raises(ValueError, al.AudioLoader, '')
    assert_raises(FileNotFoundError, al.AudioLoader, 'xxx.wav')
    filename = 'test.wav'
    df = open(filename, 'w')
    df.close()
    assert_raises(EOFError, al.load_audio, filename)
    assert_raises(EOFError, al.AudioLoader, filename)
    os.remove(filename)
    write_audio_file(filename)
    am.disable_module()
    assert_raises(IOError, al.load_audio, filename)
    assert_raises(IOError, al.AudioLoader, filename)
    os.remove(filename)
    am.enable_module()

    
def test_iter():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 1.0)
    full_data, rate = al.load_audio(filename)
    tolerance = 2.0**(-15)
    with al.AudioLoader(filename, 0.2) as data:
        for k, x in enumerate(data):
            assert_false(np.any(np.abs(x-full_data[k]) > tolerance), 'iteration %d does not match' % k)

        
def test_blocks():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename)
    full_data, rate = al.load_audio(filename)
    tolerance = 2.0**(-15)
    for n in [5000, len(full_data)+100]:
        read_data = []
        with al.AudioLoader(filename) as data:
            for x in al.blocks(data, n, 10):
                read_data.append(x[:-10].copy())
        read_data = np.vstack(read_data)
        assert_equal(full_data.shape[0]-10, read_data.shape[0], 'len of blocked data differ from input data')
        assert_equal(full_data.shape[1], read_data.shape[1], 'columns of blocked data differ from input data')
        assert_false(np.any(np.abs(full_data[:-10] - read_data) > tolerance), 'blocks() failed')
        read_data = []
        with al.AudioLoader(filename) as data:
            for x in data.blocks(n, 10):
                read_data.append(x[:-10].copy())
        read_data = np.vstack(read_data)
        assert_equal(full_data.shape[0]-10, read_data.shape[0], 'len of blocked data differ from input data')
        assert_equal(full_data.shape[1], read_data.shape[1], 'columns of blocked data differ from input data')
        assert_false(np.any(np.abs(full_data[:-10] - read_data) > tolerance), 'blocks() failed')

    def wrong_blocks(data):
        for x in al.blocks(data, 10, 20):
            pass
    assert_raises(ValueError, wrong_blocks, full_data)


def test_unwrap():
    samplerate = 44100.0
    t = np.arange(0.0, 1.0, 1.0/samplerate)
    data = np.sin(2.0*np.pi*880.0*t) * t
    al.unwrap(data)
    data = data.reshape((-1, 1))
    al.unwrap(data)
    data = data.reshape((-1, 2))
    al.unwrap(data)


def test_demo():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, duration=5.0)
    al.demo(filename, False)
    os.remove(filename)


def test_main():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, duration=5.0)
    al.main('-h')
    al.main(filename)
    al.main('-m', 'wave', filename)
    os.remove(filename)

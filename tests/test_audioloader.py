import pytest
import numpy as np

from pathlib import Path
from datetime import datetime, timedelta

import audioio.audiowriter as aw
import audioio.bufferedarray as ba
import audioio.audioloader as al
import audioio.audiomodules as am


def write_audio_file(filename, duration=20.0):
    rate = 44100.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    encoding = 'PCM_16'
    aw.write_wave(filename, data, rate, encoding=encoding)


def write_audio_files(filename, duration=60.0, nfiles=4):
    rate = 44100.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    encoding = 'PCM_16'
    m = 1000
    locs = np.zeros((m, 2), dtype=int)
    locs[:, 0] = np.sort(np.random.randint(0, len(data), m))
    locs[:, 1] = np.random.randint(0, 100, m)
    labels = np.zeros((len(locs), 2), dtype=np.object_)
    for i in range(len(labels)):
        labels[i,0] = chr(ord('a') + i % 26)
        labels[i,1] = chr(ord('A') + i % 26)*5
    start_time = datetime.now()
    file_paths = []
    n = len(data) // nfiles
    for k in range(nfiles):
        i0 = k*n
        i1 = (k+1)*n
        md = dict(DateTimeOriginal=start_time.isoformat())
        mlocs = locs[(locs[:,0] >= i0) & (locs[:,0] < i1),:]
        mlocs[:,0] -= i0
        mlabels = labels[(locs[:,0] >= i0) & (locs[:,0] < i1),:]
        aw.write_wave(filename.format(k + 1), data[i0:i1,:], rate,
                      encoding=encoding, metadata=md,
                      locs=mlocs, labels=mlabels)
        file_paths.append(filename.format(k + 1))
        start_time += timedelta(seconds=n/rate)
    return data[:n*nfiles], rate, locs, labels, n, file_paths


def test_basename():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 20.0)
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print()
        print('check basename for module %s ...' % lib)
        am.select_module(lib)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            assert data.basename() == 'test', 'wrong name'
            assert data.basename(data.filepath) == 'test', 'wrong name'
            assert data.basename(data.file_paths[0]) == 'test', 'wrong name'
            assert isinstance(data.filepath, Path), 'filepath is not Path'
            assert data.filepath.resolve() == Path(filename).resolve(), 'invalid filepath'
            assert len(data.file_paths) == 1, 'invalid len of file_paths'
            assert isinstance(data.file_paths[0], Path), 'file_paths[0] is not Path'
            assert data.file_paths[0].resolve() == Path(filename).resolve(), 'invalid file_paths[0]'
    Path(filename).unlink(True)
    am.enable_module()


def test_get_file_index():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 20.0)
    ntests = 100
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print()
        print('check file index for module %s ...' % lib)
        am.select_module(lib)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            times = data.file_start_times()
            assert len(times) == 1, 'len of file_start_times()'
            assert times[0] == 0.0, 'value of file_start_times()'
            with pytest.raises(ValueError):
                data.get_file_index(-1)
            with pytest.raises(ValueError):
                data.get_file_index(len(data))
            for inx in np.random.randint(0, len(data), ntests):
                fname, i = data.get_file_index(inx)
                assert fname == Path(filename), 'returned wrong file name'
                assert i == inx, 'returned wrong index'
    Path(filename).unlink(True)
    am.enable_module()


def test_single_frame():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 20.0)
    tolerance = 2.0**(-15)
    ntests = 500
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print()
        print('check single frame access for module %s ...' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            assert not np.any(np.abs(full_data[0] - data[0]) > tolerance), 'first frame access failed with %s module' % lib
            assert not np.any(np.abs(full_data[-1] - data[-1]) > tolerance), 'last frame access failed with %s module' % lib
            for n in range(10):
                with pytest.raises(IndexError):
                    x = data[len(data)+n]
            failed = -1
            for inx in np.random.randint(-len(data), len(data), ntests):
                if np.any(np.abs(full_data[inx] - data[inx]) > tolerance):
                    failed = inx
                    break
            assert failed < 0, 'single random frame access failed at index %d with %s module' % (failed, lib)
    Path(filename).unlink(True)
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
        print()
        print('random frame slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for n in range(5):
                assert not np.any(np.abs(data[:n]-full_data[:n]) > tolerance), 'zero slice up to %d does not match' % n
            for n in range(1, 5):
                assert not np.any(np.abs(data[:50:n]-full_data[:50:n]) > tolerance), 'step slice with step=%d does not match' % n
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.rate)
                failed = -1
                for inx in np.random.randint(0, len(data)-nframes, ntests):
                    if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > tolerance):
                        failed = inx
                        break
                assert failed < 0, 'random frame slice access failed at index %d with nframes=%d and %s module' % (failed, nframes, lib)
    Path(filename).unlink(True)
    am.enable_module()


def test_slice_pathlib():
    am.enable_module()
    filename = Path('test.wav')
    write_audio_file(filename, 20.0)
    tolerance = 2.0**(-15)
    ntests = 100
    for lib in am.installed_modules('fileio'):
        if lib in ['scipy.io.wavfile', 'pydub']:
            continue
        print()
        print('random frame slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for n in range(1, 5):
                assert not np.any(np.abs(data[:50:n]-full_data[:50:n]) > tolerance), 'step slice with step=%d does not match' % n
    filename.unlink(True)
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
        print()
        print('forward slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.rate)
                step = int(len(data)/nsteps)
                failed = -1
                for inx in range(0, len(data)-nframes, step):
                    if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > tolerance):
                        failed = inx
                        break
                assert failed < 0, 'frame slice access forward failed at index %d with nframes=%d and %s module' % (failed, nframes, lib)
    Path(filename).unlink(True)
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
        print()
        print('backward slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.rate)
                step = int(len(data)/nsteps)
                failed = -1
                print('  check backward slice access...')
                for inx in range(len(data)-nframes, 0, -step):
                    if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > tolerance):
                        failed = inx
                        break
                assert failed < 0, 'frame slice access backward failed at index %d with nframes=%d and %s module' % (failed, nframes, lib)
    Path(filename).unlink(True)
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
        print()
        print('negative slice access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0]:
                nframes = int(time*data.rate)
                step = int(len(data)/nsteps)
                failed = -1
                for inx in range(0, len(data)-nframes, step):
                    if np.any(np.abs(full_data[-inx:-inx+nframes] - data[-inx:-inx+nframes]) > tolerance):
                        failed = -inx
                        break
                assert failed < 0, 'frame slice access backward with negative indices failed at index %d with nframes=%d and %s module' % (failed, nframes, lib)
    Path(filename).unlink(True)
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
        print()
        print('multiple indices access for module %s' % lib)
        am.select_module(lib)
        full_data, rate = al.load_audio(filename, verbose=4)
        with al.AudioLoader(filename, 5.0, 2.0, verbose=4) as data:
            for time in [0.1, 1.5, 2.0, 5.5, 8.0, 20.0]:
                nframes = int(time*data.rate)
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
                    assert failed == -1, ('multiple random frame access failed with %s module at indices ' % lib) + str(inx)
    Path(filename).unlink(True)
    am.enable_module()


def test_multi_files():
    nfiles = 20
    am.enable_module()
    filename = 'test{:02d}.wav'
    full_data, rate, full_locs, full_labels, frames, file_paths = \
        write_audio_files(filename, 600.0, nfiles)
    tolerance = 2.0**(-15)
    ntests = 100
    print()
    print('access for multiple files')
    al.AudioLoader.max_open_files = 4
    al.AudioLoader.max_open_loaders = 8
    data1 = al.AudioLoader(file_paths, 5.0, 2.0, verbose=4)
    locs, labels = data1.markers()
    assert len(locs) == len(full_locs), 'number of marker locs differ'
    assert np.all(locs == full_locs), 'marker locations differ'
    assert len(labels) == len(full_labels), 'number of marker labels differ'
    assert np.all(labels == full_labels), 'marker labels differ'
    data2 = al.AudioLoader(data1.file_paths, 5.0, 2.0, verbose=4,
                           rate=data1.rate, channels=data1.channels,
                           end_indices=data1.end_indices)
    assert isinstance(data2.filepath, Path), 'filepath is not Path'
    assert data2.filepath.resolve() == Path(file_paths[0]).resolve(), 'invalid filepath'
    assert len(data2.file_paths) == nfiles, 'invalid len of file_paths'
    for k in range(nfiles):
        assert isinstance(data2.file_paths[k], Path), f'file_paths[k] is not Path'
        assert data2.file_paths[k].resolve() == Path(file_paths[k]).resolve(), f'invalid file_paths[{k}]'
    for data in [data1, data2]:
        assert len(data) == len(full_data), f'number of data elements differ: {len(data)} != {len(full_data)}'
        assert len(data) == len(full_data), f'number of data elements differ: {data.shape[0]} != {len(full_data)}'
        # get file index:
        times = data.file_start_times()
        assert len(times) == nfiles, 'len of file_start_times()'
        for i in range(nfiles):
            assert times[i] == i*frames/data.rate, 'value of file_start_times()'
        with pytest.raises(ValueError):
            data.get_file_index(-1)
        with pytest.raises(ValueError):
            data.get_file_index(len(data))
        for inx in np.random.randint(0, len(data), ntests):
            fname, i = data.get_file_index(inx)
            assert fname == Path(filename.format(1 + inx//frames)), 'returned wrong file name'
            assert i == inx%frames, 'returned wrong index'
        # single frames:
        assert not np.any(np.abs(full_data[0] - data[0]) > tolerance), 'first frame access failed with multiple files'
        assert not np.any(np.abs(full_data[-1] - data[-1]) > tolerance), 'last frame access failed with multiple files'
        for n in range(10):
            with pytest.raises(IndexError):
                x = data[len(data)+n]
        failed = -1
        for inx in np.random.randint(0, len(data), ntests):
            if np.any(np.abs(full_data[inx] - data[inx]) > tolerance):
                failed = inx
                break
        assert failed < 0, 'single random frame access failed at index %d with multiple files' % failed
        # slices:
        for n in range(0, 5, 10):
            assert not np.any(np.abs(data[:n]-full_data[:n]) > tolerance), 'zero slice up to %d does not match' % n
        for n in range(1, 5):
            assert not np.any(np.abs(data[:50:n]-full_data[:50:n]) > tolerance), 'step slice with step=%d does not match' % n
        for time in [0.1, 1.5, 2.0, 5.5, 8.0, 14.0, 20.0, 30.0]:
            nframes = int(time*data.rate)
            failed = -1
            for inx in np.random.randint(0, len(data)-nframes, ntests):
                if np.any(np.abs(full_data[inx:inx+nframes] - data[inx:inx+nframes]) > tolerance):
                    failed = inx
                    break
            assert failed < 0, 'random frame slice access failed at index %d with nframes=%d and %s module' % (failed, nframes, lib)
        data.close()
    for k in range(nfiles):
        Path(filename.format(k+1)).unlink(True)


def test_modules():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 1.0)
    for lib, load_file in al.audio_loader_funcs:
        print(lib)
        am.disable_module(lib)
        with pytest.raises(ImportError):
            load_file(filename)
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
        with pytest.raises(ImportError):
            load_funcs[lib](filename, 10.0, 2.0)
        if am.select_module(lib):
            # check double opening:
            load_funcs[lib](filename)
            load_funcs[lib](filename)
            data.close()
    Path(filename).unlink(True)
    am.enable_module()
        

def test_audio_files():
    am.enable_module()
    with pytest.raises(FileNotFoundError):
        al.load_audio('xxx.wav')
    with pytest.raises(FileNotFoundError):
        al.AudioLoader('xxx.wav')
    filename = 'test.wav'
    df = open(filename, 'w')
    df.close()
    with pytest.raises(EOFError):
        al.load_audio(filename)
    with pytest.raises(EOFError):
        al.AudioLoader(filename)
    Path(filename).unlink(True)
    write_audio_file(filename)
    am.disable_module()
    with pytest.raises(IOError):
        al.load_audio(filename)
    with pytest.raises(IOError):
        al.AudioLoader(filename)
    Path(filename).unlink(True)
    am.enable_module()

    
def test_iter():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, 1.0)
    full_data, rate = al.load_audio(filename)
    tolerance = 2.0**(-15)
    with al.AudioLoader(filename, 0.2) as data:
        for k, x in enumerate(data):
            assert not np.any(np.abs(x-full_data[k]) > tolerance), 'iteration %d does not match' % k

        
def test_blocks():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename)
    full_data, rate = al.load_audio(filename)
    tolerance = 2.0**(-15)
    for n in [5000, len(full_data)+100]:
        read_data = []
        with al.AudioLoader(filename) as data:
            for x in ba.blocks(data, n, 10):
                read_data.append(x[:-10].copy())
        read_data = np.vstack(read_data)
        assert full_data.shape[0]-10 == read_data.shape[0], 'len of blocked data differ from input data'
        assert full_data.shape[1] == read_data.shape[1], 'columns of blocked data differ from input data'
        assert not np.any(np.abs(full_data[:-10] - read_data) > tolerance), 'blocks() failed'
        read_data = []
        with al.AudioLoader(filename) as data:
            for x in data.blocks(n, 10):
                read_data.append(x[:-10].copy())
        read_data = np.vstack(read_data)
        assert full_data.shape[0]-10 == read_data.shape[0], 'len of blocked data differ from input data'
        assert full_data.shape[1] == read_data.shape[1], 'columns of blocked data differ from input data'
        assert not np.any(np.abs(full_data[:-10] - read_data) > tolerance), 'blocks() failed'

    with pytest.raises(ValueError):
        for x in ba.blocks(full_data, 10, 20):
            pass


def test_unwrap():
    duration = 0.1
    rate = 44100.0
    channels = 4
    t = np.arange(0.0, duration, 1.0/rate)
    data = 1.5*np.sin(2.0*np.pi*880.0*t) * 2**15
    data = data.astype(dtype=np.int16).astype(dtype=float)/2**15
    data = data.astype(dtype=float)
    filename = 'test.wav'
    aw.write_wave(filename, data, rate, metadata={'Gain': '20mV'},
                  encoding='PCM_16')

    with al.AudioLoader(filename) as sf:
        sf.set_unwrap(1.5, down_scale=False)
        sdata = sf[:,:]
        md = sf.metadata()['INFO']
    assert md['UnwrapThreshold'] == '1.50', 'AudioLoader with unwrap adds metadata'
    assert md['Gain'] == '20mV', 'AudioLoader with unwrap modifies gain'
    assert len(sdata) == len(t), 'AudioLoader with unwrap keeps frames'
    assert sdata.ndim == 2, 'AudioLoader with unwrap keeps two dimensions'
    assert np.max(sdata) > 1.4, 'AudioLoader with unwrap expands beyond +1'
    assert np.min(sdata) < -1.4, 'AudioLoader with unwrap expands below -1'

    with al.AudioLoader(filename) as sf:
        sf.set_unwrap(1.5)
        sdata = sf[:,:]
        md = sf.metadata()['INFO']
    assert md['UnwrapThreshold'] == '0.75', 'AudioLoader with unwrap adds metadata'
    assert md['Gain'] == '40.0mV', 'AudioLoader with unwrap modifies gain'
    assert len(sdata) == len(t), 'AudioLoader with unwrap keeps frames'
    assert sdata.ndim == 2, 'AudioLoader with unwrap keeps two dimensions'
    assert np.max(sdata) <= 1.0, 'AudioLoader with unwrap downscales below +1'
    assert np.min(sdata) >= -1.0, 'AudioLoader with unwrap downscales above -1'

    with al.AudioLoader(filename) as sf:
        sf.set_unwrap(1.5, clips=True)
        sdata = sf[:,:]
        md = sf.metadata()['INFO']
    assert md['UnwrapThreshold'] == '1.50', 'AudioLoader with unwrap adds metadata'
    assert md['UnwrapClippedAmplitude'] == '1.00', 'AudioLoader with unwrap adds metadata'
    assert md['Gain'] == '20mV', 'AudioLoader with unwrap modifies gain'
    assert len(sdata) == len(t), 'AudioLoader with unwrap keeps frames'
    assert sdata.ndim == 2, 'AudioLoader with unwrap keeps two dimensions'
    assert np.max(sdata) <= 1.0, 'AudioLoader with unwrap clips at +1'
    assert np.min(sdata) >= -1.0, 'AudioLoader with unwrap clips at -1'
    
    Path(filename).unlink(True)


def test_demo():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, duration=5.0)
    al.demo(filename, False)
    Path(filename).unlink(True)


def test_main():
    am.enable_module()
    filename = 'test.wav'
    write_audio_file(filename, duration=5.0)
    al.main('-h')
    al.main(filename)
    al.main('-m', 'wave', filename)
    Path(filename).unlink(True)

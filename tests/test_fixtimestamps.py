import pytest
import numpy as np

from pathlib import Path
from datetime import datetime, timedelta

import audioio.audiowriter as aw
import audioio.audioloader as al
import audioio.audiometadata as am
import audioio.fixtimestamps as ft


def write_audio_files(duration=100.0, nfiles=4, short=False):
    rate = 44100.0
    channels = 2
    t = np.arange(0.0, duration, 1.0/rate)
    data = np.sin(2.0*np.pi*880.0*t) * t/duration
    data = data.reshape((-1, 1))
    for k in range(data.shape[1], channels):
        data = np.hstack((data, data[:,0].reshape((-1, 1))/k))
    encoding = 'PCM_16'
    old_time = datetime.fromisoformat('2019-01-01T00:00:00')
    new_time = datetime.now()
    old_paths = []
    new_paths = []
    old_times = []
    new_times = []
    n = len(data) // nfiles
    for k in range(nfiles):
        i0 = k*n
        i1 = (k + 1)*n
        md = dict(DateTimeOriginal=old_time.isoformat())
        dts = old_time.replace(microsecond=0).isoformat()
        if short:
            filename = f'test-{dts.replace('-', '').replace(':', '')}.wav'
        else:
            filename = f'test-{dts}.wav'
        dts = new_time.replace(microsecond=0).isoformat()
        if short:
            newname = f'test-{dts.replace('-', '').replace(':', '')}.wav'
        else:
            newname = f'test-{dts}.wav'
        aw.write_wave(filename, data[i0:i1,:], rate,
                      encoding=encoding, metadata=md)
        old_paths.append(filename)
        new_paths.append(newname)
        old_times.append(old_time.replace(microsecond=0))
        new_times.append(new_time.replace(microsecond=0))
        old_time += timedelta(seconds=n/rate)
        new_time += timedelta(seconds=n/rate)
    return old_paths, old_times, new_paths, new_times
    


def test_main():
    nfiles = 4
    with pytest.raises(SystemExit):
        ft.main()
    with pytest.raises(SystemExit):
        ft.main('--version')
    with pytest.raises(SystemExit):
        ft.main('--help')
    old_paths, old_times, new_paths, new_times = \
        write_audio_files(100.0, nfiles, False)
    with pytest.raises(SystemExit):
        ft.main(*old_paths)
    with pytest.raises(ValueError):
        ft.main('-s', *old_paths)
    ft.main('-n', '-s', new_times[0].isoformat(), *old_paths)
    ft.main('-s', new_times[0].isoformat(), *old_paths)
    for fn, dt in zip(new_paths, new_times):
        assert Path(fn).is_file(), f'file not correctly renamed to {fn}'
        md = al.metadata(fn)
        mdt = am.get_datetime(md)
        assert mdt == dt, f'date and time not correctly set in metadata to {mdt.isoformat()} (should be {dt.isoformat()})'
    old_paths, old_times, new_paths, new_times = \
        write_audio_files(100.0, nfiles, True)
    ft.main('-n', '-s', new_times[0].isoformat(), *old_paths)
    ft.main('-s', new_times[0].isoformat(), *old_paths)
    for fn, dt in zip(new_paths, new_times):
        assert Path(fn).is_file(), f'file not correctly renamed to {fn}'
        md = al.metadata(fn)
        mdt = am.get_datetime(md)
        assert mdt == dt, f'date and time not correctly set in metadata to {mdt.isoformat()} (should be {dt.isoformat()})'
    old_paths, old_times, new_paths, new_times = \
        write_audio_files(100.0, nfiles, True)
    for fn in Path('.').glob('test-*.wav'):
        Path(fn).unlink()

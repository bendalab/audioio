import pytest
import time
import numpy as np
import audioio.playaudio as ap
import audioio.audiomodules as am


def test_beep():
    am.enable_module()
    print()
    print('beep with default module...')
    am.list_modules('device', True)
    try:
        ap.beep(blocking=True, verbose=2)
        ap.beep(0.5, 'a4', blocking=True, verbose=2)
        ap.beep(blocking=False, verbose=2)
        time.sleep(2.0)
        ap.close()
    except FileNotFoundError:
        print(f'test_beep() with default {ap.handle.lib} module found no device.')
    for lib in am.installed_modules('device'):
        print()
        print(f'beep with {lib} module...')
        am.select_module(lib)
        am.list_modules('device', True)
        try:
            ap.beep(blocking=True, verbose=2)
            ap.beep(blocking=False, verbose=2)
            time.sleep(2.0)
            print(f'successfully beeped with {lib} module')
            ap.close()
        except FileNotFoundError:
            print(f'test_beep() with {lib} ({ap.handle.lib}) module found no device.')
        am.enable_module()


def test_play():
    am.enable_module()
    print()
    # sine wave:
    rate = 44100.0
    t = np.arange(0.0, 0.5, 1.0/rate)
    mono_data = np.sin(2.0*np.pi*800.0*t)
    stereo_data = np.tile(mono_data, (2, 1)).T
    # fade in and out:
    try:
        ap.fade(mono_data, rate, 0.1)
        ap.fade(stereo_data, rate, 0.1)
        print('play with default module mono...')
        ap.play(mono_data, rate, blocking=True)
        ap.play(mono_data, rate, blocking=False)
        time.sleep(2.0)
        print('play with default module stereo...')
        ap.play(stereo_data, rate, blocking=True)
        ap.play(stereo_data, rate, blocking=False)
        time.sleep(2.0)
    except FileNotFoundError:
        print(f'test_play() with default {ap.handle.lib} module found no device.')
    ap.close()
    for lib in am.installed_modules('device'):
        print(f'play with {lib} module mono...')
        am.select_module(lib)
        try:
            ap.play(mono_data, rate, blocking=True, verbose=2)
            ap.play(mono_data, rate, blocking=False, verbose=2)
            time.sleep(2.0)
            print(f'play with {lib} module stereo...')
            ap.play(stereo_data, rate, blocking=True)
            ap.play(stereo_data, rate, blocking=False)
            time.sleep(2.0)
        except FileNotFoundError:
            print(f'test_play() with {lib} ({ap.handle.lib}) module found no device.')
        ap.close()
        am.enable_module()


def test_downsample():
    def sinewave(rate):
        t = np.arange(0.0, 0.5, 1.0/rate)
        mono_data = np.sin(2.0*np.pi*800.0*t)
        stereo_data = np.tile(mono_data, (2, 1)).T
        # fade in and out:
        ap.fade(mono_data, rate, 0.1)
        ap.fade(stereo_data, rate, 0.1)
        return mono_data, stereo_data
        
    am.enable_module()
    print()
    for lib in am.installed_modules('device'):
        am.select_module(lib)
        print(f'downsample wiht {lib} module ...')
        try:
            for rate in [45555.0, 100000.0, 600000.0]:
                print(' test rate %.0f Hz ...' % rate)
                mono_data, stereo_data = sinewave(rate)
                ap.play(mono_data, rate, verbose=2)
                ap.play(stereo_data, rate, verbose=2)
        except FileNotFoundError:
            print(f'test_downsample() with {lib} ({ap.handle.lib}) module found no device.')
        ap.close()
        am.enable_module()


def test_note2freq():
    fa = 460.0
    assert np.abs(ap.note2freq('a4', fa)-fa) < 1e-6, 'wrong a4 frequency'
    fp = 0.5*ap.note2freq('a0')
    for o in range(10):
        for n in 'cdefgab':
            note = '%s%d' % (n, o)
            f = ap.note2freq(note)
            assert f > fp, 'frequency of %s should be greater than the one of previous note' % note
            note = '%s#%d' % (n, o)
            fs = ap.note2freq(note)
            assert fs > f, 'frequency of %s should be greater' % note
            note = '%sb%d' % (n, o)
            fb = ap.note2freq(note)
            assert fb < f, 'frequency of %s should be greater' % note
            fp = f
    with pytest.raises(ValueError):
        ap.note2freq('h')
    with pytest.raises(ValueError):
        ap.note2freq('da')
    with pytest.raises(ValueError):
        ap.note2freq('dx#')
    with pytest.raises(ValueError):
        ap.note2freq('d4#')
    with pytest.raises(ValueError):
        ap.note2freq('d4x')
    with pytest.raises(ValueError):
        ap.note2freq('d#4x')
    with pytest.raises(ValueError):
        ap.note2freq('d-2')
    with pytest.raises(ValueError):
        ap.note2freq('')
    with pytest.raises(ValueError):
        ap.note2freq(0)


def test_demo():
    am.enable_module()
    try:
        ap.demo()
    except FileNotFoundError:
        print('test_demo() found no device.')


def test_main():
    am.enable_module()
    try:
        ap.main(['prog', '-h'])
        ap.main(['prog'])
        ap.main(['prog', '-m', 'sounddevice'])
        ap.main(['prog', 'x'])
    except FileNotFoundError:
        print('test_main() found no device.')

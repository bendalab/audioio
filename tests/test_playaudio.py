from nose.tools import assert_equal, assert_greater, assert_greater_equal, assert_less, assert_raises
import time
import numpy as np
import audioio.playaudio as ap
import audioio.audiomodules as am


def test_beep():
    am.enable_module()
    print()
    print('beep with default module...')
    try:
        ap.beep(blocking=True, verbose=2)
        ap.beep(0.5, 'a4', blocking=True, verbose=2)
        ap.beep(blocking=False, verbose=2)
        time.sleep(2.0)
        ap.handle.close()
        ap.handle = None
    except Exception as e:
        print('beep failed:', type(e), str(e))
    for lib in am.installed_modules('device'):
        print(f'beep with {lib} module...')
        am.select_module(lib)
        try:
            ap.beep(blocking=True, verbose=2)
            ap.beep(blocking=False, verbose=2)
            time.sleep(2.0)
            ap.handle.close()
            ap.handle = None
        except Exception as e:
            print('beep failed:', type(e), str(e))
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
    ap.handle.close()
    ap.handle = None
    for lib in am.installed_modules('device'):
        print(f'play with {lib} module mono...')
        am.select_module(lib)
        ap.play(mono_data, rate, blocking=True, verbose=2)
        ap.play(mono_data, rate, blocking=False, verbose=2)
        time.sleep(2.0)
        print(f'play with {lib} module stereo...')
        ap.play(stereo_data, rate, blocking=True)
        ap.play(stereo_data, rate, blocking=False)
        time.sleep(2.0)
        ap.handle.close()
        ap.handle = None
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
        for rate in [45555.0, 100000.0, 600000.0]:
            print(' test rate %.0f Hz ...' % rate)
            mono_data, stereo_data = sinewave(rate)
            ap.play(mono_data, rate, verbose=2)
            ap.play(stereo_data, rate, verbose=2)
        ap.handle.close()
        ap.handle = None
        am.enable_module()


def test_note2freq():
    fa = 460.0
    assert_less(np.abs(ap.note2freq('a4', fa)-fa), 1e-6, 'wrong a4 frequency')
    fp = 0.5*ap.note2freq('a0')
    for o in range(10):
        for n in 'cdefgab':
            note = '%s%d' % (n, o)
            f = ap.note2freq(note)
            assert_greater(f, fp, 'frequency of %s should be greater than the one of previous note' % note)
            note = '%s#%d' % (n, o)
            fs = ap.note2freq(note)
            assert_greater(fs, f, 'frequency of %s should be greater' % note)
            note = '%sb%d' % (n, o)
            fb = ap.note2freq(note)
            assert_less(fb, f, 'frequency of %s should be greater' % note)
            fp = f
    assert_raises(ValueError, ap.note2freq, 'h')
    assert_raises(ValueError, ap.note2freq, 'da')
    assert_raises(ValueError, ap.note2freq, 'dx#')
    assert_raises(ValueError, ap.note2freq, 'd4#')
    assert_raises(ValueError, ap.note2freq, 'd4x')
    assert_raises(ValueError, ap.note2freq, 'd#4x')
    assert_raises(ValueError, ap.note2freq, 'd-2')
    assert_raises(ValueError, ap.note2freq, '')
    assert_raises(ValueError, ap.note2freq, 0)


def test_demo():
    am.enable_module()
    ap.demo()


def test_main():
    am.enable_module()
    ap.main(['prog', '-h'])
    ap.main(['prog'])
    ap.main(['prog', '-m', 'sounddevice'])
    ap.main(['prog', 'x'])

import numpy as np
import audioio.audiowriter as aw
import audioio.audioloader as al
import sys

# do not print error messages:
class DevNull:
    def write(self, msg):
        pass

    
def check(samplerate_write, data_write, samplerate_read, data_read, lib, encoding):
    if np.abs(samplerate_write-samplerate_read) > 1e-8:
        return -1
    if len(data_write) != len(data_read):
        return -2
    if len(data_write.shape) != len(data_read.shape):
        return -3
    if len(data_read.shape) != 2:
        return -4
    if data_write.shape[0] != data_read.shape[0]:
        return -5
    if data_write.shape[1] != data_read.shape[1]:
        return -6
    if data_read.dtype != np.float64:
        return -7
    n = min([len(data_write), len(data_read)])
    max_error = np.max(np.abs(data_write[:n] - data_read[:n]))
    return max_error


def check_reading(md, start, sep, end):
    if md:
        print('reading %s files:  _maximum number of channels (quantization error)_' % format)
    else:
        print('reading %s files:  maximum number of channels (quantization error)' % format)
    print('')
    print(start + sep.join(['%-16s' % 'module\encoding'] + ['%-13s' % e for e in encodings]) + end)
    if md:
        print(start + sep.join(['-' * 16] + ['-' * 13 for e in encodings]) + end)
    for lib, write_file, load_file, encodings_func in audio_funcs:
        if not aw.audio_modules[lib]:
            continue
        results = start + '%-16s' % lib
        no_result = sep + '-' + ' ' * 12
        for encoding in encodings:
            encoding = encoding.upper()
            if encoding == '' or encoding in encodings_func(format):
                max_error = 0.0
                max_channel = 0
                channels = 1
                while channels <= max_channels:
                    try:
                        aw.write_audio(filename, data[:, 1:1+channels], samplerate, format=format, encoding=encoding)
                    except:
                        break
                    try:
                        data_read, samplerate_read = load_file(filename)
                        error = check(samplerate, data[:, 1:1+channels], samplerate_read, data_read, lib, encoding)
                        if error < -1e-8:
                            break
                        if max_error < error:
                            max_error = error
                        max_channel = channels
                    except:
                        break
                    channels *= 2
                if max_channel > 0:
                    results += sep + '%3d (%7.1e)' % (max_channel, max_error)
                else:
                    results += no_result
            else:
                results += no_result
        print(results + end)
    print('')

    
def check_writing(md, start, sep, end):
    if md:
        print('writing %s files: _maximum number of channels (quantization error)_' % format)
    else:
        print('writing %s files: maximum number of channels (quantization error)' % format)
    print('')
    print(start + sep.join(['%-16s' % 'module\encoding'] + ['%-13s' % e for e in encodings]) + end)
    if md:
        print(start + sep.join(['-' * 16] + ['-' * 13 for e in encodings]) + end)
    for lib, write_file, load_file, encodings_func in audio_funcs:
        if not aw.audio_modules[lib]:
            continue
        results = start + '%-16s' % lib
        no_result = sep + '-' + ' ' * 12
        for encoding in encodings:
            encoding = encoding.upper()
            if encoding == '' or encoding in encodings_func(format):
                max_error = 0.0
                max_channel = 0
                channels = 1
                while channels <= max_channels:
                    try:
                        write_file(filename, data[:, 1:1+channels], samplerate, format=format, encoding=encoding)
                    except:
                        break
                    try:
                        data_read, samplerate_read = al.load_audio(filename)
                        error = check(samplerate, data[:, 1:1+channels], samplerate_read, data_read, lib, encoding)
                        if error < -1e-8:
                            break
                        if max_error < error:
                            max_error = error
                        max_channel = channels
                    except:
                        break
                    channels *= 2
                if max_channel > 0:
                    results += sep + '%3d (%7.1e)' % (max_channel, max_error)
                else:
                    results += no_result
            else:
                results += no_result
        print(results + end)
    print('')

        
if __name__ == "__main__":

    max_channels = 520
    samplerate = 44100.0
    duration = 1.0

    md = False
    if len(sys.argv) > 1:
        md = sys.argv[1] == '-m'
    if md:
        start = '| '
        sep = ' | '
        end = ' |'
    else:
        start = ''
        sep = '  '
        end = ''
                
    # generate data:
    t = np.arange(int(duration*samplerate))/samplerate
    data = np.zeros((len(t), max_channels))
    data[:, 0] = np.sin(2.0*np.pi*880.0*t) * t/duration
    for k in range(1, max_channels):
            data[:, k] = data[:, 0]/k

    # parameter for wav file:
    filename = 'test.wav'
    format = 'WAV'
    encodings = ['PCM_U8', 'PCM_16', 'PCM_24', 'PCM_32', 'PCM_64', 'FLOAT', 'DOUBLE', 'ALAW', 'ULAW']

    # parameter for ogg file:
    ## filename = 'test.ogg'
    ## format = 'OGG'
    ## encodings = ['VORBIS']

    audio_funcs = [
        ['wave', aw.write_wave, al.load_wave, aw.encodings_wave],
        ['ewave', aw.write_ewave, al.load_ewave, aw.encodings_ewave],
        ['scipy.io.wavfile', aw.write_wavfile, al.load_wavfile, aw.encodings_wavfile],
        ['soundfile', aw.write_soundfile, al.load_soundfile, aw.encodings_soundfile],
        ['wavefile', aw.write_wavefile, al.load_wavefile, aw.encodings_wavefile],
        ['scikits.audiolab', aw.write_audiolab, al.load_audiolab, aw.encodings_audiolab],
        ]

    sys.stderr = DevNull()
    check_reading(md, start, sep, end)
    check_writing(md, start, sep, end)

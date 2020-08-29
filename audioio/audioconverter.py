"""
Convert formats of audio files.
"""

import os
import argparse
from .version import __version__, __year__
from .audioloader import load_audio
from .audiowriter import write_audio, available_formats, available_encodings


def check_format(format):
    """
    Check whether requested audio format is valid and supported.

    If the format is not available print an error message on console.

    Parameters
    ----------
    format: string
        Audio format to be checked.

    Returns
    -------
    valid: bool
        True if the requested audio format is valid.
    """
    if format and format.upper() not in available_formats():
        print('! invalid audio format "%s"!' % format)
        print('run')
        print('> %s -l' % __file__ )
        print('for a list of available formats')
        return False
    else:
        return True


def main():
    """
    Command line script for converting audio files.

    Running
    ```sh
    audioconverter --help
    ```
    prints
    ```text
    usage: audioconverter [-h] [--version] [-v] [-l] [-f FORMAT] [-e ENCODING]
                          [-o OUTPATH]
                          [file [file ...]]

    Convert audio file formats.

    positional arguments:
      file         input audio files

    optional arguments:
      -h, --help   show this help message and exit
      --version    show program's version number and exit
      -v           print debug output
      -l           list supported file formats and encodings
      -f FORMAT    audio format of output file
      -e ENCODING  audio encoding of output file
      -o OUTPATH   path or filename of output file.

    version 0.9.4 by Benda-Lab (2020-2020)
    ```
    """
    # command line arguments:
    parser = argparse.ArgumentParser(add_help=True,
        description='Convert audio file formats.',
        epilog='version %s by Benda-Lab (2020-%s)' % (__version__, __year__))
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-v', action='store_true', dest='verbose',
                        help='print debug output')
    parser.add_argument('-l', dest='list_formats', action='store_true',
                        help='list supported file formats and encodings')
    parser.add_argument('-f', dest='audio_format', default=None, type=str, metavar='FORMAT',
                        help='audio format of output file')
    parser.add_argument('-e', dest='audio_encoding', default=None, type=str, metavar='ENCODING',
                        help='audio encoding of output file')
    parser.add_argument('-o', dest='outpath', default=None, type=str,
                        help='path or filename of output file.')
    parser.add_argument('file', nargs='*', default='', type=str,
                        help='input audio files')
    args = parser.parse_args()

    check_format(args.audio_format)

    if args.list_formats:
        if not args.audio_format:
            print('available audio formats:')
            for f in available_formats():
                print('  %s' % f)
        else:
            print('available encodings for audio format %s:' % args.audio_format)
            for e in available_encodings(args.audio_format):
                print('  %s' % e)
        exit()

    # convert files:
    for infile in args.file:
        # output file:
        if not args.outpath or os.path.isdir(args.outpath):
            outfile = infile
            if args.outpath:
                outfile = os.path.join(args.outpath, outfile)
            if not args.audio_format:
                args.audio_format = 'wav'
            outfile = os.path.splitext(outfile)[0] + os.extsep + args.audio_format
        else:
            outfile = args.outpath
            ext = os.path.splitext(outfile)[1].lstrip('.')
            if args.audio_format:
                outfile = os.path.splitext(outfile)[0] + os.extsep + args.audio_format
            elif len(ext) > 0:
                args.audio_format = ext
            else:
                args.audio_format = 'wav'
                outfile = outfile + os.extsep + args.audio_format
        check_format(args.audio_format)
        if os.path.realpath(infile) == os.path.realpath(outfile):
            print('! cannot convert "%s" to itself !' % infile)
            break
        # read in audio:
        data, samplingrate = load_audio(infile)
        # write out audio:
        write_audio(outfile, data, samplingrate,
                    format=args.audio_format, encoding=args.audio_encoding)
        # message:
        if args.verbose:
            print('converted audio file "%s" to "%s"' % (infile, outfile))


if __name__ == '__main__':
    main()

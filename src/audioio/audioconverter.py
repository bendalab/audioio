"""Command line script for converting, downsampling, renaming and merging audio files.

```sh
audioconverter -o test.wav test.mp3
```
converts 'test.mp3' to 'test.wav'.

The script reads all input files with `audioio.audioloader.load_audio()`,
combines the audio and marker data and writes them along with the
metadata to an output file using `audioio.audiowriter.write_audio()`.

Thus, all formats supported by these functions and the installed
python audio modules are available. This implies that MP3 files can be
read via the [audioread](https://github.com/beetbox/audioread) module,
and they can be written via [pydub](https://github.com/jiaaro/pydub).
Many other input and output file formats are supported by the [sndfile
library](http://www.mega-nerd.com/libsndfile/), provided the
[SoundFile](http://pysoundfile.readthedocs.org) or
[wavefile](https://github.com/vokimon/python-wavefile) python packages
are [installed](https://bendalab.github.io/audioio/installation).

Metadata and markers are preserved if possible.

Run
```sh
audioconverter -l
```
for a list of supported output file formats and
```sh
audioconverter -f wav -l
```
for a list of supported encodings for a given output format (`-f` option).

Running
```sh
audioconverter --help
```
prints
```text
usage: audioconverter [-h] [--version] [-v] [-l] [-f FORMAT] [-e ENCODING] [-s SCALE] [-u [THRESH]]
                      [-U [THRESH]] [-d FAC] [-c CHANNELS] [-a KEY=VALUE] [-r KEY] [-n NUM]
                      [-o OUTPATH] [-i KWARGS]
                      [files ...]

Convert audio file formats.

positional arguments:
  files         one or more input files to be combined into a single output file

options:
  -h, --help    show this help message and exit
  --version     show program's version number and exit
  -v            print debug output
  -l            list supported file formats and encodings
  -f FORMAT     audio format of output file
  -e ENCODING   audio encoding of output file
  -s SCALE      scale the data by factor SCALE
  -u [THRESH]   unwrap clipped data with threshold relative to maximum of input range (default is
                0.5) and divide by two
  -U [THRESH]   unwrap clipped data with threshold relative to maximum of input range (default is
                0.5) and clip
  -d FAC        downsample by integer factor
  -c CHANNELS   comma and dash separated list of channels to be saved (first channel is 0)
  -a KEY=VALUE  add key-value pairs to metadata. Keys can have section names separated by "."
  -r KEY        remove keys from metadata. Keys can have section names separated by "."
  -n NUM        merge NUM input files into one output file
  -o OUTPATH    path or filename of output file. Metadata keys enclosed in curly braces will be
                replaced by their values from the input file
  -i KWARGS     key-word arguments for the data loader function

version 2.6.0 by Benda-Lab (2020-2025)
```

## Functions

- `add_arguments()`: add command line arguments to parser.
- `parse_channels()`: parse channel selection string.
- `parse_load_kwargs()`: parse additional arguments for loading data.
- `check_format()`: check whether requested audio format is valid and supported.
- `list_formats_encodings()`: list available formats or encodings.
- `make_outfile()`: make name for output file.
- `modify_data()`: modify audio data and add modifications to metadata.
- `format_outfile()`: put metadata values into name of output file.
- `main()`: command line script for converting, downsampling, renaming and merging audio files.
"""

import os
import sys
import argparse
import numpy as np

from pathlib import Path
from scipy.signal import decimate

from .version import __version__, __year__
from .audioloader import load_audio, markers, AudioLoader
from .audiometadata import flatten_metadata, unflatten_metadata
from .audiometadata import add_metadata, remove_metadata, cleanup_metadata
from .audiometadata import bext_history_str, add_history
from .audiometadata import update_gain, add_unwrap
from .audiotools import unwrap
from .audiowriter import available_formats, available_encodings
from .audiowriter import format_from_extension, write_audio


def add_arguments(parser):
    """Add command line arguments to parser.

    Parameters
    ----------
    parser: argparse.ArgumentParser
        The parser.
    """
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-v', action='count', dest='verbose', default=0,
                        help='print debug output')
    parser.add_argument('-l', dest='list_formats', action='store_true',
                        help='list supported file formats and encodings')
    parser.add_argument('-f', dest='data_format', default=None, type=str,
                        metavar='FORMAT', help='audio format of output file')
    parser.add_argument('-e', dest='encoding', default=None, type=str,
                        help='audio encoding of output file')
    parser.add_argument('-s', dest='scale', default=1, type=float,
                        help='scale the data by factor SCALE')
    parser.add_argument('-u', dest='unwrap', default=0, type=float,
                        metavar='THRESH', const=1.5, nargs='?',
                        help='unwrap clipped data with threshold relative to maximum of input range (default is 0.5) and divide by two')
    parser.add_argument('-U', dest='unwrap_clip', default=0, type=float,
                        metavar='THRESH', const=1.5, nargs='?',
                        help='unwrap clipped data with threshold relative to maximum of input range (default is 0.5) and clip')
    parser.add_argument('-d', dest='decimate', default=1, type=int,
                        metavar='FAC',
                        help='downsample by integer factor')
    parser.add_argument('-c', dest='channels', default='', type=str,
                        help='comma and dash separated list of channels to be saved (first channel is 0)')
    parser.add_argument('-a', dest='md_list', action='append', default=[],
                        type=str, metavar='KEY=VALUE',
                        help='add key-value pairs to metadata. Keys can have section names separated by "."')
    parser.add_argument('-r', dest='remove_keys', action='append', default=[],
                        type=str, metavar='KEY',
                        help='remove keys from metadata. Keys can have section names separated by "."')
    parser.add_argument('-n', dest='nmerge', default=0, type=int, metavar='NUM',
                        help='merge NUM input files into one output file')
    parser.add_argument('-o', dest='outpath', default=None, type=str,
                         help='path or filename of output file. Metadata keys enclosed in curly braces will be replaced by their values from the input file')
    parser.add_argument('-i', dest='load_kwargs', default=[],
                        action='append', metavar='KWARGS',
                        help='key-word arguments for the data loader function')
    parser.add_argument('files', nargs='*', type=str,
                        help='one or more input files to be combined into a single output file')


def parse_channels(cstr):
    """Parse channel selection string.

    Parameters
    ----------
    cstr: str
        String with comma separated channels and dash separated channel ranges.

    Returns
    -------
    channels: list of int
        List of selected channels.
    """
    cs = [s.strip() for s in cstr.split(',')]
    channels = []
    for c in cs:
        if len(c) == 0:
            continue
        css = [s.strip() for s in c.split('-')]
        if len(css) == 2:
            channels.extend(list(range(int(css[0]), int(css[1])+1)))
        else:
            channels.append(int(c))
    return channels


def parse_load_kwargs(load_strs):
    """Parse additional arguments for loading data.

    Parameters
    ----------
    load_strs: list of str
        Strings with with comma separated key-value pairs as returned
        by args.load_kwargs from `add_arguments()`.

    Returns
    -------
    load_kwargs: dict
        Key-word arguments for `load_audio()` and related functions.
        Value strings containing integer or floating point numbers
        are converted to `int` and `float`, respectively.
    """
    load_kwargs = {}
    for s in load_strs:
        for kw in s.split(','):
            kws = kw.split(':')
            if len(kws) == 2:
                key = kws[0].strip()
                value = kws[1].strip()
                try:
                    val = int(value)
                except ValueError:
                    try:
                        val = float(value)
                    except ValueError:
                        val = value
                load_kwargs[key] = val
    return load_kwargs


def check_format(format):
    """Check whether requested audio format is valid and supported.

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
    if not format or format.upper() not in available_formats():
        print(f'! invalid audio file format "{format}"!')
        print('run')
        print(f'> {__file__} -l')
        print('for a list of available formats')
        return False
    else:
        return True


def list_formats_encodings(data_format):
    """List available formats or encodings.

    Parameters
    ----------
    data_format: None or str
        If provided, list encodings for this data format.
        Otherwise, list available audio file formats.
    """
    if not data_format:
        print('available file formats:')
        for f in available_formats():
            print(f'  {f}')
    else:
        if not check_format(data_format):
            sys.exit(-1)
        print(f'available encodings for {data_format} file format:')
        for e in available_encodings(data_format):
            print(f'  {e}')

            
def make_outfile(outpath, infile, data_format, blocks, format_from_ext):
    """Make name for output file.

    Parameters
    ----------
    outpath: None or str
        Requested output path.
    infile: Path
        Path of the input file.
    data_format: None or str
        Requested output file format.
    blocks: bool
        If True, produce outputfile for group of input files.
    format_from_ext: function
        Function that inspects a filename for its extension and
        deduces a file format from it.

    Returns
    -------
    outfile: Path
        Path of output file.
    data_format: str
        Format of output file.
    """
    outpath = Path('' if outpath is None else outpath)
    if blocks and not data_format and \
       format_from_ext(outpath) is None and \
       not outpath.exists():
        outpath.mkdir()
    if outpath == Path() or outpath.is_dir():
        if outpath != Path():
            outfile = outpath / infile
        else:
            outfile = infile
        if not data_format:
            print('! need to specify an audio format via -f or a file extension !')
            sys.exit(-1)
        outfile = outfile.with_suffix('.' + data_format.lower())
    else:
        outfile = outpath
        if data_format:
            outfile = outfile.with_suffix('.' + data_format.lower())
        else:
            data_format = format_from_ext(outfile)
    return outfile, data_format


def modify_data(data, rate, metadata, channels, scale,
                unwrap_clip, unwrap_thresh, ampl_max, unit, decimate_fac):
    """Modify audio data and add modifications to metadata.

    Parameters
    ----------
    data: 2-D array of float
        The data to be written into the output file.
    rate: float
        Sampling rate of the data in Hertz.
    metadata: nested dict
        Metadata.
    channels: list of int
        List of channels to be selected from the data.
    scale: float
        Scaling factor to be applied to the data.
    unwrap_clip: float
        If larger than zero, unwrap the data using this as a threshold
        relative to `ampl_max`, and clip the data at +-`ampl_max`.
    unwrap_thresh: float
        If larger than zero, unwrap the data using this as a threshold
        relative to `ampl_max`, and downscale the data by a factor of two.
        Also update the gain in the metadata.
    ampl_max: float
        Maximum amplitude of the input range.
    unit: str
        Unit of the input range.
    decimate_fac: int
        Downsample the data by this factor.

    Returns
    -------
    """
    # select channels:
    if len(channels) > 0:
        data = data[:,channels]
    # scale data:
    if scale != 1:
        data *= scale
        if not update_gain(metadata, 1/scale):
            metadata['gain'] = 1/scale
    # fix data:
    if unwrap_clip > 1e-3:
        unwrap(data, unwrap_clip, ampl_max)
        data[data > +ampl_max] = +ampl_max
        data[data < -ampl_max] = -ampl_max
        add_unwrap(metadata, unwrap_clip*ampl_max, ampl_max, unit)
    elif unwrap_thresh > 1e-3:
        unwrap(data, unwrap_thresh, ampl_max)
        data *= 0.5
        update_gain(metadata, 0.5)
        add_unwrap(metadata, unwrap_thresh*ampl_max, 0.0, unit)
    # decimate:
    if decimate_fac > 1:
        data = decimate(data, decimate_fac, axis=0)
        rate /= decimate_fac
    return data, rate


def format_outfile(outfile, metadata):
    """Put metadata values into name of output file.

    Parameters
    ----------
    outfile: Path
        Path of output file. May contain metadata keys enclosed in curly braces.
    metadata: nested dict
        Metadata.

    Returns
    -------
    outfile: Path
        Output path with formatted name.
    """
    if len(metadata) > 0 and '{' in outfile.stem and '}' in outfile.stem:
        fmd = flatten_metadata(metadata)
        fmd = {k:(fmd[k] if isinstance(fmd[k], (int, float)) else fmd[k].replace(' ', '_')) for k in fmd}
        outfile = outfile.with_stem(outfile.stem.format(**fmd))
    return outfile

        
def main(*cargs):
    """Command line script for converting, downsampling, renaming and merging audio files.

    Parameters
    ----------
    cargs: list of strings
        Command line arguments as returned by sys.argv[1:].
    """
    # command line arguments:
    parser = argparse.ArgumentParser(add_help=True,
        description='Convert audio file formats.',
        epilog=f'version {__version__} by Benda-Lab (2020-{__year__})')
    add_arguments(parser)
    if len(cargs) == 0:
        cargs = None
    args = parser.parse_args(cargs)
    
    channels = parse_channels(args.channels)
    
    if args.list_formats:
        if args.data_format is None and len(args.files) > 0:
            args.data_format = args.files[0]
        list_formats_encodings(args.data_format)
        return

    if len(args.files) == 0 or len(args.files[0]) == 0:
        print('! need to specify at least one input file !')
        sys.exit(-1)
        
    # expand wildcard patterns:
    files = []
    if os.name == 'nt':
        for fn in args.files:
            files.extend(glob.glob(fn))
    else:
        files = args.files

    nmerge = args.nmerge
    if nmerge == 0:
        nmerge = len(files)

    # kwargs for audio loader:
    load_kwargs = parse_load_kwargs(args.load_kwargs)

    # read in audio:
    try:
        data = AudioLoader(files, verbose=args.verbose - 1,
                           **load_kwargs)
    except FileNotFoundError:
        print(f'file "{files[0]}" not found!')
        sys.exit(-1)
    if len(data.file_paths) < len(files):
        print(f'file "{files[len(data.file_paths)]}" does not continue file "{data.file_paths[-1]}"!')
        sys.exit(-1)
    md = data.metadata()
    add_metadata(md, args.md_list, '.')
    if len(args.remove_keys) > 0:
        remove_metadata(md, args.remove_keys, '.')
        cleanup_metadata(md)
    locs, labels = data.markers()
    pre_history = bext_history_str(data.encoding,
                                   data.rate,
                                   data.channels,
                                   os.fsdecode(data.filepath))
    if args.verbose > 1:
        print(f'loaded audio file "{data.filepath}"')
        
    if data.encoding is not None and args.encoding is None:
        args.encoding = data.encoding
    for i0 in range(0, len(data.file_paths), nmerge):
        infile = data.file_paths[i0]
        outfile, data_format = make_outfile(args.outpath, infile,
                                            args.data_format,
                                            nmerge < len(files),
                                            format_from_extension)
        if not check_format(data_format):
            sys.exit(-1)
        if infile.resolve() == outfile.resolve():
            print(f'! cannot convert "{infile}" to itself !')
            sys.exit(-1)

        if len(data.file_paths) > 1:
            i1 = i0 + nmerge - 1
            if i1 >= len(data.end_indices):
                i1 = len(data.end_indices) - 1
            si = data.start_indices[i0]
            ei = data.end_indices[i1]
        else:
            si = 0
            ei = data.frames
        wdata, wrate = modify_data(data[si:ei], data.rate,
                                   md, channels, args.scale,
                                   args.unwrap_clip, args.unwrap, 1.0,
                                   '', args.decimate)
        mask = (locs[:, 0] >= si) & (locs[:, 0] < ei)
        wlocs = locs[mask, :]
        if len(wlocs) > 0:
            wlocs[:, 0] -= si
        wlabels = labels[mask, :]
        outfile = format_outfile(outfile, md)
        # history:
        hkey = 'CodingHistory'
        if 'BEXT' in md:
            hkey = 'BEXT.' + hkey
        history = bext_history_str(args.encoding, wrate,
                                   data.shape[1], os.fsdecode(outfile))
        add_history(md, history, hkey, pre_history)
        # write out audio:
        try:
            write_audio(outfile, wdata, wrate, md, wlocs, wlabels,
                        format=data_format, encoding=args.encoding)
        except PermissionError:
            print(f'failed to write "{outfile}": permission denied!')
            sys.exit(-1)
        # message:
        if args.verbose > 1:
            print(f'wrote "{outfile}"')
        elif args.verbose:
            print(f'converted audio file "{infile}" to "{outfile}"')
    data.close()
    

if __name__ == '__main__':
    main(*sys.argv[1:])

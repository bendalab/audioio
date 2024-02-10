"""Loading metadata and marker lists from audio files.

For a demo run the module as:
```
python -m audioio.metadata audiofile.wav
```

## Metadata

To interface the various ways to store and read metadata of audio
files, the `audiometadata` module simply uses nested dictionaries.  The
keys are always strings. Values are strings, integers or other simple
types for key-value pairs. Value strings can also be numbers followed
by a unit. For defining subsections of key-value pairs, values can be
dictionaries . The dictionaries can be nested to arbitrary depth.

Often, audio files have very specific ways to store metadata. You can
enforce using these by providing a key with the name of the
metadata type you want, that has as a value a dictionary with the
actual metadata. For example the "INFO", "BEXT", and "iXML" chunks of
RIFF/WAVE files.

- `metadata()`: read metadata of an audio file.
- `write_metadata_text()`: write meta data into a text/yaml file.
- `print_metadata()`: write meta data to standard output.
- `flatten_metadata()`: Flatten hierachical metadata to a single dictionary.
- `unflatten_metadata()`: Unflatten a previously flattened metadata dictionary.
- `add_metadata()`: add or modify metadata.
- `update_gain()`: update gain setting in metadata.
- `add_unwrap()`: add unwrap infos to metadata.


## Markers

Markers are used to mark specific positions or regions in the audio
data.  Each marker has a position, a span, a label, and a text.
Position, and span are handled with 1-D or 2-D arrays of ints, where
each row is a marker and the columns are position and span. The span
column is optional. Labels and texts come in another 1-D or 2-D array
of objects pointing to strings. Again, rows are the markers, first
column are the labels, and second column the optional texts. Try to
keep the labels short, and use text for longer descriptions.

- `markers()`: read markers of an audio file.
- `write_markers()`: write markers to a text file or stream.
- `print_markers()`: write markers to standard output.

## Script

The module can be run as a script from the command line to display the
metadata and markers contained in an audio file:

```sh
> audiometadata logger.wav
```
prints
```text
file:
  filepath    : logger.wav
  samplingrate: 96000Hz
  channels    : 16
  frames      : 17280000
  duration    : 180.000s

metadata:
  INFO:
      Bits            : 32
      Pins            : 1-CH2R,1-CH2L,1-CH3R,1-CH3L,2-CH2R,2-CH2L,2-CH3R,2-CH3L,3-CH2R,3-CH2L,3-CH3R,3-CH3L,4-CH2R,4-CH2L,4-CH3R,4-CH3L
      Gain            : 165.00mV
      uCBoard         : Teensy 4.1
      MACAdress       : 04:e9:e5:15:3e:95
      DateTimeOriginal: 2023-10-01T14:10:02
      Software        : TeeGrid R4-senors-logger v1.0
```

Running
```sh
audioconverter --help
```
prints
```text
usage: audiometadata [-h] [--version] [-f] [-m] [-c] file

Convert audio file formats.

positional arguments:
  file        audio file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
  -f          list file format only
  -m          list metadata only
  -c          list cues/markers only

version 1.2.0 by Benda-Lab (2020-2024)
```

"""
 
import sys
import argparse
import numpy as np
from .version import __version__, __year__
from .audiomodules import *
from .riffmetadata import metadata_riff, markers_riff


def metadata(filepath, store_empty=False):
    """ Read metadata of an audio file.

    Parameters
    ----------
    filepath: string or file handle
        The RIFF/WAVE file.
    store_empty: bool
        If `False` do not add meta data with empty values.

    Returns
    -------
    meta_data: nested dict
        Meta data contained in the audio file.  Keys of the nested
        dictionaries are always strings.  If the corresponding
        values are dictionaries, then the key is the section name
        of the metadata contained in the dictionary. All other
        types of values are values for the respective key. In
        particular they are strings. But other
        simple types like ints or floats are also allowed.

    Examples
    --------
    ```
    from audioio import metadata, print_metadata
    md = metadata('data.wav')
    print_metadata(md)
    ```
    """
    try:
        return metadata_riff(filepath, store_empty)
    except ValueError: # not a RIFF file
        return {}


def write_metadata_text(fh, meta, prefix='', indent=4):
    """Write meta data into a text/yaml file or stream.

    With the default parameters, the output is a valid yaml file.

    Parameters
    ----------
    fh: filename or stream
        If not a stream, the file with name `fh` is opened.
        Otherwise `fh` is used as a stream for writing.
    meta: nested dict
        Key-value pairs of metadata to be written into the file.
    prefix: str
        This string is written at the beginning of each line.
    indent: int
        Number of characters used for indentation of sections.

    Examples
    --------
    ```
    from audioio import write_metadata
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(hh=5)))
    write_metadata('info.txt', md)
    ```
    """
    
    def write_dict(df, meta, level):
        w = 0
        for k in meta:
            if not isinstance(meta[k], dict) and w < len(k):
                w = len(k)
        for k in meta:
            clevel = level*indent
            if isinstance(meta[k], dict):
                df.write(f'{prefix}{"":>{clevel}}{k}:\n')
                write_dict(df, meta[k], level+1)
            else:
                df.write(f'{prefix}{"":>{clevel}}{k:<{w}}: {meta[k]}\n')

    if hasattr(fh, 'write'):
        own_file = False
    else:
        own_file = True
        fh = open(fh, 'w')
    write_dict(fh, meta, 0)
    if own_file:
        fh.close()
        

def print_metadata(meta, prefix='', indent=4):
    """Write meta data to standard output.

    Parameters
    ----------
    meta: nested dict
        Key-value pairs of metadata to be written into the file.
    prefix: str
        This string is written at the beginning of each line.
    indent: int
        Number of characters used for indentation of sections.

    Examples
    --------
    ```
    >>> from audioio import print_metadata
    >>> md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(hh=5)), iiii=dict(jjj=6))
    >>> print_metadata(md)
    aaaa: 2
    bbbb:
        ccc: 3
        ddd: 4
        eee:
            hh: 5
    iiii:
        jjj: 6
    ```
    """
    write_metadata_text(sys.stdout, meta, prefix, indent)


def flatten_metadata(md, keep_sections=False, sep='__'):
    """Flatten hierarchical metadata to a single dictionary.

    Parameters
    ----------
    md: nested dict
        Metadata as returned by `metadata()`.
    keep_sections: bool
        If `True`, then prefix keys with section names, separated by `sep`.
    sep: str
        String for separating section names.

    Returns
    -------
    d: dict
        Non-nested dict containing all key-value pairs of `md`.

    Examples
    --------
    ```
    >>> from audioio import print_metadata, flatten_metadata
    >>> md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(hh=5)), iiii=dict(jjj=6))
    >>> print_metadata(md)
    aaaa: 2
    bbbb:
        ccc: 3
        ddd: 4
        eee:
            hh: 5
    iiii:
        jjj: 6
    
    >>> fmd = flatten_metadata(md, keep_sections=True)
    >>> print_metadata(fmd)
    aaaa         : 2
    bbbb__ccc    : 3
    bbbb__ddd    : 4
    bbbb__eee__hh: 5
    iiii__jjj    : 6
    ```
    """
    def flatten(cd, section):
        df = {}
        for k in cd:
            if isinstance(cd[k], dict):
                df.update(flatten(cd[k], section + k + sep))
            else:
                if keep_sections:
                    df[section+k] = cd[k]
                else:
                    df[k] = cd[k]
        return df

    return flatten(md, '')


def unflatten_metadata(md, sep='__'):
    """Unflatten a previously flattened metadata dictionary.

    Parameters
    ----------
    md: dict
        Flat dictionary with key-value pairs as obtained from
        `flatten_metadata()` with `keep_sections=True`.
    sep: str
        String that separates section names.

    Returns
    -------
    d: nested dict
        Hierarchical dictionary with sub-dictionaries and key-value pairs.

    Examples
    --------
    ```
    >>> from audioio import print_metadata, unflatten_metadata
    >>> fmd = {'aaaa': 2, 'bbbb.ccc': 3, 'bbbb.ddd': 4, 'bbbb.eee.hh': 5, 'iiii.jjj': 6}
    >>> print_metadata(fmd)
    aaaa       : 2
    bbbb.ccc   : 3
    bbbb.ddd   : 4
    bbbb.eee.hh: 5
    iiii.jjj   : 6
    
    >>> md = unflatten_metadata(fmd, '.')
    >>> print_metadata(md)
    aaaa: 2
    bbbb:
        ccc: 3
        ddd: 4
        eee:
            hh: 5
    iiii:
        jjj: 6
    ```
    """
    umd = {}       # unflattened metadata
    cmd = [umd]    # current metadata dicts for each level of the hierarchy
    csk = []       # current section keys
    for k in md:
        ks = k.split(sep)
        # go up the hierarchy:
        for kss in reversed(ks[:len(csk)]):
            if kss == csk[-1]:
                break
            csk.pop()
            cmd.pop()
        # add new sections:
        for kss in ks[len(csk):-1]:
            csk.append(kss)
            cmd[-1][kss] = {}
            cmd.append(cmd[-1][kss])
        # add key-value pair:
        cmd[-1][ks[-1]] = md[k]
    return umd


def add_metadata(metadata, md_list):
    """ Add or modify metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    md_list: list of str
        List of key-value pairs for updating the metadata.

    Returns
    -------
    metadata: nested dict
        Modified metadata.
    """
    if not md_list:
        return metadata
    fmd = flatten_metadata(metadata)
    for md in md_list:
        k, v = md.split('=')
        fmd[k.strip()] = v.strip()
    return unflatten_metadata(fmd)

            
def update_gain(md, fac):
    """Update gain setting in metadata.

    Searches for the first appearance of the keyword `Gain` (case
    insensitive) in the metadata hierarchy. If found, divide the gain
    value by `fac`.

    Parameters
    ----------
    md: nested dict
        Metadata to be updated.
    fac: float
        Factor that was used to scale the data.

    Returns
    -------
    done: bool
        True if gain has been found and set.

    """
    for k in md:
        if k.strip().upper() == 'GAIN':
            vs = md[k]
            if isinstance(vs, (int, float)):
                md[k] /= fac
            else:
                # extract initial number:
                n = len(vs)
                ip = n
                for i in range(len(vs)):
                    if vs[i] == '.':
                        ip = i + 1
                    if not vs[i] in '0123456789.+-':
                        n = i
                        break
                v = float(vs[:n])
                u = vs[n:].removesuffix('/V')  # fix some TeeGrid gains
                nd = n - ip
                md[k] = f'{v/fac:.{nd}f}{u}'
            return True
        elif isinstance(md[k], dict):
            if update_gain(md[k], fac):
                return True
    return False
    
            
def add_unwrap(metadata, thresh, clip):
    """Add unwrap infos to metadata.

    If `audiotools.unwrap()` was applied to the data, then this
    function adds relevant infos to the metadata. If there is an INFO
    section in the metadata, the unwrap infos are added to this
    section, otherwise they are added to the top level of the metadata
    hierarchy.

    The threshold `thresh` used for unwrapping is saved under the key
    'UnwrapThreshold'. If `clip` is larger than zero, then the clip
    level is saved under the key 'UnwrapClippedAmplitude'.

    Parameters
    ----------
    md: nested dict
        Metadata to be updated.
    thresh: float
        Threshold used for unwrapping.
    clip: float
        Level at which unwrapped data have been clipped.

    """
    md = metadata
    for k in metadata:
        if k.strip().upper() == 'INFO':
            md = metadata['INFO']
            break
    md['UnwrapThreshold'] = f'{thresh:.2f}'
    if clip > 0:
        md['UnwrapClippedAmplitude'] = f'{clip:.2f}'
    

def markers(filepath):
    """ Read markers of an audio file.

    Parameters
    ----------
    filepath: string or file handle
        The audio file.

    Returns
    -------
    locs: 2-D array of ints
        Marker positions (first column) and spans (second column)
        for each marker (rows).
    labels: 2-D array of string objects
        Labels (first column) and texts (second column)
        for each marker (rows).

    Examples
    --------
    ```
    from audioio import markers, print_markers
    locs, labels = markers('data.wav')
    print_markers(md)
    ```
    """
    try:
        return markers_riff(filepath)
    except ValueError: # not a RIFF file
        return np.zeros((0, 2), dtype=int), np.zeros((0, 2), dtype=object)


def write_markers(fh, locs, labels=None, sep=' ', prefix=''):
    """Write markers to a text file or stream.

    Parameters
    ----------
    fh: filename or stream
        If not a stream, the file with name `fh` is opened.
        Otherwise `fh` is used as a stream for writing.
    locs: 1-D or 2-D array of ints
        Marker positions (first column) and optional spans (second column)
        for each marker (rows).
    labels: 1-D or 2-D array of string objects
        Labels (first column) and optional texts (second column)
        for each marker (rows).
    sep: str
        Column separator.
    prefix: str
        This string is written at the beginning of each line.
    """
    if hasattr(fh, 'write'):
        own_file = False
    else:
        own_file = True
        fh = open(fh, 'w')
    # what do we have:
    if locs.ndim == 1:
        locs = locs.reshape(-1, 1)
    has_span = locs.shape[1] > 1
    has_labels = False
    has_text = False
    if labels is not None and len(labels) > 0:
        has_labels = True
        if labels.ndim == 1:
            labels = labels.reshape(-1, 1)
        has_text = labels.shape[1] > 1
    # table header:
    fh.write(f'{prefix}{"position":8}')
    if has_span:
        fh.write(f'{sep}{"span":6}')
    if has_labels:
        fh.write(f'{sep}{"label":10}')
    if has_text:
        fh.write(f'{sep}{"text"}')
    fh.write('\n')
    # table data:
    for i in range(len(locs)):
        fh.write(f'{prefix}{locs[i,0]:8}')
        if has_span:
            fh.write(f'{sep}{locs[i,1]:6}')
        if has_labels:
            fh.write(f'{sep}{labels[i,0]:10}')
        if has_text:
            fh.write(f'{sep}{labels[i,1]}')
    fh.write('\n')
    if own_file:
        fh.close()

        
def print_markers(locs, labels=None, sep=' ', prefix=''):
    """Write markers to standard output.

    Parameters
    ----------
    locs: 1-D or 2-D array of ints
        Marker positions (first column) and optional spans (second column)
        for each marker (rows).
    labels: 1-D or 2-D array of string objects
        Labels (first column) and optional texts (second column)
        for each marker (rows).
    sep: str
        Column separator.
    prefix: str
        This string is written at the beginning of each line.
    """
    write_markers(sys.stdout, locs, labels, sep, prefix)
        

def demo(filepathes, list_format, list_metadata, list_cues):
    """Print metadata and markers of audio files.

    Parameters
    ----------
    filepathes: list of str
        Pathes of audio files.
    list_format: bool
        If True, list file format only.
    list_metadata: bool
        If True, list metadata only.
    list_cues: bool
        If True, list markers/cues only.
    """
    from .audioloader import AudioLoader
    for filepath in filepathes:
        if list_cues:
            locs, labels = markers(filepath)
            print_markers(locs, labels)
        elif list_metadata:
            meta_data = metadata(filepath, store_empty=False)
            print_metadata(meta_data)
        elif list_format:
            with AudioLoader(filepath, 1, 0) as sf:
                fmt_md = dict(filepath=filepath,
                              samplingrate=f'{sf.samplerate:.0f}Hz',
                              channels=sf.shape[1],
                              frames=sf.shape[0],
                              duration=f'{sf.shape[0]/sf.samplerate:.3f}s')
                print_metadata(fmt_md)
        else:
            meta_data = metadata(filepath, store_empty=False)
            locs, labels = markers(filepath)
            print('file:')
            with AudioLoader(filepath, 1, 0) as sf:
                fmt_md = dict(filepath=filepath,
                              samplingrate=f'{sf.samplerate:.0f}Hz',
                              channels=sf.shape[1],
                              frames=sf.shape[0],
                              duration=f'{sf.shape[0]/sf.samplerate:.3f}s')
                print_metadata(fmt_md, '  ')
            if len(meta_data) > 0:
                print()
                print('metadata:')
                print_metadata(meta_data, '  ')
            if len(locs) > 0:
                print()
                print('markers:')
                print_markers(locs, labels)
            if len(filepathes) > 0:
                print()
        if len(filepathes) > 0:
            print()


def main(*cargs):
    """Call demo with command line arguments.

    Parameters
    ----------
    cargs: list of strings
        Command line arguments as provided by sys.argv[1:]
    """
    # command line arguments:
    parser = argparse.ArgumentParser(add_help=True,
        description='Convert audio file formats.',
        epilog=f'version {__version__} by Benda-Lab (2020-{__year__})')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-f', dest='dataformat', action='store_true',
                        help='list file format only')
    parser.add_argument('-m', dest='metadata', action='store_true',
                        help='list metadata only')
    parser.add_argument('-c', dest='cues', action='store_true',
                        help='list cues/markers only')
    parser.add_argument('files', type=str, nargs='+',
                        help='audio file')
    if len(cargs) == 0:
        cargs = None
    args = parser.parse_args(cargs)

    demo(args.files, args.dataformat, args.metadata, args.cues)


if __name__ == "__main__":
    main(*sys.argv[1:])

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

"""
 
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

    Example
    -------

    ```
    md = aio.metadata('data.wav')
    aio.print_metadata(md)
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
    """
    write_metadata_text(sys.stdout, meta, prefix, indent)


def flatten_metadata(md, keep_sections=False):
    """Flatten hierarchical metadata to a single dictionary.

    Parameters
    ----------
    md: nested dict
        Metadata as returned by `metadata()`.
    keep_sections: bool
        If `True`, then prefix keys with section names, separated by '.'.

    Returns
    -------
    d: dict
        Non-nested dict containing all key-value pairs of `md`.
    """
    def flatten(cd, section):
        df = {}
        for k in cd:
            if isinstance(cd[k], dict):
                df.update(flatten(cd[k], section + k + '.'))
            else:
                if keep_sections:
                    df[section+k] = cd[k]
                else:
                    df[k] = cd[k]
        return df

    return flatten(md, '')


def unflatten_metadata(md):
    """Unflatten a previously flattened metadata dictionary.

    Parameters
    ----------
    md: dict
        Flat dictionary with key-value pairs as obtained from
        `flatten_metadata()` with `keep_sections=True`.

    Returns
    -------
    d: nested dict
        Hierarchical dictionary with sub-dictionaries and key-value pairs.
    """
    umd = {}       # unflattened metadata
    cmd = [umd]    # current metadata dicts for each level of the hierarchy
    csk = []       # current section keys
    for k in md:
        ks = k.split('.')
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
    if len(locs) == 0:
        return
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
        

def demo(filepath, list_metadata, list_cues):
    """Print metadata and markers of file.

    Parameters
    ----------
    filepath: string
        Path of anaudio file.
    list_metadata: bool
        If True, list metadata only.
    list_cues: bool
        If True, list markers/cues only.
    """
    if list_cues:
        locs, labels = markers(filepath)
        print_markers(locs, labels)
    elif list_metadata:
        meta_data = metadata(filepath, store_empty=False)
        print_metadata(meta_data)
    else:
        meta_data = metadata(filepath, store_empty=False)
        locs, labels = markers(filepath)
        print('file:')
        print(f'  {filepath}')
        if len(meta_data) > 0:
            print()
            print('metadata:')
            print_metadata(meta_data, '  ')
        if len(locs) > 0:
            print()
            print('markers:')
            print_markers(locs, labels)


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
    parser.add_argument('-m', dest='metadata', action='store_true',
                        help='list metadata only')
    parser.add_argument('-c', dest='cues', action='store_true',
                        help='list cues/markers only')
    parser.add_argument('file', type=str,
                        help='audio file')
    if len(cargs) == 0:
        cargs = None
    args = parser.parse_args(cargs)

    demo(args.file, args.metadata, args.cues)


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

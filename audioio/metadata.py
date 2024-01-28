"""Loading metadata and marker lists from audio files.

- `metadata()`: read metadata of an audio file.
- `flatten_metadata()`: Flatten hierachical metadata to a single dictionary.
- `unflatten_metadata()`: Unflatten a previously flattened metadata dictionary.
- `markers()`: read markers of an audio file.

For a demo run the module as:
```
python -m audioio.metadata audiofile.wav
```
"""
 
import warnings
import os.path
from .audiomodules import *
from .wavemetadata import metadata_wave, markers_wave


def metadata(filepath, store_empty=False):
    """ Read metadata of an audio file.

    Parameters
    ----------
    filepath: string or file handle
        The wave file.
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
    """
    try:
        return metadata_wave(filepath, store_empty)
    except ValueError: # not a wave file
        return {}


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
    umd = {}
    cmd = [umd]
    for k in md:
        ks = k.split('.')
        if len(ks) > len(cmd):
            # TODO: that can be several levels of subsections!
            cmd[-1][ks[-2]] = {}
            cmd.append(cmd[-1][ks[-2]])
        elif len(ks) < len(cmd):
            # TODO: that can be several levels of subsections!
            cmd.pop()
        elif len(ks) > 1 and not ks[-2] in cmd[-2]:
            # TODO: that can be several levels of subsections!
            cmd[-2][ks[-2]] = {}
            cmd[-1] = cmd[-2][ks[-2]]
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
        Positions (first column) and spans (second column)
        for each marker (rows).
    labels: 2-D array of string objects
        Marker IDs (first column), labels (second column) and
        texts (third column) for each marker (rows).
    """
    try:
        return markers_wave(filepath)
    except ValueError: # not a wave file
        return np.zeros((0, 3), dtype=int), np.zeros((0, 2), dtype=np.object)


def demo(filepath):
    """Print metadata and markers of file.

    Parameters
    ----------
    filepath: string
        Path of anaudio file.
    """
    def print_meta_data(meta_data, level=0):
        for sk in meta_data:
            md = meta_data[sk]
            if isinstance(md, dict):
                print(f'{"":<{level*4}}{sk}:')
                print_meta_data(md, level+1)
            else:
                v = str(md).replace('\n', '.')
                print(f'{"":<{level*4}s}{sk:<20s}: {v}')
        
    # read meta data:
    meta_data = metadata(filepath, store_empty=False)
    
    # print meta data:
    print()
    print('metadata:')
    print_meta_data(meta_data)
            
    # read cues:
    locs, labels = markers(filepath)
    
    # print marker table:
    if len(locs) > 0:
        print()
        print('markers:')
        print(f'{"id":5} {"position":10} {"span":8} {"label":10} {"text":10}')
        for i in range(len(locs)):
            if i < len(labels):
                print(f'{locs[i,0]:5} {locs[i,-2]:10} {locs[i,-1]:8} {labels[i,0]:10} {labels[i,1]:30}')
            else:
                print(f'{locs[i,0]:5} {locs[i,-2]:10} {locs[i,-1]:8} {"-":10} {"-":10}')


def main(*args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv[1:]
    """
    if len(args) == 0 or (args[0] == '-h' or args[0] == '--help'):
        print()
        print('Usage:')
        print('  python -m audioio.metadata [--help] <audio/file.wav>')
        print()
        return

    demo(args[0])


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

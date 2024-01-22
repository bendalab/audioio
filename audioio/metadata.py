"""Loading metadata from audio files.

- `load_metadata()`: read meta-data of an audio file.
- `flatten_metadata()`: Flatten hierachical metadata to a single dictionary.
- `unflatten_metadata()`: Unflatten a previously flattened metadata dictionary.

For a demo run the module as:
```
python -m audioio.metadata audiofile.wav
```
"""
 
import warnings
import os.path
from .audiomodules import *
from .wavemetadata import metadata_wave


def load_metadata(file, store_empty=False, first_only=False, verbose=0):
    """ Read meta-data of an audio file.

    Parameters
    ----------
    file: string or file handle
        The wave file.
    store_empty: bool
        If `False` do not add meta data with empty values.
    first_only: bool
        If `False` only store the first element of a list.
    verbose: int
        Verbosity level.

    Returns
    -------
    meta_data: nested dict
        Meta data contained in the audio file.  Keys of the nested
        dictionaries are always strings.  If the corresponding
        values are dictionaries, then the key is the section name
        of the metadata contained in the dictionary. All other
        types of values are values for the respective key. In
        particular they are strings, or list of strings. But other
        simple types like ints or floats are also allowed.
    cues: list of dict
        Cues contained in the wave file. Each item in the list provides

        - 'id': Id of the cue.
        - 'pos': Position of the cue in samples.
        - 'length': Number of samples the cue covers (optional).
        - 'repeats': How often the cue segment should be repeated (optional).
        - 'label': Label of the cue (optional).
        - 'note': Note on the cue (optional).
        - 'text': Description of cue segment (optional).
    """
    try:
        return metadata_wave(file, store_empty, verbose)
    except ValueError: # not a wave file
        return {}, []


def flatten_metadata(md, keep_sections=False):
    """Flatten hierachical metadata to a single dictionary.

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


def main(args):
    """Call demo with command line arguments.

    Parameters
    ----------
    args: list of strings
        Command line arguments as provided by sys.argv
    """
    print("Checking audioloader module ...")

    help = False
    plot = False
    file_path = None
    mod = False
    for arg in args[1:]:
        if mod:
            if not select_module(arg):
                print('can not select module %s that is not installed' % arg)
                return
            mod = False
        elif arg == '-h':
            help = True
            break
        elif arg == '-p':
            plot = True
        elif arg == '-m':
            mod = True
        else:
            file_path = arg
            break

    if help:
        print('')
        print('Usage:')
        print('  python -m audioio.audioloader [-m <module>] [-p] <audio/file.wav>')
        print('  -m: audio module to be used')
        print('  -p: plot loaded data')
        return

    if plot:
        import matplotlib.pyplot as plt

    demo(file_path, plot)


if __name__ == "__main__":
    import sys
    main(sys.argv)

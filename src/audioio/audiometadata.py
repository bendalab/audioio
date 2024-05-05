"""Working with metadata.

To interface the various ways metadata are stored in audio files, the
`audioio` package uses nested dictionaries.  The keys are always
strings. Values are strings, integers, floats, datetimes, or other
types. Value strings can also be numbers followed by a unit,
e.g. "4.2mV". For defining subsections of key-value pairs, values can
be dictionaries. The dictionaries can be nested to arbitrary depth.

```txt
>>> from audioio import print_metadata
>>> md = dict(Recording=dict(Experimenter='John Doe',
                             DateTimeOriginal='2023-10-01T14:10:02',
                             Count=42),
               Hardware=dict(Amplifier='Teensy_Amp 4.1',
                             Highpass='10Hz',
                             Gain='120mV'))
>>> print_metadata(md)
Recording:
    Experimenter    : John Doe
    DateTimeOriginal: 2023-10-01T14:10:02
    Count           : 42
Hardware:
    Amplifier: Teensy_Amp 4.1
    Highpass : 10Hz
    Gain     : 120mV
```

Often, audio files have very specific ways to store metadata. You can
enforce using these by putting them into a dictionary that is added to
the metadata with a key having the name of the metadata type you want,
e.g. the "INFO", "BEXT", "iXML", and "GUAN" chunks of RIFF/WAVE files.

## Functions

The `audiometadata` module provides functions for handling and
manipulating these nested dictionaries. Many functions take keys as
arguments for finding or setting specific key-value pairs. These keys
can be the key of a specific item of a (sub-) dictionary, no matter on
which level of the metadata hierarchy it is. For example, simply
searching for "Highpass" retrieves the corrseponding value "10Hz",
although "Highpass" is contained in the sub-dictionary (or "section")
with key "Hardware". The same item can also be specified together with
its parent keys: "Hardware.Highpass". Parent keys (or section keys)
are by default separated by '.', but all functions have a `sep`
key-word that specifies the string separating section names in
keys. Key matching is case insensitive.

Since the same items are named by many different keys in the different
types of metadata data models, the functions also take lists of keys
as arguments.

Do not forget that you can easily manipulate the metadata by means of
the standard functions of dictionaries.

If you need to make a copy of the metadata use `deepcopy`:
```
from copy import deepcopy
md_orig = deepcopy(md)
```

### Output

Write nested dictionaries as texts:

- `write_metadata_text()`: write meta data into a text/yaml file.
- `print_metadata()`: write meta data to standard output.

### Flatten

Conversion between nested and flat dictionaries:

- `flatten_metadata()`: flatten hierachical metadata to a single dictionary.
- `unflatten_metadata()`: unflatten a previously flattened metadata dictionary.

### Parse numbers with units

- `parse_number()`: parse string with number and unit.
- `change_unit()`: scale numerical value to a new unit.

### Find and get values

Find keys and get their values parsed and converted to various types:

- `find_key()`: find dictionary in metadata hierarchy containing the specified key.
- `get_number_unit()`: find a key in metadata and return its number and unit.
- `get_number()`: find a key in metadata and return its value in a given unit.
- `get_int()`: find a key in metadata and return its integer value.
- `get_bool()`: find a key in metadata and return its boolean value.
- `get_datetime()`: find keys in metadata and return a datatime.
- `get_str()`: find a key in metadata and return its string value.

### Organize metadata

Add and remove metadata:

- `strlist_to_dict()`: convert list of key-value-pair strings to dictionary.
- `add_sections()`: add sections to metadata dictionary.
- `set_metadata()`: set values of existing metadata.
- `add_metadata()`: add or modify key-value pairs.
- `move_metadata()`: remove a key from metadata and add it to a dictionary.
- `remove_metadata()`: remove key-value pairs or sections from metadata.
- `cleanup_metadata()`: remove empty sections from metadata.

### Special metadata fields

Retrieve and set specific metadata:

- `get_gain()`: get gain and unit from metadata.
- `update_gain()`: update gain setting in metadata.
- `update_starttime()`: update start-of-recording times in metadata.
- `bext_history_str()`: assemble a string for the BEXT CodingHistory field.
- `add_history()`: add a string describing coding history to metadata.
- `add_unwrap()`: add unwrap infos to metadata.

Lists of standard keys:

- `default_starttime_keys`: keys of times of start of the recording.
- `default_timeref_keys`: keys of integer time references.
- `default_gain_keys`: keys of gain settings.
- `default_history_keys`: keys of strings describing coding history.


## Command line script

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


Alternatively, the script can be run from the module as:
```
python -m src.audioio.metadata audiofile.wav
```

Running
```sh
audiometadata --help
```
prints
```text
usage: audiometadata [-h] [--version] [-f] [-m] [-c] [-t] files [files ...]

Convert audio file formats.

positional arguments:
  files       audio file

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
  -f          list file format only
  -m          list metadata only
  -c          list cues/markers only
  -t          list tags of all riff/wave chunks contained in the file

version 2.0.0 by Benda-Lab (2020-2024)
```

"""
 
import sys
import argparse
import numpy as np
import datetime as dt
from .version import __version__, __year__


def write_metadata_text(fh, meta, prefix='', indent=4, replace=None):
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
    replace: char or None
        If specified, replace special characters by this character.

    Examples
    --------
    ```
    from audioio import write_metadata
    md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(hh=5)))
    write_metadata('info.txt', md)
    ```
    """
    
    def write_dict(df, md, level, smap):
        w = 0
        for k in md:
            if not isinstance(md[k], dict) and w < len(k):
                w = len(k)
        for k in md:
            clevel = level*indent
            if isinstance(md[k], dict):
                df.write(f'{prefix}{"":>{clevel}}{k}:\n')
                write_dict(df, md[k], level+1, smap)
            else:
                value = md[k]
                if isinstance(value, (list, tuple)):
                    value = ', '.join([f'{v}' for v in value])
                else:
                    value = f'{value}'
                value = value.replace('\r\n', r'\n')
                value = value.replace('\n', r'\n')
                if len(smap) > 0:
                    value = value.translate(smap)
                df.write(f'{prefix}{"":>{clevel}}{k:<{w}}: {value}\n')

    if not meta:
        return
    if hasattr(fh, 'write'):
        own_file = False
    else:
        own_file = True
        fh = open(fh, 'w')
    smap = {}
    if replace:
        smap = str.maketrans('\r\n\t\x00', ''.join([replace]*4))
    write_dict(fh, meta, 0, smap)
    if own_file:
        fh.close()
        

def print_metadata(meta, prefix='', indent=4, replace=None):
    """Write meta data to standard output.

    Parameters
    ----------
    meta: nested dict
        Key-value pairs of metadata to be written into the file.
    prefix: str
        This string is written at the beginning of each line.
    indent: int
        Number of characters used for indentation of sections.
    replace: char or None
        If specified, replace special characters by this character.

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
    write_metadata_text(sys.stdout, meta, prefix, indent, replace)


def flatten_metadata(md, keep_sections=False, sep='.'):
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
    aaaa       : 2
    bbbb.ccc   : 3
    bbbb.ddd   : 4
    bbbb.eee.hh: 5
    iiii.jjj   : 6
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


def unflatten_metadata(md, sep='.'):
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
    
    >>> md = unflatten_metadata(fmd)
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
        for i in range(len(csk) - len(ks)):
            csk.pop()
            cmd.pop()
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


def parse_number(s):
    """Parse string with number and unit.

    Parameters
    ----------
    s: str, float, or int
        String to be parsed. The initial part of the string is
        expected to be a number, the part following the number is
        interpreted as the unit. If float or int, then return this
        as the value with empty unit.

    Returns
    -------
    v: None, int, or float
        Value of the string as float. Without decimal point, an int is returned.
        If the string does not contain a number, None is returned.
    u: str
        Unit that follows the initial number.
    n: int
        Number of digits behind the decimal point.

    Examples
    --------

    ```
    >>> from audioio import parse_number

    # integer:
    >>> parse_number('42')
    (42, '', 0)

    # integer with unit:
    >>> parse_number('42ms')
    (42, 'ms', 0)

    # float with unit:
    >>> parse_number('42.ms')
    (42.0, 'ms', 0)

    # float with unit:
    >>> parse_number('42.3ms')
    (42.3, 'ms', 1)

    # float with space and unit:
    >>> parse_number('423.17 Hz')
    (423.17, 'Hz', 2)
    ```

    """
    if not isinstance(s, str):
        if isinstance(s, int):
            return s, '', 0
        if isinstance(s, float):
            return s, '', 5
        else:
            return None, '', 0
    n = len(s)
    ip = n
    have_point = False
    for i in range(len(s)):
        if s[i] == '.':
            if have_point:
                n = i
                break
            have_point = True
            ip = i + 1
        if not s[i] in '0123456789.+-':
            n = i
            break
    if n == 0:
        return None, s, 0
    v = float(s[:n]) if have_point else int(s[:n])
    u = s[n:].strip()
    nd = n - ip if n >= ip else 0
    return v, u, nd


unit_prefixes = {'Deka': 1e1, 'deka': 1e1, 'Hekto': 1e2, 'hekto': 1e2,
                 'kilo': 1e3, 'Kilo': 1e3, 'Mega': 1e6, 'mega': 1e6,
                 'Giga': 1e9, 'giga': 1e9, 'Tera': 1e12, 'tera': 1e12, 
                 'Peta': 1e15, 'peta': 1e15, 'Exa': 1e18, 'exa': 1e18, 
                 'Dezi': 1e-1, 'dezi': 1e-1, 'Zenti': 1e-2, 'centi': 1e-2,
                 'Milli': 1e-3, 'milli': 1e-3, 'Micro': 1e-6, 'micro': 1e-6, 
                 'Nano': 1e-9, 'nano': 1e-9, 'Piko': 1e-12, 'piko': 1e-12, 
                 'Femto': 1e-15, 'femto': 1e-15, 'Atto': 1e-18, 'atto': 1e-18, 
                 'da': 1e1, 'h': 1e2, 'K': 1e3, 'k': 1e3, 'M': 1e6,
                 'G': 1e9, 'T': 1e12, 'P': 1e15, 'E': 1e18, 
                 'd': 1e-1, 'c': 1e-2, 'mu': 1e-6, 'u': 1e-6, 'm': 1e-3,
                 'n': 1e-9, 'p': 1e-12, 'f': 1e-15, 'a': 1e-18}
""" SI prefixes for units with corresponding factors. """


def change_unit(val, old_unit, new_unit):
    """Scale numerical value to a new unit.

    Adapted from https://github.com/relacs/relacs/blob/1facade622a80e9f51dbf8e6f8171ac74c27f100/options/src/parameter.cc#L1647-L1703

    Parameters
    ----------
    val: float
        Value given in `old_unit`.
    old_unit: str
        Unit of `val`.
    new_unit: str
        Requested unit of return value.

    Returns
    -------
    new_val: float
        The input value `val` scaled to `new_unit`.

    Examples
    --------

    ```
    >>> from audioio import change_unit
    >>> change_unit(5, 'mm', 'cm')
    0.5

    >>> change_unit(5, '', 'cm')
    5.0

    >>> change_unit(5, 'mm', '')
    5.0

    >>> change_unit(5, 'cm', 'mm')
    50.0

    >>> change_unit(4, 'kg', 'g')
    4000.0

    >>> change_unit(12, '%', '')
    0.12

    >>> change_unit(1.24, '', '%')
    124.0

    >>> change_unit(2.5, 'min', 's')
    150.0

    >>> change_unit(3600, 's', 'h')
    1.0

    ```

    """
    # missing unit?
    if not old_unit and not new_unit:
        return val
    if not old_unit and new_unit != '%':
        return val
    if not new_unit and old_unit != '%':
        return val

    # special units that directly translate into factors:
    unit_factors = {'%': 0.01, 'hour': 60.0*60.0, 'h': 60.0*60.0, 'min': 60.0}

    # parse old unit:
    f1 = 1.0
    if old_unit in unit_factors:
        f1 = unit_factors[old_unit]
    else:
        for k in unit_prefixes:
            if len(old_unit) > len(k) and old_unit[:len(k)] == k:
                f1 = unit_prefixes[k];
  
    # parse new unit:
    f2 = 1.0
    if new_unit in unit_factors:
        f2 = unit_factors[new_unit]
    else:
        for k in unit_prefixes:
            if len(new_unit) > len(k) and new_unit[:len(k)] == k:
                f2 = unit_prefixes[k];
  
    return val*f1/f2


def find_key(metadata, key, sep='.'):
    """Find dictionary in metadata hierarchy containing the specified key.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    key: str
        Key to be searched for (case insensitive).
        May contain section names separated by `sep`, i.e.
        "aaa.bbb.ccc" searches "ccc" (can be key-value pair or section)
        in section "bbb" that needs to be a subsection of section "aaa".
    sep: str
        String that separates section names in `key`.

    Returns
    -------
    md: dict
        The innermost dictionary matching some sections of the search key.
        If `key` is not at all contained in the metadata,
        the top-level dictionary is returned.
    key: str
        The part of the search key that was not found in `md`, or the
        the final part of the search key, found in `md`.

    Examples
    --------

    Independent of whether found or not found, you can assign to the
    returned dictionary with the returned key.

    ```
    >>> from audioio import print_metadata, find_key
    >>> md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(ff=5)), gggg=dict(hhh=6))
    >>> print_metadata(md)
    aaaa: 2
    bbbb:
        ccc: 3
        ddd: 4
        eee:
            ff: 5
    gggg:
        hhh: 6

    >>> m, k = find_key(md, 'bbbb.ddd')
    >>> m[k] = 10
    >>> print_metadata(md)
    aaaa: 2
    bbbb:
        ccc: 3
        ddd: 10
    ...

    >>> m, k = find_key(md, 'hhh')
    >>> m[k] = 12
    >>> print_metadata(md)
    ...
    gggg:
        hhh: 12

    >>> m, k = find_key(md, 'bbbb.eee.xx')
    >>> m[k] = 42
    >>> print_metadata(md)
    ...
        eee:
            ff: 5
            xx: 42
    ...
    ```

    When searching for sections, the one conaining the searched section
    is returned:
    ```py
    >>> m, k = find_key(md, 'eee')
    >>> m[k]['yy'] = 46
    >>> print_metadata(md)
    ...
        eee:
            ff: 5
            xx: 42
            yy: 46
    ...
    ```

    """
    def find_keys(metadata, keys):
        key = keys[0].strip().upper()
        for k in metadata:
            if k.upper() == key:
                if len(keys) == 1:
                    # found key:
                    return True, metadata, k
                elif isinstance(metadata[k], dict): 
                    # keep searching within the next section:
                    return find_keys(metadata[k], keys[1:])
        # search in subsections:
        for k in metadata:
            if isinstance(metadata[k], dict):
                found, mm, kk = find_keys(metadata[k], keys)
                if found:
                    return True, mm, kk
        # nothing found:
        return False, metadata, sep.join(keys)

    if not metadata:
        return {}, None
    ks = key.strip().split(sep)
    found, mm, kk = find_keys(metadata, ks)
    return mm, kk


def get_number_unit(metadata, keys, sep='.', default=None,
                    default_unit='', remove=False):
    """Find a key in metadata and return its number and unit.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    keys: str or list of str
        Keys in the metadata to be searched for (case insensitive).
        Value of the first key found is returned.
        May contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
    sep: str
        String that separates section names in `key`.
    default: None, int, or float
        Returned value if `key` is not found or the value does
        not contain a number.
    default_unit: str
        Returned unit if `key` is not found or the key's value does
        not have a unit.
    remove: bool
        If `True`, remove the found key from `metadata`.

    Returns
    -------
    v: None, int, or float
        Value referenced by `key` as float.
        Without decimal point, an int is returned.
        If none of the `keys` was found or
        the key`s value does not contain a number,
        then `default` is returned.
    u: str
        Corresponding unit.

    Examples
    --------

    ```
    >>> from audioio import get_number_unit
    >>> md = dict(aaaa='42', bbbb='42.3ms')

    # integer:
    >>> get_number_unit(md, 'aaaa')
    (42, '')

    # float with unit:
    >>> get_number_unit(md, 'bbbb')
    (42.3, 'ms')

    # two keys:
    >>> get_number_unit(md, ['cccc', 'bbbb'])
    (42.3, 'ms')

    # not found:
    >>> get_number_unit(md, 'cccc')
    (None, '')

    # not found with default value:
    >>> get_number_unit(md, 'cccc', default=1.0, default_unit='a.u.')
    (1.0, 'a.u.')
    ```

    """
    if not metadata:
        return default, default_unit
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    value = default
    unit = default_unit
    for key in keys:
        m, k = find_key(metadata, key, sep)
        if k in m:
            v, u, _ = parse_number(m[k])
            if v is not None:
                if not u:
                    u = default_unit
                if remove:
                    del m[k]
                return v, u
            elif u and unit == default_unit:
                unit = u
    return value, unit


def get_number(metadata, unit, keys, sep='.', default=None, remove=False):
    """Find a key in metadata and return its value in a given unit.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    unit: str
        Unit in which to return numerical value referenced by one of the `keys`.
    keys: str or list of str
        Keys in the metadata to be searched for (case insensitive).
        Value of the first key found is returned.
        May contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
    sep: str
        String that separates section names in `key`.
    default: None, int, or float
        Returned value if `key` is not found or the value does
        not contain a number.
    remove: bool
        If `True`, remove the found key from `metadata`.

    Returns
    -------
    v: None or float
        Value referenced by `key` as float scaled to `unit`.
        If none of the `keys` was found or
        the key`s value does not contain a number,
        then `default` is returned.

    Examples
    --------

    ```
    >>> from audioio import get_number
    >>> md = dict(aaaa='42', bbbb='42.3ms')

    # milliseconds to seconds:
    >>> get_number(md, 's', 'bbbb')
    0.0423

    # milliseconds to microseconds:
    >>> get_number(md, 'us', 'bbbb')
    42300.0

    # value without unit is not scaled:
    >>> get_number(md, 'Hz', 'aaaa')
    42

    # two keys:
    >>> get_number(md, 's', ['cccc', 'bbbb'])
    0.0423

    # not found:
    >>> get_number(md, 's', 'cccc')
    None

    # not found with default value:
    >>> get_number(md, 's', 'cccc', default=1.0)
    1.0
    ```

    """
    v, u = get_number_unit(metadata, keys, sep, None, unit, remove)
    if v is None:
        return default
    else:
        return change_unit(v, u, unit)


def get_int(metadata, keys, sep='.', default=None, remove=False):
    """Find a key in metadata and return its integer value.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    keys: str or list of str
        Keys in the metadata to be searched for (case insensitive).
        Value of the first key found is returned.
        May contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
    sep: str
        String that separates section names in `key`.
    default: None or int
        Return value if `key` is not found or the value does
        not contain an integer.
    remove: bool
        If `True`, remove the found key from `metadata`.

    Returns
    -------
    v: None or int
        Value referenced by `key` as integer.
        If none of the `keys` was found,
        the key's value does not contain a number or represents
        a floating point value, then `default` is returned.

    Examples
    --------

    ```
    >>> from audioio import get_int
    >>> md = dict(aaaa='42', bbbb='42.3ms')

    # integer:
    >>> get_int(md, 'aaaa')
    42

    # two keys:
    >>> get_int(md, ['cccc', 'aaaa'])
    42

    # float:
    >>> get_int(md, 'bbbb')
    None

    # not found:
    >>> get_int(md, 'cccc')
    None

    # not found with default value:
    >>> get_int(md, 'cccc', default=0)
    0
    ```

    """
    if not metadata:
        return default
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    for key in keys:
        m, k = find_key(metadata, key, sep)
        if k in m:
            v, _, n = parse_number(m[k])
            if v is not None and n == 0:
                if remove:
                    del m[k]
                return int(v)
    return default


def get_bool(metadata, keys, sep='.', default=None, remove=False):
    """Find a key in metadata and return its boolean value.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    keys: str or list of str
        Keys in the metadata to be searched for (case insensitive).
        Value of the first key found is returned.
        May contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
    sep: str
        String that separates section names in `key`.
    default: None or bool
        Return value if `key` is not found or the value does
        not specify a boolean value.
    remove: bool
        If `True`, remove the found key from `metadata`.

    Returns
    -------
    v: None or bool
        Value referenced by `key` as boolean.
        True if 'true', 'yes' (case insensitive) or any number larger than zero.
        False if 'false', 'no' (case insensitive) or any number equal to zero.
        If none of the `keys` was found or
        the key's value does specify a boolean value,
        then `default` is returned.

    Examples
    --------

    ```
    >>> from audioio import get_bool
    >>> md = dict(aaaa='TruE', bbbb='No', cccc=0, dddd=1, eeee=True, ffff='ui')

    # case insensitive:
    >>> get_bool(md, 'aaaa')
    True

    >>> get_bool(md, 'bbbb')
    False

    >>> get_bool(md, 'cccc')
    False

    >>> get_bool(md, 'dddd')
    True

    >>> get_bool(md, 'eeee')
    True

    # not found:
    >>> get_bool(md, 'ffff')
    None

    # two keys (string is preferred over number):
    >>> get_bool(md, ['cccc', 'aaaa'])
    True

    # two keys (take first match):
    >>> get_bool(md, ['cccc', 'ffff'])
    False

    # not found with default value:
    >>> get_bool(md, 'ffff', default=False)
    False
    ```

    """
    if not metadata:
        return default
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    val = default
    mv = None
    kv = None
    for key in keys:
        m, k = find_key(metadata, key, sep)
        if k in m and not isinstance(m[k], dict):
            vs = m[k]
            v, _, _ = parse_number(vs)
            if v is not None:
                val = abs(v) > 1e-8
                mv = m
                kv = k
            elif isinstance(vs, str):
                if vs.upper() in ['TRUE', 'T', 'YES', 'Y']:
                    if remove:
                        del m[k]
                    return True
                if vs.upper() in ['FALSE', 'F', 'NO', 'N']:
                    if remove:
                        del m[k]
                    return False
    if not mv is None and not kv is None and remove:
        del mv[kv]
    return val


default_starttime_keys = [['DateTimeOriginal'],
                          ['OriginationDate', 'OriginationTime'],
                          ['Location_Time'],
                          ['Timestamp']]
"""Default keys of times of start of the recording in metadata.
Used by `get_datetime()` and `update_starttime()` functions.
"""

def get_datetime(metadata, keys=default_starttime_keys,
                 sep='.', default=None, remove=False):
    """Find keys in metadata and return a datatime.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    keys: tuple of str or list of tuple of str
        Datetimes can be stored in metadata as two separate key-value pairs,
        one for the date and one for the time. Or by a single key-value pair
        for a date-time values. This is why the keys need to be specified in
        tuples with one or tow keys.
        Value of the first tuple of keys found is returned.
        Keys may contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
        You can modify the default keys via the `default_starttime_keys` list
        of the `audiometadata` module.
    sep: str
        String that separates section names in `key`.
    default: None or str
        Return value if `key` is not found or the value does
        not contain a string.
    remove: bool
        If `True`, remove the found key from `metadata`.

    Returns
    -------
    v: None or datetime
        Datetime referenced by `keys`.
        If none of the `keys` was found, then `default` is returned.

    Examples
    --------

    ```
    >>> from audioio import get_datetime
    >>> import datetime as dt
    >>> md = dict(date='2024-03-02', time='10:42:24',
                  datetime='2023-04-15T22:10:00')

    # separate date and time:
    >>> get_datetime(md, ('date', 'time'))
    datetime.datetime(2024, 3, 2, 10, 42, 24)

    # single datetime:
    >>> get_datetime(md, ('datetime',))
    datetime.datetime(2023, 4, 15, 22, 10)

    # two alternative key tuples:
    >>> get_datetime(md, [('aaaa',), ('date', 'time')])
    datetime.datetime(2024, 3, 2, 10, 42, 24)

    # not found:
    >>> get_datetime(md, ('cccc',))
    None

    # not found with default value:
    >>> get_datetime(md, ('cccc', 'dddd'),
                     default=dt.datetime(2022, 2, 22, 22, 2, 12))
    datetime.datetime(2022, 2, 22, 22, 2, 12)
    ```

    """
    if not metadata:
        return default
    if len(keys) > 0 and isinstance(keys[0], str):
        keys = (keys,)
    for keyp in keys:
        if len(keyp) == 1:
            m, k = find_key(metadata, keyp[0], sep)
            if k in m:
                v = m[k]
                if isinstance(v, dt.datetime):
                    if remove:
                        del m[k]
                    return v
                elif isinstance(v, str):
                    if remove:
                        del m[k]
                    return dt.datetime.fromisoformat(v)
        else:
            md, kd = find_key(metadata, keyp[0], sep)
            if not kd in md:
                continue
            if isinstance(md[kd], dt.date):
                date = md[kd]
            elif isinstance(md[kd], str):
                date = dt.date.fromisoformat(md[kd])
            else:
                continue
            mt, kt = find_key(metadata, keyp[1], sep)
            if not kt in mt:
                continue
            if isinstance(mt[kt], dt.time):
                time = mt[kt]
            elif isinstance(mt[kt], str):
                time = dt.time.fromisoformat(mt[kt])
            else:
                continue
            if remove:
                del md[kd]
                del mt[kt]
            return dt.datetime.combine(date, time)
    return default


def get_str(metadata, keys, sep='.', default=None, remove=False):
    """Find a key in metadata and return its string value.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    keys: str or list of str
        Keys in the metadata to be searched for (case insensitive).
        Value of the first key found is returned.
        May contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
    sep: str
        String that separates section names in `key`.
    default: None or str
        Return value if `key` is not found or the value does
        not contain a string.
    remove: bool
        If `True`, remove the found key from `metadata`.

    Returns
    -------
    v: None or str
        String value referenced by `key`.
        If none of the `keys` was found, then `default` is returned.

    Examples
    --------

    ```
    >>> from audioio import get_str
    >>> md = dict(aaaa=42, bbbb='hello')

    # string:
    >>> get_str(md, 'bbbb')
    'hello'

    # int as str:
    >>> get_str(md, 'aaaa')
    '42'

    # two keys:
    >>> get_str(md, ['cccc', 'bbbb'])
    'hello'

    # not found:
    >>> get_str(md, 'cccc')
    None

    # not found with default value:
    >>> get_str(md, 'cccc', default='-')
    '-'
    ```

    """
    if not metadata:
        return default
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    for key in keys:
        m, k = find_key(metadata, key, sep)
        if k in m and not isinstance(m[k], dict):
            v = m[k]
            if remove:
                del m[k]
            return str(v)
    return default


def add_sections(metadata, sections, value=False, sep='.'):
    """Add sections to metadata dictionary.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    key: str
        Names of sections to be added to `metadata`.
        Section names separated by `sep`. 
    value: bool
        If True, then the last element in `key` is a key for a value,
        not a section.
    sep: str
        String that separates section names in `key`.

    Returns
    -------
    md: dict
        Dictionary of the last added section.
    key: str
        Last key. Only returned if `value` is set to `True`.

    Examples
    --------

    Add a section and a sub-section to the metadata:
    ```
    >>> from audioio import print_metadata, add_sections
    >>> md = dict()
    >>> m = add_sections(md, 'Recording.Location')
    >>> m['Country'] = 'Lummerland'
    >>> print_metadata(md)
    Recording:
        Location:
            Country: Lummerland
    ```

    Add a section with a key-value pair:
    ```
    >>> md = dict()
    >>> m, k = add_sections(md, 'Recording.Location', True)
    >>> m[k] = 'Lummerland'
    >>> print_metadata(md)
    Recording:
        Location: Lummerland
    ```

    Adds well to `find_key()`:
    ```
    >>> md = dict(Recording=dict())
    >>> m, k = find_key(md, 'Recording.Location.Country')
    >>> m, k = add_sections(m, k, True)
    >>> m[k] = 'Lummerland'
    >>> print_metadata(md)
    Recording:
        Location:
            Country: Lummerland
    ```

    """
    mm = metadata
    ks = sections.split(sep)
    n = len(ks)
    if value:
        n -= 1
    for k in ks[:n]:
        if len(k) == 0:
            continue
        mm[k] = dict()
        mm = mm[k]
    if value:
        return mm, ks[-1]
    else:
        return mm


def strlist_to_dict(mds):
    """Convert list of key-value-pair strings to dictionary.

    Parameters
    ----------
    mds: None or dict or str or list of str
        - None - returns empty dictionary.
        - Flat dictionary - returned as is.
        - String with key and value separated by '='.
        - List of strings with keys and values separated by '='.
        Keys may contain section names.

    Returns
    -------
    md_dict: dict
        Flat dictionary with key-value pairs.
        Keys may contain section names.
        Values are strings, other types or dictionaries.
    """
    if mds is None:
        return {}
    if isinstance(mds, dict):
        return mds
    if not isinstance(mds, (list, tuple, np.ndarray)):
        mds = (mds,)
    md_dict = {}
    for md in mds:
        k, v = md.split('=')
        k = k.strip()
        v = v.strip()
        md_dict[k] = v
    return md_dict


def set_metadata(metadata, mds, sep='.'):
    """Set values of existing metadata.

    Only if a key is found in the metadata, its value is updated.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    mds: dict or str or list of str
        - Flat dictionary with key-value pairs for updating the metadata.
          Values can be strings, other types or dictionaries.
        - String with key and value separated by '='.
        - List of strings with key and value separated by '='.
        Keys may contain section names separated by `sep`.
    sep: str
        String that separates section names in the keys of `md_dict`.

    Examples
    --------
    ```
    >>> from audioio import print_metadata, set_metadata
    >>> md = dict(Recording=dict(Time='early'))
    >>> print_metadata(md)
    Recording:
        Time: early

    >>> set_metadata(md, {'Artist': 'John Doe',       # new key-value pair
                          'Recording.Time': 'late'})  # change value of existing key
    >>> print_metadata(md)
    Recording:
        Time   : late
    ```

    See also
    --------
    add_metadata()
    strlist_to_dict()

    """
    if metadata is None:
        return
    md_dict = strlist_to_dict(mds)
    for k in md_dict:
        mm, kk = find_key(metadata, k, sep)
        if kk in mm:
            mm[kk] = md_dict[k]

        
def add_metadata(metadata, mds, sep='.'):
    """Add or modify key-value pairs.

    If a key does not exist, it is added to the metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    mds: dict or str or list of str
        - Flat dictionary with key-value pairs for updating the metadata.
          Values can be strings, other types or dictionaries.
        - String with key and value separated by '='.
        - List of strings with key and value separated by '='.
        Keys may contain section names separated by `sep`.
    sep: str
        String that separates section names in the keys of `md_list`.

    Examples
    --------
    ```
    >>> from audioio import print_metadata, add_metadata
    >>> md = dict(Recording=dict(Time='early'))
    >>> print_metadata(md)
    Recording:
        Time: early

    >>> add_metadata(md, {'Artist': 'John Doe',               # new key-value pair
                          'Recording.Time': 'late',           # change value of existing key 
                          'Recording.Quality': 'amazing',     # new key-value pair in existing section
                          'Location.Country': 'Lummerland'])  # new key-value pair in new section
    >>> print_metadata(md)
    Recording:
        Time   : late
        Quality: amazing
    Artist: John Doe
    Location:
        Country: Lummerland
    ```

    See also
    --------
    set_metadata()
    strlist_to_dict()

    """
    if metadata is None:
        return
    md_dict = strlist_to_dict(mds)
    for k in md_dict:
        mm, kk = find_key(metadata, k, sep)
        mm, kk = add_sections(mm, kk, True, sep)
        mm[kk] = md_dict[k]



def move_metadata(src_md, dest_md, keys, new_key=None, sep='.'):
    """Remove a key from metadata and add it to a dictionary.

    Parameters
    ----------
    src_md: nested dict
        Metadata from which a key is removed.
    dest_md: dict
        Dictionary to which the found key and its value are added.
    keys: str or list of str
        List of keys to be searched for in `src_md`.
        Move the first one found to `dest_md`.
        See the `audiometadata.find_key()` function for details.
    new_key: None or str
        If specified add the value of the found key as `new_key` to
        `dest_md`. Otherwise, use the search key.
    sep: str
        String that separates section names in `keys`.

    Returns
    -------
    moved: bool
        `True` if key was found and moved to dictionary.
    
    Examples
    --------
    ```
    >>> from audioio import print_metadata, move_metadata
    >>> md = dict(Artist='John Doe', Recording=dict(Gain='1.42mV'))
    >>> move_metadata(md, md['Recording'], 'Artist', 'Experimentalist')
    >>> print_metadata(md)
    Recording:
        Gain           : 1.42mV
        Experimentalist: John Doe
    ```
    
    """
    if not src_md:
        return False
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    for key in keys:
        m, k = find_key(src_md, key, sep)
        if k in m:
            dest_key = new_key if new_key else k
            dest_md[dest_key] = m.pop(k)
            return True
    return False

            
def remove_metadata(metadata, key_list, sep='.'):
    """Remove key-value pairs or sections from metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    key_list: str or list of str
        List of keys to key-value pairs or sections to be removed
        from the metadata.
    sep: str
        String that separates section names in the keys of `key_list`.

    Examples
    --------
    ```
    >>> from audioio import print_metadata, remove_metadata
    >>> md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4))
    >>> remove_metadata(md, ('ccc',))
    >>> print_metadata(md)
    aaaa: 2
    bbbb:
        ddd: 4
    ```

    """
    if not metadata:
        return
    if not isinstance(key_list, (list, tuple, np.ndarray)):
        key_list = (key_list,)
    for k in key_list:
        mm, kk = find_key(metadata, k, sep)
        if kk in mm:
            del mm[kk]
            
        
def cleanup_metadata(metadata):
    """Remove empty sections from metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata.

    Examples
    --------
    ```
    >>> from audioio import print_metadata, cleanup_metadata
    >>> md = dict(aaaa=2, bbbb=dict())
    >>> cleanup_metadata(md)
    >>> print_metadata(md)
    aaaa: 2
    ```

    """
    if not metadata:
        return
    for k in list(metadata):
        if isinstance(metadata[k], dict):
            if len(metadata[k]) == 0:
                del metadata[k]
            else:
                cleanup_metadata(metadata[k])


default_gain_keys = ['gain']
"""Default keys of gain settings in metadata. Used by `get_gain()` function.
"""

def get_gain(metadata, gain_key=default_gain_keys, sep='.',
             default=None, default_unit='', remove=False):
    """Get gain and unit from metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata with key-value pairs.
    gain_key: str or list of str
        Key in the file's metadata that holds some gain information.
        If found, the data will be multiplied with the gain,
        and if available, the corresponding unit is returned.
        See the `audiometadata.find_key()` function for details.
        You can modify the default keys via the `default_gain_keys` list
        of the `audiometadata` module.
    sep: str
        String that separates section names in `gain_key`.
    default: None or float
        Returned value if no valid gain was found in `metadata`.
    default_unit: str
        Returned unit if no valid gain was found in `metadata`.
    remove: bool
        If `True`, remove the found key from `metadata`.

    Returns
    -------
    fac: float
        Gain factor. If not found in metadata return 1.
    unit: string
        Unit of the data if found in the metadata, otherwise "a.u.".
    """
    v, u = get_number_unit(metadata, gain_key, sep, default,
                           default_unit, remove)
    # fix some TeeGrid gains:
    if len(u) >= 2 and u[-2:] == '/V':
        u = u[:-2]
    return v, u

            
def update_gain(metadata, fac, gain_key=default_gain_keys, sep='.'):
    """Update gain setting in metadata.

    Searches for the first appearance of a gain key in the metadata
    hierarchy. If found, divide the gain value by `fac`.

    Parameters
    ----------
    metadata: nested dict
        Metadata to be updated.
    fac: float
        Factor that was used to scale the data.
    gain_key: str or list of str
        Key in the file's metadata that holds some gain information.
        If found, the data will be multiplied with the gain,
        and if available, the corresponding unit is returned.
        See the `audiometadata.find_key()` function for details.
        You can modify the default keys via the `default_gain_keys` list
        of the `audiometadata` module.
    sep: str
        String that separates section names in `gain_key`.

    Returns
    -------
    done: bool
        True if gain has been found and set.


    Examples
    --------

    ```
    >>> from audioio import print_metadata, update_gain
    >>> md = dict(Artist='John Doe', Recording=dict(gain='1.4mV'))
    >>> update_gain(md, 2)
    >>> print_metadata(md)
    Artist: John Doe
    Recording:
        gain: 0.70mV
    ```

    """
    if not metadata:
        return False
    if not isinstance(gain_key, (list, tuple, np.ndarray)):
        gain_key = (gain_key,)
    for gk in gain_key:
        m, k = find_key(metadata, gk, sep)
        if k in m and not isinstance(m[k], dict):
            vs = m[k]
            if isinstance(vs, (int, float)):
                m[k] = vs/fac
            else:
                v, u, n = parse_number(vs)
                if not v is None:
                    # fix some TeeGrid gains:
                    if len(u) >= 2 and u[-2:] == '/V':
                        u = u[:-2]
                    m[k] = f'{v/fac:.{n+1}f}{u}'
                    return True
    return False


default_timeref_keys = ['TimeReference']
"""Default keys of integer time references in metadata.
Used by `update_starttime()` function.
"""

def update_starttime(metadata, deltat, rate,
                     time_keys=default_starttime_keys,
                     ref_keys=default_timeref_keys):
    """Update start-of-recording times in metadata.

    Add `deltat` to `time_keys`and `ref_keys` fields in the metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata to be updated.
    deltat: float
        Time in seconds to be added to start times.
    rate: float
        Sampling rate of the data in Hertz.
    time_keys: tuple of str or list of tuple of str
        Keys to fields denoting calender times, i.e. dates and times.
        Datetimes can be stored in metadata as two separate key-value pairs,
        one for the date and one for the time. Or by a single key-value pair
        for a date-time values. This is why the keys need to be specified in
        tuples with one or two keys.
        Keys may contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
        You can modify the default time keys via the `default_starttime_keys`
        list of the `audiometadata` module.
    ref_keys: str or list of str
        Keys to time references, i.e. integers in seconds relative to
        a reference time.
        Keys may contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
        You can modify the default reference keys via the
        `default_timeref_keys` list of the `audiometadata` module.

    Returns
    -------
    success: bool
        True if at least one time has been updated.

    Example
    -------
    ```
    >>> from audioio import print_metadata, update_starttime
    >>> md = dict(DateTimeOriginal='2023-04-15T22:10:00',
                  OtherTime='2023-05-16T23:20:10',
                  BEXT=dict(OriginationDate='2024-03-02',
                            OriginationTime='10:42:24',
                            TimeReference=123456))
    >>> update_starttime(md, 4.2, 48000)
    >>> print_metadata(md)
    DateTimeOriginal: 2023-04-15T22:10:04
    OtherTime       : 2023-05-16T23:20:10
    BEXT:
        OriginationDate: 2024-03-02
        OriginationTime: 10:42:28
        TimeReference  : 325056
    ```

    """
    if not metadata:
        return False
    if not isinstance(deltat, dt.timedelta):
        deltat = dt.timedelta(seconds=deltat)
    success = False
    if len(time_keys) > 0 and isinstance(time_keys[0], str):
        time_keys = (time_keys,)
    for key in time_keys:
        if len(key) == 1:
            # datetime:
            m, k = find_key(metadata, key[0])
            if k in m and not isinstance(m[k], dict):
                if isinstance(m[k], dt.datetime):
                    m[k] += deltat
                else:
                    datetime = dt.datetime.fromisoformat(m[k]) + deltat
                    m[k] = datetime.isoformat(timespec='seconds')
                success = True
        else:
            # separate date and time:
            md, kd = find_key(metadata, key[0])
            if not kd in md or isinstance(md[kd], dict):
                continue
            if isinstance(md[kd], dt.date):
                date = md[kd]
                is_date = True
            else:
                date = dt.date.fromisoformat(md[kd])
                is_date = False
            mt, kt = find_key(metadata, key[1])
            if not kt in mt or isinstance(mt[kt], dict):
                continue
            if isinstance(mt[kt], dt.time):
                time = mt[kt]
                is_time = True
            else:
                time = dt.time.fromisoformat(mt[kt])
                is_time = False
            datetime = dt.datetime.combine(date, time) + deltat
            md[kd] = datetime.date() if is_date else datetime.date().isoformat()
            mt[kt] = datetime.time() if is_time else datetime.time().isoformat(timespec='seconds')
            success = True
    # time reference in samples:
    if isinstance(ref_keys, str):
        ref_keys = (ref_keys,)
    for key in ref_keys:
        m, k = find_key(metadata, key)
        if k in m and not isinstance(m[k], dict):
            is_int = isinstance(m[k], int)
            tref = int(m[k])
            tref += int(np.round(deltat.total_seconds()*rate))
            m[k] = tref if is_int else f'{tref}'
            success = True
    return success


def bext_history_str(encoding, rate, channels, text=None):
    """ Assemble a string for the BEXT CodingHistory field.

    Parameters
    ----------
    encoding: str or None
        Encoding of the data.
    rate: int or float
        Sampling rate in Hertz.
    channels: int
        Number of channels.
    text: str or None
        Optional free text.

    Returns
    -------
    s: str
        String for the BEXT CodingHistory field,
        something like "A=PCM_16,F=44100,W=16,M=stereo,T=cut out"
    """
    codes = []
    bits = None
    if encoding is not None:
        if encoding[:3] == 'PCM':
            bits = int(encoding[4:])
            encoding = 'PCM'
        codes.append(f'A={encoding}')
    codes.append(f'F={rate:.0f}')
    if bits is not None:
        codes.append(f'W={bits}')
    mode = None
    if channels == 1:
        mode = 'mono'
    elif channels == 2:
        mode = 'stereo'
    if mode is not None:
        codes.append(f'M={mode}')
    if text is not None:
        codes.append(f'T={text.rstrip()}')
    return ','.join(codes)


default_history_keys = ['History',
                        'CodingHistory',
                        'BWF_CODING_HISTORY']
"""Default keys of strings describing coding history in metadata.
Used by `add_history()` function.
"""

def add_history(metadata, history, new_key=None, pre_history=None,
                history_keys=default_history_keys, sep='.'):
    """Add a string describing coding history to metadata.
    
    Add `history` to the `history_keys` fields in the metadata.  If
    none of these fields are present but `new_key` is specified, then
    assign `pre_history` and `history` to this key. If this key does
    not exist in the metadata, it is created.

    Parameters
    ----------
    metadata: nested dict
        Metadata to be updated.
    history: str
        String to be added to the history.
    new_key: str or None
        Sections and name of a history key to be added to `metadata`.
        Section names are separated by `sep`.
    pre_history: str or None
        If a new key `new_key` is created, then assign this string followed
        by `history`.
    history_keys: str or list of str
        Keys to fields where to add `history`.
        Keys may contain section names separated by `sep`. 
        See `audiometadata.find_key()` for details.
        You can modify the default history keys via the `default_history_keys`
        list of the `audiometadata` module.
    sep: str
        String that separates section names in `new_key` and `history_keys`.

    Returns
    -------
    success: bool
        True if the history string has beend added to the metadata.

    Example
    -------
    Add string to existing history key-value pair:
    ```
    >>> from audioio import add_history
    >>> md = dict(aaa='xyz', BEXT=dict(CodingHistory='original recordings'))
    >>> add_history(md, 'just a snippet')
    >>> print(md['BEXT']['CodingHistory'])
    original recordings
    just a snippet
    ```

    Assign string to new key-value pair:
    ```
    >>> md = dict(aaa='xyz', BEXT=dict(OriginationDate='2024-02-12'))
    >>> add_history(md, 'just a snippet', 'BEXT.CodingHistory', 'original data')
    >>> print(md['BEXT']['CodingHistory'])
    original data
    just a snippet
    ```

    """
    if not metadata:
        return False
    if isinstance(history_keys, str):
        history_keys = (history_keys,)
    success = False
    for keys in history_keys:
        m, k = find_key(metadata, keys)
        if k in m and not isinstance(m[k], dict):
            s = m[k]
            if len(s) >= 1 and s[-1] != '\n' and s[-1] != '\r':
                s += '\r\n'
            s += history
            m[k] = s
            success = True
    if not success and new_key:
        m, k = find_key(metadata, new_key, sep)
        m, k = add_sections(m, k, True, sep)
        s = ''
        if pre_history is not None:
            s = pre_history
        if len(s) >= 1 and s[-1] != '\n' and s[-1] != '\r':
            s += '\r\n'
        s += history
        m[k] = s
        success = True
    return success
    
            
def add_unwrap(metadata, thresh, clip=0, unit=''):
    """Add unwrap infos to metadata.

    If `audiotools.unwrap()` was applied to the data, then this
    function adds relevant infos to the metadata. If there is an INFO
    section in the metadata, the unwrap infos are added to this
    section, otherwise they are added to the top level of the metadata
    hierarchy.

    The threshold `thresh` used for unwrapping is saved under the key
    'UnwrapThreshold' as a string. If `clip` is larger than zero, then
    the clip level is saved under the key 'UnwrapClippedAmplitude' as
    a string.

    Parameters
    ----------
    md: nested dict
        Metadata to be updated.
    thresh: float
        Threshold used for unwrapping.
    clip: float
        Level at which unwrapped data have been clipped.
    unit: str
        Unit of `thresh` and `clip`.

    Examples
    --------

    ```
    >>> from audioio import print_metadata, add_unwrap
    >>> md = dict(INFO=dict(Time='early'))
    >>> add_unwrap(md, 0.6, 1.0)
    >>> print_metadata(md)
    INFO:
        Time                  : early
        UnwrapThreshold       : 0.60
        UnwrapClippedAmplitude: 1.00
    ```

    """
    if metadata is None:
        return
    md = metadata
    for k in metadata:
        if k.strip().upper() == 'INFO':
            md = metadata['INFO']
            break
    md['UnwrapThreshold'] = f'{thresh:.2f}{unit}'
    if clip > 0:
        md['UnwrapClippedAmplitude'] = f'{clip:.2f}{unit}'
    

def demo(file_pathes, list_format, list_metadata, list_cues, list_chunks):
    """Print metadata and markers of audio files.

    Parameters
    ----------
    file_pathes: list of str
        Pathes of audio files.
    list_format: bool
        If True, list file format only.
    list_metadata: bool
        If True, list metadata only.
    list_cues: bool
        If True, list markers/cues only.
    list_chunks: bool
        If True, list all chunks contained in a riff/wave file.
    """
    from .audioloader import AudioLoader
    from .audiomarkers import print_markers
    from .riffmetadata import read_chunk_tags
    for filepath in file_pathes:
        if len(file_pathes) > 1 and (list_cues or list_metadata or
                                     list_format or list_chunks):
            print(filepath)
        if list_chunks:
            chunks = read_chunk_tags(filepath)
            print(f'  {"chunk tag":10s} {"position":10s}  {"size":10s}')
            for tag in chunks:
                pos = chunks[tag][0] - 8
                size = chunks[tag][1] + 8
                print(f'  {tag:9s} {pos:10d} {size:10d}')
            if len(file_pathes) > 1:
                print()
            continue
        with AudioLoader(filepath, 1, 0, verbose=0) as sf:
            fmt_md = sf.format_dict()
            meta_data = sf.metadata()
            locs, labels = sf.markers()
            if list_cues:
                if len(locs) > 0:
                    print_markers(locs, labels)
            elif list_metadata:
                print_metadata(meta_data, replace='.')
            elif list_format:
                print_metadata(fmt_md)
            else:
                print('file:')
                print_metadata(fmt_md, '  ')
                if len(meta_data) > 0:
                    print()
                    print('metadata:')
                    print_metadata(meta_data, '  ', replace='.')
                if len(locs) > 0:
                    print()
                    print('markers:')
                    print_markers(locs, labels)
                if len(file_pathes) > 1:
                    print()
        if len(file_pathes) > 1:
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
    parser.add_argument('-t', dest='chunks', action='store_true',
                        help='list tags of all riff/wave chunks contained in the file')
    parser.add_argument('files', type=str, nargs='+',
                        help='audio file')
    if len(cargs) == 0:
        cargs = None
    args = parser.parse_args(cargs)

    demo(args.files, args.dataformat, args.metadata, args.cues, args.chunks)


if __name__ == "__main__":
    main(*sys.argv[1:])

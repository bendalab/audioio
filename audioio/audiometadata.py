"""Working with metadata.

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

- `write_metadata_text()`: write meta data into a text/yaml file.
- `print_metadata()`: write meta data to standard output.
- `flatten_metadata()`: flatten hierachical metadata to a single dictionary.
- `unflatten_metadata()`: unflatten a previously flattened metadata dictionary.
- `find_key()`: find dictionary in metadata hierarchy containing the specified key.
- `add_sections()`: add sections to metadata dictionary.
- `add_metadata()`: add or modify metadata.
- `remove_metadata()`: remove key-value pairs from metadata.
- `cleanup_metadata()`: remove empty sections from metadata.
- `parse_number()`: parse string with number and unit.
- `change_unit()`: scale numerical value to a new unit.
- `get_number_unit()`: find a key in metadata and return its number and unit.
- `get_number()`: find a key in metadata and return its value in a given unit.
- `get_int()`: find a key in metadata and return its integer value.
- `get_bool()`: find a key in metadata and return its boolean value.
- `get_str()`: find a key in metadata and return its string value.
- `get_gain()`: get gain and unit from metadata.
- `update_gain()`: update gain setting in metadata.
- `add_unwrap()`: add unwrap infos to metadata.


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


Alternatively, the script can be run from the module as:
```
python -m audioio.metadata audiofile.wav
```

Running
```sh
audiometadata --help
```
prints
```text
usage: audiomodules [--version] [--help] [PACKAGE]

Installation status and instructions of python audio packages.

optional arguments:
  --help      show this help message and exit
  --version   show version number and exit
  PACKAGE     show installation instructions for PACKAGE

version 2.0.0 by Benda-Lab (2015-2024)
```

"""
 
import sys
import argparse
import numpy as np
from .version import __version__, __year__


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
    
    def write_dict(df, md, level):
        w = 0
        for k in md:
            if not isinstance(md[k], dict) and w < len(k):
                w = len(k)
        for k in md:
            clevel = level*indent
            if isinstance(md[k], dict):
                df.write(f'{prefix}{"":>{clevel}}{k}:\n')
                write_dict(df, md[k], level+1)
            else:
                df.write(f'{prefix}{"":>{clevel}}{k:<{w}}: {md[k]}\n')

    if meta is None:
        return
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


def find_key(metadata, key, sep='__'):
    """Find dictionary in metadata hierarchy containing the specified key.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    key: str
        Key to be searched for (case insensitive).
        May contain section names separated by `sep`. 
    sep: str
        String that separates section names in `key`.

    Returns
    -------
    md: None or dict
        If `key` specifies a section, then this section is returned.
        If `key`specifies a key-value pair, then the dictionary
        containing the key is returned.
        If only some first sections of `key` have been found,
        then the innermost matching dictionary is returned, together 
        with the part of `key` that has not been found.
        If `key` is not at all contained in the metadata,
        the top-level dictionary is returned.
    key: None or str
        If `key` was found, the actual key into `md` specifying a
        key-value pair. None if `key` specifies a section. If `key`
        was not found, then the part of `key`that was not found.

    Examples
    --------

    When searching for key-value pairs, then independent of whether
    found or not found, you can assign to the returned dictionary with
    the returned key:

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
    >>> m, k = find_key(md, 'bbbb__ddd')
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

    >>> m, k = find_key(md, 'bbbb__eee__xx')
    >>> m[k] = 42
    >>> print_metadata(md)
    ...
        eee:
            ff: 5
            xx: 42
    ...
    ```

    When searching for sections, the innermost found is returned:
    ```
    >>> m, k = find_key(md, 'eee')
    >>> m['yy'] = 46
    >>> print_metadata(md)
    ...
        eee:
            ff: 5
            xx: 42
            yy: 46
    ...
    >>> m, k = find_key(md, 'gggg__zzz')
    >>> k
    'zzz'
    >>> m[k] = 64
    >>> print_metadata(md)
    ...
    gggg:
        hhh: 12
        zzz: 64
    ```

    """
    def find_keys(metadata, keys):
        key = keys[0].strip().upper()
        for k in metadata:
            if k.upper() == key:
                if isinstance(metadata[k], dict):
                    if len(keys) > 1:
                        # keep searching within the next section:
                        return find_keys(metadata[k], keys[1:])
                    else:
                        # found section:
                        return True, metadata[k], None
                elif len(keys) == 1:
                    # found key-value pair:
                    return True, metadata, k
                break
        # search in sections:
        for k in metadata:
            if isinstance(metadata[k], dict):
                found, mm, kk = find_keys(metadata[k], keys)
                if found:
                    return True, mm, kk
        # nothing found:
        return False, metadata, sep.join(keys)

    if metadata is None:
        return {}, None
    ks = key.strip().split(sep)
    found, mm, kk = find_keys(metadata, ks)
    return mm, kk


def add_sections(metadata, sections, value=False, sep='__'):
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
    >>> m = add_sections(md, 'Recording__Location')
    >>> m['Country'] = 'Lummerland'
    >>> print_metadata(md)
    Recording:
        Location:
            Country: Lummerland
    ```

    Add a section with a key-value pair:
    ```
    >>> md = dict()
    >>> m, k = add_sections(md, 'Recording__Location', True)
    >>> m[k] = 'Lummerland'
    >>> print_metadata(md)
    Recording:
        Location: Lummerland
    ```

    Adds well to `find_key()`:
    ```
    >>> md = dict(Recording=dict())
    >>> m, k = find_key(md, 'Recording__Location__Country')
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

        
def add_metadata(metadata, md_list, sep='__'):
    """Add or modify metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    md_list: list of str
        List of key-value pairs for updating the metadata.
        Values are separated from keys by '='.
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

    >>> add_metadata(md, ['Artist=John Doe',                # new key-value pair
                          'Recording__Time=late',           # change value of existing key 
                          'Recording__Quality=amazing',     # new key-value pair in existing section
                          'Location__Country=Lummerland'])  # new key-value pair in new section
    >>> print_metadata(md)
    Recording:
        Time   : late
        Quality: amazing
    Artist: John Doe
    Location:
        Country: Lummerland
    ```

    """
    if metadata is None:
        return
    for md in md_list:
        k, v = md.split('=')
        mm, kk = find_key(metadata, k, sep)
        mm, kk = add_sections(mm, kk, True, sep)
        mm[kk] = v.strip()

        
def remove_metadata(metadata, key_list, sep='__'):
    """Remove key-value pairs from metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata.
    key_list: list of str
        List of keys to key-value pairs to be removed from the metadata.
    sep: str
        String that separates section names in the keys of `key_list`.

    Examples
    --------
    ```
    >>> from audioio import print_metadata, remove_metadata
    >>> md = dict(aaaa=2, bbbb=dict(ccc=3, ddd=4, eee=dict(ff=5)))
    >>> remove_metadata(md, ('ccc',))
    >>> print_metadata(md)
    aaaa: 2
    bbbb:
        ddd: 4
        eee:
            ff: 5
    ```

    """
    if metadata is None:
        return
    for k in key_list:
        mm, kk = find_key(metadata, k, sep)
        if not kk is None and kk in mm:
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
    for k in list(metadata):
        if isinstance(metadata[k], dict):
            if len(metadata[k]) == 0:
                del metadata[k]
            else:
                cleanup_metadata(metadata[k])
            

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
    if not hasattr(s, '__len__'):
        if isinstance(s, int):
            return s, '', 0
        else:
            return s, '', 5
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


def get_number_unit(metadata, keys, sep='__', default=None, default_unit=''):
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
    if metadata is None or len(metadata) == 0:
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
                return v, u
            elif u and unit == default_unit:
                unit = u
    return value, unit


def get_number(metadata, unit, keys, sep='__', default=None):
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
    v, u = get_number_unit(metadata, keys, sep, None, unit)
    if v is None:
        return default
    else:
        return change_unit(v, u, unit)


def get_int(metadata, keys, sep='__', default=None):
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
    if metadata is None or len(metadata) == 0:
        return default, default_unit
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    for key in keys:
        m, k = find_key(metadata, key, sep)
        if k in m:
            v, _, n = parse_number(m[k])
            if v is not None and n == 0:
                return int(v)
    return default


def get_bool(metadata, keys, sep='__', default=None):
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
    if metadata is None or len(metadata) == 0:
        return default, default_unit
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    val = default
    for key in keys:
        m, k = find_key(metadata, key, sep)
        if k in m:
            vs = m[k]
            v, _, _ = parse_number(vs)
            if v is not None:
                val = abs(v) > 1e-8
            else:
                if vs.upper() in ['TRUE', 'T', 'YES', 'Y']:
                    return True
                if vs.upper() in ['FALSE', 'F', 'NO', 'N']:
                    return False
    return val


def get_str(metadata, keys, sep='__', default=None):
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
    if metadata is None or len(metadata) == 0:
        return default, default_unit
    if not isinstance(keys, (list, tuple, np.ndarray)):
        keys = (keys,)
    for key in keys:
        m, k = find_key(metadata, key, sep)
        if k in m:
            return str(m[k])
    return default


def get_gain(metadata, gainkey=['gain', 'scale', 'unit'], sep='__'):
    """Get gain and unit from metadata.

    Parameters
    ----------
    metadata: nested dict
        Metadata with key-value pairs.
    gainkey: str or list of str
        Key in the file's metadata that holds some gain information.
        If found, the data will be multiplied with the gain,
        and if available, the corresponding unit is returned.
        See the `audiometadata.find_key()` function for details.
    sep: str
        String that separates section names in `gainkey`.

    Returns
    -------
    fac: float
        Gain factor. If not found in metadata return 1.
    unit: string
        Unit of the data if found in the metadata, otherwise "a.u.".
    """
    v, u = get_number_unit(metadata, gainkey, sep, 1.0, 'a.u.')
    # fix some TeeGrid gains:
    if len(u) >= 2 and u[-2:] == '/V':
        u = u[:-2]
    return v, u

            
def update_gain(metadata, fac, gainkey=['gain', 'scale', 'unit'], sep='__'):
    """Update gain setting in metadata.

    Searches for the first appearance of the keyword `Gain` (case
    insensitive) in the metadata hierarchy. If found, divide the gain
    value by `fac`.

    Parameters
    ----------
    metadata: nested dict
        Metadata to be updated.
    fac: float
        Factor that was used to scale the data.
    gainkey: str or list of str
        Key in the file's metadata that holds some gain information.
        If found, the data will be multiplied with the gain,
        and if available, the corresponding unit is returned.
        See the `audiometadata.find_key()` function for details.
    sep: str
        String that separates section names in `gainkey`.

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
    if metadata is None or len(metadata) == 0:
        return fac, unit
    if not isinstance(gainkey, (list, tuple, np.ndarray)):
        gainkey = (gainkey,)
    for gk in gainkey:
        m, k = find_key(metadata, gk, sep)
        if k in m:
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
    from .audiomarkers import print_markers
    for filepath in filepathes:
        with AudioLoader(filepath, 1, 0) as sf:
            fmt_md = dict(filepath=filepath,
                          samplingrate=f'{sf.samplerate:.0f}Hz',
                          channels=sf.shape[1],
                          frames=sf.shape[0],
                          duration=f'{sf.shape[0]/sf.samplerate:.3f}s')
            meta_data = sf.metadata(store_empty=False)
            locs, labels = sf.markers()
            if list_cues:
                if len(locs) > 0:
                    print_markers(locs, labels)
            elif list_metadata:
                print_metadata(meta_data)
            elif list_format:
                print_metadata(fmt_md)
            else:
                print('file:')
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

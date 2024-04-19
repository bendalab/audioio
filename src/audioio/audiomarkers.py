"""Working with marker lists.

Markers are used to mark specific positions or regions in the audio
data.  Each marker has a position (cue, event), a span, a label, and a
text.  Position, and span are handled with 1-D or 2-D arrays of ints,
where each row is a marker and the columns are position and optional
span. Labels and texts come in another 1-D or 2-D array of objects
pointing to strings. Again, rows are the markers, first column are the
labels, and second column the optional texts. Try to keep the labels
short, and use text for longer descriptions.

- `write_markers()`: write markers to a text file or stream.
- `print_markers()`: write markers to standard output.

"""

import sys


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
    fh.write(f'{prefix}{"position":10}')
    if has_span:
        fh.write(f'{sep}{"span":8}')
    if has_labels:
        fh.write(f'{sep}{"label":10}')
    if has_text:
        fh.write(f'{sep}{"text"}')
    fh.write('\n')
    # table data:
    for i in range(len(locs)):
        fh.write(f'{prefix}{locs[i,0]:10}')
        if has_span:
            fh.write(f'{sep}{locs[i,1]:8}')
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
        

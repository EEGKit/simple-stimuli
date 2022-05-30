"""Fill docstrings to avoid redundant docstrings in multiple files.

Inspired from mne: https://mne.tools/stable/index.html
Inspired from mne.utils.docs.py by Eric Larson <larson.eric.d@gmail.com>
"""

import sys
from typing import Callable, List

# ------------------------- Documentation dictionary -------------------------
docdict = dict()

# ---------------------------------- verbose ---------------------------------
docdict[
    "verbose"
] = """
verbose : int | str | bool | None
    Sets the verbosity level. The verbosity increases gradually between
    "CRITICAL", "ERROR", "WARNING", "INFO" and "DEBUG".
    If None is provided, the verbosity is set to "WARNING".
    If a bool is provided, the verbosity is set to "WARNING" for False and to
    "INFO" for True."""

# ----------------------------------- audio ----------------------------------
docdict[
    "audio_volume"
] = """
volume : float | tuple
    If an int or a float is provided, the sound will use only one channel
    (mono). If a 2-length tuple is provided, the sound will use 2
    channels (stereo). The volume of each channel is given between 0 and 100.
    For stereo, the volume is given as (L, R)."""
docdict[
    "audio_sample_rate"
] = """
sample_rate : int
    Sampling frequency of the sound. The default is 44100 kHz."""
docdict[
    "audio_duration"
] = """
duration : float
    Duration of the sound. The default is 1 second."""

# ----------------------------------- visual ----------------------------------
docdict[
    "window_name"
] = """
window_name : str
    Name of the window in which the visual is displayed."""
docdict[
    "window_size"
] = """
window_size : tuple | None
    Either None to automatically select a window size based on the
    available monitors, or a 2-length of positive integer sequence as
    (width, height)."""
docdict[
    "color"
] = """The color is provided as a matplotlib string or a
(B, G, R) tuple of int8 set between 0 and 255."""
docdict[
    "position"
] = """
The position of the object can be either defined as the string 'center' or
'centered' to position the object in the center of the window; or as a 2-length
tuple of positive integer. The position is defined in opencv coordinates, with
(0, 0) being the top left corner of the window."""
docdict[
    "length"
] = """
length : int
    Number of pixels used to draw the length of the bar."""
docdict[
    "width"
] = """
width : int
    Number of pixels used to draw the width of the bar."""

# ------------------------- Documentation functions --------------------------
docdict_indented = dict()


def fill_doc(f: Callable) -> Callable:
    """Fill a docstring with docdict entries.

    Parameters
    ----------
    f : callable
        The function to fill the docstring of (modified in place).

    Returns
    -------
    f : callable
        The function, potentially with an updated __doc__.
    """
    docstring = f.__doc__
    if not docstring:
        return f

    lines = docstring.splitlines()
    indent_count = _indentcount_lines(lines)

    try:
        indented = docdict_indented[indent_count]
    except KeyError:
        indent = " " * indent_count
        docdict_indented[indent_count] = indented = dict()

        for name, docstr in docdict.items():
            lines = [
                indent + line if k != 0 else line
                for k, line in enumerate(docstr.strip().splitlines())
            ]
            indented[name] = "\n".join(lines)

    try:
        f.__doc__ = docstring % indented
    except (TypeError, ValueError, KeyError) as exp:
        funcname = f.__name__
        funcname = docstring.split("\n")[0] if funcname is None else funcname
        raise RuntimeError(f"Error documenting {funcname}:\n{str(exp)}")

    return f


def _indentcount_lines(lines: List[str]) -> int:
    """Minimum indent for all lines in line list.

    >>> lines = [' one', '  two', '   three']
    >>> indentcount_lines(lines)
    1
    >>> lines = []
    >>> indentcount_lines(lines)
    0
    >>> lines = [' one']
    >>> indentcount_lines(lines)
    1
    >>> indentcount_lines(['    '])
    0
    """
    indent = sys.maxsize
    for line in lines:
        line_stripped = line.lstrip()
        if line_stripped:
            indent = min(indent, len(line) - len(line_stripped))
    if indent == sys.maxsize:
        return 0
    return indent


def copy_doc(source: Callable) -> Callable:
    """Copy the docstring from another function (decorator).

    The docstring of the source function is prepepended to the docstring of the
    function wrapped by this decorator.

    This is useful when inheriting from a class and overloading a method. This
    decorator can be used to copy the docstring of the original method.

    Parameters
    ----------
    source : callable
        The function to copy the docstring from.

    Returns
    -------
    wrapper : callable
        The decorated function.

    Examples
    --------
    >>> class A:
    ...     def m1():
    ...         '''Docstring for m1'''
    ...         pass
    >>> class B(A):
    ...     @copy_doc(A.m1)
    ...     def m1():
    ...         ''' this gets appended'''
    ...         pass
    >>> print(B.m1.__doc__)
    Docstring for m1 this gets appended
    """

    def wrapper(func):
        if source.__doc__ is None or len(source.__doc__) == 0:
            raise RuntimeError(
                f"The docstring from {source.__name__} could not be copied "
                "because it was empty."
            )
        doc = source.__doc__
        if func.__doc__ is not None:
            doc += func.__doc__
        func.__doc__ = doc
        return func

    return wrapper

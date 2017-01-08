# Copyright (c) 2016, Science and Technology Facilities Council
# This software is distributed under a BSD licence. See LICENSE.txt.

"""
utils
-----

Utility functions used by the other modules in the mrcfile package.

Functions
---------

* :func:`data_dtype_from_header`: 
* :func:`data_shape_from_header`:
* :func:`mode_from_dtype`: Convert a numpy dtype to an MRC mode number.
* :func:`dtype_from_mode`: Convert an MRC mode number to a numpy dtype.
* :func:`machine_stamp_from_byte_order`: Get a machine stamp from a byte order
    indicator.
* :func:`spacegroup_is_volume_stack`: Identify if a space group number
    represents a volume stack.

"""

# Import Python 3 features for future-proofing
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

import numpy as np

from .constants import IMAGE_STACK_SPACEGROUP


def data_dtype_from_header(header):
    """Return the data dtype indicated by the given header.
    
    This method calls dtype_from_mode() to get the basic dtype, and then makes
    sure that the byte order of the new dtype matches the byte order of the
    header's mode field.
    
    Args:
        header: An MRC header as a numpy record array.
    
    Returns:
        The numpy dtype object for the data array corresponding to the given
        header.
    """
    mode = header.mode
    return dtype_from_mode(mode).newbyteorder(mode.dtype.byteorder)


def data_shape_from_header(header):
    """Return the data shape indicated by the given header.
    
    Args:
        header: An MRC header as a numpy record array.
    
    Returns:
        The shape tuple for the data array corresponding to the given header.
    """
    nx = header.nx
    ny = header.ny
    nz = header.nz
    mz = header.mz
    ispg = header.ispg
    
    if spacegroup_is_volume_stack(ispg):
        shape = (nz // mz, mz, ny, nx)
    elif ispg == IMAGE_STACK_SPACEGROUP and nz == 1:
        # Use a 2D array for a single image
        shape = (ny, nx)
    else:
        shape = (nz, ny, nx)
    
    return shape


_dtype_to_mode = dict(f2=2, f4=2, i1=0, i2=1, u1=6, u2=6, c8=4)

def mode_from_dtype(dtype):
    """Return the MRC mode number corresponding to the given numpy dtype.
    
    The conversion is as follows:
    
    float16   -> mode 2 (data will be widened to 32 bits in the file)
    float32   -> mode 2
    int8      -> mode 0
    int16     -> mode 1
    uint8     -> mode 6 (data will be widened to 16 bits in the file)
    uint16    -> mode 6
    complex64 -> mode 4
    
    Note that there is no numpy dtype which corresponds to MRC mode 3.
    
    Args:
        dtype: A numpy dtype object.
    
    Returns:
        The MRC mode number.
    
    Raises:
        ValueError: There is no corresponding MRC mode for the given dtype.
    """
    kind_and_size = dtype.kind + str(dtype.itemsize)
    if kind_and_size in _dtype_to_mode:
        return _dtype_to_mode[kind_and_size]
    raise ValueError("dtype '{0}' cannot be converted "
                     "to an MRC file mode".format(dtype))


_mode_to_dtype = { 0: np.int8,
                   1: np.int16,
                   2: np.float32,
                   4: np.complex64,
                   6: np.uint16 }

def dtype_from_mode(mode):
    """Return the numpy dtype corresponding to the given MRC mode number.
    
    The mode parameter may be given as a Python scalar, numpy scalar or
    single-item numpy array.
    
    The conversion is as follows:
    
    mode 0 -> int8
    mode 1 -> int16
    mode 2 -> float32
    mode 4 -> complex64
    mode 6 -> uint16
    
    Note that mode 3 is not supported as there is no matching numpy dtype.
    
    Args:
        mode: The MRC mode number. This may be given as any type which can be
            converted to an int, for example a Python scalar (int or float),
            a numpy scalar or a single-item numpy array.
    
    Returns:
        The numpy dtype object corresponding to the given mode.
    
    Raises:
        ValueError: There is no corresponding dtype for the given mode.
    """
    mode = int(mode)
    if mode in _mode_to_dtype:
        return np.dtype(_mode_to_dtype[mode])
    else:
        raise ValueError("Unrecognised mode '{0}'".format(mode))


_byte_order_to_machine_stamp = {'<': bytearray((0x44, 0x44, 0, 0)),
                                '>': bytearray((0x11, 0x11, 0, 0))}

def machine_stamp_from_byte_order(byte_order='='):
    """Return the machine stamp corresponding to the given byte order indicator.
    
    Args:
        byte_order: The byte order indicator: one of '=', '<' or '>', as
            defined and used by numpy dtype objects.
    
    Returns:
        The machine stamp which corresponds to the given byte order, as a
        bytearray. This will be either (0x44, 0x44, 0, 0) for little-endian
        or (0x11, 0x11, 0, 0) for big-endian. If the given byte order indicator
        is '=', the native byte order is used.
    
    Raises:
        ValueError: The byte order indicator is unrecognised.
    """
    # If byte order is '=', replace it with the system-native order
    if byte_order == '=':
        byte_order = '<' if sys.byteorder == 'little' else '>'
    
    if byte_order in _byte_order_to_machine_stamp:
        return _byte_order_to_machine_stamp[byte_order]
    else:
        raise ValueError("Unrecognised byte order "
                         "indicator '{0}'".format(byte_order))

def spacegroup_is_volume_stack(ispg):
    """Identify if the given space group number represents a volume stack.
    
    Args:
        ispg: The space group number, as an integer, numpy scalar or single-
            element numpy array.
    
    Returns:
        True if the space group number is in the range 401--630.
    """
    return 401 <= ispg <= 630

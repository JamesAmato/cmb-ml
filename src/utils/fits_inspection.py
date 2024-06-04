from typing import Dict

import numpy as np
import healpy as hp
from astropy.io import fits
import matplotlib.pyplot as plt
from pathlib import Path
from pprint import pprint


ASSUME_FITS_HEADER = 1


def print_out_header(fits_fn):
    """
    Print out the header of a FITS file.

    Args:
        fits_fn: The filename of the FITS file.
    """
    
    # Open the FITS file
    with fits.open(fits_fn) as hdul:
        # Loop over all HDUs in the FITS file
        for i, hdu in enumerate(hdul):
            print(f"Header for HDU {i}:")
            for card in hdu.header.cards:
                print(f"{card.keyword}: {card.value}")
            print("\n" + "-"*50 + "\n")


def get_num_fields_in_hdr(fits_fn, hdu) -> int:
    """
    Get the number of fields in the header of the specified HDU
    (Header Data Unit) in a FITS file.

    Args:
        fits_fn: The filename of the FITS file.
        hdu: The index of the HDU.

    Returns:
        The number of fields in the header.
    """
    
    with fits.open(fits_fn) as hdul:
        n_fields = len(hdul[hdu].columns)
    return n_fields


# def lookup_field_idx(field_str, fits_fn, hdu):
#     n_fields = get_num_fields_in_hdr(fits_fn, hdu)
#     T_n_fields = 3
#     TQU_n_fields = 10
    
#     if n_fields == T_n_fields:
#         field_str_to_idx = {"T": 2}
#     elif n_fields == TQU_n_fields:
#         field_str_to_idx = {"T": 4,
#                             "Q": 7,
#                             "U": 9}
#     else:
#         raise ValueError(f"Unexpected number of fields in fits file.")

#     try:
#         field_idx = field_str_to_idx[field_str]
#     except KeyError:
#         ok_field_strs = ", ".join(field_str_to_idx.keys())
#         raise ValueError(f"FITS file has only {ok_field_strs}, but {field_str} was requested.")
#     return field_idx    


def get_field_unit(fits_fn, hdu, field_idx):
    """
    Get the unit of a specific field in the header of the 
    specified HDU (Header Data Unit) in a FITS file.

    Args:
        fits_fn: The filename of the FITS file.
        hdu: The index of the HDU.
        field_idx: THe index of the field.

    Returns:
        The unit of the field.
    """
    
    with fits.open(fits_fn) as hdul:
        try:
            field_num = field_idx + 1
            unit = hdul[hdu].header[f"TUNIT{field_num}"]
        except KeyError:
            unit = ""
    return unit


def get_num_fields(fits_fn) -> Dict[int, int]:
    """
    Get the number of fields in each HDU (Header Data Unit)
    of a FITS file.

    Args:
        fits_fn: The filename of the FITS file.

    Returns:
        A dictionary where the keys area the HDU indices and the
        values are the number of fields in each HDU.
    """
    
    # Open the FITS file
    n_fields = {}
    with fits.open(fits_fn) as hdul:
        # Loop over all HDUs in the FITS file
        for i, hdu in enumerate(hdul):
            if i == 0:
                continue  # skip 0; it's fits boilerplate
            for card in hdu.header.cards:
                if card.keyword == "TFIELDS":
                    n_fields[i] = card.value
    return n_fields


def print_fits_information(fits_fn) -> None:
    """
    Print out the information of a FITS file.

    Args:
        fits_fn: The filename of the FITS file.
    """
    
    fits_info = get_fits_information(fits_fn)
    pprint(fits_info)


def get_fits_information(fits_fn):
    """
    Get detailed information about a FITS file.

    Args:
        fits_fn: The filename of the FITS file.

    Returns:
        A nested dictionary where the keys of the top level are
        the indices of the HDUs (Header Data Units) and the values
        are dictionaries containing information about the HDU. These
        dictionaries contain the header of the HDU and a dictionary
        ("FIELDS") where the keys are the indices of each field and
        the values are dictionaries containing the type and unit of
        each field.
    """
    
    n_fields_per_hdu = get_num_fields(fits_fn)
    watch_keys = {}
    types_str_base = "TTYPE"
    units_str_base = "TUNIT"
    maps_info = {}
    for hdu_n in n_fields_per_hdu:
        indices = list(range(1, n_fields_per_hdu[hdu_n] + 1))
        field_types_keys = [f"{types_str_base}{i}" for i in indices]
        field_units_keys = [f"{units_str_base}{i}" for i in indices]
        watch_keys[hdu_n] = {"types": field_types_keys, "units": field_units_keys}

        maps_info[hdu_n] = {}
    with fits.open(fits_fn) as hdul:
        # Loop over all HDUs in the FITS file
        for hdu_n, hdu in enumerate(hdul):
            if hdu_n == 0:
                continue
            maps_info[hdu_n] = dict(hdu.header)
            maps_info[hdu_n]["FIELDS"] = {}
            print(hdu_n, hdu.data.shape, '\n', hdu.data)
            for field_n in range(1, n_fields_per_hdu[hdu_n] + 1):
                field_info = {}
                # Construct the keys for type and unit
                ttype_key = f'TTYPE{field_n}'
                tunit_key = f'TUNIT{field_n}'

                # Retrieve type and unit for the current field, if they exist
                field_info['type'] = maps_info[hdu_n].get(ttype_key, None)
                field_info['unit'] = maps_info[hdu_n].get(tunit_key, None)

                # Add the field info to the fields_info dictionary
                maps_info[hdu_n]["FIELDS"][field_n] = field_info
    return maps_info


def show_all_maps(fits_fn):
    """
    Display all maps in each HDU (Header Data Unit)
    of a FITS file.

    Args:
        fits_fn: The filename of the FITS file.
    """
    
    n_fields_per_hdu = get_num_fields(fits_fn)
    for hdu_n, n_fields in n_fields_per_hdu.items():
        for field in range(n_fields):
            print(hdu_n, field)
            this_map = hp.read_map(fits_fn, hdu=hdu_n, field=field)
            hp.mollview(this_map)
            plt.show()


def show_one_map(fits_fn, hdu_n, field_n):
    """
    Display a specific map from a FITS file.

    Args:
        fits_fn: The filename of the FITS file.
        hdu_n: The number of the HDU (Header Data Unit).
        field_n: The number of the field.
    """
    
    this_map = hp.read_map(fits_fn, hdu=hdu_n, field=field_n)
    hp.mollview(this_map)
    plt.show()


def get_map_dtype(m: np.ndarray):
    """
    Get the data type of a map in a format compatible
    with numba and mpi4py.

    Args:
        m: Numpy array representing the map.

    Returns:
        The data type of the map.
    """
    
    # From PySM3 template.py's read_map function, with minimal alteration:
    dtype = m.dtype
    # numba only supports little endian
    if dtype.byteorder == ">":
        dtype = dtype.newbyteorder()
    # mpi4py has issues if the dtype is a string like ">f4"
    if dtype == np.dtype(np.float32):
        dtype = np.dtype(np.float32)
    elif dtype == np.dtype(np.float64):
        dtype = np.dtype(np.float64)
    # End of used portion
    return dtype
    
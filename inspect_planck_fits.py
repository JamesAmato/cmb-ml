import os
import re
import astropy.io.fits as fits
import healpy as hp
import numpy as np
import pysm3.units as u
from pprint import pprint
from astropy.cosmology import Planck15


def process_fits_files(directory):
    """
    Pull the variance values from the officially released cleaned maps
            Convert to sd (units of K_CMB), provide statistics
    """
    results = {}
    freq_pattern = re.compile(r'SkyMap_([0-9]{3})')

    # j = 0
    for filename in os.listdir(directory):
        # j+=1
        # if j > 1:
        #     break

        if filename.endswith(".fits"):
            file_path = os.path.join(directory, filename)

            # Extract frequency from filename
            match = freq_pattern.search(filename)
            if match:
                frq_int = int(match.group(1))
                frequency = int(match.group(1)) * u.GHz
            else:
                continue  # Skip file if frequency is not found

            if frq_int in [545, 857]:
                field_idcs = [2]
            else:
                field_idcs = [4, 7, 9]

            # Open the FITS file
            with fits.open(file_path) as hdul:
                results[f"{frq_int:>3}"] = {}

                for i in field_idcs:
                    # Get the units for the field
                    units = hdul[1].header.get(f'TUNIT{i}', 'unknown')

                    # Read the field using healpy
                    field_map = hp.read_map(file_path, field=i)
                    field_map = np.sqrt(field_map)

                    # Convert units if necessary
                    if units == "MJy/sr":
                        field_map = (field_map * u.MJy / u.sr).to(
                            u.K, equivalencies=u.thermodynamic_temperature(frequency, Planck15.Tcmb0)
                        ).value

                    # Compute statistics
                    max_val = np.max(field_map) * 1e6
                    min_val = np.min(field_map) * 1e6
                    mean_val = np.mean(field_map) * 1e6
                    median_val = np.median(field_map) * 1e6
                    q1_val = np.percentile(field_map, 25) * 1e6
                    q3_val = np.percentile(field_map, 75) * 1e6

                    field_strs = {2: "I", 4:"I", 7: "Q", 9: "U"}
                    
                    results[f"{frq_int:>3}"][field_strs[i]] = {
                        '0  min   ': f"{min_val:>15.2f}",
                        '1  Q1    ': f"{q1_val:>15.2f}",
                        '2  median': f"{median_val:>15.2f}",
                        '3  Q3    ': f"{q3_val:>15.2f}",
                        '4  max   ': f"{max_val:>15.2f}", 
                        '5  mean  ': f"{mean_val:>15.2f}",
                    }
    return results

directory_path = 'planck_assets'
files_data = process_fits_files(directory_path)
pprint(files_data)

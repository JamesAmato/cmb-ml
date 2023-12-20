import pysm3
import healpy as hp
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np


colombi1_cmap = ListedColormap(np.loadtxt("planck_colormap.txt")/255.)
colombi1_cmap.set_bad("gray") # color of missing pixels
colombi1_cmap.set_under("white") # color of background, necessary if you want to use

fits_file = 'COM_CMB_IQU-commander_2048_R3.00_full.fits'

# Fields 5 and 7 are T and U maps with inpainting (0 and 2 are without inpainting)
T_map = pysm3.template.read_map(fits_file, field=5, unit="K_CMB", nside=512) * 1e6
U_map = pysm3.template.read_map(fits_file, field=7, unit="K_CMB", nside=512) * 1e6

# SOLUTION FOUND: Smooth it. Where's the documentation of this? Who cares.
fwhm_degrees = 1.0  # Full width at half maximum in degrees
T_map_smoothed = hp.smoothing(T_map, fwhm=np.radians(fwhm_degrees))
U_map_smoothed = hp.smoothing(U_map, fwhm=np.radians(fwhm_degrees))

# alternate file read method, checked to confirm that it's not a pysm3 issue:
# T_map = hp.read_map(fits_file, field=7) * 1e6
# U_map = hp.read_map(fits_file, field=7) * 1e6

hp.mollview(T_map_smoothed, min=-300, max=300, title="Jim Plotting Official Map T Field", cmap=colombi1_cmap)
hp.mollview(U_map_smoothed, min=-2.5, max=2.5, title="Jim Plotting Official Map U Field", cmap=colombi1_cmap)
plt.show()



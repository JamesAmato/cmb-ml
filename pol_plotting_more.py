import pysm3
import healpy as hp
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from astropy.io import fits


colombi1_cmap = ListedColormap(np.loadtxt("planck_colormap.txt")/255.)
colombi1_cmap.set_bad("gray") # color of missing pixels
colombi1_cmap.set_under("white") # color of background, necessary if you want to use

# c4_map_file_u = '/home/jim/.astropy/cache/download/url/c401770abdd03d22b962ec8d355038ea/contents'
fits_file = 'COM_CMB_IQU-commander_2048_R3.00_full.fits'

# Open the FITS file
# with fits.open(fits_file) as hdul:
#     # Loop over all HDUs in the FITS file
#     for i, hdu in enumerate(hdul):
#         print(f"Header for HDU {i}:")
#         for card in hdu.header.cards:
#             print(f"{card.keyword}: {card.value}")
#         print("\n" + "-"*50 + "\n")
a = pysm3.template.read_map(fits_file, field=7, unit="K_CMB", nside=512) * 1e6
# a = hp.read_map(fits_file, field=7) * 1e6
# hp.mollview(a, min=-300, max=300, title="Jim Plotting Official Map T Field", cmap=cmap)
hp.mollview(a, min=-2.5, max=2.5, title="Jim Plotting Official Map U Field", cmap=colombi1_cmap)
# hp.mollview(a, min=-300, max=300, cmap=cmap)
# hp.mollview(a, min=-2.5, max=2.5, cmap=cmap)
plt.show()

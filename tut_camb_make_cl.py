# From https://camb.readthedocs.io/en/latest/CAMBdemo.html; Use first 5 cells only (for now)

import sys, platform, os
import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import camb
from camb import model, initialpower


print('Using CAMB %s installed at %s'%(camb.__version__,os.path.dirname(camb.__file__)))
# make sure the version and path is what you expect

#Set up a new set of parameters for CAMB
pars = camb.CAMBparams()
#This function sets up with one massive neutrino and helium set using BBN consistency
pars.set_cosmology(H0=67.5, ombh2=0.022, omch2=0.122, mnu=0.06, omk=0, tau=0.06)
pars.InitPower.set_params(As=2e-9, ns=0.965, r=0)
pars.set_for_lmax(2500, lens_potential_accuracy=0)

results = camb.get_results(pars)

powers =results.get_cmb_power_spectra(pars, CMB_unit='muK')
for name in powers: 
    print(name)

#plot the total lensed CMB power spectra versus unlensed, and fractional difference
totCL=powers['total']
unlensedCL=powers['unlensed_scalar']

print(totCL.shape)
#Python CL arrays are all zero based (starting at L=0), Note L=0,1 entries will be zero by default.
#The different CL are always in the order TT, EE, BB, TE (with BB=0 for unlensed scalar results).


# # Plot results; green is unlensed, black is lensed. TODO: Add a legend!
# ls = np.arange(totCL.shape[0])
# fig, ax = plt.subplots(2,2, figsize = (12,12))
# ax[0,0].plot(ls,totCL[:,0], color='k')
# ax[0,0].plot(ls,unlensedCL[:,0], color='C2')
# ax[0,0].set_title(r'$TT\, [\mu K^2]$')
# ax[0,1].plot(ls[2:], 1-unlensedCL[2:,0]/totCL[2:,0]);
# ax[0,1].set_title(r'Fractional TT lensing')
# ax[1,0].plot(ls,totCL[:,1], color='k')
# ax[1,0].plot(ls,unlensedCL[:,1], color='C2')
# ax[1,0].set_title(r'$EE\, [\mu K^2]$')
# ax[1,1].plot(ls,totCL[:,3], color='k')
# ax[1,1].plot(ls,unlensedCL[:,3], color='C2')
# ax[1,1].set_title(r'$TE\, [\mu K^2]$');
# for ax in ax.reshape(-1): 
#     ax.set_xlim([2,2500])
#     ax.set_xlabel(r'$\ell$')
# plt.show()


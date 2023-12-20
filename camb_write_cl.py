# From https://camb.readthedocs.io/en/latest/CAMBdemo.html; Use first 5 cells only (for now)

import os
import numpy as np
import healpy as hp
import camb


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

#plot the total lensed CMB power spectra versus unlensed, and fractional difference
totCL=powers['total']
unlensedCL=powers['unlensed_scalar']

hp.fitsfunc.write_cl("test.fits", totCL, overwrite=True)

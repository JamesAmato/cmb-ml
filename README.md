# ml_cmb_pysm_sims - Physics

For Physics questions, test cases, and answers. I've removed much of the README; installation instructions are in other branches.

# Physics Questions


- [x] WMAP chain parameters are pulled by grabbing values at the same row from multiple files. Should each parameter get its own index instead? Alternatively, should some parameters come from index i and others i+1?
  - It is correct as it stands; pull one index to account for the row

CAMB
- [x] Ok to use CAMB instead of class?
  - Typically, they are used interchangeably; it often depends on other software and what's most compatible
- [ ] Should CAMB be run with an Lmax=8150?
- [ ] Is CAMB deterministic?
  - Believed to be yes; not sure if confirmation is needed.
- [ ] Should CAMB be run with an Lmax=8150?
- [x] **Is CAMB being used correctly to generate CMB power spectra**? I believe that currently it is running with several defaults; I do not know if those defaults are reasonable.
  - Yes. Probably. I don't know if Physics has looked at it; but Jim followed instructions.
- [ ] Is the CAMB power spectrum file truly the fiducial power spectrum toward which we should train the model?

CMB Realizations
- [ ] Are CMB realizations correctly produced? 
  - I'm using code for a Lensed CMB, because that allows me to input a power spectrum from a file (the one output by CAMB). I'm forcing "apply_delens" (possibly a misnomer) to False; this may be incorrect. 
- [ ] Is the CMB realization that I save the correct "fiducial" CMB, which would be associated with the fiducial power spectrum?
  - Probably now correctly downgraded

Derived PS
- [ ] Is the "derived" power spectrum, the calculation based on ANAFAST of the fiducial CMB map, correctly derived? 
- [ ] Is the lmax correct/reasonable?
- [ ] Should this be used as the truth, the target toward which we train models?
    - Probably no? Certainly not for the Lit Review anyways

Sky
- [ ] Is the Sky initialized at the correct nside (or should it be higher than the target nside at output)?
  - Now it is (2048 for nside<2048; 2*nside otherwise)

Beam Smoothing
- [ ] Is beam smoothing (smoothing_and_coordinate_transform) correctly applied? 
- [ ] Is the nside for that correct?
- [ ] Is the lmax for that correct?
  - I've seen [the ANAFAST documentation](https://healpix.sourceforge.io/html/fac_anafast.htm) and find it somewhat confusing. I currently use 2*lmax.
  - There may be ringing in the images around the bright spot in the middle. More occurs when I use nside_sky=nside_out, but still some nevertheless.
- [ ] Is this method sufficient, or should RIMO's be used?

Noise
- [ ] **Is noise correctly determined**? There is a process of scaling down the resolution of some variance signal, then finding the square root of that to serve as standard deviation for Gaussian draws.
  - I think this has been fixed using the power parameter for ud_grade() when creating the noise cache
- [ ] Why is noise for polarization so large? It seems to drown out other signals.
  - This is currently improved, but may need more work?
- [ ] Should I use all COV channels to determine noise which has proper variance?
  - I currently use only diagonal elements of the covariance matrix, for simplicity.
- [ ] Is this method sufficient, or should RIMO's be used?

Other
- [ ] What other output is needed from the simulations in order for Commander and NILC to function properly?
- [ ] Are the unit conversions correctly performed? 
  - (MJy/sr)
  - In physics_instrument_noise.py, planck_result_to_sd_map(), line 28
  - In physics_instrument_noise.py, make_random_noise_map(), line 42
- [ ] Are the CalTech maps appropriately bandpassed?
- [ ] Polarization: are there preferred orientations for CMB Q and U maps? 
  - There appear to be up-down directions in Q and diagonals in U.

# Full output of URLErrors (temporary section):

```
(ml_cmb_pysm_sims) jimcamato@Jims-Laptop ml_cmb_pysm_sims % /Users/jimcamato/miniconda3/envs/ml_cmb_pysm_sims/bin/python /Users/jim
camato/Developer/ml_cmb_pysm_sims/fixed_map_synth4.py
545
OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Downloading https://portal.nersc.gov/project/cmb/pysm-data/websky/0.4/radio/radio_0584.0.fits
|==============================================================>------------------------------| 1.0G/1.6G (67.43%) ETA 24m 7s
File not found, please make sure you are using the latest version of PySM 3
While working on lowplus, error in detector 545.
<urlopen error Unable to open any source! Exceptions were {'https://portal.nersc.gov/project/cmb/pysm-data/websky/0.4/radio/radio_0584.0.fits': ContentTooShortError('File was supposed to be 1610619840 bytes but we only got 1086108642 bytes. Download failed.'), 'http://www.astropy.org/astropy-data/websky/0.4/radio/radio_0584.0.fits': <HTTPError 404: 'Not Found'>}>
857
Downloading https://portal.nersc.gov/project/cmb/pysm-data/websky/0.4/cib/cib_0857.0.fits
|==============================================================>------------------------------| 1.0G/1.6G (67.68%) ETA 23m25s
File not found, please make sure you are using the latest version of PySM 3
While working on lowplus, error in detector 857.
<urlopen error Unable to open any source! Exceptions were {'https://portal.nersc.gov/project/cmb/pysm-data/websky/0.4/cib/cib_0857.0.fits': ContentTooShortError('File was supposed to be 1610619840 bytes but we only got 1090100572 bytes. Download failed.'), 'http://www.astropy.org/astropy-data/websky/0.4/cib/cib_0857.0.fits': <HTTPError 404: 'Not Found'>}>
```

# Credit / References

https://camb.readthedocs.io/en/latest/CAMBdemo.html

import pysm3.units as u


# Abandoned, rolled into planck_instrument.py


# As near as I can tell, Petroff used the U-STOKES Map from 
#       HFI_SkyMap_100_2048_R3.01_full.fits
#       His comment on line 32 says he uses TT covariance, 
#       however, FIELD=0 (I may have a bad version of his code).
#       Either way, he uses those values as the "scale" for np.random.normal
#       which seems ... I don't know. See A8 (2016) VIII section 6.1
#       In the paper itself, the phrasing is ambiguous; there do exist 
#       2018 simulation variance maps. Those are not used here.

# LFI Data from 15-03-aa26998-15, the Planck 2015 results III
#       Tables 5-7 on pages 24,25; "total" rows  and "rms" columns only
#       The 2018 Data provides realizations of maps (I think - JA)
#       The 2013 Data does not separate I, Q, U

lfi_systematic_uncertainties = {
    30: {"I": 0.61 * u.uK_CMB,
         "Q": 0.52 * u.uK_CMB,
         "U": 0.49 * u.uK_CMB},
    44: {"I": 0.45 * u.uK_CMB,
         "Q": 0.37 * u.uK_CMB,
         "U": 0.37 * u.uK_CMB},
    70: {"I": 0.47 * u.uK_CMB,
         "Q": 0.46 * u.uK_CMB,
         "U": 0.48 * u.uK_CMB}
}

# HFI Data from 15-08-aa25820-15, the Planck 2015 results VII
#       Table 4 on page 13; the Variance Map column
# TODO  THIS IS NOT THE CORRECT WAY TO DO THIS

hfi_systematic_uncertainties = {
    100: {"I": 1538 * u.uK_CMB,
          "Q": 2346 * u.uK_CMB,
          "U": 2346 * u.uK_CMB},
    143: {"I": 769 * u.uK_CMB,
          "Q": 1631 * u.uK_CMB,
          "U": 1631 * u.uK_CMB},
    217: {"I": 1105 * u.uK_CMB,
          "Q": 2512 * u.uK_CMB,
          "U": 2512 * u.uK_CMB},
    353: {"I": 3692 * u.uK_CMB,
          "Q": 10615 * u.uK_CMB,
          "U": 10615 * u.uK_CMB},
    545: {"I": 0.612 * (u.MJy / u.sr),
          "Q": 0.612 * (u.MJy / u.sr),
          "U": 0.612 * (u.MJy / u.sr)},
    857: {"I": 0.660 * (u.MJy / u.sr),
          "Q": 0.660 * (u.MJy / u.sr),
          "U": 0.660 * (u.MJy / u.sr)},
}


planck_uncertainties = {**lfi_systematic_uncertainties, **hfi_systematic_uncertainties}

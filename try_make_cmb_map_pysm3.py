import pysm3
import pysm3.units as u
import matplotlib.pyplot as plt
import healpy as hp
from planck_cmap import colombi1_cmap


# Goal: PySM3 to produce a basic CMB map, observed with the known instrument fwhm

def simulate_sky():    
    nside = 512

    planck_data = {
        30: {"center_frequency": 28.4, "fwhm": 33.102652125 * u.arcmin},
        44: {"center_frequency": 44.1, "fwhm": 27.94348615 * u.arcmin},
        70: {"center_frequency": 70.4, "fwhm": 13.07645961 * u.arcmin},
        100: {"center_frequency": 100.89, "fwhm": 9.682 * u.arcmin},
        143: {"center_frequency": 142.876, "fwhm": 7.303 * u.arcmin},
        217: {"center_frequency": 221.156, "fwhm": 5.021 * u.arcmin},
        353: {"center_frequency": 357.5, "fwhm": 4.944 * u.arcmin},
        545: {"center_frequency": 555.2, "fwhm": 4.831 * u.arcmin},
        857: {"center_frequency": 866.8, "fwhm": 4.638 * u.arcmin}
    }

    sky = pysm3.Sky(nside=nside, preset_strings=["c1"])

    field_strs = ["T", "Q", "U"]
    val_ranges = [dict(min=-300, max=300),
                  dict(min=-2.5, max=2.5),
                  dict(min=-2.5, max=2.5),]

    freq = 100
    frequency = freq * u.GHz
    skymaps = sky.get_emission(frequency)

    for skymap, field_str, val_range in zip(skymaps, field_strs, val_ranges):
        map_smoothed = pysm3.apply_smoothing_and_coord_transform(
            skymap, fwhm=planck_data[freq]["fwhm"])
        hp.mollview(map_smoothed, **val_range, 
                    title=f"Model: c1, Field: {field_str}, {freq} GHz", 
                    unit=skymap.unit,
                    cmap=colombi1_cmap)
        plt.show()


if __name__ == "__main__":
    simulate_sky()

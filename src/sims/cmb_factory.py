import logging

from pathlib import Path
from pysm3 import CMBLensed
from omegaconf.errors import ConfigAttributeError
from src.core import Asset


logger = logging.getLogger(__name__)


class CMBFactory:
    """
    A class that generates a PySM3 CMBLensed object.

    Attributes:
        nside_sky (int): The nside resolution of the sky and CMB.

    Methods:
        make_cmb_lensed(seed, cmb_ps_fid_path): Generate a CMBLensed object.
    """
    
    def __init__(self, nside_sky):
        self.nside = nside_sky
        self.max_nside_pysm_component = None
        self.apply_delens = False
        self.delensing_ells = None
        self.map_dist = None

    def make_cmb_lensed(self, seed, cmb_ps_fid_path) -> CMBLensed:
        """
        Generate a PySM3 CMBLensed object.

        Args:
            seed (int): The seed used to generate the CMB.
            cmb_ps_fid_path (str): The path to the fiducial power spectra.

        Returns:
            CMBLensed: The generated PySM3 CMBLensed object.
        """
        
        return CMBLensed(nside=self.nside,
                         cmb_spectra=cmb_ps_fid_path,
                         cmb_seed=seed,
                         max_nside=self.max_nside_pysm_component,
                         apply_delens=self.apply_delens,
                         delensing_ells=self.delensing_ells,
                         map_dist=self.map_dist)
    

from abc import ABC, abstractmethod
import logging

import numpy as np
import healpy as hp

from src.utils.physics_beam import Beam


logger = logging.getLogger(__name__)


def get_autopower(map_, mask, lmax):
    """
    Calculate the auto power spectrum of a map.

    Args:
        map_: The input map.
        mask: The mask to apply to apply to the map.
        lmax: The maximum multipole to include in the power spectrum.

    Returns:
        THe auto power spectrum of the map.
    """
    
    return get_xpower(map1=map_, map2=map_, mask=mask, lmax=lmax)


def get_xpower(map1, map2, mask, lmax, use_pixel_weights=False):
    """
    Calculate the cross power spectrum of two maps.

    Args:
        map1: The first input map.
        map2: The second input map.
        mask: The mask to apply to the maps.
        lmax: The maximum multipole to include in the power spectrum.
        use_pixel_weights: Optional boolean to use pixel weights in the anafast function.

    Returns:
        The cross power spectrum of the two maps.
    """
    
    if mask is None:
        ps = hp.anafast(map1, map2, lmax=lmax, use_pixel_weights=use_pixel_weights)
    else:
        mean1 = np.sum(map1*mask)/np.sum(mask)
        mean2 = np.sum(map2*mask)/np.sum(mask)
        fsky = np.sum(mask)/mask.shape[0]
        ps = hp.anafast(mask*(map1-mean1),
                        mask*(map2-mean2),
                        lmax=lmax,
                        use_pixel_weights=use_pixel_weights)
        ps = ps / fsky
    return ps


def _cl_to_dl(cl, ells):
    norm = ells * (ells+1) / (np.pi * 2)
    return cl * norm


def _dl_to_cl(dl, ells):
    norm = ells * (ells+1) / (np.pi * 2)
    return dl / norm


class PowerSpectrum(ABC):
    """
    An abstract base class representing a power spectrum.

    Attributes:
        name: The name of the power spectrum.
        cl: The power spectrum in Cl format.
        ells: The multipoles of the power spectrum.
        is_convolved: Optional boolean of whether the power spectrum is already convolved with the beam.
    """

    def __init__(self, 
                 name: str, 
                 cl: np.ndarray, 
                 ells: np.ndarray, 
                 is_convolved:bool=True):
        self.name = name
        self.ells = ells
        self._ps = cl
        self._is_cl: bool = True
        self._is_beam_convolved: bool = is_convolved

    @property
    def conv_cl(self):
        self.ensure_cl()
        self.ensure_beam_convolved()
        return self._ps

    @property
    def conv_dl(self):
        self.ensure_dl()
        self.ensure_beam_convolved()
        return self._ps

    @property
    def deconv_cl(self):
        self.ensure_cl()
        self.ensure_beam_deconvolved()
        return self._ps

    @property
    def deconv_dl(self):
        self.ensure_dl()
        self.ensure_beam_deconvolved()
        return self._ps

    def ensure_cl(self):
        if not self._is_cl:
            self.dl_2_cl()

    def ensure_dl(self):
        if self._is_cl:
            self.cl_2_dl()

    def ensure_beam_convolved(self):
        if not self._is_beam_convolved:
            self.convolve()

    def ensure_beam_deconvolved(self):
        if self._is_beam_convolved:
            self.deconvolve()

    @abstractmethod
    def convolve(self):
        pass

    @abstractmethod
    def deconvolve(self):
        pass

    def cl_2_dl(self):
        self._ps = _cl_to_dl(cl=self._ps, ells=self.ells)
        self._is_cl = False

    def dl_2_cl(self):
        self._ps = _dl_to_cl(cl=self._ps, ells=self.ells)
        self._is_cl = True


class AutoSpectrum(PowerSpectrum):
    """
    A class representing an auto power spectrum.

    Attributes:
        name: The name of the power spectrum.
        cl: The power spectrum in Cl format.
        ells: The multipoles of the power spectrum.
        beam: The beam to convolve with the power spectrum.
        is_convolved: Boolean of whether the power spectrum is already convolved with the beam.

    Methods:
        convolve(): Convolve the power spectrum with the beam.
        deconvolve(): Deconvolve the power spectrum with the beam.
    """

    def __init__(self, 
                 name: str, 
                 cl: np.ndarray, 
                 ells: np.ndarray, 
                 beam: Beam, 
                 is_convolved: bool):
        super().__init__(name, cl, ells, is_convolved)
        self.beam = beam

    def convolve(self):
        if not self._is_beam_convolved:
            self._ps = self.beam.conv2(self._ps)
            self._is_beam_convolved = True
        else:
            logger.warning("AutoSpectrum is already convolved. No action taken.")

    def deconvolve(self):
        if self._is_beam_convolved:
            self._ps = self.beam.deconv2(self._ps)
            self._is_beam_convolved = False
        else:
            logger.warning("AutoSpectrum is already deconvolved. No action taken.")


class CrossSpectrum(PowerSpectrum):
    """
    A class representing a cross power spectrum.

    Attributes:
        name: The name of the power spectrum.
        cl: The power spectrum in Cl format.
        ells: The multipoles of the power spectrum.
        beam1: The first beam to convolve with the power spectrum.
        beam2: The second beam to convolve with the power spectrum.
        is_convolved: Boolean of whether the power spectrum is already convolved with the beam.

    Methods:
        convolve(): Convolve the power spectrum with the two beams.
        deconvolve(): Deconvolve the power spectrum with the two beams.
    """

    def __init__(self, 
                 name: str, 
                 cl: np.ndarray, 
                 ells: np.ndarray, 
                 beam1: Beam, 
                 beam2: Beam, 
                 is_convolved:bool):
        super().__init__(name, cl, ells, is_convolved)
        self.beam1 = beam1
        self.beam2 = beam2

    def convolve(self):
        if not self._is_beam_convolved:
            self._ps = self.beam1.conv1(self.beam2.conv1(self._ps))
            self._is_beam_convolved = True
        else:
            logger.warning("CrossSpectrum is already convolved. No action taken.")

    def deconvolve(self):
        if self._is_beam_convolved:
            self._ps = self.beam2.deconv1(self.beam1.deconv1(self._ps))
            self._is_beam_convolved = False
        else:
            logger.warning("CrossSpectrum is already deconvolved. No action taken.")


def get_auto_ps_result(map_, mask, lmax, beam, is_convolved, name=None) -> PowerSpectrum:
    """
    Calculate the auto power spectrum of a map and
    return it as an AutoSpectrum object.

    Args:
        map_: The input map.
        mask: The mask to apply to apply to the map.
        lmax: The maximum multipole to include in the power spectrum.
        beam: The beam to convolve with the power spectrum.
        is_convolved: Boolean of whether the power spectrum is already convolved with the beam.
        name: Optional name of the power spectrum.

    Returns:
        The auto power specturm as an AutoSpectrum object
    """
    
    cl = get_autopower(map_, mask, lmax)
    ells = np.arange(lmax + 1)
    return AutoSpectrum(name, cl, ells, beam, is_convolved)


def get_x_ps_result(map1, map2, mask, lmax, beam1, beam2, is_convolved, name=None) -> PowerSpectrum:
    """
    Calculate the cross power spectrum of two maps and
    return it as a CrossSpectrum object.

    Args:
        map1: The first input map.
        map2: The second input map.
        mask: The mask to apply to the maps.
        lmax: The maximum multipole to include in the power spectrum.
        beam1: The first beam to convolve with the power spectrum.
        beam2: The second beam to convolve with the power spectrum.
        is_convolved: Boolean of whether the power spectrum is already convolved with the beam.
        name: Optional name of the power spectrum.

    Returns:
        The cross power spectrum as a CrossSpectrum object.
    """

    cl = get_xpower(map1=map1,
                    map2=map2,
                    mask=mask,
                    lmax=lmax)
    ells = np.arange(lmax + 1)
    return CrossSpectrum(name, cl, ells, beam1, beam2, is_convolved)

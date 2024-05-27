from abc import ABC, abstractmethod
import logging

import numpy as np
import healpy as hp

from src.utils.physics_beam import Beam


logger = logging.getLogger(__name__)


def get_autopower(map_, mask, lmax):
    return get_xpower(map1=map_, map2=map_, mask=mask, lmax=lmax)


def get_xpower(map1, map2, mask, lmax, use_pixel_weights=False):
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
    def __init__(self, name: str, cl: np.ndarray, ells: np.ndarray):
        self.name = name
        self.ells = ells
        self._ps = cl
        self._is_cl: bool = True
        self._is_beam_convolved: bool = True

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
    def __init__(self, name: str, cl: np.ndarray, ells: np.ndarray, beam: Beam):
        super().__init__(name, cl, ells)
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
    def __init__(self, name: str, cl: np.ndarray, ells: np.ndarray, beam1: Beam, beam2: Beam):
        super().__init__(name, cl, ells)
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


def get_auto_ps_result(map_, mask, lmax, beam, name=None) -> PowerSpectrum:
    cl = get_autopower(map_, mask, lmax)
    ells = np.arange(lmax + 1)
    return AutoSpectrum(name, cl, ells, beam)


def get_x_ps_result(map1, map2, mask, lmax, beam1, beam2, name=None) -> PowerSpectrum:
    cl = get_xpower(map1=map1,
                    map2=map2,
                    mask=mask,
                    lmax=lmax)
    ells = np.arange(lmax + 1)
    return CrossSpectrum(name, cl, ells, beam1, beam2)

import healpy as hp
from astropy.io import fits

import numpy as np


class Beam:
    """
    Utility class representing an detector beam for convolution or deconvolution.
    Beams may need to be squared for autopower spectra.

    Attributes:
        beam: The beam profile used for convolution or deconvolution.

    Methods:
        conv1(ps): Apply the beam to the input power spectrum using convolution.
        conv2(ps): Apply the squared beam to the input power spectrum using convolution.
        deconv1(ps): Remove the effect of the beam from the input power spectrum using deconvolution.
        deconv2(ps): Remove the effect of the squared beam from the input power spectrum using deconvolution.
    """

    def __init__(self, beam) -> None:
        self.beam = beam

    def conv1(self, ps):
        """
        Apply the beam to the input power crosspectrum using convolution.
        The expectation is that this beam is for one map and another beam will
        be applied for the other map.

        Args:
            ps: The input power spectrum.

        Returns:
            The power spectrum with the beam applied.
        """
        ps_applied = ps * self.beam
        return ps_applied

    def conv2(self, ps):
        """
        Apply the squared beam to the input power autospectrum using convolution.
        This beam is effectively applied twice (for the same map appearing twice in the
        autopower spectrum calculation)

        Args:
            ps: The input power spectrum.

        Returns:
            The power spectrum with the squared beam applied.
        """
        ps_applied = ps * (self.beam ** 2)
        return ps_applied

    def deconv1(self, ps):
        """
        Remove the effect of the beam from the input power spectrum using deconvolution.
        The expectation is that this beam is for one map and another beam will
        be applied for the other map.

        Args:
            ps: The input power spectrum.

        Returns:
            The power spectrum with the beam effect removed.
        """
        # TODO: Handle zeros in beam
        ps_applied = ps / self.beam

        # TODO: Use this method instead
        # log_ps = np.log(ps)
        # log_beam = np.log(self.beam)
        # log_applied = log_ps - log_beam
        # ps_applied = np.exp(log_applied)
        return ps_applied

    def deconv2(self, ps):
        """
        Remove the effect of the squared beam from the input power spectrum using deconvolution.
        This beam is effectively applied twice (for the same map appearing twice in the
        autopower spectrum calculation)

        Args:
            ps: The input power spectrum.

        Returns:
            The power spectrum with the squared beam effect removed.
        """
        # TODO: Implement deconvolution with squared beam
        pass
        # TODO: Handle zeros in beam
        ps_applied = ps / (self.beam ** 2)

        # TODO: Use this method instead
        # log_ps = np.log(ps)
        # log_beam = np.log(self.beam)
        # log_applied = log_ps - 2 * log_beam
        # ps_applied = np.exp(log_applied)
        return ps_applied


class GaussianBeam(Beam):
    def __init__(self, beam_fwhm, lmax) -> None:
        """
        beam_fwhm in arcmin
        """
        # Convert fwhm from arcmin to radians
        self.fwhm = beam_fwhm * np.pi / (180*60)
        self.lmax = lmax
        beam = hp.gauss_beam(self.fwhm, lmax=lmax)
        super().__init__(beam)


class PlanckBeam(Beam):
    def __init__(self, planck_path, lmax) -> None:
        self.planck_path = planck_path
        self.lmax = lmax
        beam = get_planck_beam(planck_path, lmax)
        super().__init__(beam)


class NoBeam(Beam):
    def __init__(self, lmax) -> None:
        self.lmax = lmax
        beam = np.ones(lmax)
        super().__init__(beam)


def get_planck_beam(planck_path, lmax):
    hdul = fits.open(planck_path)
    beam = hdul[2].data['INT_BEAM']
    return Beam(beam[:lmax+1])

from typing import Optional, Dict
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Detector:
    """
    A data class representing a Detector.

    Attributes:
        nom_freq: The nominal frequency of the detector.
        fields: The fields of the detector.
        cen_freq: (Optional) The central frequency of the detector.
        fwhm: (Optional) The full width at half maximum of the detector.
    """
    
    nom_freq: int
    fields: str
    cen_freq: Optional[float] = None
    fwhm: Optional[float] = None

@dataclass(frozen=True)
class Instrument:
    """
    A data class representing an Instrument.

    Attributes:
        dets: A dictionary where the keys are detector IDs and the values are Detector objects.
    """
    
    dets: Dict[int, Detector]


def make_detector(det_info, band, fields):
    """
    Create a Detector object based on the specified information.
    The Detector object is a frozen dataclass.

    Args:
        det_info: A DataFrame containing the detector information.
        band: The band of the detector.
        fields: The fields of the detector.

    Returns:
        A Detector object with the specified information.
    """
    
    band_str = str(band)
    try:
        assert band_str in det_info['band']
    except AssertionError:
        raise KeyError(f"A detector specified in the configs, {band} " \
                        f"(converted to {band_str}) does not exist in " \
                        f"the given QTable path.")

    center_frequency = det_info.loc[band_str]['center_frequency']
    fwhm = det_info.loc[band_str]['fwhm']
    return Detector(nom_freq=band, cen_freq=center_frequency, fwhm=fwhm, fields=fields)


def make_instrument(cfg, det_info=None):
    """
    Create an Instrument object based on the specified configuration
    and detector information. The Instrument object is a frozen dataclass
    containing:
            detector_freqs x map_fields
            which are a subset of the full_instrument
            and the information for each from the planck_bandpasstable

    Args:
        cfg: The config object containing the instrument information.
        det_info: (Optional) A DataFrame containing the detector information.

    Returns:
        An Instrument object with the specified information.
    """
    scen_fields = cfg.scenario.map_fields
    full_instrument = cfg.scenario.full_instrument
    instrument_dets = {}
    for freq in cfg.scenario.detector_freqs:
        available_fields = full_instrument[freq]
        selected_fields = ''.join([field for field in available_fields if field in scen_fields])
        assert len(selected_fields) > 0, f"No fields were found for {freq} detector. Available fields: {available_fields}, Scenario fields: {scen_fields}."
        if det_info:
            det = make_detector(det_info, band=freq, fields=selected_fields)
        else:
            det = Detector(nom_freq=freq, fields=selected_fields)
        instrument_dets[freq] = det
    return Instrument(instrument_dets)

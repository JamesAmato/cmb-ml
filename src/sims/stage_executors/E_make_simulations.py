from typing import Dict

import hydra
from omegaconf import DictConfig
from pathlib import Path

from astropy.units import Quantity
import pysm3
import pysm3.units as u
from pysm3 import CMBLensed
import numpy as np
import camb

import logging

from..cmb_factory import CMBFactory
from ..random_seed_manager import FieldLevelSeedFactory, SimLevelSeedFactory
from ..detector import make_detector

from ...core import (
    BaseStageExecutor,
    ExperimentParameters,
    Split,
    Asset
)

from ..handlers.qtable_handler import QTableHandler # Import to register handler
# from ..handlers.psmaker_handler import PSHandler # Handler is not used for simulation.

from ..physics_cmb import change_nside_of_map
from ..physics_instrument_noise import make_random_noise_map

logger = logging.getLogger(__name__)

class SimCreatorExecutor(BaseStageExecutor):
    def __init__(self, cfg: DictConfig, experiment: ExperimentParameters) -> None:
        # The following stage_str must match the pipeline yaml
        super().__init__(cfg, experiment, stage_str='make_sims')

        self.planck_deltabandpass = self.assets_in['planck_deltabandpass']
        
        with self.name_tracker.set_context('src_root', cfg.local_system.noise_src_dir):
            self.deltabandpass = self.planck_deltabandpass.read()

        self.in_noise_cache = self.assets_in['noise_cache']
        self.in_wmap_fixed = self.assets_in['wmap_config_fixed']
        self.in_wmap_varied = self.assets_in['wmap_config_varied']
        self.in_ps_fixed = self.assets_in['cmb_ps_fid_fixed']
        self.in_ps_varied = self.assets_in['cmb_ps_fid_varied']

        self.out_cmb_map_fid = self.assets_out['cmb_map_fid']
        self.out_sims = self.assets_out['sims']

        # seed maker objects
        self.cmb_seed_factory = SimLevelSeedFactory(cfg, 'cmb')
        self.noise_seed_factory = FieldLevelSeedFactory(cfg, 'noise')

        # Initialize constants from configs
        self.nside_out = self.experiment.nside
        self.nside_sky = cfg.simulation.nside_sky
        self.planck_freqs = self.experiment.detector_freqs
        self.field_strings = self.experiment.map_fields
        preset_strings = list(cfg.simulation.preset_strings)
        self.lmax_pysm3_smoothing = int(cfg.simulation.cmb.derived_ps_nsmax_x * self.nside_out)

        self.placeholder = pysm3.Model(nside=self.nside_sky, max_nside=self.nside_sky)
        logger.debug('Creating PySM3 Sky object')
        self.sky = pysm3.Sky(nside=self.nside_sky,
                            component_objects=[self.placeholder],
                            preset_strings=preset_strings,
                            output_unit='K_CMB')
        logger.debug('Done creating PySM3 Sky object')
        self.cmb_factory = CMBFactory(cfg)

    def execute(self) -> None:
        super().execute()

    def process_split(self, split: Split) -> None:
        if split.ps_fidu_fixed:
            logger.debug(f"Working in {split.name}, fixed ps")
            self.process_sims(split, self.in_ps_fixed)
        else:
            logger.debug(f"Working in {split.name}, varied ps")
            self.process_sims(split, self.in_ps_varied)

    def process_sims(self, split, ps) -> None:
        for sim in split.iter_sims():
            with self.name_tracker.set_context("sim_num", sim):
                logger.debug(f"Creating simulation {split.name}:{sim}")
                cmb_seed = self.cmb_seed_factory.get_seed(split, sim)
                cmb = self.cmb_factory.make_cmb_lensed(cmb_seed, ps)
                self.sky.components[0] = cmb
                self.save_cmb_map_realization(cmb, self.out_cmb_map_fid)

                for freq in self.planck_freqs:
                    detector = make_detector(self.deltabandpass, freq)
                    skymaps = self.sky.get_emission(detector.cen_freq)

                    obs_map = []
                    for skymap, field_str in zip(skymaps, self.field_strings):
                        if freq in [545, 857] and field_str != "T":
                            continue
                        map_smoothed = pysm3.apply_smoothing_and_coord_transform(skymap, 
                                                                                 detector.fwhm, 
                                                                                 lmax=self.lmax_pysm3_smoothing, 
                                                                                 output_nside=self.nside_out)
                        noise_seed = self.noise_seed_factory.get_seed(split, sim, freq, field_str)
                        noise_map = self.get_noise_map(freq, field_str, noise_seed)
                        final_map = map_smoothed + noise_map
                        obs_map.append(final_map)

                    self.out_sims.write({str(freq): obs_map})
                    logger.debug(f"For {split.name}:{sim}, {freq} GHz: done with channel")
                logger.debug(f"For {split.name}:{sim}, done with simulation")

    def save_cmb_map_realization(self, cmb: CMBLensed, asset: Asset):
        cmb_realization: Quantity = cmb.map
        cmb_realization_units = cmb_realization.unit
        cmb_realization_data = cmb_realization.value  # The map itself
        nside_out = self.nside_out
        scaled_map = change_nside_of_map(cmb_realization_data, nside_out)
        scaled_map = scaled_map * cmb_realization_units
        # logger.debug(f"For {self.name_tracker.context['split']}:{self.name_tracker.context['sim_num']}, saving fiducial cmb_map")
        # TODO: Get answer of asset handler healpymap vs sim.write_fid_map
        asset.write(scaled_map)

    def get_noise_map(self, freq, field_str, noise_seed, center_frequency=None):
        with self.name_tracker.set_context('freq', freq):
            with self.name_tracker.set_context('field', field_str):
                # logger.debug(f"For {self.name_tracker.context['split']}:{self.name_tracker.context['sim_num']}, Getting noise map for {freq} GHz, {field_str}")
                sd_map = self.in_noise_cache.read()
                noise_map = make_random_noise_map(sd_map, noise_seed, center_frequency)
                return noise_map

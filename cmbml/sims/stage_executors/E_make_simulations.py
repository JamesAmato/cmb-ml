from typing import Dict
from pathlib import Path
import logging

import hydra
from omegaconf import DictConfig

import numpy as np
from astropy.units import Quantity
import camb
import pysm3
import pysm3.units as u
from pysm3 import CMBLensed

from cmbml.sims.cmb_factory import CMBFactory
from cmbml.sims.random_seed_manager import FieldLevelSeedFactory, SimLevelSeedFactory
from cmbml.utils.planck_instrument import make_instrument, Instrument

from cmbml.core import (
    BaseStageExecutor,
    Split,
    Asset, AssetWithPathAlts
)

from cmbml.core.asset_handlers.qtable_handler import QTableHandler # Import to register handler
from cmbml.core.asset_handlers.psmaker_handler import CambPowerSpectrum # Import for typing hint
from cmbml.core.asset_handlers.healpy_map_handler import HealpyMap # Import for VS Code hints

from cmbml.utils.map_formats import convert_pysm3_to_hp
from cmbml.sims.physics_cmb import downgrade_map
from cmbml.sims.physics_instrument_noise import make_random_noise_map


logger = logging.getLogger(__name__)


class SimCreatorExecutor(BaseStageExecutor):
    def __init__(self, cfg: DictConfig) -> None:
        # The following stage_str must match the pipeline yaml
        super().__init__(cfg, stage_str='make_sims')

        self.out_cmb_map: Asset = self.assets_out['cmb_map']
        self.out_obs_maps: Asset = self.assets_out['obs_maps']
        out_cmb_map_handler: HealpyMap
        out_obs_maps_handler: HealpyMap

        self.in_noise_cache: Asset = self.assets_in['noise_cache']
        self.in_cmb_ps: AssetWithPathAlts = self.assets_in['cmb_ps']
        in_det_table: Asset = self.assets_in['planck_deltabandpass']
        in_noise_cache_handler: HealpyMap
        in_cmb_ps_handler: CambPowerSpectrum
        in_det_table_handler: QTableHandler

        # TODO: Check this. Remove other instances in other Executors.
        # with self.name_tracker.set_context('src_root', cfg.local_system.assets_dir):
        det_info = in_det_table.read()

        # The instrument object contains both
        #   - information about physical detector parameters
        #   - information about configurations, (such as fields to use)
        self.instrument: Instrument = make_instrument(cfg=cfg, det_info=det_info)

        # seed maker objects
        self.cmb_seed_factory     = SimLevelSeedFactory(cfg, cfg.model.sim.cmb.seed_string)
        self.noise_seed_factory   = FieldLevelSeedFactory(cfg, cfg.model.sim.noise.seed_string)

        # Initialize constants from configs
        self.nside_sky = self.get_nside_sky()
        logger.info(f"Simulations will generated at nside_sky = {self.nside_sky}.")

        self.nside_out = cfg.scenario.nside
        logger.info(f"Simulations will be output at nside_out = {self.nside_out}")

        self.lmax_out = int(cfg.model.sim.pysm_beam_lmax_ratio * self.nside_out)
        logger.info(f"Simulation beam convolution will occur with lmax = {self.lmax_out}")

        self.units = cfg.scenario.units
        logger.info(f"Simulations will have units of {self.units}")

        self.preset_strings = list(cfg.model.sim.preset_strings)
        logger.info(f"Preset strings are {self.preset_strings}")
        self.output_units = cfg.scenario.units
        self.cmb_factory = CMBFactory(self.nside_sky)

        # Placeholder so we don't recreate the sky object over and over
        self.sky = None

    def execute(self) -> None:
        logger.debug(f"Running {self.__class__.__name__} execute() method")
        placeholder = pysm3.Model(nside=self.nside_sky, max_nside=self.nside_sky)
        logger.debug('Creating PySM3 Sky object')
        self.sky = pysm3.Sky(nside=self.nside_sky,
                             component_objects=[placeholder],
                             preset_strings=self.preset_strings,
                             output_unit=self.output_units)
        logger.debug('Done creating PySM3 Sky object')
        self.default_execute()

    def process_split(self, split: Split) -> None:
        for sim in split.iter_sims():
            with self.name_tracker.set_context("sim_num", sim):
                self.process_sim(split, sim_num=sim)

    def process_sim(self, split: Split, sim_num: int) -> None:
        sim_name = self.name_tracker.sim_name()
        logger.debug(f"Creating simulation {split.name}:{sim_name}")
        cmb_seed = self.cmb_seed_factory.get_seed(split, sim_num)
        ps_path = self.in_cmb_ps.path_alt if split.ps_fidu_fixed else self.in_cmb_ps.path
        cmb = self.cmb_factory.make_cmb(cmb_seed, ps_path)
        self.sky.components[0] = cmb
        self.save_cmb_map_realization(cmb)

        for freq, detector in self.instrument.dets.items():
            skymaps = self.sky.get_emission(detector.cen_freq)

            obs_map = []
            column_names = []
            for skymap, field_str in zip(skymaps, detector.fields):
                # Use pysm3.apply_smoothing... to convolve the map with the planck detector beam
                map_smoothed = pysm3.apply_smoothing_and_coord_transform(skymap, 
                                                                         detector.fwhm, 
                                                                         lmax=self.lmax_out, 
                                                                         output_nside=self.nside_out)
                noise_seed = self.noise_seed_factory.get_seed(split.name, sim_num, freq, field_str)
                noise_map = self.get_noise_map(freq, field_str, noise_seed)
                final_map = map_smoothed + noise_map
                obs_map.append(final_map)

                column_names.append(field_str + "_STOKES")

            with self.name_tracker.set_contexts(dict(freq=freq)):
                self.out_obs_maps.write(data=obs_map,
                                        column_names=column_names)
            logger.debug(f"For {split.name}:{sim_name}, {freq} GHz: done with channel")
        logger.debug(f"For {split.name}:{sim_name}, done with simulation")

    def save_cmb_map_realization(self, cmb: CMBLensed):
        cmb_realization: Quantity = cmb.map
        # PySM3 components always include T, Q, U, so we need to extract the temperature map
        if self.instrument.map_fields == 'I':
            cmb_realization = cmb_realization[0]

        # Break out astropy units information, healpy doesn't play well with it (downgrade function)
        cmb_data, cmb_units = convert_pysm3_to_hp(cmb_realization)

        scaled_map = downgrade_map(cmb_data, self.nside_out, lmax_in=None, lmax_out=self.lmax_out)

        self.out_cmb_map.write(data=scaled_map, column_units=cmb_units)

    def get_noise_map(self, freq, field_str, noise_seed, center_frequency=None):
        with self.name_tracker.set_context('freq', freq):
            with self.name_tracker.set_context('field', field_str):
                sd_map = self.in_noise_cache.read()
                noise_map = make_random_noise_map(sd_map, noise_seed, center_frequency)
                return noise_map

    def get_nside_sky(self):
        nside_out = self.cfg.scenario.nside
        nside_sky_set = self.cfg.model.sim.get("nside_sky", None)
        nside_sky_factor = self.cfg.model.sim.get("nside_sky_factor", None)

        nside_sky = nside_sky_set if nside_sky_set else nside_out * nside_sky_factor
        return nside_sky

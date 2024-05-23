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

from ..cmb_factory import CMBFactory
from ..random_seed_manager import FieldLevelSeedFactory, SimLevelSeedFactory
from utils.planck_instrument import make_instrument, Instrument

from core import (
    BaseStageExecutor,
    Split,
    Asset, AssetWithPathAlts
)

from core.asset_handlers.qtable_handler import QTableHandler # Import to register handler
from core.asset_handlers.psmaker_handler import PowerSpectrum # Import for typing hint

from core.asset_handlers import HealpyMap # Import for VS Code hints

from utils.map_formats import convert_pysm3_to_hp

from ..physics_cmb import change_nside_of_map
from ..physics_instrument_noise import make_random_noise_map

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
        in_cmb_ps_handler: PowerSpectrum
        in_det_table_handler: QTableHandler

        with self.name_tracker.set_context('src_root', cfg.local_system.noise_src_dir):
            det_info = in_det_table.read()
        self.instrument: Instrument = make_instrument(cfg=cfg, det_info=det_info)

        # seed maker objects
        self.cmb_seed_factory     = SimLevelSeedFactory(cfg, cfg.model.sim.cmb.seed_string)
        self.noise_seed_factory   = FieldLevelSeedFactory(cfg, cfg.model.sim.noise.seed_string)

        # Initialize constants from configs
        self.nside_sky = self.get_nside_sky()
        logger.info(f"Simulations will generated at nside_sky = {self.nside_sky}.")

        self.nside_out = cfg.scenario.nside
        logger.info(f"Simulations will be output at nside_out = {self.nside_out}")
        
        self.lmax_pysm3_smoothing = int(cfg.model.sim.cmb.derived_ps_nsmax_x * self.nside_out)
        logger.info(f"Simulation beam convolution will occur with lmax = {self.lmax_pysm3_smoothing}.")
        
        self.units = cfg.scenario.units
        logger.info(f"Simulations will have units of {self.units}")

        # placeholder = pysm3.Model(nside=self.nside_sky, max_nside=self.nside_sky)

        ##############################
        # Start of Adam's stuff
        ##############################



        # self.varied_comp_strs = list(dict(cfg.model.sim.components.varied).keys())
        self.fixed_comp_strs = list(dict(cfg.model.sim.components).keys())

        self.inst_comps = []

        logger.debug('Instantiating fixed PySM3 component objects')
        for comp in self.fixed_comp_strs:
            self.inst_comps.append(hydra.utils.instantiate(cfg.model.sim.components[comp]))

            # param_dict = dict(cfg.model.sim.components[comp])
            # param_dict.pop("_target_")
            # cmp = pysm3.ModifiedBlackBody(**param_dict)
            # self.inst_comps.append(cmp)

            a = 1

        # logger.debug('got components: {aasdbfhasdkjbhf}')

        logger.debug('Done instantiating fixed PySM3 component objects')

        self.preset_strings = list(cfg.model.sim.preset_strings)
        logger.info(f"Preset strings are {self.preset_strings}")

        self.output_unit = cfg.scenario.units

        # Instantiate components
        # varied_comp_strs = list(dict(cfg.components.varied).keys())
        # fixed_comp_strs = list(dict(cfg.components.fixed).keys())
        # placeholder = []
        # inst_comps = []

        # for comp in varied_comp_strs:
        #     # if comp is noise:
        #     #     continue
        #     placeholder.append(comp)

        # Needs to be per sim
        # ???
        # logger.debug('Instantiating varied PySM3 component objects')
        # for c, i in enumerate(placeholder):
        #     self.sky_components[i] = instantiate(cfg.components.varied[c])
        # logger.debug('Done instantiating varied PySM3 component objects')

        # logger.debug('Instantiating fixed PySM3 component objects')
        # for comp in fixed_comp_strs:
        #     inst_comps.append(instantiate(cfg.components.fixed[comp]))
        # logger.debug('Done instantiating fixed PySM3 component objects')

        # preset_strings = list(cfg.model.sim.preset_strings)
        # logger.info(f"Preset strings are {preset_strings}")
        
        # logger.debug('Creating PySM3 Sky object')
        # sky = instantiate(
        #     cfg.sky,
        #     component_objects = inst_comps,
        #     preset_strings = preset_strings
        # )
        # logger.debug('Done creating PySM3 Sky object')

        ##############################
        # End of Adam's stuff
        ##############################

        # logger.debug('Creating PySM3 Sky object')        
        # self.sky = pysm3.Sky(nside=self.nside_sky,
        #                      component_objects=[placeholder],
        #                      preset_strings=preset_strings,
        #                      output_unit=cfg.scenario.units)
        # logger.debug('Done creating PySM3 Sky object')

        self.cmb_factory = CMBFactory(self.nside_sky)

    def execute(self) -> None:

        ##############################
        # Adam's stuff
        ##############################

        # self.placeholder = []

        # for comp in self.varied_comp_strs:
        #     # if comp is noise:
        #     #     continue
        #     p = pysm3.Model(nside=self.nside_sky, max_nside=self.nside_sky)
        #     self.placeholder.append(p)

        # self.placeholder.append(self.inst_comps)

        logger.debug('Creating PySM3 Sky object')        
        self.sky = pysm3.Sky(nside=self.nside_sky,
                             component_objects=self.inst_comps,
                             preset_strings=self.preset_strings,
                             output_unit=self.output_unit)
        logger.debug('Done creating PySM3 Sky object')

        # logger.debug(f"Executing SimCreatorExecutor execute()")
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
        cmb = self.cmb_factory.make_cmb_lensed(cmb_seed, ps_path)
        self.sky.components[0] = cmb
        self.save_cmb_map_realization(cmb)

        ##############################
        # Adam's stuff
        ##############################

        # Don't worry about this yet
        # logger.debug('Instantiating varied PySM3 component objects')
        # for c, i in enumerate(self.placeholder):
        #     self.sky.components[i] = instantiate(cfg.components.varied[c])
        # logger.debug('Done instantiating varied PySM3 component objects')

        for freq, detector in self.instrument.dets.items():
            skymaps = self.sky.get_emission(detector.cen_freq)

            obs_map = []
            column_names = []
            for skymap, field_str in zip(skymaps, detector.fields):
                # Use pysm3.apply_smoothing_...  to convolve the map with the planck detector beam
                map_smoothed = pysm3.apply_smoothing_and_coord_transform(skymap, 
                                                                         detector.fwhm, 
                                                                         lmax=self.lmax_pysm3_smoothing, 
                                                                         output_nside=self.nside_out)
                noise_seed = self.noise_seed_factory.get_seed(split, sim_num, freq, field_str)
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
        nside_out = self.nside_out
        cmb_data, cmb_units = convert_pysm3_to_hp(cmb_realization)
        scaled_map = change_nside_of_map(cmb_data, nside_out)
        self.out_cmb_map.write(data=scaled_map, column_units=cmb_units)

    def get_noise_map(self, freq, field_str, noise_seed, center_frequency=None):
        with self.name_tracker.set_context('freq', freq):
            with self.name_tracker.set_context('field', field_str):
                # logger.debug(f"For {self.name_tracker.context['split']}:{self.name_tracker.context['sim_num']}, Getting noise map for {freq} GHz, {field_str}")
                sd_map = self.in_noise_cache.read()
                noise_map = make_random_noise_map(sd_map, noise_seed, center_frequency)
                return noise_map

    def get_nside_sky(self):
        nside_out = self.cfg.scenario.nside
        nside_sky_set = self.cfg.model.sim.get("nside_sky", None)
        nside_sky_factor = self.cfg.model.sim.get("nside_sky_factor", None)

        nside_sky = nside_sky_set if nside_sky_set else nside_out * nside_sky_factor
        return nside_sky

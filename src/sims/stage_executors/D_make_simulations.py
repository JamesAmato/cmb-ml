from typing import Dict

import hydra
from omegaconf import DictConfig
from pathlib import Path

import pysm3
import pysm3.units as u
from pysm3 import CMBLensed
import numpy as np
import camb

import logging

from ..sim_stuff import CMBFactory, FieldLevelSeedFactory, SimLevelSeedFactory
from ..detector import make_detector

from ...core import (
    BaseStageExecutor,
    ExperimentParameters,
    Split,
    Asset
)

from ..specific_handlers.qtable_handler import QTableHandler # Import to register handler
from ..specific_handlers.psmaker_handler import PSHandler # Import to register handler

from ..physics_cmb import map2ps, convert_to_log_power_spectrum, scale_fiducial_cmb
from ..physics_instrument_noise import make_random_noise_map

logger = logging.getLogger(__name__)

class SimCreatorExecutor(BaseStageExecutor):
    def __init__(self, cfg: DictConfig, experiment: ExperimentParameters) -> None:
        self.stage_str = 'create-sims'
        super().__init__(cfg, experiment)

        self.planck_deltabandpass = self.assets_in['planck_deltabandpass']
        
        with self.name_tracker.set_context('src_root', cfg.local_system.noise_src_dir):
            self.deltabandpass = self.planck_deltabandpass.read()
        

        self.in_noise_cache = self.assets_in['noise_cache']
        self.in_wmap_fixed = self.assets_in['wmap_config_fixed']
        self.in_wmap_varied = self.assets_in['wmap_config_varied']
        self.in_ps_fixed = self.assets_in['cmb_ps_fid_fixed']
        self.in_ps_varied = self.assets_in['cmb_ps_fid_varied']

        self.out_cmb_map_fid = self.assets_out['cmb_map_fid']
        self.out_cmb_ps_der = self.assets_out['cmb_ps_der']
        self.out_sims = self.assets_out['sims']

        # seed maker objects
        self.cmb_seed_factory = SimLevelSeedFactory(cfg, 'cmb')
        self.noise_seed_factory = FieldLevelSeedFactory(cfg, 'noise')
        # Initialize constants from configs

        self.nside_out = self.experiment.nside
        self.nside_sky = cfg.simulation.nside_sky
        
        assert self.nside_sky > self.nside_out, "nside of sky should be greater than nside of target output by at least a factor of 2"

        self.preset_strings = list(cfg.simulation.preset_strings)
        self.planck_freqs = self.experiment.detector_freqs
        self.field_strings = self.experiment.map_fields
        self.lmax_pysm3_smoothing = int(cfg.simulation.cmb.derived_ps_nsmax_x * self.nside_out)
        self.lmax_derived_ps = int(cfg.simulation.cmb.derived_ps_nsmax_x * self.nside_out)

        self.placeholder = pysm3.Model(nside=self.nside_sky, max_nside=self.nside_sky)
        logger.debug('creating sky')
        self.sky = pysm3.Sky(nside=self.nside_sky,
                            component_objects=[self.placeholder],
                            preset_strings=self.preset_strings,
                            output_unit='K_CMB')
        logger.debug('done creating sky')
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
                
                
                logger.debug(f"Making CMB")
                cmb = self.cmb_factory.make_cmb_lensed(cmb_seed, ps)
                logger.debug(f"Done making CMB")

                logger.debug(f"Hotswapping CMB in sky for {sim}")
                self.sky.components[0] = cmb
                logger.debug(f"Done hotswapping CMB in sky for {sim}")

                self.save_fid_cmb_map(cmb, self.out_cmb_map_fid)

                logger.debug(f"Writing derived ps at ell_max = {self.lmax_derived_ps} for {sim}")
                self.save_der_cmb_ps(cmb, self.out_cmb_ps_der, lmax=self.lmax_derived_ps)

                for freq in self.planck_freqs:
                    detector = make_detector(self.deltabandpass, freq)

                    logger.debug(f"for {sim}, {freq} GHz, getting sky emission")
                    skymaps = self.sky.get_emission(detector.cen_freq)
                    logger.debug(f"for {sim}, {freq} GHz, getting sky emission done")

                    obs_map = []
                    for skymap, field_str in zip(skymaps, self.field_strings):
                        if freq in [545, 857] and field_str != "T":
                            logger.debug(f"Skipping {freq} GHz, {field_str}: source data not found at frequency.")
                            continue
                        
                        logger.debug(f'for {sim}, {freq} GHz, {field_str}: applying beam effects')
                        map_smoothed = pysm3.apply_smoothing_and_coord_transform(skymap, 
                                                                                 detector.fwhm, 
                                                                                 lmax=self.lmax_pysm3_smoothing, 
                                                                                 output_nside=self.nside_out)
                        logger.debug(f'for {sim}, {freq} GHz, {field_str}: making noise')
                        noise_seed = self.noise_seed_factory.get_seed(split, sim, freq, field_str)
                        noise_map = self.get_noise_map(freq, field_str, noise_seed)
                        final_map = map_smoothed + noise_map
                        obs_map.append(final_map)
                        logger.debug(f"for {sim}, {freq} GHz, {field_str}: done with field")

                    logger.debug(f"for {sim}, {freq} GHz: writing file")
                    self.out_sims.write({str(freq): obs_map})
                    logger.info(f"for {sim}, {freq} GHz: done with channel")
                logger.debug(f"for {sim}: done with simulation")

    def save_fid_cmb_map(self, cmb: CMBLensed, asset: Asset):
        fid_cmb_map = cmb.map
        units = fid_cmb_map.unit        # Astropy being all clever and tracking unity
        values = fid_cmb_map.value       # The numbers in the array
        nside_out = self.nside_out
        scaled_map = scale_fiducial_cmb(values, nside_out)
        scaled_map = scaled_map * units
        logger.debug(f"Saving fiducial cmb_map for {asset.path.parent.name}")
        # TODO: Get answer of asset handler healpymap vs sim.write_fid_map
        asset.write(scaled_map)


    def save_der_cmb_ps(self, cmb: CMBLensed, asset: Asset, lmax: int):
        logger.debug(f"Getting derived cmb_ps for {asset.path.parent.name}")
        fid_cmb_map = cmb.map
        ps_cl = map2ps(fid_cmb_map, lmax)
        ps_dl = convert_to_log_power_spectrum(ps_cl)
        logger.debug(f"Saving fiducial cmb_ps for {asset.path.parent.name}")
        camb.results.save_cmb_power_array(asset.path,
                                        array=ps_dl,
                                        labels="TT EE BB TE EB TB")

    
    def get_noise_map(self, freq, field_str, noise_seed, center_frequency=None):
        with self.name_tracker.set_context('freq', freq):
            with self.name_tracker.set_context('field', field_str):
                logger.debug(f"Getting noise map for {freq} GHz, {field_str}")
                sd_map = self.in_noise_cache.read()
                noise_map = make_random_noise_map(sd_map, noise_seed, center_frequency)
                return noise_map
    



        
        



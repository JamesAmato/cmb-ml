from typing import List, Dict
import logging

import numpy as np

from omegaconf import DictConfig

from core import BaseStageExecutor, Split, Asset
from .make_pyilc_config import ILCConfigMaker
from .qtable_handler import QTableHandler  # Import needed to register QTableHandler
from pyilc_redir.pyilc_wrapper import run_ilc
from utils import make_instrument, Instrument
from utils.suppress_print import SuppressPrint


logger = logging.getLogger(__name__)


class PredictionExecutor(BaseStageExecutor):
    def __init__(self, cfg: DictConfig) -> None:
        logger.debug("Initializing NILC PredictExecutor")
        super().__init__(cfg, stage_str = "predict")

        self.out_config: Asset = self.assets_out["config_file"]
        self.out_model: Asset = self.assets_out["model"]
        self.out_cmb_asset: Asset = self.assets_out["cmb_map"]

        self.in_obs_assets: Asset = self.assets_in["obs_maps"]
        self.in_planck_deltabandpass: Asset = self.assets_in["planck_deltabandpass"]
        in_det_table: Asset = self.assets_in['planck_deltabandpass']
        # with self.name_tracker.set_context("src_root", cfg.local_system.assets_dir):
        #     planck_bandpass = self.in_planck_deltabandpass.read()
        with self.name_tracker.set_context('src_root', cfg.local_system.assets_dir):
            det_info = in_det_table.read()

        self.instrument: Instrument = make_instrument(cfg=cfg)
        self.channels = self.instrument.dets.keys()

        self.model_cfg_maker = ILCConfigMaker(cfg, det_info)

    def execute(self) -> None:
        self.default_execute()

    def process_split(self, 
                      split: Split) -> None:
        logger.info(f"Executing PredictExecutor process_split() for split: {split.name}.")
        for sim in split.iter_sims():
            with self.name_tracker.set_context("sim_num", sim):
                self.process_sim()

    def process_sim(self) -> None:
        working_path = self.out_model.path
        working_path.mkdir(exist_ok=True, parents=True)

        input_paths = []
        for freq in self.instrument.dets.keys():
            with self.name_tracker.set_context("freq", freq):
                path = self.in_obs_assets.path
                # Convert to string; we're going to convert this information to a yaml file
                input_paths.append(str(path))

        cfg_dict = self.model_cfg_maker.make_config(output_path=working_path,
                                                    input_paths=input_paths)
        self.out_config.write(data=cfg_dict)
        logger.info("Running PyILC Code...")
        with SuppressPrint():
            run_ilc(self.out_config.path)
        logger.info("Moving resulting map.")
        self.move_result()

    def move_result(self):
        result_dir = self.out_model.path
        result_prefix = self.cfg.model.pyilc.output_prefix
        result_ext = self.cfg.model.pyilc.save_as
        result_fn = f"{result_prefix}needletILCmap_component_CMB.{result_ext}"

        result_path = result_dir / result_fn
        destination_path = self.out_cmb_asset.path

        destination_path.parent.mkdir(exist_ok=True, parents=True)

        result_path.rename(destination_path)
from typing import Dict, List
import logging

import numpy as np

from omegaconf import DictConfig

from core import (
    BaseStageExecutor,
    Split,
    Asset
    )
from src.utils import make_instrument, Instrument
from core.asset_handlers import HealpyMap, Config # Import for typing hint


logger = logging.getLogger(__name__)


class PreprocessMakeScaleExecutor(BaseStageExecutor):
    def __init__(self, cfg: DictConfig) -> None:
        logger.debug("Initializing CMBNNCS PreprocessMakeScaleParamsExecutor")
        # The following string must match the pipeline yaml
        super().__init__(cfg, stage_str = "make_normalization")

        self.instrument: Instrument = make_instrument(cfg=cfg)

        self.channels: List[str] = ["cmb", *self.instrument.dets]

        self.out_norm_file: Asset = self.assets_out["norm_file"]
        out_norm_file_handler: Config
        self.in_cmb_map: Asset = self.assets_in["cmb_map"]
        self.in_obs_maps: Asset = self.assets_in["obs_maps"]
        in_cmb_map_handler: HealpyMap
        in_obs_map_handler: HealpyMap

        # TODO: Move this to a better config file (note duplicate reminder in config.yaml)
        self.scale_features = cfg.model.cmbnncs.preprocess.scale_features
        self.scale_target = cfg.model.cmbnncs.preprocess.scale_target

    def execute(self) -> None:
        logger.debug("PreprocessMakeScaleParamsExecutor execute() method.")
        # Defining extrema at the scope of the stage: we want extrema of all maps across splits
        #    Note that some channels won't use all fields (e.g. 545, 857 only have intensity)
        scale_factors = {}
        for freq, detector in self.instrument.dets.items():
            scale_factors[freq] = {}
            for field_char in detector.fields:
                scale_factors[freq][field_char] = {}
                scale_factors[freq][field_char]['scale'] = self.scale_features
        scale_factors['cmb'] = {field_char: {'scale': self.scale_target} for field_char in self.cfg.scenario.map_fields}
        self.out_norm_file.write(data=scale_factors)

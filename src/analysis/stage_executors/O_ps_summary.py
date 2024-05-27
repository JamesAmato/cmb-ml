import logging
from typing import Union, Tuple, List, Any, Dict

from omegaconf import DictConfig

import numpy as np
import pandas as pd
import json

from src.core import (BaseStageExecutor,
                       Split, 
                       Asset)

from src.core.asset_handlers.asset_handlers_base import EmptyHandler, Config
from src.core.asset_handlers.psmaker_handler import NumpyPowerSpectrum

logger = logging.getLogger(__name__)

class PowerSpectrumSummaryExecutor(BaseStageExecutor):
    def __init__(self, cfg: DictConfig) -> None:
        super().__init__(cfg, stage_str="ps_summary")

        self.overall_stats: Asset = self.assets_out["overall_stats"]
        self.epoch_stats: Asset = self.assets_out["epoch_stats"]
        self.out_stats_per_split: Asset = self.assets_out["stats_per_split"]
        out_ps_overall_stats_handler: EmptyHandler

        self.in_ps_report: Asset = self.assets_in["report"]
        self.in_ps_dist: Asset = self.assets_in["wmap_distribution"]
        in_handlers: Union[Config, EmptyHandler]

    def execute(self) -> None:
        logger.debug(f"Running {self.__class__.__name__} execute()")
        report_path = self.in_ps_report.path
        df = pd.read_csv(report_path)
        # print(df.info())
        df['epoch'] = df['epoch'].astype(str)
        df['epoch'] = df['epoch'].replace("nan", "", inplace=True)

        for epoch in self.model_epochs:
            logger.info(f"Generating summary for epoch {epoch}.")
            with self.name_tracker.set_context('epoch', epoch):
                epoch_df = df[df['epoch']==str(epoch)]
                self.summary_tables(epoch_df)

    def summary_tables(self, df):
        # Compute overall averages, excluding non-numeric fields like 'sim' and 'split'
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        overall_stats = df[numeric_columns].agg(['mean', 'std'])
        stats_per_split = df.groupby('split')[numeric_columns].agg(['mean', 'std'])
        overall_path = self.epoch_stats.path
        self.epoch_stats.write()
        overall_stats.reset_index().to_csv(overall_path, index=False)
        per_split_path = self.out_stats_per_split.path
        stats_per_split.reset_index().to_csv(per_split_path, index=False)

    def generate_stats(self):
        report_data = self.in_ps_report.read()
        # dist_data = json.load(self.in_ps_dist.path)

        report_df = pd.DataFrame(report_data)

        pairs = ['real_pred', 'real_theory', 'pred_theory']

        for pair in pairs:
            report_df[pair + '_rmse'] = np.sqrt(report_df[pair + '_mse'])

        agg_df = report_df.groupby(['epoch', 'split']).agg(['mean', 'std'])

        report_path = self.out_ps_overall_stats.path
        self.out_ps_overall_stats.write()
        agg_df.reset_index().to_csv(report_path)

        print(pd.read_csv(report_path))
from omegaconf import DictConfig, OmegaConf
from typing import Dict, List

from ..get_wmap_params import get_wmap_indices, pull_params_from_file
from pathlib import Path

from ...core import (
    BaseStageExecutor,
    ExperimentParameters,
    Split,
    Asset
)

class ConfigExecutor(BaseStageExecutor):
    def __init__(self, cfg: DictConfig, experiment: ExperimentParameters) -> None:
        self.stage_str = "create-configs"
        super().__init__(cfg, experiment)

        self.out_split_config: Asset = self.assets_out['split_configs']
        self.out_param_config: Asset = self.assets_out['param_configs']
        self.in_config: Asset = self.assets_in['configs_dir']

        self.wmap_param_labels = cfg.simulation.cmb.wmap_params
        self.wmap_chain_length = cfg.simulation.cmb.wmap_chain_length
        self.wmap_chains_dir = Path(cfg.local_system.wmap_chains_dir)
        
        self.seed = cfg.simulation.cmb.wmap_indcs_seed

    def execute(self) -> None:
        super().execute()

    def process_split(self, split: Split) -> None:
        split_cfg_dict = dict(
            ps_fidu_fixed = split.ps_fidu_fixed,
            n_sims = split.n_sims,
            wmap_chain_idcs = self.make_chain_idcs_for_each_split(split, self.seed)[split.name]
        )

        with self.name_tracker.set_context("split", split.name):
            print(self.name_tracker.context)
            path = self.out_split_config.path
            print(f'writing to path: {path}')
            print(split_cfg_dict)
            split_yaml = OmegaConf.create(split_cfg_dict)

            with open(path, 'w') as f:
                OmegaConf.save(config=split_yaml, f=f)

        self.make_cosmo_param_configs(split_cfg_dict['wmap_chain_idcs'], split)

        
        

    def make_chain_idcs_for_each_split(self, split: Split, seed:int) -> Dict[str, List[int]]:
        n_indices_total = split.n_sims
        all_chain_indices = get_wmap_indices(n_indices_total, seed, wmap_chain_length=self.wmap_chain_length)
        # convert from numpy array of np.int64 to List[int] for OmegaConf
        all_chain_indices = getattr(all_chain_indices, "tolist", lambda: all_chain_indices)()
        
        last_index_used = 0
        chain_idcs_dict = {}
    
        first_index = last_index_used
        last_index_used = first_index + split.n_sims
        chain_idcs_dict[split.name] = all_chain_indices[first_index: last_index_used]

        return chain_idcs_dict
    
    def make_cosmo_param_configs(self, chain_idcs, split):
        
        
        wmap_params = pull_params_from_file(wmap_chain_path=self.wmap_chains_dir,
                                            chain_idcs=chain_idcs,
                                            params_to_get=self.wmap_param_labels,
                                            wmap_chain_length=self.wmap_chain_length)

        if split.ps_fidu_fixed:
            n_sims_to_process = 1
        else:
            n_sims_to_process = split.n_sims
        
        for i in range(n_sims_to_process):
            these_params = {key: values[i] for key, values in wmap_params.items()}
            print(these_params)
            # sim = split.get_sim(i)
            # sim.write_wmap_params_file(these_params)

    
    

# logger.debug("Creating split configurations")
#     seed = cfg.simulation.cmb.wmap_indcs_seed
#     chain_idcs_dict = dataset_configs_builder.make_chain_idcs_for_each_split(seed)
#     dataset_configs_builder.make_split_configs(chain_idcs_dict)
    
#     logger.debug("Creating cosmological parameters")
#     dataset_configs_builder.make_cosmo_param_configs()



  
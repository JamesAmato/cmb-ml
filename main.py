import logging

import hydra

from src.core import (
                      PipelineContext,
                    #   BaseStageExecutor,
                      LogMaker
                      )
# from src.sims import DirectoryExecutor 

from src.sims.stage_executors.A_make_dirs import DirectoryExecutor 
# from src.sims.stage_executors.B_make_configs import ConfigExecutor
from src.sims.stage_executors.asdf import ConfigExecutor

logger = logging.getLogger(__name__)


@hydra.main(version_base=None, config_path="cfg", config_name="config")
def make_all_simulations(cfg):
    logger.debug(f"Running {__name__} in {__file__}")

    log_maker = LogMaker(cfg)
    log_maker.log_scripts_to_hydra(source_script=__file__)

    pipeline_context = PipelineContext(cfg)

    pipeline_context.add_pipe(DirectoryExecutor)
    pipeline_context.add_pipe(ConfigExecutor)
    # pipeline_context.add_pipe(PreprocessExecutor)
    # pipeline_context.add_pipe(TrainingExecutor)
    # pipeline_context.add_pipe(PredictionExecutor)

    pipeline_context.run_pipeline()

    logger.info("Petroff pipeline completed.")
    log_maker.copy_hydra_run_to_dataset_log()


if __name__ == "__main__":
    make_all_simulations()

import logging
import hydra
from utils.hydra_log_helper import *


logger = logging.getLogger(__name__)


@hydra.main(version_base=None, config_path="cfg", config_name="config")
def test_class(cfg):
    logger.setLevel("DEBUG")
    log_cfg(cfg, caller_name="main")
    pass


if __name__ == "__main__":
    test_class()

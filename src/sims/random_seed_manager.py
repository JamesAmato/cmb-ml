
from typing import List
import logging
from hashlib import sha256
from omegaconf import DictConfig

from omegaconf.errors import ConfigAttributeError

from src.core import Split


logger = logging.getLogger('seed_logger')


class SeedMaker:
    """
    A class that manages seeds for randomization.

    Attributes:
        cfg (DictConfig): The Hydra config to use.
        sky_component (str): The sky component to randomly generate.

    Methods:
        sim_num_str(sim): Retrieve the simulation number.
        get_base_string(cfg): Retrieve the seed base string.
        get_component_string(cfg, sky_component): Retrieve the seed string of a component.
    """
    
    def __init__(self, 
                 cfg: DictConfig, 
                 sky_component: str) -> None:
        self.base: str = self.get_base_string(cfg)
        self.component: str = self.get_component_string(cfg, sky_component)
        self.str_num_digits = cfg.file_system.sim_str_num_digits
        try:
            "".join([self.base, ""])
        except TypeError as e:
            raise e

    def sim_num_str(self, sim: int) -> str:
        """
        Retrieve the simulation number.

        Args:
            sim (int): The simulation to get the number of.

        Returns:
            str: The simulation number in string form.
        """
        
        return f"{sim:0{self.str_num_digits}d}"
    
    def get_base_string(self,
                        cfg: DictConfig):
        """
        Retrieve the seed base string from the config.

        Args:
            cfg (DictConfig): The Hydra config to read.

        Returns:
            str: The seed base string.
        """
        
        base_string = cfg.model.sim.seed_base_string
        return str(base_string)

    def get_component_string(self, 
                             cfg: DictConfig, 
                             sky_component: str) -> str:
        """
        Retrieve the seed string of the specified sky component.

        Args:
            cfg (DictConfig): The Hydra config to read.
            sky_component (str): The specified sky component.

        Returns:
            str: The seed string of the component.
        """
        
        try:
            base_string = cfg.model.sim[sky_component].seed_string
            pass
        except ConfigAttributeError as e:
            if self.use_backup_strs:
                logger.warning(f"No seed string set for {sky_component} yaml; using '{sky_component}'.")
                base_string = sky_component
            else:
                logger.error(f"No seed string set for {sky_component} yaml; backup string disabled.")
                raise e
        return str(base_string)

    def _get_seed(self, *args: List[str]) -> int:
        try:
            str_list = [self.base, *args]
            seed_str = "_".join(str_list)
        except Exception as e:
            raise e
        seed_int = self.string_to_seed(seed_str)
        return seed_int

    @staticmethod
    def string_to_seed(input_string: str) -> int:
        hash_object = sha256(input_string.encode())
        # Convert the hash to an integer
        hash_integer = int(hash_object.hexdigest(), 16)
        # Reduce the size to fit into expected seed range of ints (for numpy/pysm3)
        seed = hash_integer % (2**32)
        logger.info(f"Seed for {input_string} is {seed}.")
        return seed


class SimLevelSeedFactory(SeedMaker):
    """
    An implementation of the SeedMaker class that
    creates simulation level seeds

    Attributes:
        cfg (DictConfig): The Hydra config to use.
        sky_component (str): The sky component to use.

    Methods:
        get_seed(split, sim): Generate and retrieve a seed.
    """
    
    def __init__(self, 
                 cfg: DictConfig, 
                 sky_component: str) -> None:
        super().__init__(cfg, sky_component)

    def get_seed(self, 
                 split: Split, 
                 sim: int) -> int:
        """
        Generate and retrieve the seed of the
        specified split for a simulation.

        Args:
            split (Split): The specified split.
            sim (int): The specified simulation.

        Returns:
            int: The generated seed.
        """
        
        split_str = split.name
        sim_str = self.sim_num_str(sim)
        return self._get_seed(split_str, sim_str, self.component)


class FieldLevelSeedFactory(SeedMaker):
    """
    An implementation of the SeedMaker class that
    creates field level seeds

    Attributes:
        cfg (DictConfig): The Hydra config to use.
        sky_component (str): The sky component to use.

    Methods:
        get_seed(split, sim): Generate and retrieve a seed.
    """

    def __init__(self, 
                 cfg: DictConfig, 
                 sky_component: str) -> None:
        super().__init__(cfg, sky_component)

    def get_seed(self, 
                 split: Split, 
                 sim: int, 
                 freq: int, 
                 field_str: str):
        """
        Generate and retrieve the seed of the
        specified field.

        Args:
            split (Split): The specified split.
            sim (int): The specified simulation.
            freq (int): The specified frequency.
            field_str (str): The specified field string.

        Returns:
            int: The generated seed.
        """

        split_str = split.name
        sim_str = self.sim_num_str(sim)
        freq_str = str(freq)
        return self._get_seed(split_str, sim_str, freq_str, field_str, self.component)

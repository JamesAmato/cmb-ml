from typing import Any, Dict, List, Union
from pathlib import Path
import yaml
import logging

import numpy as np
import healpy as hp

from .experiment import ExperimentParameters
from .asset_handler_registration import register_handler

logger = logging.getLogger(__name__)


class GenericHandler:
    def __init__(self, experiment: ExperimentParameters) -> None:
        self.experiment = experiment

    def read(self, path: Path):
        raise NotImplementedError("This read() should be implemented by children classes.")

    def write(self, path: Path, data: Any):
        raise NotImplementedError("This write() should be implemented by children classes.")

class NoHandler(GenericHandler):
    def read(self, path: Path):
        raise NotImplementedError("This is a no-operation placeholder and has no read() function.")

    def write(self, path: Path, data: Any):
        raise NotImplementedError("This is a no-operation placeholder and has no write() function.")


class HealpyMap(GenericHandler):
    def read(self, path: Union[Path, str]):
        path = Path(path)
        map_fields = self.experiment.map_fields_tuple
        try:
            this_map: np.ndarray = hp.read_map(path, field=map_fields)
        except IndexError as e:
            if len(map_fields) > 1:
                # logger.warning("Defaulting to reading a single field from the file. The 857 and 545 maps have no polarization information. Consider suppressing this warning if running a large run.")
                map_fields = tuple([0])
                this_map = hp.read_map(path, field=map_fields)
            else:
                raise e
        except FileNotFoundError as e:
            raise FileNotFoundError(f"This map file cannot be found: {path}")
        # When healpy reads a single map that I've generated with simulations,
        #    the bite order is Big-Endian instead of native ('>' instead of '=')
        if this_map.dtype.byteorder == '>':
            # The byteswap() method swaps the byte order of the array elements
            # The newbyteorder() method changes the dtype to native byte order without changing the actual data
            this_map = this_map.byteswap().newbyteorder()
        if len(map_fields) == 1:
            this_map = this_map.reshape(1, -1)
        if self.experiment.precision == "float":
            this_map = this_map.astype(np.float32)
        return this_map

    def write(self, path: Union[Path, str], data: List[np.ndarray]):
        path = Path(path)
        _make_directories(path)
        hp.write_map(path, data, dtype=data[0].dtype, overwrite=True)

class HealpyMapTemp(HealpyMap):
    def write(self, path: Union[Path, str], cmb_map):
        # Note the difference is the addition of map_unit
        map_unit = str(cmb_map.unit)
        path = Path(path)
        _make_directories(path)
        hp.write_map(path, m=cmb_map, column_units=map_unit, dtype=cmb_map.dtype, overwrite=True)

class ManyHealpyMaps(GenericHandler):
    def __init__(self, experiment: ExperimentParameters) -> None:
        super().__init__(experiment)
        self.handler: GenericHandler = HealpyMap(experiment)

    def read(self, path: Union[Path, str]) -> Dict[str, np.ndarray]:
        path = Path(path)
        maps = {}
        for det in self.experiment.detector_freqs:
            fn_template = path.name
            fn = fn_template.format(det=det)
            this_path = path.parent / fn
            maps[det] = self.handler.read(this_path)
        return maps

    def write(self, path: Union[Path, str], data: Dict[str, np.ndarray]) -> None:
        path = Path(path)
        for det, map_to_write in data.items():
            fn_template = path.name
            fn = fn_template.format(det=det)
            this_path = path.parent / fn
            self.handler.write(this_path, map_to_write)

class ManyHealpyMapsTemp(ManyHealpyMaps):
    def __init__(self, experiment: ExperimentParameters) -> None:
        super().__init__(experiment)
        self.handler: GenericHandler = HealpyMapTemp(experiment)

    def write(self, path: Union[Path, str], data: Dict[str, np.ndarray]) -> None:
        path = Path(path)
        for det, map_to_write in data.items():
            # Note the difference is the addition of... the list check.
            if isinstance(map_to_write, list):
                map_to_write = np.stack(map_to_write, axis=0)
            fn_template = path.name
            fn = fn_template.format(det=det)
            this_path = path.parent / fn
            self.handler.write(this_path, map_to_write)

class Config(GenericHandler):
    def read(self, path: Path) -> Dict:
        logger.debug(f"Reading config from '{path}'")
        with open(path, 'r') as infile:
            data = yaml.safe_load(infile)
        return data

    def write(self, path, data) -> None:
        logger.debug(f"Writing config to '{path}'")
        _make_directories(path)
        unnumpy_data = _convert_numpy(data)
        with open(path, 'w') as outfile:
            yaml.dump(unnumpy_data, outfile, default_flow_style=False)

def _convert_numpy(obj: Union[Dict[str, Any], List[Any], np.generic]) -> Any:
    # Recursive function
    # The `Any`s in the above signature should be the same as the signature itself
    # GPT4, minimal modification
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, dict):
        return {key: _convert_numpy(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy(item) for item in obj]
    else:
        return obj


def _make_directories(path: Union[Path, str]) -> None:
    path = Path(path)
    folders = path.parent
    folders.mkdir(exist_ok=True, parents=True)


register_handler("NoHandler", NoHandler)
register_handler("HealpyMap", HealpyMap)
register_handler("ManyHealpyMaps", ManyHealpyMaps)
register_handler("Config", Config)

# TODO: Clarify about these
register_handler("HealpyMapTemp", HealpyMapTemp)
register_handler("ManyHealpyMapsTemp", ManyHealpyMapsTemp)
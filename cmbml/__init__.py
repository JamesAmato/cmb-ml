__version__ = "0.1.0"

from cmbml.core import PipelineContext

try:
    from ._build_info import BUILD_INFO
except ImportError:
    BUILD_INFO = None
    
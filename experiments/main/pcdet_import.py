import sys
import types
import importlib.util
from pathlib import Path


def install_pcdet_version_shim():
    if "pcdet.version" not in sys.modules:
        module = types.ModuleType("pcdet.version")
        module.__version__ = "0.6.0+233f849"
        sys.modules["pcdet.version"] = module


def _register_stub_package(name, path=None):
    module = types.ModuleType(name)
    if path is not None:
        module.__path__ = [str(path)]
    sys.modules[name] = module
    return module


def load_voxel_backbone(openpcdet_root):
    root = Path(openpcdet_root).resolve()

    for name in ("pcdet", "pcdet.models", "pcdet.models.backbones_3d", "pcdet.utils"):
        if name not in sys.modules:
            _register_stub_package(name, root / Path(*name.split(".")))

    spconv_utils_path = root / "pcdet/utils/spconv_utils.py"
    spconv_utils_spec = importlib.util.spec_from_file_location(
        "pcdet.utils.spconv_utils", spconv_utils_path
    )
    spconv_utils = importlib.util.module_from_spec(spconv_utils_spec)
    sys.modules["pcdet.utils.spconv_utils"] = spconv_utils
    spconv_utils_spec.loader.exec_module(spconv_utils)

    backbone_path = root / "pcdet/models/backbones_3d/spconv_backbone.py"
    backbone_spec = importlib.util.spec_from_file_location(
        "pcdet.models.backbones_3d.spconv_backbone", backbone_path
    )
    backbone = importlib.util.module_from_spec(backbone_spec)
    sys.modules["pcdet.models.backbones_3d.spconv_backbone"] = backbone
    backbone_spec.loader.exec_module(backbone)
    return backbone

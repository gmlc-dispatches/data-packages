from dataclasses import dataclass
from functools import singledispatch
from importlib import import_module
from importlib import metadata
from importlib import resources
import logging
from pathlib import Path
from types import ModuleType
from typing import Dict
from typing import Iterable
from typing import Optional


_logger = logging.getLogger(__name__)


@dataclass
class PackageInfo:
    key: str
    package_name: str
    distribution_name: str
    version: Optional[str] = None

    @classmethod
    def from_entry_points(cls, group: str) -> Iterable["PackageInfo"]:
        for distr in metadata.distributions():
            for ep in distr.entry_points:
                if ep.group == group:
                    yield cls(
                        key=ep.name,
                        package_name=ep.value,
                        distribution_name=distr.metadata["Name"],
                        version=distr.version,
                    )


def available(group="data_packages") -> Dict[str, PackageInfo]:
    discovered = list(PackageInfo.from_entry_points(group))
    if not discovered:
        _logger.warning("No package discovered from {group!r}")
    return {
        info.key: info
        for info in discovered
    }


PackageResource = Optional[str]


@singledispatch
def path(package: ModuleType, resource: PackageResource = None) -> Path:
    if resource is not None:
        with resources.path(package, resource) as p:
            return Path(p)

    locs = package.__spec__.submodule_search_locations
    assert locs is not None, package
    return Path(list(locs)[0])


@path.register
def _from_package_info(info: PackageInfo, resource: PackageResource = None) -> Path:
    imported = import_module(info.package_name)
    return path(imported, resource)


@path.register
def _from_string(key: str, resource: PackageResource = None) -> Path:
    by_key = dict(available())
    try:
        info = by_key[key]
    except KeyError:
        raise LookupError(f"{key!r} not found among registered packages: {package_name_by_key}")

    return path(info, resource)

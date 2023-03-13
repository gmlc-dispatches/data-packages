from dataclasses import dataclass
from functools import singledispatch
from importlib import import_module
import importlib_metadata as metadata  # packages_distribution() only on 3.10+
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

    @classmethod
    def from_parent_package(cls, root_package_name: str, subpackage_containing_data: str = "packages") -> Iterable["PackageInfo"]:
        for distr_name in metadata.packages_distributions()[root_package_name]:
            distr = metadata.distribution(distr_name)
            for pkg_file_path in distr.files:
                try:
                    top_level, parent, key, fname = pkg_file_path.parts
                except ValueError:
                    # wrong number of items to unpack
                    continue
                if (
                    top_level != root_package_name or
                    parent != subpackage_containing_data or
                    fname not in {"__init__.py"}
                ):
                    continue

                yield cls(
                    key=key,
                    package_name=".".join([top_level, parent, key]),
                    distribution_name=distr_name,
                    version=distr.version,
                )


def discovered(parent_name: str = "dispatches_data") -> Dict[str, PackageInfo]:
    discovered = [
        info for info in PackageInfo.from_parent_package(parent_name)
        if not info.package_name == __spec__.name
    ]

    if not discovered:
        _logger.warning(f"No package discovered from parent package {parent_name!r}")

    return {
        info.key: info
        for info in discovered
    }


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
    by_key = dict(discovered())
    try:
        info = by_key[key]
    except KeyError:
        raise LookupError(f"{key!r} not found among discovered packages: {package_name_by_key}")

    return path(info, resource)

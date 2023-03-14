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
from typing import List
from typing import Optional
from typing import Union


__all__ = [
    "path",
    "files",
    "discovered",
]


_logger = logging.getLogger(__name__)


_MODNAME_SEPARATOR = "."


def _modname_to_parts(name: str) -> List[str]:
    return name.split(_MODNAME_SEPARATOR)


def _parts_to_modname(parts: Iterable[str]) -> str:
    return _MODNAME_SEPARATOR.join(parts)


@dataclass
class PackageInfo:
    """
    Utility class representing information associated with each data package.
    """

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
    def from_parent_package(cls, dotted_name: str) -> Iterable["PackageInfo"]:
        """
        Get information for data packages discovered under the common parent package specified by ``dotted_name``.

        Returns:
            An iterable of :class:`PackageInfo` objects (one for each discovered data package)
        """

        parent_package_parts = list(_modname_to_parts(dotted_name))
        top_level = parent_package_parts[0]

        for distr_name in metadata.packages_distributions()[top_level]:
            distr = metadata.distribution(distr_name)
            for pkg_file_path in distr.files:
                *parent_parts, key, fname = pkg_file_path.parts
                if (
                    fname not in {"__init__.py"} or
                    list(parent_parts) != parent_package_parts
                ):
                    continue

                yield cls(
                    key=key,
                    package_name=_parts_to_modname([*parent_parts, key]),
                    distribution_name=distr_name,
                    version=distr.version,
                )


def discovered(parent: str = "dispatches_data.packages") -> Dict[str, PackageInfo]:
    """
    Get information about data packages that have been discovered in the current environment.

    Returns:
        A dict whose keys are the discovered data package directory's name,
        and the values are :class:`PackageInfo` instances for that data package.
    """

    discovered_infos = [
        info for info in PackageInfo.from_parent_package(parent)
        if not info.package_name == __spec__.name
    ]

    if not discovered:
        _logger.warning("No package discovered from parent package %r", parent)

    return {
        info.key: info
        for info in discovered_infos
    }


PackageResource = Optional[str]


@singledispatch
def path(package: ModuleType, resource: PackageResource = None) -> Path:
    """
    Get the absolute path to a data package as a :py:class:`pathlib.Path` object.

    The data package can be specified as any of the supported types (via :func:`functools.singledispatch`).

    Args:
        package: The data package, as one of the supported types

        resource: If given, it must refer to a file (not a directory) located inside the data package directory
            (not in a subdirectory). If the file specified by ``resource`` is found, its path (rather than the package directory's path)
            will be returned

    Returns:
        Absolute path to the data package or to the file specified by ``resource`` contained inside it.
    """
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
    except KeyError as exc:
        raise LookupError(f"{key!r} not found among discovered packages: {by_key}") from exc

    return path(info, resource)


AnyPackageSpecifier = Union[str, PackageInfo, ModuleType]
GlobPattern = str


def files(spec: AnyPackageSpecifier, pattern: GlobPattern = "**/*", relative: bool = False) -> List[Path]:
    """
    Get absolute paths to files inside a data package.

    Only files (as opposed to directories) are returned.

    By default, all files from all subdirectories are returned. The ``pattern`` argument can be specified to only return
    files matching the pattern.

    .. important:: Note that certain patterns (most importantly the recursive directory pattern ``**``) only match
       *directories*, rather than *files*, and therefore (somewhat counter-intuitively) might cause
       an empty list to be returned (since this function filters out directory paths from the result).
       In general, to match files, the ``**`` pattern must be used in combination with at least 
       a path separator and ``*``.
       See e.g. the pattern matching all files recursively (which is the default): ``**/*``.

    Arguments:
        spec: The data package specified in any of the supported ways (see :func:`path`)
        pattern: A glob pattern (as supported by :mod:`glob` or :meth:`pathlib.Path.glob`)
        relative: If given, the returned paths will be relative to the data package directory

    Returns:
        Absolute paths of files found within the data package as a :class:`list` of :class:`pathlib.Path` objects.
    """

    pkg_dir = path(spec)
    file_paths = (
        p
        for p in pkg_dir.glob(pattern)
        if p.is_file()
    )
    if relative:
        file_paths = (p.relative_to(pkg_dir) for p in file_paths)

    return sorted(file_paths)

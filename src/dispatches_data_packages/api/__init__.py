from functools import singledispatch
import logging
from pathlib import Path
from types import ModuleType


_logger = logging.getLogger(__name__)


def _get_entry_points_by_name(group: str) -> dict:
    eps = entry_points()[group]
    return {ep.name: ep for ep in eps}


def available(group="data-packages") -> dict:
    d = {}
    eps = entry_points()[group]
    for ep in eps:
        d[ep.name] = ep.module
    return d


@singledispatch
def path(package: ModuleType, name: str = None):
    if name is not None:
        with resources.path(package, name) as p:
            return Path(p)

    locs = package.__spec__.submodule_search_locations
    assert locs is not None, package
    return Path(list(locs)[0])


@path.register
def _from_string(key: str, name: str = None):
    package_name_by_key = dict(available())
    try:
        package_name = package_name_by_key[key]
        package = import_module(package_name)
    except KeyError:
        raise LookupError(f"{key!r} not found among registered packages: {package_name_by_key}")

    return path(package, name)

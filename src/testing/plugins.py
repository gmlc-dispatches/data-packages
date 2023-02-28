from pathlib import Path
from typing import List

import pytest

from dispatches_data_packages import api


def _is_nonempty(p: Path, min_size_bytes: int = 1) -> bool:
    if p.exists() and p.is_file():
        return p.stat().st_size >= min_size_bytes
    return False


class DataPackage(pytest.Item):
    def __init__(self, *, required: List[Path], **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.required = list(required)

    def runtest(self):
        if self.key not in api.available():
            raise LookupError(f"Data package {key} not found")
        path = api.path(self.key)
        if not path:
            raise LookupError("Could not find path")
        missing = []
        for fname in required:
            fpath = path / fname
            if not _is_nonempty_file(fpath):
                missing.append(fpath)
        if missing:
            raise ValueError(f"The following files are required but are missing: {missing}")

    def reportinfo(self):
        return self.name, 0, self.key


class DataPackagePlugin:
    def __init__(self, required_files):
        self.required_files = list(required_files)
        self._to_check = []

    def pytest_addoption(self, parser):
        parser.addoption("--data-package", dest="data_packages", action="append")

    def pytest_configure(self, config):
        self._to_check = list(config.option.data_packages)

    def pytest_collection_modifyitems(self, session, items):
        for key in self._to_check:
            item = DataPackage.from_parent(
                session,
                name="data_packages::{key}",
                key=key,
                required=list(self.required_files),
            )
            items.append(item)


plugin = DataPackagePlugin(
    required_files=[
        "LICENSE.md",
        "__init__.py",
        "README.md",
    ],
)

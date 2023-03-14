from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List

import pytest

from dispatches_data import api


def _is_nonempty_file(p: Path, min_size_bytes: int = 1) -> bool:
    if p.exists() and p.is_file():
        return p.stat().st_size >= min_size_bytes
    return False


class DataPackage(pytest.Item):
    def __init__(self, *, key: str, **kwargs):
        super().__init__(**kwargs)
        self.key = key

    def runtest(self):
        discovered = api.discovered()
        if self.key not in discovered:
            raise LookupError(f"Data package {self.key} not found in {list(discovered)}")
        path = api.path(self.key)
        if not path:
            raise LookupError("Could not find path")

    def reportinfo(self):
        return self.name, 0, self.key


class RequiredContent(pytest.Item):
    def __init__(self, *, key: str, file_name: str, text: str, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.file_name = file_name
        self.text = text

    def runtest(self):
        fpath = api.path(self.key, resource=self.file_name)
        
        if not fpath.is_file():
            raise FileNotFoundError(f"No file named {self.file_name!r} found for {self.key}")
        file_text = fpath.read_text()
        if not file_text:
            raise ValueError(f"No text found in {fpath}")
        if not self.text.lower() in file_text.lower():
            raise ValueError(f"Required text {self.text!r} not found in {self.file_name}")

    def reportinfo(self):
        return self.name, 0, self.text


class DataPackagePlugin:
    def __init__(self, required: Dict[str, str]):
        self.required = required
        self._to_check = []

    def pytest_addoption(self, parser):
        parser.addoption("--data-package", dest="data_packages", action="append")

    def pytest_configure(self, config):
        self._to_check = list(config.option.data_packages)

    def _create_test_items(self, key: str, parent) -> Iterable[pytest.Item]:
        for_package = DataPackage.from_parent(
            parent,
            name=key,
            key=key,
        )
        yield for_package
        for text, fname in self.required.items():
            yield RequiredContent.from_parent(
                for_package,
                name=f"{fname}:{text}",
                key=key,
                file_name=fname,
                text=text,
            )

    def pytest_collection_modifyitems(self, session, items):
        for key in self._to_check:
            for item in self._create_test_items(key, session):
                items.append(item)


plugin = DataPackagePlugin(required={"copyright": "README.md", "license": "README.md"})

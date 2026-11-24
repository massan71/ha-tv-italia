"""Carica epg.py e const.py senza Home Assistant (sono moduli puri)."""
import importlib.util
import sys
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "tv_italia"
FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"tv_italia_{name}", COMPONENT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def epg():
    return _load("epg")


@pytest.fixture(scope="session")
def const():
    return _load("const")


@pytest.fixture(scope="session")
def mini_xml() -> bytes:
    return (FIXTURES / "mini.xml").read_bytes()

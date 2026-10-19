"""Smoke test: environment imports work and SIM_VERSION is readable."""
import importlib


def test_imports():
    for mod in ("torch", "numpy", "pandas", "pyarrow", "brian2"):
        importlib.import_module(mod)


def test_sim_version():
    from borer_sim import SIM_VERSION
    assert isinstance(SIM_VERSION, str) and SIM_VERSION

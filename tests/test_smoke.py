"""Smoke test: the skeleton imports and unsafe operations default to off."""
from intent_pipeline.config import settings


def test_package_imports():
    assert settings is not None


def test_dry_run_defaults_on():
    # Cost-control invariant: nothing hits a paid API until DRY_RUN is set False.
    assert settings.dry_run is True

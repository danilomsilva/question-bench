"""Smoke test: the package imports and the toolchain runs."""

import item_bench


def test_package_imports() -> None:
    assert hasattr(item_bench, "hello")

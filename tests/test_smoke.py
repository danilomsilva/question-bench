"""Smoke test: the package imports and the toolchain runs."""

import question_bench


def test_package_imports() -> None:
    assert hasattr(question_bench, "hello")

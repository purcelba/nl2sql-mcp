"""Pytest configuration: register the `db` marker and skip it by default."""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-db",
        action="store_true",
        default=False,
        help="Run tests that require a live Postgres (marker: db)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "db: test requires a live Postgres (skip unless --run-db)"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-db"):
        return
    skip_db = pytest.mark.skip(reason="needs --run-db")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip_db)

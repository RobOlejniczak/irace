"""Package level tests."""


import pytest

import irace


def test_package():
    """Assert that the irace package imports successfully."""

    assert irace

    from irace.stats import Client
    assert Client

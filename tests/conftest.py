import os
import sys

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC)


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_bridge_reader():
    # the bridge keeps one reader per process; every test starts without one
    from nbe_blackstar import bridge

    bridge._reader = None
    yield
    bridge._reader = None

import os

import pytest

from nbe_blackstar.protocol import Proxy


def _proxy_without_network():
    # set() must refuse before touching the socket, so no connection is needed
    return Proxy.__new__(Proxy)


def test_set_refused_without_env(monkeypatch):
    monkeypatch.delenv("NBE_ALLOW_WRITE", raising=False)
    with pytest.raises(PermissionError):
        _proxy_without_network().set("settings/boiler/temp", "70")


def test_set_refused_when_env_is_not_true(monkeypatch):
    monkeypatch.setenv("NBE_ALLOW_WRITE", "yes")
    with pytest.raises(PermissionError):
        _proxy_without_network().set("settings/boiler/temp", "70")

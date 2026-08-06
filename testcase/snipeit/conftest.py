import pytest

from base.snipeit_client import SnipeItClient
from conf.snipeit_settings import SnipeItSettings


@pytest.fixture(scope='session')
def system_login():
    """Override the legacy mock-server login for Snipe-IT tests."""
    yield


@pytest.fixture(scope='session')
def snipeit_settings():
    return SnipeItSettings.load()


@pytest.fixture
def snipeit_client(snipeit_settings):
    client = SnipeItClient(snipeit_settings)
    yield client
    client.close()


@pytest.fixture
def anonymous_snipeit_client(snipeit_settings):
    client = SnipeItClient(snipeit_settings, token=None)
    yield client
    client.close()

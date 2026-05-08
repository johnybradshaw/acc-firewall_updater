import pytest

from acc_fwu.firewall import get_public_ip


@pytest.fixture(autouse=True)
def _clear_public_ip_cache():
    """Clear the process-wide public-IP cache between tests so each test sees
    its own mock for ``requests.get`` / ``get_public_ip``."""
    get_public_ip.cache_clear()
    yield
    get_public_ip.cache_clear()

"""Stellar client: mock mode returns synthetic tx_hash; circuit breaker exists."""

import pytest

from damay_api.clients.stellar import StellarClient
from damay_api.config import get_settings


@pytest.mark.asyncio
async def test_mock_mode_returns_synthetic_tx_hash():
    settings = get_settings()
    assert settings.stellar_mock_mode is True
    client = StellarClient(settings)
    try:
        res = await client.invoke_reputation_record_contribution(
            "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", weight=1
        )
        assert res.mock is True
        assert len(res.tx_hash) == 64
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_stellar_client_has_circuit_breaker():
    settings = get_settings()
    client = StellarClient(settings)
    try:
        assert client._breaker.fail_max == 5
        assert client._breaker.reset_timeout == 30
    finally:
        await client.aclose()

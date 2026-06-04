"""Shared pytest helpers for live codenames.game tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from cno_sdk.client import CNOClient
from cno_sdk.room import CreatedRoom, create_room


@pytest.fixture
async def live_client() -> AsyncIterator[CNOClient]:
    client = await CNOClient.create_room(nickname="SDK-Test-Bot")
    client._log_session = False
    try:
        yield client
    finally:
        await client.leave()


@pytest.fixture
async def live_room() -> AsyncIterator[CreatedRoom]:
    created = await create_room(nickname="SDK-Test-Bot")
    created.client._log_session = False
    try:
        yield created
    finally:
        await created.client.leave()

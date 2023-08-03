from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from app.common.process_status import ProcessStatus, ProcessStatusManager, process_status_handler


@pytest.mark.asyncio
async def test_process_status_start():
    manager = ProcessStatusManager()
    manager.start()
    assert manager.get_current() == ProcessStatus.RUNNING


@pytest.mark.asyncio
async def test_process_status_complete():
    manager = ProcessStatusManager()
    manager.complete()
    assert manager.get_current() == ProcessStatus.WAITING


@pytest.mark.asyncio
async def test_process_status_handler(mocker: MockerFixture):
    # given
    start_pather = mocker.patch("app.common.process_status.manager.start")
    stop_pather = mocker.patch("app.common.process_status.manager.complete")

    # when
    await process_status_handler(AsyncMock())()

    # then
    start_pather.assert_called_once()
    stop_pather.assert_called_once()

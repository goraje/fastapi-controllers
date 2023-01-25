import asyncio
import time

import pytest
from fastapi import Depends, FastAPI, Response, status
from fastapi.testclient import TestClient

from fastapi_controllers import Controller, delete, get, head, options, patch, post, put, trace


def sync_dependency() -> str:
    # DO SOME FAKE SYNC STUFF
    time.sleep(0.01)
    return "SYNC TEST"


class SyncTestController(Controller):
    prefix = "/test-sync"

    def __init__(self, message: str = Depends(sync_dependency)) -> None:  # noqa: B008
        self.message = message

    @delete("", response_class=Response)
    def test_delete(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @get("", response_class=Response)
    def test_get(self) -> Response:
        return Response(content=self.message, status_code=status.HTTP_200_OK)

    @head("", response_class=Response)
    def test_head(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @options("", response_class=Response)
    def test_options(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @patch("", response_class=Response)
    def test_patch(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @post("", response_class=Response)
    def test_post(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @put("", response_class=Response)
    def test_put(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @trace("", response_class=Response)
    def test_trace(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)


async def async_dependency() -> str:
    # DO SOME FAKE ASYNC STUFF
    await asyncio.sleep(0.01)
    return "ASYNC TEST"


class AsyncTestController(Controller):
    prefix = "/test-async"

    def __init__(self, message: str = Depends(async_dependency)) -> None:  # noqa: B008
        self.message = message

    @delete("", response_class=Response)
    async def test_delete(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @get("", response_class=Response)
    async def test_get(self) -> Response:
        return Response(content=self.message, status_code=status.HTTP_200_OK)

    @head("", response_class=Response)
    async def test_head(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @options("", response_class=Response)
    async def test_options(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @patch("", response_class=Response)
    async def test_patch(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @post("", response_class=Response)
    async def test_post(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @put("", response_class=Response)
    async def test_put(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @trace("", response_class=Response)
    async def test_trace(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)


@pytest.fixture
def sync_test_client() -> TestClient:
    app = FastAPI()
    app.include_router(SyncTestController.create_router())
    return TestClient(app)


@pytest.fixture
def async_test_client() -> TestClient:
    app = FastAPI()
    app.include_router(AsyncTestController.create_router())
    return TestClient(app)

"""Public behavior exercised without pytest or an editable source installation."""

# The wheel check intentionally has no test-framework dependencies.
# ruff: noqa: PT009, PT027

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from typing import Annotated, final

from fastapi import Depends, FastAPI
from starlette.types import Message, Scope

import fastapi_controllers
from fastapi_controllers import create_router, get, router


def greeting() -> str:
    return "hello"


@final
@router(prefix="/greet")
class Greeter:
    def __init__(self, word: Annotated[str, Depends(greeting)]) -> None:
        self.word: str = word

    @get("")
    async def greet(self, name: str) -> str:
        return f"{self.word}:{name}"


def call(app: FastAPI, path: str, query: bytes) -> tuple[int, bytes]:
    """Serve one GET request through the ASGI interface, without an HTTP client."""
    sent: list[Message] = []

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        sent.append(message)

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": query,
        "headers": [],
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
    }
    asyncio.run(app(scope, receive, send))
    start, *body = sent
    status: object = start["status"]  # pyright: ignore[reportAny]
    chunks: list[object] = [part["body"] for part in body]
    assert isinstance(status, int)
    return status, b"".join(c for c in chunks if isinstance(c, bytes))


class InstalledWheelTests(unittest.TestCase):
    def test_public_exports(self) -> None:
        for name in fastapi_controllers.__all__:
            self.assertTrue(hasattr(fastapi_controllers, name), name)
        package = Path(fastapi_controllers.__file__)
        self.assertTrue(package.with_name("py.typed").is_file())

    def test_controller_round_trip(self) -> None:
        app = FastAPI()
        app.include_router(create_router(Greeter))
        self.assertEqual(call(app, "/greet", b"name=wheel"), (200, b'"hello:wheel"'))

    def test_bad_decorator_argument_raises(self) -> None:
        with self.assertRaises(TypeError):
            get("/x", not_a_param=1)  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # ty: ignore[unknown-argument]


if __name__ == "__main__":
    if not Path(fastapi_controllers.__file__).is_relative_to(Path(sys.prefix)):
        raise SystemExit(
            "fastapi_controllers was not imported from the isolated environment"
        )
    unittest.main()

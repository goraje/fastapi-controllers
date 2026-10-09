from __future__ import annotations

from typing import Annotated, final

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, params
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing_extensions import override

from fastapi_controllers import (
    Controller,
    delete,
    get,
    head,
    options,
    patch,
    post,
    put,
    trace,
    websocket,
)

VERBS = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT", "TRACE"]


def sync_message() -> str:
    return "sync"


async def async_message() -> str:
    return "async"


def require_token(x_token: Annotated[str | None, Header()] = None) -> None:
    if x_token != "secret":
        raise HTTPException(status_code=401)


class Item(BaseModel):
    name: str


@final
class SyncController(Controller):
    prefix = "/sync"

    def __init__(self, message: Annotated[str, Depends(sync_message)]) -> None:
        self.message = message

    @delete("")
    def remove(self) -> str:
        return self.message

    @get("")
    def read(self) -> str:
        return self.message

    @head("")
    def peek(self) -> str:
        return self.message

    @options("")
    def describe(self) -> str:
        return self.message

    @patch("")
    def amend(self) -> str:
        return self.message

    @post("")
    def create(self) -> str:
        return self.message

    @put("")
    def replace(self) -> str:
        return self.message

    @trace("")
    def echo(self) -> str:
        return self.message


@final
class AsyncController(Controller):
    prefix = "/async"

    def __init__(self, message: Annotated[str, Depends(async_message)]) -> None:
        self.message = message

    @delete("")
    async def remove(self) -> str:
        return self.message

    @get("")
    async def read(self) -> str:
        return self.message

    @head("")
    async def peek(self) -> str:
        return self.message

    @options("")
    async def describe(self) -> str:
        return self.message

    @patch("")
    async def amend(self) -> str:
        return self.message

    @post("")
    async def create(self) -> str:
        return self.message

    @put("")
    async def replace(self) -> str:
        return self.message

    @trace("")
    async def echo(self) -> str:
        return self.message

    @websocket("/ws")
    async def stream(self, ws: WebSocket) -> None:
        await ws.accept()
        await ws.send_text(self.message)
        await ws.close()


def client(*controllers: type[Controller]) -> TestClient:
    app = FastAPI()
    for controller in controllers:
        app.include_router(controller.create_router())
    return TestClient(app)


@pytest.mark.parametrize("prefix", ["/sync", "/async"])
@pytest.mark.parametrize("verb", VERBS)
def test_every_http_verb_is_routed(verb: str, prefix: str) -> None:
    assert (
        client(SyncController, AsyncController).request(verb, prefix).status_code == 200
    )


@pytest.mark.parametrize(
    ("prefix", "message"), [("/sync", "sync"), ("/async", "async")]
)
def test_init_dependencies_reach_self(prefix: str, message: str) -> None:
    assert client(SyncController, AsyncController).get(prefix).text == f'"{message}"'


def test_websocket_endpoints_get_self() -> None:
    with client(AsyncController).websocket_connect("/async/ws") as ws:
        assert ws.receive_text() == "async"


def test_decorated_methods_stay_callable() -> None:
    assert SyncController("hi").read() == "hi"


def test_class_router_params_apply() -> None:
    @final
    class Guarded(Controller):
        prefix = "/guarded"
        tags = ["guarded"]
        dependencies = [params.Depends(require_token)]

        @get("")
        def read(self) -> str:
            return "ok"

    assert client(Guarded).get("/guarded").status_code == 401
    assert (
        client(Guarded).get("/guarded", headers={"x-token": "secret"}).status_code
        == 200
    )
    route = next(r for r in Guarded.create_router().routes if isinstance(r, APIRoute))
    assert route.tags == ["guarded"]


def test_routes_register_in_definition_order() -> None:
    class Items(Controller):
        @get("/me")
        def z_me(self) -> str:
            return "me"

        @get("/{item_id}")
        def a_by_id(self, item_id: str) -> str:
            return item_id

    assert client(Items).get("/me").text == '"me"'


def test_self_is_bound_per_controller_through_include_router() -> None:
    class Base(Controller):
        @get("/who")
        def who(self) -> str:
            return type(self).__name__

    class First(Base): ...

    class Second(Base): ...

    first, second = First.create_router(), Second.create_router()
    app1, app2 = FastAPI(), FastAPI()
    app1.include_router(first)
    app2.include_router(second)
    assert TestClient(app1).get("/who").text == '"First"'
    assert TestClient(app2).get("/who").text == '"Second"'


def test_overridden_route_keeps_its_original_slot() -> None:
    class Base(Controller):
        @get("/a")
        def first(self) -> str:
            return "base"

        @get("/b")
        def second(self) -> str:
            return "base"

    class Child(Base):
        @get("/a")
        @override
        def first(self) -> str:
            return "child"

    assert [
        r.path for r in Child.create_router().routes if isinstance(r, APIRoute)
    ] == ["/a", "/b"]
    assert client(Child).get("/a").text == '"child"'


def test_path_query_and_body_params_resolve() -> None:
    class Items(Controller):
        @post("/items/{item_id}")
        def update(self, item_id: int, item: Item, q: str | None = None) -> str:
            return f"{item_id}:{item.name}:{q}"

    response = client(Items).post("/items/7", params={"q": "x"}, json={"name": "pen"})
    assert response.text == '"7:pen:x"'


def test_stacked_decorators_register_both_routes() -> None:
    class Multi(Controller):
        @get("/one")
        @get("/two")
        def both(self) -> str:
            return "ok"

    assert client(Multi).get("/one").status_code == 200
    assert client(Multi).get("/two").status_code == 200

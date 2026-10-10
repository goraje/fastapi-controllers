from __future__ import annotations

import inspect
from collections.abc import Callable, Coroutine
from typing import Annotated, ClassVar, final

import pytest
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    Response,
    WebSocket,
    params,
)
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing_extensions import override

from fastapi_controllers import (
    create_router,
    delete,
    get,
    head,
    options,
    patch,
    post,
    put,
    router,
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
@router(prefix="/sync")
class SyncController:
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
@router(prefix="/async")
class AsyncController:
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


def paths(controller: type) -> list[str]:
    return [r.path for r in create_router(controller).routes if isinstance(r, APIRoute)]


def client(*controllers: type) -> TestClient:
    app = FastAPI()
    for controller in controllers:
        app.include_router(create_router(controller))
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
    @router(
        prefix="/guarded",
        tags=["guarded"],
        dependencies=[params.Depends(require_token)],
    )
    class Guarded:
        @get("")
        def read(self) -> str:
            return "ok"

    assert client(Guarded).get("/guarded").status_code == 401
    assert (
        client(Guarded).get("/guarded", headers={"x-token": "secret"}).status_code
        == 200
    )
    route = next(r for r in create_router(Guarded).routes if isinstance(r, APIRoute))
    assert route.tags == ["guarded"]


def test_routes_register_in_definition_order() -> None:
    class Items:
        @get("/me")
        def z_me(self) -> str:
            return "me"

        @get("/{item_id}")
        def a_by_id(self, item_id: str) -> str:
            return item_id

    assert client(Items).get("/me").text == '"me"'


def test_self_is_bound_per_controller_through_include_router() -> None:
    class Base:
        @get("/who")
        def who(self) -> str:
            return type(self).__name__

    class First(Base): ...

    class Second(Base): ...

    first, second = create_router(First), create_router(Second)
    app1, app2 = FastAPI(), FastAPI()
    app1.include_router(first)
    app2.include_router(second)
    assert TestClient(app1).get("/who").text == '"First"'
    assert TestClient(app2).get("/who").text == '"Second"'


def test_overridden_route_keeps_its_original_slot() -> None:
    class Base:
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

    assert [r.path for r in create_router(Child).routes if isinstance(r, APIRoute)] == [
        "/a",
        "/b",
    ]
    assert client(Child).get("/a").text == '"child"'


def test_path_query_and_body_params_resolve() -> None:
    class Items:
        @post("/items/{item_id}")
        def update(self, item_id: int, item: Item, q: str | None = None) -> str:
            return f"{item_id}:{item.name}:{q}"

    response = client(Items).post("/items/7", params={"q": "x"}, json={"name": "pen"})
    assert response.text == '"7:pen:x"'


def test_stacked_decorators_register_both_routes() -> None:
    class Multi:
        @get("/one")
        @get("/two")
        def both(self) -> str:
            return "ok"

    assert client(Multi).get("/one").status_code == 200
    assert client(Multi).get("/two").status_code == 200
    # Decorators apply bottom-up, so the one nearest to def registers first.
    assert paths(Multi) == ["/two", "/one"]


def test_multiple_inheritance_registers_rightmost_base_first() -> None:
    class Left:
        @get("/left")
        def left(self) -> str:
            return "left"

    class Right:
        @get("/right")
        def right(self) -> str:
            return "right"

    class Both(Left, Right): ...

    assert paths(Both) == ["/right", "/left"]


@router(prefix="/base", dependencies=[params.Depends(require_token)])
class Base:
    @get("")
    def read(self) -> str:
        return "ok"


@router(prefix="/sub")
class Sub(Base): ...


@router(dependencies=[])
class Public(Base): ...


class Plain(Base): ...


def test_router_settings_are_inherited_and_overridden() -> None:
    assert create_router(Base).prefix == "/base"
    assert create_router(Sub).prefix == "/sub"
    assert create_router(Plain).prefix == "/base"
    assert create_router(Sub, prefix="/call").prefix == "/call"
    assert client(Sub).get("/sub").status_code == 401


def test_subclass_settings_replace_base_settings() -> None:
    assert client(Public).get("/base").status_code == 200
    assert client(Base).get("/base").status_code == 401


def test_stacked_router_decorators_merge() -> None:
    @router(prefix="/stacked")
    @router(tags=["stacked"])
    class Stacked:
        @get("")
        def read(self) -> str:
            return "ok"

    built = create_router(Stacked)
    assert (built.prefix, built.tags) == ("/stacked", ["stacked"])


def test_router_lists_are_copied_per_router() -> None:
    @router(tags=["once"])
    class Tagged:
        @get("")
        def read(self) -> str:
            return "ok"

    create_router(Tagged).tags.append("leaked")
    assert create_router(Tagged).tags == ["once"]


def test_class_without_routes_is_rejected() -> None:
    class Empty: ...

    with pytest.raises(TypeError, match="has no routes"):
        create_router(Empty)


def test_override_without_route_decorator_is_rejected() -> None:
    class Child(Base):
        @override
        def read(self) -> str:
            return "child"

    with pytest.raises(TypeError, match=r"Child\.read overrides a route"):
        create_router(Child)

    class Grandchild(Child):
        @get("/again")
        @override
        def read(self) -> str:
            return "grandchild"

    assert paths(Grandchild) == ["/base/again"]


def test_route_decorators_reject_wrapped_functions() -> None:
    def plain() -> str:
        return "plain"

    with pytest.raises(TypeError, match="plain method, not staticmethod"):
        _ = get("/s")(staticmethod(plain))


def test_wrapped_route_methods_are_rejected() -> None:
    class Static:
        @staticmethod
        @get("/s")
        def s() -> str:
            return "s"

    class Class:
        @classmethod
        @get("/c")
        def c(cls) -> str:
            return "c"

    for controller in (Static, Class):
        with pytest.raises(TypeError, match="route decorators need a plain method"):
            create_router(controller)


def test_router_params_are_rejected() -> None:
    class Legacy(Base):
        __router_params__: ClassVar[dict[str, object]] = {"prefix": "/legacy"}

    class LegacyChild(Legacy): ...

    for controller in (Legacy, LegacyChild):
        with pytest.raises(TypeError, match="__router_params__ is no longer supported"):
            create_router(controller)


def test_runtime_signatures_mirror_fastapi() -> None:
    assert list(inspect.signature(get).parameters)[0] == "path"
    assert list(inspect.signature(router).parameters)[0] == "prefix"
    assert list(inspect.signature(create_router).parameters)[:2] == ["cls", "prefix"]
    assert repr(get).startswith("<function get ")
    assert repr(router).startswith("<function router ")


@pytest.mark.parametrize("func", [get, router, create_router])
def test_help_is_readable(func: Callable[..., object]) -> None:
    # help() renders exactly these two.
    signature = str(inspect.signature(func))
    assert "Doc(" not in signature
    assert "DefaultPlaceholder" not in signature
    assert "\n    tags: " in (inspect.getdoc(func) or "")


class TaggedRoute(APIRoute):
    @override
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[object, object, Response]]:
        handler = super().get_route_handler()

        async def tagged(request: Request) -> Response:
            response = await handler(request)
            response.headers["x-route-class"] = "tagged"
            return response

        return tagged


def test_init_only_router_arguments_apply() -> None:
    @router(route_class=TaggedRoute)
    class Custom:
        @get("/custom")
        def read(self) -> str:
            return "ok"

    response = client(Custom).get("/custom")
    assert response.headers["x-route-class"] == "tagged"
    app = FastAPI()
    app.include_router(create_router(Custom, route_class=APIRoute))
    assert "x-route-class" not in TestClient(app).get("/custom").headers

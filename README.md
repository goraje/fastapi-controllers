<p>
    <h1 align="center">fastapi-controllers</h1>
    <p align="center">
        A simple solution for organizing your FastAPI endpoints
    </p>
    <p align="center">
    <img src="https://badgen.net/pypi/v/fastapi-controllers"/>
    <img src="https://badgen.net/pypi/license/fastapi-controllers"/>
    <img src="https://badgen.net/pypi/python/fastapi-controllers"/>
    <img src="https://github.com/goraje/fastapi-controllers/actions/workflows/test.yml/badge.svg">
    </p>
</p>

## Organize your API endpoints

`fastapi-controllers` offers a simple solution for organizing your API endpoints into controller classes, embracing the concept of class-based views.

## Features

- class-based approach to organizing FastAPI endpoints
- decorators with exactly the arguments of their FastAPI counterparts, checked by type checkers and completed by IDEs
- class-scoped APIRouter settings that subclasses inherit
- instance-scoped definition of FastAPI dependencies
- sync, async and websocket endpoints
- controller inheritance

## Installation

```sh
pip install fastapi-controllers
```

## Minimal working example

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from fastapi_controllers import create_router, get, websocket


class ExampleController:
    @get("/example")
    async def get_example(self) -> dict[str, str]:
        return {"message": "Hello"}

    @websocket("/ws")
    async def ws_example(self, ws: WebSocket) -> None:
        await ws.accept()
        try:
            while True:
                data = await ws.receive_text()
                await ws.send_text(f"Received: {data}")
        except WebSocketDisconnect:
            pass


app = FastAPI()
app.include_router(create_router(ExampleController))
```

A controller is a plain class whose endpoints are methods decorated with route decorators. `create_router` creates a FastAPI `APIRouter` and populates it with the controller's routes. Include it in the application in the usual way, with `app.include_router`. `create_router` raises `TypeError` if the class has no routes.

Save the example as `example.py` and serve it with an ASGI server, for example the FastAPI CLI:

```sh
pip install "fastapi[standard]"
fastapi dev example.py
```

## Same arguments as FastAPI

Every decorator, and `create_router`, takes exactly the arguments of its FastAPI counterpart. There is no new naming convention to learn:

- `get` has the signature of `APIRouter.get`, `websocket` has the signature of `APIRouter.websocket`, and so on for every route decorator;
- `router` and `create_router` take the arguments of `APIRouter` itself;
- mypy, pyright and ty check the arguments, and IDEs complete them;
- an unknown or missing decorator argument raises `TypeError` as soon as the class is defined;
- `help()` and other runtime tools show the FastAPI arguments too;
- a decorated method or class keeps its type, and a decorated method stays callable as an ordinary method.

Route decorators apply to plain methods only. A route decorator on a `staticmethod`, a `classmethod` or another wrapper object raises `TypeError`.

```python
from fastapi_controllers import create_router, router
from fastapi_controllers import delete, get, head, options, patch, post, put, trace, websocket
```

## Configure the APIRouter

The `router` class decorator sets the `APIRouter` arguments of a controller. `create_router` takes the same arguments; a value passed to `create_router` replaces the value set by `router`.

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from fastapi_controllers import create_router, get, post, router

security = HTTPBasic()


async def authorized_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> None: ...


class ExampleRequest(BaseModel):
    name: str


class ExampleResponse(BaseModel):
    message: str


@router(prefix="/example", tags=["example"], dependencies=[Depends(authorized_user)])
class ExampleController:
    @get("")
    async def get_example(self) -> ExampleResponse:
        return ExampleResponse(message="Hello")

    @post("")
    async def post_example(self, data: ExampleRequest) -> ExampleResponse:
        return ExampleResponse(message=f"Hello, {data.name}!")


app = FastAPI()
app.include_router(
    create_router(
        ExampleController,
        deprecated=True,
        responses={404: {"description": "Not found"}},
    )
)
```

> **Warning**: An argument replaces the earlier value as a whole. Lists are not combined. For example, `create_router(ExampleController, dependencies=[...])` removes the `authorized_user` dependency. To add a dependency, pass it to `app.include_router`, which keeps the router's own dependencies.

## Instance-scoped dependencies

Define instance-scoped attributes in the controller's `__init__`. They give every endpoint easy access to common dependencies. FastAPI resolves the `__init__` dependencies and builds a fresh controller instance for each request.

```python
from typing import Annotated

from fastapi import Depends, FastAPI

from fastapi_controllers import create_router, get, router


class DbSession:
    @property
    def status(self) -> str:
        return "CONNECTED"


async def get_db_session() -> DbSession:
    return DbSession()


@router(prefix="/example")
class ExampleController:
    def __init__(self, session: Annotated[DbSession, Depends(get_db_session)]) -> None:
        self.session = session

    @get("")
    async def get_status(self) -> dict[str, str]:
        return {"status": self.session.status}


app = FastAPI()
app.include_router(create_router(ExampleController))
```

## Route order and inheritance

FastAPI serves a request from the first registered route that matches it. `create_router` registers routes in this order:

- within a class, in the order the methods are defined, so `/me` defined before `/{item_id}` takes precedence;
- a base controller's routes before its subclass's routes;
- with multiple inheritance, in reverse method resolution order, so `class C(A, B)` registers the routes of `B` before those of `A`;
- for decorators stacked on one method, bottom-up: the decorator nearest to `def` registers first.

A subclass inherits the routes of its base controllers. To override a route, redefine the method **and decorate it again**. The override keeps the original route's position. `create_router` raises `TypeError` if a subclass redefines a route method without a route decorator.

A subclass also inherits the `router` settings of its base controllers. The settings merge argument by argument: a subclass's `router` value replaces its base's, and a `create_router` argument replaces both.

```python
from fastapi_controllers import get, router


@router(prefix="/base", tags=["items"])
class BaseController:
    @get("/me")
    async def me(self) -> str:
        return "me"

    @get("/{item_id}")
    async def item(self, item_id: int) -> int:
        return item_id


@router(prefix="/child")  # keeps tags=["items"]
class ChildController(BaseController):
    @get("/me")
    async def me(self) -> str:
        return "child"
```

## Migrating from 0.3.x

Releases before 1.0.0 may break the API. Each break comes with a migration step in this section.

> **Warning**: The `Controller` class is gone, and controllers no longer read the `prefix`, `tags` and `dependencies` class attributes. They are now ordinary class attributes, so nothing raises an error when they are set. Router dependencies defined there, such as authentication, stop running, and their routes become public. Move these attributes to `@router(...)` (step 3) before you deploy the upgrade. `create_router` raises `TypeError` only for a controller that still defines `__router_params__`.

This command finds the code that steps 2, 3 and 5 change:

```sh
grep -rnE '\bController\b|\.create_router\(|__router_params__|fastapi_controllers\.(controllers|definitions|helpers|routing)|\.route_(args|kwargs|meta)' --include='*.py' .
```

Steps 4 and 6 need a review of each controller.

### 1. Update the requirements

`fastapi-controllers` now needs Python 3.11 or later and FastAPI 0.124.0 or later. Version 0.3.x needed Python 3.8 or later and any FastAPI.

### 2. Turn controllers into plain classes

Remove the `Controller` base class from every controller. Replace every `ExampleController.create_router()` call with `create_router(ExampleController)`, and import `create_router` from `fastapi_controllers`.

### 3. Move the router settings to `@router`

Move the `prefix`, `tags` and `dependencies` class attributes, and every `__router_params__` entry, into the `router` class decorator. It takes every `APIRouter` argument. In 0.3.x, a `__router_params__` value overrode the class attribute of the same name. If a controller sets both, keep the `__router_params__` value.

In 0.3.x, subclasses shared and changed their base's `__router_params__`, so a subclass could silently use another controller's `prefix`. Check the paths of every subclass after you migrate.

Before (0.3.x):

```python
from fastapi import Depends, FastAPI

from fastapi_controllers import Controller, get


async def authorized_user() -> None: ...


class ExampleController(Controller):
    prefix = "/example"
    __router_params__ = {"dependencies": [Depends(authorized_user)], "deprecated": True}

    @get("")
    async def get_example(self) -> str:
        return "Hello"


app = FastAPI()
app.include_router(ExampleController.create_router())
```

After:

```python
from fastapi import Depends, FastAPI

from fastapi_controllers import create_router, get, router


async def authorized_user() -> None: ...


@router(prefix="/example", dependencies=[Depends(authorized_user)], deprecated=True)
class ExampleController:
    @get("")
    async def get_example(self) -> str:
        return "Hello"


app = FastAPI()
app.include_router(create_router(ExampleController))
```

### 4. Give every endpoint a `self` parameter

The first parameter of every decorated method now receives the controller instance, whatever its name. In 0.3.x, only a parameter named `self` received it, so a method without `self` got its first parameter from the request. Add `self` as the first parameter of every decorated method.

Before (0.3.x):

```python
from fastapi import WebSocket

from fastapi_controllers import Controller, websocket


class ExampleController(Controller):
    @websocket("/ws")
    async def ws_example(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.close()
```

After:

```python
from fastapi import WebSocket

from fastapi_controllers import websocket


class ExampleController:
    @websocket("/ws")
    async def ws_example(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.close()
```

### 5. Stop reading routes from the class

The decorators now return the method unchanged. `ExampleController.get_example` is a plain function, not a `Route` object, so `.endpoint`, `.route_args`, `.route_kwargs` and `.route_meta` no longer exist. To inspect the routes, read `create_router(ExampleController).routes`.

The modules `fastapi_controllers.controllers`, `fastapi_controllers.definitions`, `fastapi_controllers.helpers` and `fastapi_controllers.routing` no longer exist. Import everything from `fastapi_controllers`.

### 6. Check the route order

In 0.3.x, routes were registered in alphabetical order of their method names. They now follow the order in [Route order and inheritance](#route-order-and-inheritance). Where one path can match another, such as `/{item_id}` and `/me`, define the more specific route first.

In 0.3.x, a subclass method that overrode a route without a route decorator silently removed the route. `create_router` now raises `TypeError` for it. Decorate the override again.

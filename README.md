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

`fastapi-controllers` offers a simple solution for organizing your API endpoints by means of a `Controller` class embracing the concept of class-based views.

## Features

- class-based approach to organizing FastAPI endpoints
- route decorators with exactly the arguments of their `APIRouter` counterparts, checked by type checkers and completed by IDEs
- class-scoped definition of APIRouter parameters
- instance-scoped definition of FastAPI dependencies
- sync, async and websocket endpoints
- controller inheritance

## Installation

```sh
pip install fastapi-controllers
```

## Minimal working example

```python
from fastapi import FastAPI, WebSocket

from fastapi_controllers import Controller, get, websocket


class ExampleController(Controller):
    @get("/example")
    async def get_example(self) -> dict[str, str]:
        return {"message": "Hello"}

    @websocket("/ws")
    async def ws_example(self, ws: WebSocket) -> None:
        await ws.accept()
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"Received: {data}")


app = FastAPI()
app.include_router(ExampleController.create_router())
```

`Controller.create_router` creates a FastAPI `APIRouter` and populates it with the controller's routes. Include it in the application in the usual way, with `app.include_router`.

## Same arguments as FastAPI

Each decorator takes exactly the arguments of the matching `APIRouter` method. For example, `get` has the signature of `APIRouter.get`, and `websocket` has the signature of `APIRouter.websocket`. There is no new naming convention to learn:

- mypy, pyright and ty check the arguments, and IDEs complete them;
- an unknown or missing argument raises `TypeError` as soon as the class is defined;
- a decorated method keeps its type and stays callable as an ordinary method.

```python
from fastapi_controllers import delete, get, head, options, patch, post, put, trace, websocket
```

## Use class variables to customize your APIRouter

The class variables `prefix`, `tags` and `dependencies` set the APIRouter parameters of the same names.

```python
from typing import Annotated

from fastapi import Depends, FastAPI, params
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from fastapi_controllers import Controller, get, post

security = HTTPBasic()


async def authorized_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> None: ...


class ExampleRequest(BaseModel):
    name: str


class ExampleResponse(BaseModel):
    message: str


class ExampleController(Controller):
    prefix = "/example"
    tags = ["example"]
    dependencies = [params.Depends(authorized_user)]

    @get("")
    async def get_example(self) -> ExampleResponse:
        return ExampleResponse(message="Hello")

    @post("")
    async def post_example(self, data: ExampleRequest) -> ExampleResponse:
        return ExampleResponse(message=f"Hello, {data.name}!")


app = FastAPI()
app.include_router(ExampleController.create_router())
```

Pass any other router parameter to `app.include_router`, which accepts most of them:

```python
from fastapi import FastAPI

from fastapi_controllers import Controller


class ExampleController(Controller):
    prefix = "/example"


app = FastAPI()
app.include_router(
    ExampleController.create_router(),
    deprecated=True,
    responses={404: {"description": "Not found"}},
)
```

## Instance-scoped dependencies

Define instance-scoped attributes in the controller's `__init__`. They give every endpoint easy access to common dependencies. FastAPI resolves the `__init__` dependencies and builds a fresh controller instance for each request.

```python
from typing import Annotated

from fastapi import Depends, FastAPI

from fastapi_controllers import Controller, get


class DbSession:
    @property
    def status(self) -> str:
        return "CONNECTED"


async def get_db_session() -> DbSession:
    return DbSession()


class ExampleController(Controller):
    prefix = "/example"

    def __init__(self, session: Annotated[DbSession, Depends(get_db_session)]) -> None:
        self.session = session

    @get("")
    async def get_status(self) -> dict[str, str]:
        return {"status": self.session.status}


app = FastAPI()
app.include_router(ExampleController.create_router())
```

## Route order and inheritance

Routes are registered in the order they are defined, so `/me` defined before `/{item_id}` takes precedence. A subclass inherits the routes of its base controllers. To override a route, redefine the method **and decorate it again**. The override keeps the original route's position.

```python
from fastapi_controllers import Controller, get


class BaseController(Controller):
    @get("/me")
    async def me(self) -> str:
        return "me"

    @get("/{item_id}")
    async def item(self, item_id: int) -> int:
        return item_id


class ChildController(BaseController):
    prefix = "/child"

    @get("/me")
    async def me(self) -> str:
        return "child"
```

<p>
    <h1 align="center">fastapi-controllers</h1>
    <p align="center">
        A simple solution for organizing your FastAPI endpoints
    </p>
    <p align="center">
    <img src="https://badgen.net/badge/python/3.8|3.9|3.10|3.11/blue?icon=pypi"/>
    <img src="https://badgen.net/badge/license/MIT/blue"/>
    <img src="https://github.com/goraje/fastapi-controllers/actions/workflows/test.yml/badge.svg">
    </p>
</p>

## Organize your API endpoints

`fastapi-controllers` offers a simple solution for organizing your API endpoints by means of a `Controller` class embracing the concept of class-based views.

## Features

- class-based approach to organizing FastAPI endpoints
- class-scoped definition of APIRouter parameters
- instance-scoped definition of FastAPI dependencies
- it integrates seamlessly with the FastAPI framework
- works with both sync and async endpoints

## Installation

```sh
pip install fastapi-controllers
```

## Minimal working example

```python
import uvicorn
from fastapi import FastAPI, Response, status

from fastapi_controllers import Controller, get


class ExampleController(Controller):
    @get("/example", response_class=Response)
    async def get_example(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    app = FastAPI()
    app.include_router(ExampleController.create_router())
    uvicorn.run(app)
```

FastAPI's `APIRouter` is created and populated with API routes by the `Controller.create_router` method and can be incorporated into the application in the usual way via `app.include_router`.

## Seamless integration

The router-related parameters as well as those of HTTP request-specific decorators are expected to be the same as those used by `fastapi.APIRouter` and `fastapi.APIRouter.<request_method>`. Validation of the provided parameters is performed during initialization via the `inspect` module. This ensures compatibility with the FastAPI framework and prevents the introduction of a new, unnecessary naming convention.

### Supported HTTP request methods

```python
from fastapi_controllers import delete, get, head, options, patch, post, put, trace
```

## Use class variables to customize your APIRouter

Class variables can be used to set the commonly used APIRouter parameters: `prefix`, `dependencies` and `tags`.

```python
import uvicorn
from fastapi import Depends, FastAPI, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from fastapi_controllers import Controller, get, post

security = HTTPBasic()


async def authorized_user(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    ...


class ExampleRequest(BaseModel):
    name: str


class ExampleResponse(BaseModel):
    message: str


class ExampleController(Controller):
    prefix = "/example"
    tags = ["example"]
    dependencies = [Depends(authorized_user)]

    @get("", response_class=Response)
    async def get_example(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @post("", response_model=ExampleResponse)
    async def post_example(self, data: ExampleRequest) -> ExampleResponse:
        return ExampleResponse(message=f"Hello, {data.name}!")


if __name__ == "__main__":
    app = FastAPI()
    app.include_router(ExampleController.create_router())
    uvicorn.run(app)
```
### Additional APIRouter parameters
Additional APIRouter parameters can be provided via the `__router_params__` class variable in form of a mapping.

```python
import uvicorn
from fastapi import FastAPI, Response, status

from fastapi_controllers import Controller, get


class ExampleController(Controller):
    prefix = "/example"
    tags = ["example"]
    __router_params__ = {"deprecated": True}

    @get("", response_class=Response)
    async def get_example(self) -> Response:
        return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    app = FastAPI()
    app.include_router(ExampleController.create_router())
    uvicorn.run(app)
```
>**Important**:
>**Beware of assigning values to the same parameter twice (directly on class-level and through `__router_params__`). The values stored in `__router_params__` have precedence and will override your other settings if a name conflict arises. E.g. the following `Controller` would create an `APIRouter` with `prefix=/override`, `tags=["override"]` and `dependencies=[Depends(override)]`**

```python
from fastapi import Depends

from fastapi_controllers import Controller


class ExampleController(Controller):
    prefix = "/example"
    tags = ["example"]
    dependencies = [Depends(example)]
    __router_params__ = {
        "prefix": "/override",
        "tags": ["override"],
        "dependencies": [Depends(override)],
    }
```


## Instance-scoped dependencies

Instance-scoped attributes can be defined in the `__init__` method of the `Controller` and offer an easy way to access common dependencies for all endpoints.

```python
import json

import uvicorn
from fastapi import Depends, FastAPI, Response, status

from fastapi_controllers import Controller, get


class DbSession:
    @property
    def status(self) -> str:
        return "CONNECTED"


async def get_db_session() -> DbSession:
    return DbSession()


class ExampleController(Controller):
    prefix = "/example"

    def __init__(self, session: DbSession = Depends(get_db_session)) -> None:
        self.session = session

    @get("", response_class=Response)
    async def get_status(self) -> Response:
        return Response(
            content=json.dumps({"status": f"{self.session.status}"}),
            status_code=status.HTTP_200_OK,
            media_type="application/json",
        )


if __name__ == "__main__":
    app = FastAPI()
    app.include_router(ExampleController.create_router())
    uvicorn.run(app)
    uvicorn.run(app)
```

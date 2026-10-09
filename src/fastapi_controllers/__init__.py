"""Class-based controllers for FastAPI."""

import functools
import inspect
from collections.abc import Callable, Sequence
from enum import Enum
from types import FunctionType
from typing import ClassVar, Concatenate, ParamSpec, Protocol, TypeVar, cast

from fastapi import APIRouter, params

__all__ = [
    "Controller",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "trace",
    "websocket",
]

_P = ParamSpec("_P")
_F = TypeVar("_F", bound=Callable[..., object])
_ROUTES = "_fastapi_controllers_routes"
_Route = tuple[
    Callable[..., Callable[[FunctionType], object]],
    tuple[object, ...],
    dict[str, object],
]


class _Decorator(Protocol):
    # A generic __call__ keeps the decorated method's type in every checker;
    # ty loses the TypeVar of a plain Callable[[_F], _F] return.
    def __call__(self, func: _F, /) -> _F: ...


def _route(
    method: Callable[Concatenate[APIRouter, _P], object],
) -> Callable[_P, _Decorator]:
    """Mirror an APIRouter decorator method; record its arguments on the function."""

    def factory(*args: _P.args, **kwargs: _P.kwargs) -> _Decorator:
        inspect.signature(method).bind(None, *args, **kwargs)

        def mark(func: _F) -> _F:
            routes = vars(func).setdefault(_ROUTES, [])  # pyright: ignore[reportAny]
            routes.append((method, args, kwargs))  # pyright: ignore[reportAny]
            return func

        return mark

    return factory


delete = _route(APIRouter.delete)
get = _route(APIRouter.get)
head = _route(APIRouter.head)
options = _route(APIRouter.options)
patch = _route(APIRouter.patch)
post = _route(APIRouter.post)
put = _route(APIRouter.put)
trace = _route(APIRouter.trace)
websocket = _route(APIRouter.websocket)


class Controller:
    prefix: ClassVar[str] = ""
    tags: ClassVar[list[str | Enum] | None] = None
    dependencies: ClassVar[Sequence[params.Depends] | None] = None

    @classmethod
    def create_router(cls) -> APIRouter:
        """Build an APIRouter with this controller's routes in definition order."""
        members: dict[str, object] = {}
        for klass in reversed(cls.__mro__):
            # An overridden name keeps its first (base) slot.
            members.update(vars(klass))
        router = APIRouter(
            prefix=cls.prefix, tags=cls.tags, dependencies=cls.dependencies
        )
        for member in members.values():
            if isinstance(member, FunctionType) and (
                routes := cast("list[_Route]", vars(member).get(_ROUTES, []))
            ):
                endpoint = _bind_self(cls, member)
                for method, args, kwargs in routes:
                    method(router, *args, **kwargs)(endpoint)
        return router


def _bind_self(cls: type[Controller], func: FunctionType) -> FunctionType:
    """Copy func; FastAPI injects a fresh cls instance as its first parameter."""
    copy = FunctionType(
        func.__code__,
        func.__globals__,
        func.__name__,
        func.__defaults__,
        func.__closure__,
    )
    copy.__kwdefaults__ = func.__kwdefaults__
    functools.update_wrapper(copy, func)
    sig = inspect.signature(func)
    first, *rest = sig.parameters.values()
    vars(copy)["__signature__"] = sig.replace(
        parameters=[
            first.replace(default=params.Depends(cls)),
            *(p.replace(kind=p.KEYWORD_ONLY) for p in rest),
        ]
    )
    return copy

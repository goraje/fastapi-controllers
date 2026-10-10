"""Class-based controllers for FastAPI."""

import functools
import inspect
from collections.abc import Callable
from types import FunctionType
from typing import (
    Annotated,
    Concatenate,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    get_args,
    get_origin,
)

from fastapi import APIRouter, params
from fastapi.datastructures import DefaultPlaceholder

__all__ = [
    "create_router",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "router",
    "trace",
    "websocket",
]

_P = ParamSpec("_P")
_F = TypeVar("_F", bound=Callable[..., object])
_C = TypeVar("_C", bound=type)
_ROUTES = "_fastapi_controllers_routes"
_SETTINGS = "_fastapi_controllers_router"
_Route = tuple[
    Callable[..., Callable[[FunctionType], object]],
    tuple[object, ...],
    dict[str, object],
]


class _Decorator(Protocol):
    # A generic __call__ keeps the decorated method's type in every checker;
    # ty loses the TypeVar of a plain Callable[[_F], _F] return.
    def __call__(self, func: _F, /) -> _F: ...


class _ClassDecorator(Protocol):
    def __call__(self, cls: _C, /) -> _C: ...


def _require_function(obj: object) -> None:
    if not isinstance(obj, FunctionType):
        msg = f"route decorators need a plain method, not {type(obj).__name__}"
        raise TypeError(msg)


def _without_self(method: Callable[..., object]) -> list[inspect.Parameter]:
    _, *rest = inspect.signature(method).parameters.values()
    return rest


def _show_signature(
    func: Callable[..., object], source: str, *parameters: inspect.Parameter
) -> None:
    """Show the mirrored FastAPI arguments, readably, in help() and IDEs.

    FastAPI documents each argument as Annotated[type, Doc(...)] and wraps some
    defaults in DefaultPlaceholder; pydoc prints both raw, so unwrap them and
    move each Doc's first paragraph into the docstring.
    """
    shown: list[inspect.Parameter] = []
    docs: list[str] = []
    for param in parameters:
        annotation = cast("object", param.annotation)
        metadata: list[object] = []
        if get_origin(annotation) is Annotated:
            annotation, *metadata = cast("tuple[object, ...]", get_args(annotation))
        default = cast("object", param.default)
        if isinstance(default, DefaultPlaceholder):
            default = cast("object", default.value)
        shown.append(param.replace(annotation=annotation, default=default))
        for item in metadata:
            if isinstance(doc := getattr(item, "documentation", None), str):
                summary = inspect.cleandoc(doc).split("\n\n")[0].replace("\n", " ")
                docs.append(f"    {param.name}: {summary}")
    vars(func)["__signature__"] = inspect.signature(func).replace(parameters=shown)
    func.__doc__ = "\n".join(
        [inspect.cleandoc(func.__doc__ or ""), "", f"Arguments of {source}:", *docs]
    )


def _route(
    method: Callable[Concatenate[APIRouter, _P], object],
) -> Callable[_P, _Decorator]:
    """Mirror an APIRouter decorator method; record its arguments on the function."""

    def factory(*args: _P.args, **kwargs: _P.kwargs) -> _Decorator:
        """Mark a controller method as a route of the matching APIRouter method."""
        inspect.signature(method).bind(None, *args, **kwargs)

        def mark(func: _F) -> _F:
            _require_function(func)
            routes = vars(func).setdefault(_ROUTES, [])  # pyright: ignore[reportAny]
            routes.append((method, args, kwargs))  # pyright: ignore[reportAny]
            return func

        return mark

    factory.__name__ = factory.__qualname__ = cast("FunctionType", method).__name__
    _show_signature(
        factory, f"fastapi.APIRouter.{factory.__name__}", *_without_self(method)
    )
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


def _settings(
    init: Callable[Concatenate[APIRouter, _P], None],
) -> Callable[_P, _ClassDecorator]:
    """Mirror APIRouter.__init__; record its keyword arguments on the class."""

    def factory(*args: _P.args, **kwargs: _P.kwargs) -> _ClassDecorator:
        """Record APIRouter arguments on a controller class."""
        inspect.signature(init).bind(None, *args, **kwargs)

        def mark(cls: _C) -> _C:
            # vars(cls) is read-only; setattr gives each class its own dict.
            setattr(cls, _SETTINGS, {**vars(cls).get(_SETTINGS, {}), **kwargs})
            return cls

        return mark

    factory.__name__ = factory.__qualname__ = "router"
    _show_signature(factory, "fastapi.APIRouter", *_without_self(init))
    return factory


router = _settings(APIRouter.__init__)


def _create_router(
    new_router: Callable[_P, APIRouter],
) -> Callable[Concatenate[type, _P], APIRouter]:
    """Mirror APIRouter(); the class supplies defaults and routes."""

    def create_router(cls: type, /, *args: _P.args, **kwargs: _P.kwargs) -> APIRouter:
        """Build an APIRouter from cls's routes and @router settings.

        Settings merge key by key along the MRO; a subclass's value replaces
        its base's, and the call's arguments replace both.
        """
        if hasattr(cls, "__router_params__"):
            msg = (
                f"{cls.__qualname__}: __router_params__ is no longer supported; "
                "move its entries to @router(...) (see the README migration guide)"
            )
            raise TypeError(msg)
        endpoints = _endpoints(cls)
        if not endpoints:
            msg = f"{cls.__qualname__} has no routes"
            raise TypeError(msg)
        settings: dict[str, object] = {}
        for klass in reversed(cls.__mro__):
            settings.update(cast("dict[str, object]", vars(klass).get(_SETTINGS, {})))
        # APIRouter keeps list arguments by reference; copy them per router.
        settings = {
            key: list(value) if isinstance(value, list) else value  # pyright: ignore[reportUnknownArgumentType]
            for key, value in settings.items()
        }
        api_router = new_router(*args, **{**settings, **kwargs})  # type: ignore[arg-type]  # pyright: ignore[reportCallIssue]  # ty: ignore[invalid-argument-type]
        for func in endpoints:
            endpoint = _bind_self(cls, func)
            for method, route_args, route_kwargs in _routes(func):
                method(api_router, *route_args, **route_kwargs)(endpoint)
        return api_router

    create_router.__qualname__ = "create_router"
    cls_param = inspect.signature(create_router).parameters["cls"]
    _show_signature(
        create_router,
        "fastapi.APIRouter",
        cls_param,
        *inspect.signature(new_router).parameters.values(),
    )
    return create_router


create_router = _create_router(APIRouter)


def _endpoints(cls: type) -> list[FunctionType]:
    """Return cls's route methods in registration order.

    Raises TypeError where a route would otherwise be dropped silently.
    """
    members: dict[str, object] = {}
    routed: set[str] = set()
    for klass in reversed(cls.__mro__):
        # An overridden name keeps its first (base) slot.
        members.update(vars(klass))
        routed.update(name for name in vars(klass) if _routes(members[name]))
    endpoints: list[FunctionType] = []
    for name, member in members.items():
        if isinstance(member, staticmethod | classmethod) and _routes(
            cast("object", member.__func__)
        ):
            msg = f"{cls.__qualname__}.{name}: route decorators need a plain method"
            raise TypeError(msg)
        if isinstance(member, FunctionType) and _routes(member):
            endpoints.append(member)
        elif name in routed:
            msg = (
                f"{cls.__qualname__}.{name} overrides a route without a route "
                "decorator; decorate it again"
            )
            raise TypeError(msg)
    return endpoints


def _routes(member: object) -> list[_Route]:
    """Return the routes recorded on member by route decorators."""
    if not isinstance(member, FunctionType):
        return []
    return cast("list[_Route]", vars(member).get(_ROUTES, []))


def _bind_self(cls: type, func: FunctionType) -> FunctionType:
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

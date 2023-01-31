from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, ClassVar, Dict, Tuple

from fastapi import APIRouter


class HTTPRequestMethod(str, Enum):
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"
    TRACE = "TRACE"


class RouteMeta:
    def __init__(self, *, binds: Callable[..., Any]) -> None:
        self.binds = binds


class HTTPRouteMeta(RouteMeta):
    def __init__(self, *, binds: Callable[..., Any], request_method: HTTPRequestMethod) -> None:
        super().__init__(binds=binds)
        self.request_method = request_method


class WebsocketRouteMeta(RouteMeta):
    ...


@dataclass
class RouteMetadata:
    delete: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.delete, request_method=HTTPRequestMethod.DELETE)
    get: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.get, request_method=HTTPRequestMethod.GET)
    head: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.head, request_method=HTTPRequestMethod.HEAD)
    options: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.options, request_method=HTTPRequestMethod.OPTIONS)
    patch: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.patch, request_method=HTTPRequestMethod.PATCH)
    post: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.post, request_method=HTTPRequestMethod.POST)
    put: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.put, request_method=HTTPRequestMethod.PUT)
    trace: ClassVar[RouteMeta] = HTTPRouteMeta(binds=APIRouter.trace, request_method=HTTPRequestMethod.TRACE)
    websocket: ClassVar[RouteMeta] = WebsocketRouteMeta(binds=APIRouter.websocket)


@dataclass
class Route:
    endpoint: Callable[..., Any]
    route_meta: RouteMeta
    route_args: Tuple[Any, ...]
    route_kwargs: Dict[str, Any]

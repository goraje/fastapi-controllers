import weakref
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple

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


class RouteDefinition:
    def __init__(self, *, binds: weakref.CallableProxyType) -> None:
        self.binds = binds


class HTTPRouteDefinition(RouteDefinition):
    def __init__(self, *, binds: weakref.CallableProxyType, request_method: HTTPRequestMethod) -> None:
        super().__init__(binds=binds)
        self.request_method = request_method


class WebsocketRouteDefinition(RouteDefinition):
    ...


@dataclass
class RouteData:
    route_definition: RouteDefinition
    route_args: Tuple[Any, ...]
    route_kwargs: Dict[str, Any]


@dataclass
class Route:
    delete = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.delete), request_method=HTTPRequestMethod.DELETE)
    get = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.get), request_method=HTTPRequestMethod.GET)
    head = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.head), request_method=HTTPRequestMethod.HEAD)
    options = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.options), request_method=HTTPRequestMethod.OPTIONS)
    patch = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.patch), request_method=HTTPRequestMethod.PATCH)
    post = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.post), request_method=HTTPRequestMethod.POST)
    put = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.put), request_method=HTTPRequestMethod.PUT)
    trace = HTTPRouteDefinition(binds=weakref.proxy(APIRouter.trace), request_method=HTTPRequestMethod.TRACE)
    websocket = WebsocketRouteDefinition(binds=weakref.proxy(APIRouter.websocket))

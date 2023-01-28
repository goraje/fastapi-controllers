from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


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
    def __init__(self, *, binds: str) -> None:
        self.binds = binds


class HTTPRouteDefinition(RouteDefinition):
    def __init__(self, *, binds: str, request_method: HTTPRequestMethod) -> None:
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
    delete = HTTPRouteDefinition(binds="delete", request_method=HTTPRequestMethod.DELETE)
    get = HTTPRouteDefinition(binds="get", request_method=HTTPRequestMethod.GET)
    head = HTTPRouteDefinition(binds="head", request_method=HTTPRequestMethod.HEAD)
    options = HTTPRouteDefinition(binds="options", request_method=HTTPRequestMethod.OPTIONS)
    patch = HTTPRouteDefinition(binds="patch", request_method=HTTPRequestMethod.PATCH)
    post = HTTPRouteDefinition(binds="post", request_method=HTTPRequestMethod.POST)
    put = HTTPRouteDefinition(binds="put", request_method=HTTPRequestMethod.PUT)
    trace = HTTPRouteDefinition(binds="trace", request_method=HTTPRequestMethod.TRACE)
    websocket = WebsocketRouteDefinition(binds="websocket")

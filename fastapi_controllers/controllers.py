import inspect
import weakref
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from fastapi import APIRouter, params

from fastapi_controllers.definitions import HTTPRouteDefinition, RouteData, WebsocketRouteDefinition
from fastapi_controllers.helpers import _replace_signature, _validate_against_signature


class Controller:
    prefix: str = ""
    dependencies: Optional[Sequence[params.Depends]] = None
    tags: Optional[List[Union[str, Enum]]] = None
    __router_params__: Optional[Dict[str, Any]] = None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__router_params__ = cls.__router_params__ or {}
        for param in ["prefix", "dependencies", "tags"]:
            if not cls.__router_params__.get(param):
                cls.__router_params__[param] = getattr(cls, param)
        _validate_against_signature(weakref.proxy(APIRouter.__init__), kwargs=cls.__router_params__)

    @classmethod
    def create_router(cls) -> APIRouter:
        """
        Create a new APIRouter instance and populate the APIRoutes.

        Returns:
            APIRouter: An APIRouter instance.
        """
        router = APIRouter(**cls.__router_params__)  # type: ignore
        for _, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            _replace_signature(cls, func)
            route_data: Optional[RouteData] = getattr(func, "__route_data__", None)
            if route_data:
                if isinstance(route_data.route_definition, HTTPRouteDefinition):
                    router.add_api_route(
                        route_data.route_args[0],
                        func,
                        *route_data.route_args[1:],
                        methods=[route_data.route_definition.request_method],
                        **route_data.route_kwargs,
                    )
                if isinstance(route_data.route_definition, WebsocketRouteDefinition):
                    router.add_api_websocket_route(
                        route_data.route_args[0],
                        func,
                        *route_data.route_args[1:],
                        **route_data.route_kwargs,
                    )
        return router

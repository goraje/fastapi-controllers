import inspect
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from fastapi import APIRouter, params

from fastapi_controllers.definitions import HTTPRouteMeta, Route, WebsocketRouteMeta
from fastapi_controllers.helpers import _replace_signature, _validate_against_signature


def _is_route(obj: Any) -> bool:
    """
    Check if an object is an instance of Route.

    Args:
        obj: The object to be checked.

    Returns:
        True if the checked object is an instanc of Route.
    """
    return isinstance(obj, Route)


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
        _validate_against_signature(APIRouter.__init__, kwargs=cls.__router_params__)

    @classmethod
    def create_router(cls) -> APIRouter:
        """
        Create a new APIRouter instance and populate the APIRoutes.

        Returns:
            APIRouter: An APIRouter instance.
        """
        router = APIRouter(**(cls.__router_params__ or {}))
        for _, route in inspect.getmembers(cls, predicate=_is_route):
            _replace_signature(cls, route.endpoint)
            if isinstance(route.route_meta, HTTPRouteMeta):
                router.add_api_route(
                    route.route_args[0],
                    route.endpoint,
                    *route.route_args[1:],
                    methods=[route.route_meta.request_method],
                    **route.route_kwargs,
                )
            if isinstance(route.route_meta, WebsocketRouteMeta):
                router.add_api_websocket_route(
                    route.route_args[0],
                    route.endpoint,
                    *route.route_args[1:],
                    **route.route_kwargs,
                )
        return router

import inspect
from enum import Enum
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Union

from fastapi import APIRouter, params

from fastapi_controllers.helpers import _replace_signature, _validate_against_apirouter_signature


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
        _validate_against_apirouter_signature("__init__", kwargs=cls.__router_params__)

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
            api_route_data: Optional[SimpleNamespace] = getattr(func, "__api_route_data__", None)
            if api_route_data:
                router.add_api_route(
                    api_route_data.args[0],
                    func,
                    *api_route_data.args[1:],
                    **api_route_data.kwargs,
                )
        return router

from enum import Enum
from types import SimpleNamespace
from typing import Any, Callable

from fastapi_controllers.helpers import _validate_against_apirouter_signature


class _HTTPRequestMethod(str, Enum):
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"
    TRACE = "TRACE"


class _RouteDecorator:
    method: str

    def __init_subclass__(cls, method: _HTTPRequestMethod) -> None:
        super().__init_subclass__()
        cls.method = method

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        if self.args and callable(self.args[0]):
            raise TypeError("You must provide a path for the route.")
        self.kwargs = kwargs
        _validate_against_apirouter_signature(self.method.lower(), args=args, kwargs=kwargs)

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self.kwargs["methods"] = [self.method]
        self.kwargs["name"] = self.kwargs.get("name") or func.__name__
        self.kwargs["description"] = func.__doc__ or "No description provided."
        func.__api_route_data__ = SimpleNamespace(args=self.args, kwargs=self.kwargs)  # type: ignore
        return func


class delete(_RouteDecorator, method=_HTTPRequestMethod.DELETE):
    ...


class get(_RouteDecorator, method=_HTTPRequestMethod.GET):
    ...


class head(_RouteDecorator, method=_HTTPRequestMethod.HEAD):
    ...


class options(_RouteDecorator, method=_HTTPRequestMethod.OPTIONS):
    ...


class patch(_RouteDecorator, method=_HTTPRequestMethod.PATCH):
    ...


class post(_RouteDecorator, method=_HTTPRequestMethod.POST):
    ...


class put(_RouteDecorator, method=_HTTPRequestMethod.PUT):
    ...


class trace(_RouteDecorator, method=_HTTPRequestMethod.TRACE):
    ...

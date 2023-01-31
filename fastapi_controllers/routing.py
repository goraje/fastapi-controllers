from typing import Any, Callable, Dict, Tuple

from fastapi_controllers.definitions import Route, RouteMeta, RouteMetadata
from fastapi_controllers.helpers import _validate_against_signature


class _RouteDecorator:
    route_meta: RouteMeta

    def __init_subclass__(cls, route_meta: RouteMeta) -> None:
        super().__init_subclass__()
        cls.route_meta = route_meta

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.route_args = args
        self.route_kwargs = kwargs
        _validate_against_signature(self.route_meta.binds, args=args, kwargs=kwargs)

    def __call__(self, endpoint: Callable[..., Any]) -> Route:
        return Route(
            endpoint=endpoint,
            route_meta=self.route_meta,
            route_args=self.route_args,
            route_kwargs=self.route_kwargs,
        )

    @property
    def route_args(self) -> Tuple[Any, ...]:
        return self._route_args

    @route_args.setter
    def route_args(self, value: Tuple[Any, ...]) -> None:
        self._route_args = value

    @property
    def route_kwargs(self) -> Dict[str, Any]:
        return self._route_kwargs

    @route_kwargs.setter
    def route_kwargs(self, value: Dict[str, Any]) -> None:
        self._route_kwargs = value


class delete(_RouteDecorator, route_meta=RouteMetadata.delete):
    ...


class get(_RouteDecorator, route_meta=RouteMetadata.get):
    ...


class head(_RouteDecorator, route_meta=RouteMetadata.head):
    ...


class options(_RouteDecorator, route_meta=RouteMetadata.options):
    ...


class patch(_RouteDecorator, route_meta=RouteMetadata.patch):
    ...


class post(_RouteDecorator, route_meta=RouteMetadata.post):
    ...


class put(_RouteDecorator, route_meta=RouteMetadata.put):
    ...


class trace(_RouteDecorator, route_meta=RouteMetadata.trace):
    ...


class websocket(_RouteDecorator, route_meta=RouteMetadata.websocket):
    ...

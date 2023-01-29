from typing import Any, Callable, Dict, Tuple

from fastapi_controllers.definitions import Route, RouteData, RouteDefinition
from fastapi_controllers.helpers import _validate_against_signature


class _RouteDecorator:
    _route_definition: RouteDefinition

    def __init_subclass__(cls, route_definition: RouteDefinition) -> None:
        super().__init_subclass__()
        cls._route_definition = route_definition

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.route_args = args
        self.route_kwargs = kwargs
        _validate_against_signature(self._route_definition.binds, args=args, kwargs=kwargs)

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        func.__route_data__ = RouteData(  # type: ignore
            route_definition=self._route_definition,
            route_args=self.route_args,
            route_kwargs=self.route_kwargs,
        )
        return func

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


class delete(_RouteDecorator, route_definition=Route.delete):
    ...


class get(_RouteDecorator, route_definition=Route.get):
    ...


class head(_RouteDecorator, route_definition=Route.head):
    ...


class options(_RouteDecorator, route_definition=Route.options):
    ...


class patch(_RouteDecorator, route_definition=Route.patch):
    ...


class post(_RouteDecorator, route_definition=Route.post):
    ...


class put(_RouteDecorator, route_definition=Route.put):
    ...


class trace(_RouteDecorator, route_definition=Route.trace):
    ...


class websocket(_RouteDecorator, route_definition=Route.websocket):
    ...

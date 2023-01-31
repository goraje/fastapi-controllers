from typing import Type
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from fastapi_controllers.definitions import HTTPRequestMethod, Route, RouteMeta
from fastapi_controllers.routing import _RouteDecorator, delete, get, head, options, patch, post, put, trace

HTTP_DECO_DEFINITIONS = {
    delete: HTTPRequestMethod.DELETE,
    get: HTTPRequestMethod.GET,
    head: HTTPRequestMethod.HEAD,
    options: HTTPRequestMethod.OPTIONS,
    patch: HTTPRequestMethod.PATCH,
    post: HTTPRequestMethod.POST,
    put: HTTPRequestMethod.PUT,
    trace: HTTPRequestMethod.TRACE,
}


class FakeMeta(RouteMeta):
    ...


def original_method() -> None:
    ...


def fake_method() -> None:
    ...


binds = original_method


class fake(_RouteDecorator, route_meta=FakeMeta(binds=binds)):
    ...


@pytest.fixture
def validator(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("fastapi_controllers.routing._validate_against_signature")


def describe_RouteDecorator() -> None:
    def it_validates_the_parameters_of_the_decorated_method(validator: MagicMock) -> None:
        fake("/test", keyword="TEST")(fake_method)
        validator.assert_called_once_with(
            fake.route_meta.binds,
            args=("/test",),
            kwargs={
                "keyword": "TEST",
            },
        )

    def it_creates_a_route_instance_for_the_decorated_method(validator: MagicMock) -> None:
        route = fake("/test", keyword="TEST")(fake_method)
        assert isinstance(route, Route)
        assert isinstance(route.route_meta, FakeMeta)
        assert route.route_meta.binds == binds
        assert route.route_args == ("/test",)
        assert route.route_kwargs == {"keyword": "TEST"}


def describe_decorators() -> None:
    @pytest.mark.parametrize("decorator", HTTP_DECO_DEFINITIONS.keys())
    def it_is_a_subclass_of_route_decorator(decorator: Type[_RouteDecorator]) -> None:
        assert issubclass(decorator, _RouteDecorator)

    @pytest.mark.parametrize("decorator,method", HTTP_DECO_DEFINITIONS.items())
    def it_handles_the_proper_http_request_method(
        decorator: Type[_RouteDecorator],
        method: HTTPRequestMethod,
    ) -> None:
        assert decorator.route_meta.request_method == method  # type: ignore

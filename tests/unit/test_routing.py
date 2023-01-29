import weakref
from typing import Type
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from fastapi_controllers.definitions import HTTPRequestMethod, RouteData, RouteDefinition
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


class FakeDefinition(RouteDefinition):
    ...


def original_method() -> None:
    ...


def fake_method() -> None:
    ...


binds = weakref.proxy(original_method)


class fake(_RouteDecorator, route_definition=FakeDefinition(binds=binds)):
    ...


@pytest.fixture
def validator(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("fastapi_controllers.routing._validate_against_signature")


def describe_RouteDecorator() -> None:
    def it_validates_the_parameters_of_the_decorated_method(validator: MagicMock) -> None:
        fake("/test", keyword="TEST")(fake_method)
        validator.assert_called_once_with(
            fake._route_definition.binds,
            args=("/test",),
            kwargs={
                "keyword": "TEST",
            },
        )

    def it_adds_route_data_to_the_decorated_method(validator: MagicMock) -> None:
        wrapped = fake("/test", keyword="TEST")(fake_method)
        assert isinstance(wrapped.__route_data__, RouteData)  # type: ignore
        assert isinstance(wrapped.__route_data__.route_definition, FakeDefinition)  # type: ignore
        assert wrapped.__route_data__.route_definition.binds == binds  # type: ignore
        assert wrapped.__route_data__.route_args == ("/test",)  # type: ignore
        assert wrapped.__route_data__.route_kwargs == {"keyword": "TEST"}  # type: ignore


def describe_decorators() -> None:
    @pytest.mark.parametrize("decorator", HTTP_DECO_DEFINITIONS.keys())
    def it_is_a_subclass_of_route_decorator(decorator: Type[_RouteDecorator]) -> None:
        assert issubclass(decorator, _RouteDecorator)

    @pytest.mark.parametrize("decorator,method", HTTP_DECO_DEFINITIONS.items())
    def it_handles_the_proper_http_request_method(
        decorator: Type[_RouteDecorator],
        method: HTTPRequestMethod,
    ) -> None:
        assert decorator._route_definition.request_method == method  # type: ignore

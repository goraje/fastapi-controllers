from types import SimpleNamespace
from typing import Type
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from fastapi_controllers.routing import _HTTPRequestMethod, _RouteDecorator, delete, get, head, options, patch, post, put, trace

DEFINITIONS = {
    delete: _HTTPRequestMethod.DELETE,
    get: _HTTPRequestMethod.GET,
    head: _HTTPRequestMethod.HEAD,
    options: _HTTPRequestMethod.OPTIONS,
    patch: _HTTPRequestMethod.PATCH,
    post: _HTTPRequestMethod.POST,
    put: _HTTPRequestMethod.PUT,
    trace: _HTTPRequestMethod.TRACE,
}


def fake_method() -> None:
    ...


class fake(_RouteDecorator, method=_HTTPRequestMethod.GET):
    ...


@pytest.fixture
def validator(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("fastapi_controllers.routing._validate_against_apirouter_signature")


def describe_RouteDecorator() -> None:
    def it_enforces_the_path_parameter() -> None:
        with pytest.raises(TypeError) as exc:
            fake(fake_method)
        assert str(exc.value) == "You must provide a path for the route."

    def it_validates_the_parameters_of_the_decorated_method(validator: MagicMock) -> None:
        fake("/test", keyword="TEST")(fake_method)
        validator.assert_called_once_with(
            fake.method.lower(),
            args=("/test",),
            kwargs={
                "keyword": "TEST",
                "methods": ["GET"],
                "name": "fake_method",
                "description": "No description provided.",
            },
        )

    def it_adds_api_route_data_to_the_decorated_method(validator: MagicMock) -> None:
        wrapped = fake("/test", keyword="TEST")(fake_method)
        assert isinstance(wrapped.__api_route_data__, SimpleNamespace)  # type: ignore
        assert wrapped.__api_route_data__.args == ("/test",)  # type: ignore
        assert wrapped.__api_route_data__.kwargs == {  # type: ignore
            "keyword": "TEST",
            "methods": ["GET"],
            "name": "fake_method",
            "description": "No description provided.",
        }


def describe_decorators() -> None:
    @pytest.mark.parametrize("decorator", DEFINITIONS.keys())
    def it_is_a_subclass_of_route_decorator(decorator: Type[_RouteDecorator]) -> None:
        assert issubclass(decorator, _RouteDecorator)

    @pytest.mark.parametrize("decorator,method", DEFINITIONS.items())
    def it_handles_the_proper_http_request_method(
        decorator: Type[_RouteDecorator],
        method: _HTTPRequestMethod,
    ) -> None:
        assert decorator.method == method

from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter
from pytest_mock import MockerFixture

from fastapi_controllers.controllers import Controller
from fastapi_controllers.routing import get


@pytest.fixture(autouse=True)
def validator(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("fastapi_controllers.controllers._validate_against_apirouter_signature")


def describe_Controller() -> None:
    def it_sets_router_params() -> None:
        class FakeController(Controller):
            prefix = "/test"
            dependencies = ["TEST"]  # type: ignore
            tags = ["TEST"]
            __router_params__ = {
                "prefix": "/override",
                "tags": ["override"],
                "deprecated": True,
            }

        assert FakeController.__router_params__ == {
            "prefix": "/override",
            "dependencies": ["TEST"],
            "tags": ["override"],
            "deprecated": True,
        }

    def it_validates_apirouter_parameters(validator: MagicMock) -> None:
        class _(Controller):
            ...

        validator.assert_called_once_with(
            "__init__",
            kwargs={
                "prefix": "",
                "dependencies": None,
                "tags": None,
            },
        )

    def describe_create_router() -> None:
        def it_creates_an_apirouter() -> None:
            class FakeController(Controller):
                prefix = "/test"

                @get("/get", deprecated=True)
                def fake_method(self) -> None:
                    ...

            result = FakeController.create_router()
            assert isinstance(result, APIRouter)

        def it_replaces_method_signatures(mocker: MockerFixture) -> None:
            replace = mocker.patch("fastapi_controllers.controllers._replace_signature")

            class FakeController(Controller):
                prefix = "/test"

                @get("/get", deprecated=True)
                def fake_method(self) -> None:
                    ...

            FakeController.create_router()
            replace.assert_called_once_with(FakeController, FakeController.fake_method)

        def it_configures_the_router_and_routes(mocker: MockerFixture) -> None:
            apirouter = mocker.patch("fastapi_controllers.controllers.APIRouter")

            class FakeController(Controller):
                prefix = "/test"

                @get("/get", deprecated=True)
                def fake_method(self) -> None:
                    ...

            FakeController.create_router()
            apirouter.assert_called_once_with(prefix="/test", dependencies=None, tags=None)
            apirouter.return_value.add_api_route.assert_called_once_with(
                "/get",
                FakeController.fake_method,
                deprecated=True,
                methods=["GET"],
            )

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from fastapi_controllers.routing import _HTTPRequestMethod


def describe_test_controller_async() -> None:
    @pytest.mark.parametrize("http_request_method", _HTTPRequestMethod.__members__.values())
    def it_responds_to_http_methods(
        async_test_client: TestClient,
        http_request_method: _HTTPRequestMethod,
    ) -> None:
        request_func = getattr(async_test_client, http_request_method.lower(), None)
        if request_func:
            response = request_func("/test-async")
            assert response.status_code == status.HTTP_200_OK

    def it_resolves_async_dependencies(async_test_client: TestClient) -> None:
        response = async_test_client.get("/test-async")
        assert response.status_code == status.HTTP_200_OK
        assert response.text == "ASYNC TEST"

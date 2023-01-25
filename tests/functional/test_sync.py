import pytest
from fastapi import status
from fastapi.testclient import TestClient

from fastapi_controllers.routing import _HTTPRequestMethod


def describe_test_controller_sync() -> None:
    @pytest.mark.parametrize("http_request_method", _HTTPRequestMethod.__members__.values())
    def it_responds_to_http_methods(
        sync_test_client: TestClient,
        http_request_method: _HTTPRequestMethod,
    ) -> None:
        request_func = getattr(sync_test_client, http_request_method.lower(), None)
        if request_func:
            response = request_func("/test-sync")
            assert response.status_code == status.HTTP_200_OK

    def it_resolves_sync_dependencies(sync_test_client: TestClient) -> None:
        response = sync_test_client.get("/test-sync")
        assert response.status_code == status.HTTP_200_OK
        assert response.text == "SYNC TEST"

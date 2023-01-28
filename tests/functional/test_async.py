import pytest
from fastapi import status
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from fastapi_controllers.definitions import HTTPRequestMethod


def describe_test_controller_async() -> None:
    @pytest.mark.parametrize("http_request_method", HTTPRequestMethod.__members__.values())
    def it_responds_to_http_methods(
        async_test_client: TestClient,
        http_request_method: HTTPRequestMethod,
    ) -> None:
        request_func = getattr(async_test_client, http_request_method.lower(), None)
        if request_func:
            response = request_func("/test-async")
            assert response.status_code == status.HTTP_200_OK

    def it_supports_websockets(async_test_client: TestClient) -> None:
        with pytest.raises(WebSocketDisconnect):
            with async_test_client.websocket_connect("/ws") as websocket:
                data = websocket.receive_json()
                assert data == {"msg": "Hello WebSocket"}

    def it_resolves_async_dependencies(async_test_client: TestClient) -> None:
        response = async_test_client.get("/test-async")
        assert response.status_code == status.HTTP_200_OK
        assert response.text == "ASYNC TEST"

from typing import assert_type, final

import pytest

from fastapi_controllers import create_router, get, router, websocket


@final
@router(prefix="/typed")
class Typed:
    @get("/{n}", status_code=201, response_model=None)
    def double(self, n: int) -> int:
        return n * 2


def test_decorated_method_keeps_its_type() -> None:
    assert assert_type(Typed().double(2), int) == 4


def test_unknown_keyword_argument_is_rejected() -> None:
    with pytest.raises(TypeError):
        get("/x", not_a_param=1)  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # ty: ignore[unknown-argument]


def test_missing_path_is_rejected() -> None:
    with pytest.raises(TypeError):
        get()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # ty: ignore[missing-argument]


def test_websocket_rejects_http_only_arguments() -> None:
    with pytest.raises(TypeError):
        websocket("/ws", status_code=200)  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # ty: ignore[unknown-argument]


def test_wrong_argument_type_is_rejected_statically() -> None:
    # Static-only: inspect's bind() checks arity, not types.
    assert callable(get(123))  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]  # ty: ignore[invalid-argument-type]


def test_router_rejects_unknown_argument() -> None:
    with pytest.raises(TypeError):
        router(not_a_param=1)  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # ty: ignore[unknown-argument]


def test_router_wrong_argument_type_is_rejected_statically() -> None:
    # Static-only: inspect's bind() checks arity, not types.
    assert callable(router(prefix=1))  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]  # ty: ignore[invalid-argument-type]


def test_create_router_rejects_unknown_argument() -> None:
    with pytest.raises(TypeError):
        create_router(Typed, not_a_param=1)  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # ty: ignore[unknown-argument]


def test_create_router_requires_a_class() -> None:
    with pytest.raises(TypeError):
        create_router(prefix="/x")  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # ty: ignore[missing-argument]

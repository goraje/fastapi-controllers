import inspect
from typing import Any

import pytest
from fastapi import params

from fastapi_controllers.helpers import _replace_signature, _validate_against_signature


class Fake:
    def fake_method(self, positional: Any, *, keyword: "str") -> None:
        ...


def describe_validate_against_signature() -> None:
    def it_validates_method_parameters_against_the_desired_signature() -> None:
        _validate_against_signature(
            Fake.fake_method,
            args=("test",),
            kwargs={"keyword": "TEST"},
        )

    def it_raises_an_error_on_missing_positional_args() -> None:
        with pytest.raises(TypeError):
            _validate_against_signature(
                Fake.fake_method,
                args=tuple(),
                kwargs={"keyword": "TEST"},
            )

    def it_raises_an_error_on_missing_keyword_args() -> None:
        with pytest.raises(TypeError):
            _validate_against_signature(
                Fake.fake_method,
                args=("test",),
                kwargs={},
            )

    def it_raises_an_error_on_additional_keyword_args() -> None:
        with pytest.raises(TypeError):
            _validate_against_signature(
                Fake.fake_method,
                args=("test",),
                kwargs={"keyword": "TEST", "additional": "TEST"},
            )

    def it_raises_an_error_on_additional_positional_args() -> None:
        with pytest.raises(TypeError):
            _validate_against_signature(
                Fake.fake_method,
                args=("test", "test"),
                kwargs={},
            )


def describe_replace_signature() -> None:
    def it_replaces_the_signature_of_an_instance_method() -> None:
        class Test:
            def test(self, positional: Any, *, keyword: str) -> None:
                ...

        _replace_signature(Test, Test.test)
        replaced_params = list(inspect.signature(Test.test).parameters.values())
        assert replaced_params[0].name == "self"
        assert replaced_params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert isinstance(replaced_params[0].default, params.Depends)
        assert replaced_params[0].default.dependency == Test
        assert replaced_params[1].name == "positional"
        assert replaced_params[1].kind == inspect.Parameter.KEYWORD_ONLY
        assert replaced_params[2].name == "keyword"
        assert replaced_params[2].kind == inspect.Parameter.KEYWORD_ONLY

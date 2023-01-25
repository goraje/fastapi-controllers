import inspect
from typing import Any, Callable, Dict, Optional, Tuple, Type

from fastapi import APIRouter, Depends


def _validate_against_apirouter_signature(
    method_name: str,
    args: Optional[Tuple[Any, ...]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Validate method parameters against those of the corresponding APIRouter method.

    Args:
        method_name: The name of an APIRouter method to validate against.
        args: The positional arguments of the method.
        kwargs: The keyword arguments of the method.
    """
    target_sig = inspect.signature(getattr(APIRouter, method_name))
    valid_sig = target_sig.replace(parameters=list(target_sig.parameters.values())[1:])
    valid_sig.bind(*(args or tuple()), **(kwargs or {}))


def _replace_signature(cls: Type, func: Callable[..., Any]) -> None:
    orig_sig = inspect.signature(func)
    new_params = [
        param.replace(
            kind=inspect.Parameter.KEYWORD_ONLY,
        )
        if param.name != "self"
        else param.replace(default=Depends(cls))
        for param in list(orig_sig.parameters.values())
    ]
    func.__signature__ = orig_sig.replace(parameters=new_params)  # type: ignore

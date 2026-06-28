from __future__ import annotations

import inspect
from functools import cached_property
from types import ModuleType
from typing import Any

import numpy as np


def safe_repr(val: Any, max_len: int = 200) -> str | None:
    if val is inspect.Parameter.empty:
        return None
    try:
        if inspect.isclass(val):
            return f"<class '{val.__module__}.{val.__qualname__}'>"
        text = repr(val)
    except Exception:
        text = f"<{type(val).__name__}>"
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _annotation_str(annotation: Any) -> str | None:
    if annotation is inspect.Parameter.empty:
        return None
    if isinstance(annotation, str):
        return annotation
    return getattr(annotation, "__name__", None) or str(annotation)


def _parameter_node(param: inspect.Parameter) -> dict[str, Any]:
    return {
        "name": param.name,
        "annotation": _annotation_str(param.annotation),
        "default": safe_repr(param.default),
        "kind": str(param.kind),
    }


def safe_signature(obj: Any) -> dict[str, Any] | None:
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):
        return None

    return_annotation = sig.return_annotation
    return {
        "parameters": [_parameter_node(p) for p in sig.parameters.values()],
        "return_annotation": _annotation_str(return_annotation),
    }


def get_doc(obj: Any) -> dict[str, str | None]:
    full = inspect.getdoc(obj)
    if not full:
        return {"summary": None, "full": None}
    parts = full.split("\n\n", 1)
    summary = parts[0].strip()
    return {"summary": summary, "full": full}


def get_mro_chain(cls: type) -> list[str]:
    return [c.__name__ for c in cls.__mro__]


def _defined_in(name: str, cls: type) -> str | None:
    for base in cls.__mro__:
        if name in base.__dict__:
            return base.__name__
    return None


def _is_public(name: str) -> bool:
    return not name.startswith("_") or name == "__init__"


def _member_doc(member: Any) -> dict[str, str | None]:
    if isinstance(member, property):
        return get_doc(member.fget) if member.fget else {"summary": None, "full": None}
    if isinstance(member, cached_property):
        return get_doc(member.func)
    return get_doc(member)


def get_class_members(cls: type) -> dict[str, list[dict[str, Any]]]:
    methods: list[dict[str, Any]] = []
    properties: list[dict[str, Any]] = []
    class_attributes: list[dict[str, Any]] = []

    for name, member in inspect.getmembers(cls):
        if not _is_public(name):
            continue

        defined_in = _defined_in(name, cls)

        if inspect.isroutine(member) or (
            isinstance(member, (staticmethod, classmethod))
            and member.__func__ is not None
        ):
            target = member
            if isinstance(member, (staticmethod, classmethod)):
                target = member.__func__
            sig = safe_signature(target)
            doc = _member_doc(target)
            methods.append(
                {
                    "name": name,
                    "defined_in": defined_in,
                    "parameters": sig["parameters"] if sig else [],
                    "return_annotation": sig["return_annotation"] if sig else None,
                    "doc": doc,
                }
            )
            continue

        if isinstance(member, (property, cached_property)):
            doc = _member_doc(member)
            properties.append(
                {
                    "name": name,
                    "defined_in": defined_in,
                    "doc": doc,
                }
            )
            continue

        if name in cls.__dict__ and not inspect.ismodule(member):
            class_attributes.append(
                {
                    "name": name,
                    "defined_in": defined_in,
                    "value_type": type(member).__name__,
                    "value_repr": safe_repr(member),
                }
            )

    methods.sort(key=lambda m: m["name"])
    properties.sort(key=lambda p: p["name"])
    class_attributes.sort(key=lambda a: a["name"])

    return {
        "methods": methods,
        "properties": properties,
        "class_attributes": class_attributes,
    }


def qualified_name(obj: Any) -> str | None:
    if isinstance(obj, ModuleType):
        return obj.__name__
    module = getattr(obj, "__module__", None)
    qualname = getattr(obj, "__qualname__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    return qualname


def classify_export(obj: Any) -> str:
    if inspect.ismodule(obj):
        return "module"
    if inspect.isclass(obj):
        return "class"
    if inspect.isfunction(obj):
        return "function"
    type_name = type(obj).__name__
    if type_name == "ManimColor":
        return "color"
    if isinstance(obj, np.ndarray):
        return "ndarray"
    if isinstance(obj, (int, float, str, bool, type(None))):
        return "constant"
    return type_name.lower()


def export_module(obj: Any) -> str | None:
    if isinstance(obj, ModuleType):
        return obj.__name__
    return getattr(obj, "__module__", None)

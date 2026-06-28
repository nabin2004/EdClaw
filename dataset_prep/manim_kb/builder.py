from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from types import ModuleType
from typing import Any

import manim

from .introspect import (
    classify_export,
    export_module,
    get_class_members,
    get_doc,
    get_mro_chain,
    qualified_name,
    safe_repr,
    safe_signature,
)


def _base_node(name: str, obj: Any, kind: str) -> dict[str, Any]:
    doc = get_doc(obj)
    return {
        "name": name,
        "kind": kind,
        "module": export_module(obj),
        "qualified_name": qualified_name(obj),
        "doc": doc,
    }


def _build_class_node(name: str, cls: type) -> dict[str, Any]:
    node = _base_node(name, cls, "class")
    node["bases"] = [base.__name__ for base in cls.__bases__]
    node["mro"] = get_mro_chain(cls)
    ctor = safe_signature(cls.__init__)
    node["constructor"] = {"parameters": ctor["parameters"] if ctor else []}
    members = get_class_members(cls)
    node["methods"] = members["methods"]
    node["properties"] = members["properties"]
    node["class_attributes"] = members["class_attributes"]
    return node


def _build_function_node(name: str, func: Any) -> dict[str, Any]:
    node = _base_node(name, func, "function")
    sig = safe_signature(func)
    node["parameters"] = sig["parameters"] if sig else []
    node["return_annotation"] = sig["return_annotation"] if sig else None
    return node


def _build_value_node(name: str, obj: Any, kind: str) -> dict[str, Any]:
    node = _base_node(name, obj, kind)
    node["value_type"] = type(obj).__name__
    node["value_repr"] = safe_repr(obj)
    return node


def _build_module_node(name: str, module: ModuleType) -> dict[str, Any]:
    node = _base_node(name, module, "module")
    node["submodule_path"] = module.__name__
    return node


def _build_export_node(name: str, obj: Any) -> dict[str, Any]:
    kind = classify_export(obj)
    if kind == "class":
        return _build_class_node(name, obj)
    if kind == "function":
        return _build_function_node(name, obj)
    if kind == "module":
        return _build_module_node(name, obj)
    if kind in {"color", "ndarray", "constant"}:
        return _build_value_node(name, obj, kind)
    return _build_value_node(name, obj, kind)


def _insert_module_path(tree: dict[str, Any], module_path: str | None, export_name: str) -> None:
    if not module_path:
        return
    parts = module_path.split(".")
    current = tree
    for part in parts:
        current = current.setdefault(part, {})
    exports = current.setdefault("_exports", [])
    if export_name not in exports:
        exports.append(export_name)


def build_knowledge_base() -> dict[str, Any]:
    exports: dict[str, Any] = {}
    module_tree: dict[str, Any] = {}
    inheritance: dict[str, list[str]] = {}
    kind_counts: Counter[str] = Counter()

    for name in sorted(dir(manim)):
        if name.startswith("_"):
            continue
        obj = getattr(manim, name)
        node = _build_export_node(name, obj)
        exports[name] = node
        kind_counts[node["kind"]] += 1
        _insert_module_path(module_tree, node.get("module"), name)
        if node["kind"] == "class":
            inheritance[name] = node["mro"]

    return {
        "meta": {
            "manim_version": getattr(manim, "__version__", "unknown"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_exports": len(exports),
            "counts_by_kind": dict(sorted(kind_counts.items())),
        },
        "exports": exports,
        "module_tree": module_tree,
        "inheritance": inheritance,
    }

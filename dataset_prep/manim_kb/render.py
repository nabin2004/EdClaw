from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.tree import Tree

KIND_ORDER = [
    "class",
    "function",
    "color",
    "constant",
    "ndarray",
    "module",
]


def _format_parameters(parameters: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for param in parameters:
        if param["name"] == "self":
            continue
        chunk = param["name"]
        if param.get("annotation"):
            chunk += f": {param['annotation']}"
        if param.get("default") is not None:
            chunk += f" = {param['default']}"
        parts.append(chunk)
    return ", ".join(parts)


def _format_method_signature(method: dict[str, Any]) -> str:
    params = _format_parameters(method.get("parameters", []))
    ret = method.get("return_annotation")
    sig = f"{method['name']}({params})"
    if ret:
        sig += f" -> {ret}"
    return sig


def write_json(kb: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(kb, handle, indent=2, ensure_ascii=False)
    return output_path


def _render_class_markdown(name: str, node: dict[str, Any]) -> list[str]:
    lines = [f"### {name}", ""]
    if node["doc"]["summary"]:
        lines.append(node["doc"]["summary"])
        lines.append("")
    lines.append(f"- **Module:** `{node.get('module')}`")
    lines.append(f"- **Bases:** {', '.join(node.get('bases', [])) or '—'}")
    lines.append(f"- **MRO:** {' → '.join(node.get('mro', []))}")
    ctor_params = _format_parameters(node.get("constructor", {}).get("parameters", []))
    lines.append(f"- **Constructor:** `{name}({ctor_params})`")
    lines.append(f"- **Methods:** {len(node.get('methods', []))}")
    for method in node.get("methods", []):
        marker = "" if method.get("defined_in") == name else f" _(from {method.get('defined_in')})_"
        lines.append(f"  - `{_format_method_signature(method)}`{marker}")
    if node.get("properties"):
        lines.append(f"- **Properties:** {len(node['properties'])}")
        for prop in node["properties"]:
            marker = "" if prop.get("defined_in") == name else f" _(from {prop.get('defined_in')})_"
            lines.append(f"  - `{prop['name']}`{marker}")
    lines.append("")
    return lines


def _render_function_markdown(name: str, node: dict[str, Any]) -> list[str]:
    params = _format_parameters(node.get("parameters", []))
    ret = node.get("return_annotation")
    signature = f"{name}({params})"
    if ret:
        signature += f" -> {ret}"
    lines = [f"### {name}", ""]
    if node["doc"]["summary"]:
        lines.append(node["doc"]["summary"])
        lines.append("")
    lines.append(f"- **Module:** `{node.get('module')}`")
    lines.append(f"- **Signature:** `{signature}`")
    lines.append("")
    return lines


def _render_value_markdown(name: str, node: dict[str, Any]) -> list[str]:
    lines = [
        f"### {name}",
        "",
        f"- **Module:** `{node.get('module')}`",
        f"- **Type:** `{node.get('value_type')}`",
        f"- **Value:** `{node.get('value_repr')}`",
        "",
    ]
    return lines


def write_markdown(kb: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meta = kb["meta"]
    lines = [
        "# Manim Knowledge Base",
        "",
        f"- **Manim version:** {meta['manim_version']}",
        f"- **Generated at:** {meta['generated_at']}",
        f"- **Total exports:** {meta['total_exports']}",
        "",
    ]

    exports: dict[str, Any] = kb["exports"]
    grouped: dict[str, list[str]] = {kind: [] for kind in KIND_ORDER}
    other_kinds: list[str] = []
    for name, node in exports.items():
        kind = node["kind"]
        if kind in grouped:
            grouped[kind].append(name)
        else:
            other_kinds.append(name)

    section_titles = {
        "class": "Classes",
        "function": "Functions",
        "color": "Colors",
        "constant": "Constants",
        "ndarray": "NumPy Arrays",
        "module": "Modules",
    }

    for kind in KIND_ORDER:
        names = sorted(grouped[kind])
        if not names:
            continue
        lines.append(f"## {section_titles[kind]} ({len(names)})")
        lines.append("")
        for name in names:
            node = exports[name]
            if kind == "class":
                lines.extend(_render_class_markdown(name, node))
            elif kind == "function":
                lines.extend(_render_function_markdown(name, node))
            else:
                lines.extend(_render_value_markdown(name, node))

    if other_kinds:
        lines.append(f"## Other ({len(other_kinds)})")
        lines.append("")
        for name in sorted(other_kinds):
            lines.extend(_render_value_markdown(name, exports[name]))

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _add_class_tree(branch: Tree, name: str, node: dict[str, Any], verbose: bool) -> None:
    label = f"[bold cyan]{name}[/] [dim](class, {len(node.get('methods', []))} methods)[/]"
    class_branch = branch.add(label)
    if not verbose:
        return
    ctor_params = _format_parameters(node.get("constructor", {}).get("parameters", []))
    class_branch.add(f"[green]__init__[/]({ctor_params})")
    for method in node.get("methods", []):
        defined = method.get("defined_in")
        suffix = "" if defined == name else f" [dim]from {defined}[/]"
        class_branch.add(f"[yellow]{_format_method_signature(method)}[/]{suffix}")


def _add_export_tree(branch: Tree, name: str, node: dict[str, Any], verbose: bool) -> None:
    kind = node["kind"]
    if kind == "class":
        _add_class_tree(branch, name, node, verbose)
        return
    if kind == "function":
        params = _format_parameters(node.get("parameters", []))
        ret = node.get("return_annotation")
        sig = f"{name}({params})"
        if ret:
            sig += f" -> {ret}"
        branch.add(f"[magenta]{sig}[/] [dim](function)[/]")
        return
    branch.add(f"[white]{name}[/] [dim]({kind})[/]")


def print_tree(kb: dict[str, Any], verbose: bool = False) -> None:
    console = Console()
    meta = kb["meta"]
    root = Tree(
        f"[bold]Manim KB[/] [dim]v{meta['manim_version']} · {meta['total_exports']} exports[/]"
    )

    exports: dict[str, Any] = kb["exports"]
    grouped: dict[str, list[str]] = {kind: [] for kind in KIND_ORDER}
    other: list[str] = []
    for name, node in exports.items():
        kind = node["kind"]
        if kind in grouped:
            grouped[kind].append(name)
        else:
            other.append(name)

    section_labels = {
        "class": "Classes",
        "function": "Functions",
        "color": "Colors",
        "constant": "Constants",
        "ndarray": "Arrays",
        "module": "Modules",
    }

    for kind in KIND_ORDER:
        names = sorted(grouped[kind])
        if not names:
            continue
        section = root.add(f"[bold]{section_labels[kind]}[/] ({len(names)})")
        for name in names:
            _add_export_tree(section, name, exports[name], verbose)

    if other:
        section = root.add(f"[bold]Other[/] ({len(other)})")
        for name in sorted(other):
            _add_export_tree(section, name, exports[name], verbose)

    console.print(root)

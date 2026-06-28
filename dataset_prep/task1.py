import json


def format_signature(name, parameters):
    parts = []
    for p in parameters:
        s = p["name"]
        if "VAR_POSITIONAL" in p["kind"]:
            s = "*" + s
        if "VAR_KEYWORD" in p["kind"]:
            s = "**" + s
        if p.get("annotation"):
            s += f": {p['annotation']}"
        if p.get("default") is not None:
            s += f" = {p['default']}"
        parts.append(s)
    return f"{name}({', '.join(parts)})"


def make_docstring_row(class_name, export):
    full_doc = export.get("doc", {}).get("full")
    if not full_doc:
        return None
    return {
        "instruction": f"Read and memorize the full documentation for the `{class_name}` class in Manim.",
        "output": full_doc,
    }


def make_inheritance_row(class_name, export):
    bases = export.get("bases", [])
    output = ", ".join(bases)
    return {
        "instruction": f"List all the direct base (super) classes of the `{class_name}` class.",
        "output": output,
    }


def make_constructor_row(class_name, export):
    parameters = export.get("constructor", {}).get("parameters", [])
    if not parameters:
        return None
    return {
        "instruction": f"Memorize the exact constructor signature for the `{class_name}` class.",
        "output": format_signature(class_name, parameters),
    }


def make_method_row(class_name, method):
    method_name = method["name"]
    if method_name == "__init__" or method_name.startswith("_"):
        return None

    parameters = method.get("parameters", [])
    non_self = [p for p in parameters if p["name"] != "self"]

    if len(non_self) == 0:
        return {
            "instruction": f"What is the exact method name for `{method_name}` in the `{class_name}` class? (No parameters)",
            "output": method_name,
        }

    return {
        "instruction": f"Memorize the exact signature for the `{method_name}` method of the `{class_name}` class.",
        "output": format_signature(method_name, parameters),
    }


def task1_memorise(data):
    rows = []
    for name, info in data["exports"].items():
        if info["kind"] != "class":
            continue

        row = make_docstring_row(name, info)
        if row:
            rows.append(row)

        rows.append(make_inheritance_row(name, info))

        row = make_constructor_row(name, info)
        if row:
            rows.append(row)

        for method in info.get("methods", []):
            row = make_method_row(name, method)
            if row:
                rows.append(row)

    return rows


def save_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    with open("output/manim_kb.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    rows = task1_memorise(data)
    output_path = "output/sft_memorise.jsonl"
    save_jsonl(rows, output_path)
    print(f"Wrote {len(rows)} examples to {output_path}")

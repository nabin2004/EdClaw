import json
import random

from task1 import save_jsonl, task1_memorise

random.seed(42)


def generate_summarization_tasks(data):
    tasks = []
    for name, details in data["exports"].items():
        if details.get("kind") != "class":
            continue
        doc = details.get("doc", {})
        summary = doc.get("summary") or doc.get("full", "")
        if summary:
            tasks.append({
                "instruction": f"Summarize the purpose of the class `{name}` in Manim in one concise sentence.",
                "output": summary[:300],
            })
    return tasks


def generate_gist_tasks(data):
    tasks = []
    for name, details in data["exports"].items():
        if details.get("kind") != "class":
            continue
        methods = details.get("methods", [])
        method_names = [m["name"] for m in methods if not m["name"].startswith("_")]
        if method_names:
            gist = ", ".join(method_names[:5])
            tasks.append({
                "instruction": f"List the main methods of the class `{name}`.",
                "output": gist,
            })
    return tasks


def generate_nli_tasks(data):
    tasks = []
    all_classes = [
        c for c, d in data["exports"].items() if d.get("kind") == "class"
    ]

    for name, details in data["exports"].items():
        if details.get("kind") != "class":
            continue
        bases = details.get("bases", [])

        for base in bases:
            tasks.append({
                "instruction": f"Based on the Manim API, is it true that `{name}` inherits from `{base}`? Answer Yes or No.",
                "output": "Yes",
            })

        candidates = [c for c in all_classes if c != name and c not in bases]
        if candidates:
            for _ in range(min(2, len(candidates))):
                wrong_base = random.choice(candidates)
                candidates.remove(wrong_base)
                tasks.append({
                    "instruction": f"Based on the Manim API, is it true that `{name}` inherits from `{wrong_base}`? Answer Yes or No.",
                    "output": "No",
                })

    return tasks


def generate_fill_blank_tasks(data):
    tasks = []
    for name, details in data["exports"].items():
        if details.get("kind") != "class":
            continue

        constr = details.get("constructor")
        if constr and constr.get("parameters"):
            params = constr["parameters"]
            for p in params:
                if p.get("default") is not None:
                    tasks.append({
                        "instruction": f"Complete the constructor: `{name}({p['name']} = ____)`",
                        "output": p["default"],
                    })
                    break

        for method in details.get("methods", []):
            if method.get("parameters"):
                for p in method["parameters"]:
                    if p.get("default") is not None:
                        tasks.append({
                            "instruction": f"Complete the call: `{name}.{method['name']}({p['name']} = ____)`",
                            "output": p["default"],
                        })
                        break

    return tasks


def generate_multichoice_tasks(data):
    tasks = []
    class_methods = {}
    for name, details in data["exports"].items():
        if details.get("kind") == "class":
            methods = [
                m["name"]
                for m in details.get("methods", [])
                if not m["name"].startswith("_")
            ]
            class_methods[name] = methods

    for cls, methods in class_methods.items():
        if not methods:
            continue
        correct = random.choice(methods)
        all_methods = [m for m_list in class_methods.values() for m in m_list]
        wrong_options = [m for m in all_methods if m != correct and m not in methods]
        if len(wrong_options) < 2:
            continue
        options = random.sample(wrong_options, 2) + [correct]
        random.shuffle(options)
        tasks.append({
            "instruction": f"Which of the following is a valid method of the class `{cls}`? Options: " + ", ".join(options),
            "output": correct,
        })

    return tasks


def generate_bugfix_tasks(data):
    tasks = []
    bug_templates = [
        {
            "instruction": "Correct the following code that is supposed to rotate by 90 degrees, but it's missing a constant: `mobject.rotate(90)`",
            "output": "mobject.rotate(90 * DEGREES)",
        },
        {
            "instruction": "Correct the instantiation of a red circle. The code uses `fill_color` but the correct parameter is `color`.",
            "output": "circle = Circle(radius=2, color=RED)",
        },
    ]
    for template in bug_templates:
        tasks.append({
            "instruction": template["instruction"],
            "output": template["output"],
        })
    return tasks


def generate_teaching_tasks(data):
    tasks = []
    for name, details in data["exports"].items():
        if details.get("kind") != "class":
            continue
        doc = details.get("doc", {})
        summary = doc.get("summary") or doc.get("full", "")
        if summary:
            tasks.append({
                "instruction": f"Teach a beginner about the `{name}` class. Explain what it does and how to use it in a few sentences.",
                "output": summary[:300],
            })
    return tasks


def task2_comprehension(data):
    tasks = []
    tasks.extend(generate_summarization_tasks(data))
    tasks.extend(generate_gist_tasks(data))
    tasks.extend(generate_nli_tasks(data))
    return tasks


def task3_self_reflection(data):
    tasks = []
    tasks.extend(generate_fill_blank_tasks(data))
    tasks.extend(generate_multichoice_tasks(data))
    tasks.extend(generate_bugfix_tasks(data))
    tasks.extend(generate_teaching_tasks(data))
    return tasks


def generate_full_curriculum(data):
    tasks = []
    tasks.extend(task1_memorise(data))
    tasks.extend(task2_comprehension(data))
    tasks.extend(task3_self_reflection(data))
    return tasks


if __name__ == "__main__":
    with open("output/manim_kb.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    comprehension_rows = task2_comprehension(data)
    save_jsonl(comprehension_rows, "output/sft_comprehension.jsonl")
    print(f"Wrote {len(comprehension_rows)} examples to output/sft_comprehension.jsonl")

    reflection_rows = task3_self_reflection(data)
    save_jsonl(reflection_rows, "output/sft_self_reflection.jsonl")
    print(f"Wrote {len(reflection_rows)} examples to output/sft_self_reflection.jsonl")

    curriculum_rows = generate_full_curriculum(data)
    save_jsonl(curriculum_rows, "output/manim_curriculum.jsonl")
    print(f"Wrote {len(curriculum_rows)} examples to output/manim_curriculum.jsonl")
